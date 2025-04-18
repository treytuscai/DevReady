"""Methods for code execution"""
import json
import re
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
        full_code = format_python(code, test_input, expected_method)
    elif language == "javascript":
        full_code = format_javascript(code, test_input, expected_method)
    elif language == "typescript":
        language = "javascript"
        full_code = execute_typescript_as_javascript(code, test_input, expected_method)
    elif language == "go":
        full_code = format_go(code, test_input, expected_method)
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
                "stdout": parsed_data.get("stdout", "").split("\n") 
                if parsed_data.get("stdout") else None,
                "stderr": parsed_data.get("stderr", "").split("\n") 
                if parsed_data.get("stderr") else None
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
        try:
            # Try to parse expected output as JSON
            expected = json.loads(test.expectedOutput)
        except json.JSONDecodeError:
            # If not valid JSON, use the raw string value
            expected = test.expectedOutput
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
    language = data.get("language", "python")

    if language == "js":
        language = "javascript"
    elif language == "ts":
        language = "typescript"
    else:
        language = language

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
    language = data.get("language", "python")

    if language == "js":
        language = "javascript"
    elif language == "ts":
        language = "typescript"
    else:
        language = language

    if not code:
        return jsonify({"error": "No code provided"}), 400

    question = Question.query.get_or_404(question_id)
    results, all_passed = run_tests(code,
                                    question.testCases,
                                    question.expected_method,
                                    language=language)

    try:
        submission = Submission(
            userID=current_user.userID,
            questionID=question_id,
            code=code,
            result="Passed" if all_passed else "Failed",
            language=language
        )
        db.session.add(submission)
        db.session.commit()
    except Exception as e:
        return jsonify({"error": f"Failed to save submission: {str(e)}"}), 500

    return jsonify({
        "passed": all_passed,
        "results": results
    })

def format_python(code, test_input, expected_method):
    """Format Python submission"""
    return """
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
        if isinstance(input_data, dict):
            result = sol.{expected_method}(**input_data)
        else:
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

def format_javascript(code, test_input, expected_method):
    """Format JavaScript submission to handle multiple JS function definition patterns."""

    js_input = json.dumps(test_input)
    
    # Add special handling for common problem types
    function_call_block = ""
    
    try:
        input_data = json.loads(test_input)
        
        if isinstance(input_data, dict):
            # TwoSum (#1)
            if expected_method.lower() == "twosum" and "nums" in input_data and "target" in input_data:
                function_call_block = f"""
                if (typeof twoSum === 'function') {{
                    result = twoSum(input.nums, input.target);
                }} else if (typeof Solution === 'function' && typeof (new Solution()).twoSum === 'function') {{
                    const solution = new Solution();
                    result = solution.twoSum(input.nums, input.target);
                }}"""
                
            # FindMedianSortedArrays (#4)
            elif expected_method.lower() == "findmediansortedarrays" and "nums1" in input_data and "nums2" in input_data:
                function_call_block = f"""
                if (typeof findMedianSortedArrays === 'function') {{
                    result = findMedianSortedArrays(input.nums1, input.nums2);
                }} else if (typeof Solution === 'function' && typeof (new Solution()).findMedianSortedArrays === 'function') {{
                    const solution = new Solution();
                    result = solution.findMedianSortedArrays(input.nums1, input.nums2);
                }}"""
                
            # ZigZag Conversion (#6)
            elif expected_method.lower() == "convert" and "s" in input_data and "numRows" in input_data:
                function_call_block = f"""
                if (typeof convert === 'function') {{
                    result = convert(input.s, input.numRows);
                }} else if (typeof Solution === 'function' && typeof (new Solution()).convert === 'function') {{
                    const solution = new Solution();
                    result = solution.convert(input.s, input.numRows);
                }}"""
                
            # Regular Expression Matching (#10)
            elif expected_method.lower() == "ismatch" and "s" in input_data and "p" in input_data:
                function_call_block = f"""
                if (typeof isMatch === 'function') {{
                    result = isMatch(input.s, input.p);
                }} else if (typeof Solution === 'function' && typeof (new Solution()).isMatch === 'function') {{
                    const solution = new Solution();
                    result = solution.isMatch(input.s, input.p);
                }}"""
                
            # 3Sum Closest (#16)
            elif expected_method.lower() == "threesumclosest" and "nums" in input_data and "target" in input_data:
                function_call_block = f"""
                if (typeof threeSumClosest === 'function') {{
                    result = threeSumClosest(input.nums, input.target);
                }} else if (typeof Solution === 'function' && typeof (new Solution()).threeSumClosest === 'function') {{
                    const solution = new Solution();
                    result = solution.threeSumClosest(input.nums, input.target);
                }}"""
    except:
        pass
            
            # If we didn't set a special function call block, use the default behavior
    if not function_call_block:
        function_call_block = f"""
        if (typeof {expected_method} === 'function') {{
            result = {expected_method}(input);
        }}
        else if (typeof Solution === 'function' && typeof (new Solution())['{expected_method}'] === 'function') {{
            const solution = new Solution();
            result = solution['{expected_method}'](input);
        }}
        else if (typeof {expected_method}Solution === 'function') {{
            result = {expected_method}Solution(input);
        }}"""
    
    formatted_code = f"""
