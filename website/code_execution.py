"""Methods for code execution"""
import json
import requests
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from website.models import Question, Submission
from website.extensions import db

code_exec_blueprint = Blueprint("code_exec", __name__)

CODE_EXECUTOR_URL = "https://code-runner-new.livelypebble-17c142a1.eastus.azurecontainerapps.io/run"

def execute_code_with_test(code, test_input, expected_method, language):
    """Runs code on a given test input and returns stdout, stderr, and the function result."""
    if language == "python":
        full_code = """
# Common imports for LeetCode problems
from typing import List, Dict, Tuple, Optional, Set
import collections
from collections import defaultdict, Counter, deque
import heapq
import bisect
import math
import functools

""" + code + f"""

# Test runner
import json
import sys
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

# Parse input
input_data = {test_input}

# Run solution
sol = Solution()
stdout_buffer = StringIO()
stderr_buffer = StringIO()

with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
    try:
        result = sol.{expected_method}(input_data)
    except Exception as e:
        print(f"{{type(e).__name__}}: {{str(e)}}", file=sys.stderr)
        result = None

# Format output
print(json.dumps({{
    "result": result,
    "stdout": stdout_buffer.getvalue(),
    "stderr": stderr_buffer.getvalue()
}}))
"""
    else:
        # Future support for other languages would go here
        return {
            "output": None,
            "stdout": None,
            "stderr": [f"Language '{language}' is not supported yet"]
        }

    # Call the remote code execution service
    payload = {
        "language": language,
        "code": full_code,
        "timeout": 5
    }

    try:
        response = requests.post(
            CODE_EXECUTOR_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code != 200:
            return {
                "output": None,
                "stdout": None,
                "stderr": [f"Code execution service error: {response.text}"]
            }

        # Parse the response
        result = response.json()
        output_text = result.get("output", "")

        # Try to extract our formatted result
        try:
            # Parse the JSON output from our test runner
            parsed_data = json.loads(output_text.strip())

            return {
                "output": parsed_data.get("result"),
                "stdout": parsed_data.get("stdout", "").split("\n") if parsed_data.get("stdout") else None,
                "stderr": parsed_data.get("stderr", "").split("\n") if parsed_data.get("stderr") else None
            }
        except json.JSONDecodeError:
            # If output is not valid JSON, return as plain output
            return {
                "output": None,
                "stdout": output_text.split("\n") if output_text else None,
                "stderr": None
            }

    except requests.RequestException as e:
        return {
            "output": None,
            "stdout": None,
            "stderr": [f"Request failed: {str(e)}"]
        }
    except Exception as e:
        return {
            "output": None,
            "stdout": None,
            "stderr": [f"Unexpected error: {str(e)}"]
        }

def run_tests(code, test_cases, expected_method, language):
    """Runs the given user code against question's test cases."""
    results = []
    all_passed = True

    for test in test_cases:
        execution_result = execute_code_with_test(code, test.inputData, expected_method, language)
        output = execution_result["output"]  # Extract function output
        expected = json.loads(test.expectedOutput)
        passed = output == expected

        results.append({
            "passed": passed,
            "input": test.inputData if test.isSample else "Hidden",
            "expected": test.expectedOutput if test.isSample else "Hidden",
            "output": output,
            "stdout": execution_result.get("stdout", []),
            "stderr": execution_result.get("stderr", [])
        })

        if not passed:
            all_passed = False

    return results, all_passed

@code_exec_blueprint.route("/run/<int:question_id>", methods=["POST"])
@login_required
def run_code_samples(question_id):
    """Runs user's code against sample test cases when called."""
    data = request.get_json()
    code = data.get("code")
    language = data.get("language", "python") #Default Py for now

    if not code:
        return jsonify({"error": "No code provided"}), 400

    try:
        question = Question.query.get_or_404(question_id)
        sample_tests = [test for test in question.testCases if test.isSample]
        results, all_passed = run_tests(code, sample_tests, question.expected_method, language)

        return jsonify({
            "passed": all_passed,
            "results": results
        })
    except Exception as e:
        return jsonify({"error": f"Error running sample tests: {str(e)}"}), 500

@code_exec_blueprint.route("/submit/<int:question_id>", methods=["POST"])
@login_required
def submit_solution(question_id):
    """Runs submitted code against test cases, returning results."""
    data = request.get_json()
    code = data.get("code")

    if not code:
        return jsonify({"error": "No code provided"}), 400

    question = Question.query.get_or_404(question_id)
    results, all_passed = run_tests(code, question.testCases, question.expected_method, language="python")

    try:
        submission = Submission(
            userID=current_user.userID,
            questionID=question_id,
            code=code,
            result="Passed" if all_passed else "Failed",
            language="python"
        )
        db.session.add(submission)
        db.session.commit()
    except Exception as e:
        return jsonify({"error": f"Failed to save submission: {str(e)}"}), 500

    return jsonify({
        "passed": all_passed,
        "results": results
    })
