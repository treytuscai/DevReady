"""Methods for code execution"""
import os
import subprocess
import tempfile
import shutil
import json
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from website.models import Question, Submission
from website.extensions import db

code_exec_blueprint = Blueprint("code_exec", __name__)

def execute_code_with_test(code, test_input, expected_method):
    """Runs code on a given test input and returns stdout, stderr, and the function result."""
    temp_dir = tempfile.mkdtemp()
    try:
        imports = (
            "from typing import List, Dict, Tuple, Set, Deque\n"
            "import math\n"
            "import heapq\n"
            "import bisect\n"
            "import collections\n"
            "from collections import deque, Counter, defaultdict, OrderedDict, namedtuple\n"
            "import itertools\n"
            "import string\n"
            "import re\n"
            "import random\n"
            "import time\n"
            "import sys\n"
            "import json\n"
            "import functools\n"
            "import operator\n"
        )

        runner = (
            "\nif __name__ == '__main__':\n"
            "    import sys, json, io\n"
            "    from contextlib import redirect_stdout, redirect_stderr\n"
            "    data = sys.stdin.read().strip()\n"
            "    args = json.loads(data)\n"
            "    sol = Solution()\n"
            "    f_stdout = io.StringIO()\n"
            "    f_stderr = io.StringIO()\n"
            "    with redirect_stdout(f_stdout), redirect_stderr(f_stderr):\n"
            f"        try:\n"
            f"            output = sol.{expected_method}(args)\n"
            f"        except Exception as e:\n"
            f"            type = str(type(e).__name__)\n"
            f"            print(type + ': ' + str(e), file=sys.stderr)\n"
            f"            output = None\n"
            "    printed_output = f_stdout.getvalue().strip()\n"
            "    error_output = f_stderr.getvalue().strip()\n"
            "    output_data = {\n"
            "        'stdout': printed_output.split('\\n') if printed_output else None,\n"
            "        'stderr': error_output.split('\\n') if error_output else None,\n"
            "        'output': output\n"
            "    }\n"
            "    # Ensure all values in output_data are serializable\n"
            "    def convert_to_serializable(obj):\n"
            "        if isinstance(obj, set):\n"
            "            return list(obj)  # Convert sets to lists\n"
            "        elif isinstance(obj, deque):\n"
            "            return list(obj)  # Convert deque to list\n"
            "        elif isinstance(obj, frozenset):\n"
            "            return list(obj)  # Convert frozenset to list (or set if you prefer)\n"
            "        elif isinstance(obj, dict):\n"
            "            return {key: convert_to_serializable(value) for key, value in obj.items()}\n"
            "        elif isinstance(obj, list):\n"
            "            return [convert_to_serializable(item) for item in obj]\n"
            "        else:\n"
            "            return obj\n"
            "    # Apply the serialization function to output_data\n"
            "    output_data = convert_to_serializable(output_data)\n"
            "    print(json.dumps(output_data))\n"
        )

        full_code = imports + code + runner
        code_file = os.path.join(temp_dir, "solution.py")

        with open(code_file, "w", encoding="utf-8") as f:
            f.write(full_code)

        process = subprocess.run(
            ["python3", code_file],
            input=test_input,
            capture_output=True,
            text=True,
            timeout=5
        )

        # Capture stdout and stderr from the subprocess
        if process.returncode != 0:
            error_message = process.stderr.strip()
            error_message = error_message.split(":", 1)[-1].strip()
            output_data = {
                'stdout': None,
                'stderr': error_message.split('\n'),
                'output': None
            }
        else:
            output_data = json.loads(process.stdout.strip())
        return output_data

    finally:
        shutil.rmtree(temp_dir)

def run_tests(code, test_cases, expected_method):
    """Runs the given user code against question's test cases."""
    results = []
    all_passed = True

    for test in test_cases:
        execution_result = execute_code_with_test(code, test.inputData, expected_method)
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

    if not code:
        return jsonify({"error": "No code provided"}), 400

    try:
        question = Question.query.get_or_404(question_id)
        sample_tests = [test for test in question.testCases if test.isSample]
        results, all_passed = run_tests(code, sample_tests, question.expected_method)

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
    results, all_passed = run_tests(code, question.testCases, question.expected_method)

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