// User submitted code:
{code}

// Test runner for JavaScript
(function() {{
    const input = JSON.parse({js_input});
    let result = null;
    let stdout_capture = "";
    let stderr_capture = ""; 

    try {{
        {function_call_block}
        else {{
            throw new Error(`Runtime Error: Function '{expected_method}' not found. Make sure it's defined as a global function, a method on a Solution class, or matches expected naming patterns.`);
        }}
    }} catch (e) {{
        stderr_capture = e.toString();
        result = null;
    }}
    
    console.log(JSON.stringify({{
        result: result,
        stdout: stdout_capture,
        stderr: stderr_capture
    }}));
}})();
"""
    return formatted_code



def execute_typescript_as_javascript(code, test_input, expected_method):
    """
    Converts TypeScript to JavaScript by stripping type annotations.
    Uses a regex to capture function declarations and then splits parameters
    on commas to remove each type annotation.
    """
    # Regex to capture function declaration with parameters and optional return type.
    function_pattern = re.compile(
        r'function\s+([a-zA-Z0-9_$]+)\s*\(\s*(.*?)\s*\)\s*(?::\s*[a-zA-Z0-9_$<>\[\],\s|&{}]+)?\s*\{',
        flags=re.DOTALL
    )

    def process_function_match(match):
        func_name = match.group(1)
        params = match.group(2)
        # Split parameters by comma and remove type annotations for each
        def strip_param(param):
            return re.sub(r'\s*:\s*.*', '', param).strip()
        param_list = [strip_param(p) for p in params.split(',') if p.strip()]
        new_params = ', '.join(param_list)
        return f'function {func_name}({new_params}) {{'

    # Apply the function signature stripping:
    js_code = function_pattern.sub(process_function_match, code)

    # Remove other type-level syntax:
    # 1. Object type annotations (e.g., "const obj: { [key: string]: number } = {}")
    js_code = re.sub(
        r'(const|let|var)\s+([a-zA-Z0-9_$]+)\s*:\s*\{\s*\[[^\]]+\]\s*:[^=]+\}\s*=',
        r'\1 \2 =',
        js_code
    )
    # 2. Variable declarations with types (e.g., "let x: number = ...")
    js_code = re.sub(
        r'(let|var|const)\s+([a-zA-Z0-9_$]+)\s*:\s*[a-zA-Z0-9_$<>\[\],\s|&{}]+\s*=',
        r'\1 \2 =',
        js_code
    )
    # 3. Class field declarations with types (e.g., "field: number;")
    js_code = re.sub(
        r'([a-zA-Z0-9_$]+)\s*:\s*[a-zA-Z0-9_$<>\[\],\s|&{}]+\s*;',
        r'\1;',
        js_code
    )
    # 4. Remove interface or type definitions entirely
    interface_type_pattern = re.compile(
        r'(interface|type)\s+[a-zA-Z0-9_$]+\s*(\{\s*[^}]*\}|\s*=\s*[^;]*);?',
        re.DOTALL
    )
    js_code = interface_type_pattern.sub('', js_code)
    # 5. Remove generic type annotations (e.g., "<number, string>")
    js_code = re.sub(r'<[a-zA-Z0-9_$<>\[\],\s|&{}]+>', '', js_code)
    # 6. Remove type assertions (e.g., "as SomeType")
    js_code = re.sub(r'\s+as\s+[a-zA-Z0-9_$<>\[\],\s|&{}]+', '', js_code)
    # 7. Remove non-null assertions (e.g., "variable!")
    js_code = re.sub(r'([a-zA-Z0-9_$\.\(\)\[\]]+)!', r'\1', js_code)

    # Now wrap the stripped code in our standard JavaScript test runner:
    return format_javascript(js_code, test_input, expected_method)

def format_go(code, test_input, expected_method):
    """Format Go submission to handle Go's execution model."""

    # Convert test_input to a Go-compatible string representation
    import json

    try:
        input_data = json.loads(test_input)
    except:
        input_data = test_input

    # Build a Go-compatible string for the input
    input_declaration = ""
    function_call = ""

    if isinstance(input_data, list):
        # Handle array/slice input
        if all(isinstance(x, int) for x in input_data):
            # Integer array
            input_declaration = f"input := []int{{{', '.join(map(str, input_data))}}}"
            function_call = f"result := {expected_method}(input)"
        elif all(isinstance(x, float) for x in input_data):
            # Float array
            input_declaration = f"input := []float64{{{', '.join(map(str, input_data))}}}"
            function_call = f"result := {expected_method}(input)"
        elif all(isinstance(x, str) for x in input_data):
            # String array
            string_elements = []
            for x in input_data:
                string_elements.append(f'\"{x}\"')
            input_declaration = f"input := []string{{{', '.join(string_elements)}}}"
            function_call = f"result := {expected_method}(input)"
        elif all(isinstance(x, list) for x in input_data):
            # 2D array/matrix
            if all(all(isinstance(y, int) for y in row) for row in input_data):
                # 2D int array
                rows = []
                for row in input_data:
                    rows.append(f"{{{', '.join(map(str, row))}}}")
                input_declaration = f"input := [][]int{{{', '.join(rows)}}}"
                function_call = f"result := {expected_method}(input)"
            else:
                # Generic 2D array - handle with interface{}
                input_declaration = "// Complex input structure, using JSON parsing"
                json_str = json.dumps(input_data)
                input_declaration += f"\ninputJSON := `{json_str}`"
                input_declaration += "\nvar input [][]interface{}"
                input_declaration += "\njson.Unmarshal([]byte(inputJSON), &input)"
                function_call = f"result := {expected_method}(input)"
    elif isinstance(input_data, dict):
        
        if expected_method.lower() == "twosum" and "nums" in input_data and "target" in input_data:
            #Two Sum (#1)
            nums = input_data["nums"]
            target = input_data["target"]
            if isinstance(nums, list) and all(isinstance(x, int) for x in nums):
                input_declaration = f"nums := []int{{{', '.join(map(str, nums))}}}\ntarget := {target}"
                function_call = f"result := {expected_method}(nums, target)"
        elif expected_method.lower() == "findmediansortedarrays" and "nums1" in input_data and "nums2" in input_data:
            #Find Median of Sorted Arrays (#4)
            nums1 = input_data["nums1"]
            nums2 = input_data["nums2"]
            if isinstance(nums1, list) and all(isinstance(x, int) for x in nums1) and isinstance(nums2, list) and all(isinstance(x, int) for x in nums2):
                input_declaration = f"nums1 := []int{{{', '.join(map(str, nums1))}}}\nnums2 := []int{{{', '.join(map(str, nums2))}}}"
                function_call = f"result := {expected_method}(nums1, nums2)"
                
        elif expected_method.lower() == "convert" and "s" in input_data and "numRows" in input_data:
            #Zigzag Conversion (#6)
            s = input_data["s"]
            numRows = input_data["numRows"]
            if isinstance(s, str) and isinstance(numRows, int):
                input_declaration = f"s := \"{s}\"\nnumRows := {numRows}"
                function_call = f"result := {expected_method}(s, numRows)"
        elif expected_method.lower() == "ismatch" and "s" in input_data and "p" in input_data:
            #Regular Expression Matching (#10)
            s = input_data["s"]
            p = input_data["p"]
            if isinstance(s, str) and isinstance(p, str):
                input_declaration = f"s := \"{s}\"\np := \"{p}\""
                function_call = f"result := isMatch(s, p)"
        elif expected_method.lower() == "threesumclosest" and "nums" in input_data and "target" in input_data:
            #3Sum Closest (#16)
            nums = input_data["nums"]
            target = input_data["target"]
            if isinstance(nums, list) and all(isinstance(x, int) for x in nums):
                input_declaration = f"nums := []int{{{', '.join(map(str, nums))}}}\ntarget := {target}"
                function_call = f"result := threeSumClosest(nums, target)"
        elif isinstance(input_data, int):
        # Single integer
            input_declaration = f"input := {input_data}"
            function_call = f"result := {expected_method}(input)"
            
    elif isinstance(input_data, float):
        # Single float
        input_declaration = f"input := {input_data}"
        function_call = f"result := {expected_method}(input)"
    elif isinstance(input_data, str):
        # Single string
        input_declaration = f"input := \"{input_data}\""
        function_call = f"result := {expected_method}(input)"
    else:
        # Generic fallback
        input_declaration = "// Complex or unknown input type, using JSON parsing"
        json_str = json.dumps(input_data) if input_data is not None else "null"
        input_declaration += f"\ninputJSON := `{json_str}`"
        input_declaration += "\nvar input interface{}"
        input_declaration += "\njson.Unmarshal([]byte(inputJSON), &input)"
        function_call = f"result := {expected_method}(input)"

    formatted_code = f"""
package main

import (
    "encoding/json"
    "fmt"
)

// User submitted code:
{code}

func main() {{
    // Set up test input
    {input_declaration}
    
    // Call user function
    {function_call}
    
    // Convert result to JSON for output
    resultJSON, err := json.Marshal(result)
    if err != nil {{
        fmt.Printf("{{\\\"stderr\\\": \\\"Error serializing result: %v\\\"}}", err)
        return
    }}
    
    // Output result in JSON format for test runner to parse
    fmt.Printf("{{\\\"result\\\": %s}}", resultJSON)
}}
"""
    return formatted_code

