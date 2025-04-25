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
                # Prevent empty lines in list
                "stdout": [line for line in parsed_data.get("stdout", "").split("\n") if line]
                if parsed_data.get("stdout") else None,
                "stderr": [line for line in parsed_data.get("stderr", "").split("\n") if line]
                if parsed_data.get("stderr") else None
            }
        except json.JSONDecodeError:
            # If output is not valid JSON, return as plain output
            return {
                "output": None,
                "stdout": None,
                "stderr": [line for line in output_text.split("\n") if line]
                if output_text else None
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
        if needs_sorted_result(expected_method):
            if output and isinstance(output[0], list):
                output = sorted([sorted(inner) for inner in output], key=lambda x: (x[0], x[1], x[2]))
                expected = sorted([sorted(inner) for inner in expected], key=lambda x: (x[0], x[1], x[2]))
            else:
                output = sorted(output) if output else None
                expected = sorted(expected) if output else None
            
            
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
    is_linked_list = is_linked_list_question(expected_method)

    base_imports = """
# Common imports for LeetCode problems
from typing import List, Dict, Tuple, Optional, Set
import collections
from collections import defaultdict, Counter, deque
import heapq
import bisect
import math
import functools
"""

    linked_list_code = """
# LinkedList implementation for LinkedList problems
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
            
def list_to_linked_list(values):
    if not values:
        return None
    head = ListNode(values[0])
    current = head
    for val in values[1:]:
        current.next = ListNode(val)
        current = current.next
    return head
        
def linked_list_to_list(head):
    if head is None:
        return []
    result = []
    current = head
    while current:
        result.append(current.val)
        current = current.next
    return result
""" if is_linked_list else ""

    input_processing = """
# Process linked list inputs if needed
if isinstance(input_data, dict):
    # Check if any inputs are potential linked list values
    for key, value in input_data.items():
        if isinstance(value, list) and (key.endswith('head') or key == 'head' or key.endswith('list') or key.endswith('l1') or key.endswith('l2')):
            # Convert list to LinkedList
            input_data[key] = list_to_linked_list(value)
elif isinstance(input_data, list):
    # If it's a linked list question and input is a list, convert it
    input_data = list_to_linked_list(input_data)
""" if is_linked_list else ""

    output_processing = """
# Convert linked list results back to Python lists for comparison
if result is None:
    result = None  # Keep None as None
elif isinstance(result, ListNode):
    result = linked_list_to_list(result)
elif isinstance(result, list) and result and isinstance(result[0], ListNode):
    result = [linked_list_to_list(node) for node in result]
""" if is_linked_list else ""

    full_code = base_imports + linked_list_code + code + f"""
# Test runner
import json
import sys
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

# Parse input
input_data = {test_input}

{input_processing}

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

{output_processing}

# Format output
print(json.dumps({{
    "result": result,
    "stdout": stdout_buffer.getvalue(),
    "stderr": stderr_buffer.getvalue()
}}))
"""
    return full_code

def format_javascript(code, test_input, expected_method):
    """Format JavaScript submission with linked list support."""

    is_linked_list = is_linked_list_question(expected_method)

    # Define ListNode globally, before the IIFE
    global_linked_list_code = """
// Define ListNode globally so user code can access it
function ListNode(val, next) {
    this.val = (val === undefined ? 0 : val);
    this.next = (next === undefined ? null : next);
}
""" if is_linked_list else ""

    # Helper functions inside the IIFE
    linked_list_helpers = """
    // Helper functions for linked list operations
    function listToLinkedList(values) {
        if (!values || values.length === 0) {
            return null;
        }

        const head = new ListNode(values[0]);
        let current = head;
        
        for (let i = 1; i < values.length; i++) {
            current.next = new ListNode(values[i]);
            current = current.next;
        }

        return head;
    }

    function linkedListToList(head) {
        if (!head) {
            return [];
        }

        const result = [];
        let current = head;

        while (current) {
            result.push(current.val);
            current = current.next;
        }

        return result;
    }
""" if is_linked_list else ""

    js_input = json.dumps(test_input)

    # Add special handling for linked list problems
    linked_list_input_processing = """
    // Process linked list inputs
    if (typeof input === 'object' && input !== null) {
        for (const key in input) {
            if (Array.isArray(input[key]) && 
                (key === 'head' || key.endsWith('head') || key === 'l1' || key === 'l2' || key.endsWith('list'))) {
                input[key] = listToLinkedList(input[key]);
            }
        }
    } else if (Array.isArray(input)) {
        input = listToLinkedList(input);
    }
""" if is_linked_list else ""

    linked_list_output_processing = """
    // Convert linked list results back to arrays for JSON serialization
    if (result !== null && typeof result === 'object' && 'val' in result && 'next' in result) {
        result = linkedListToList(result);
    } else if (Array.isArray(result) && result.length > 0 && 
              result[0] && typeof result[0] === 'object' && 
              'val' in result[0] && 'next' in result[0]) {
        result = result.map(node => linkedListToList(node));
    } else {
    }
""" if is_linked_list else ""

    # Function call block with pattern matching
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

            # AddTwoNumbers (#2)
            elif expected_method.lower() == "addtwonumbers" and "l1" in input_data and "l2" in input_data:
                function_call_block = f"""
                if (typeof addTwoNumbers === 'function') {{
                    result = addTwoNumbers(input.l1, input.l2);
                }} else if (typeof Solution === 'function' && typeof (new Solution()).addTwoNumbers === 'function') {{
                    const solution = new Solution();
                    result = solution.addTwoNumbers(input.l1, input.l2);
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
                
            #4Sum (#18)
            elif expected_method.lower() == "foursum" and "nums" in input_data and "target" in input_data:
                function_call_block = f"""
                if (typeof fourSum === 'function') {{
                    result = fourSum(input.nums, input.target);
                }} else if (typeof Solution === 'function' && typeof (new Solution()).fourSum === 'function') {{
                    const solution = new Solution();
                    result = solution.fourSum(input.nums, input.target);
                }}"""
            
            # RemoveNthFromEnd (#19)
            elif expected_method.lower() == "removenthfromend" and "head" in input_data and "n" in input_data:
                function_call_block = f"""
                if (typeof removeNthFromEnd === 'function') {{
                    result = removeNthFromEnd(input.head, input.n);
                }} else if (typeof Solution === 'function' && typeof (new Solution()).removeNthFromEnd === 'function') {{
                    const solution = new Solution();
                    result = solution.removeNthFromEnd(input.head, input.n);
                }}"""

    except:
        pass

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
{global_linked_list_code}
// User submitted code:
{code}

// Test runner for JavaScript
(function() {{
{linked_list_helpers}

    const input = JSON.parse({js_input});
    let result = null;
    let stdout_capture = "";
    let stderr_capture = ""; 

    try {{
{linked_list_input_processing}

{function_call_block}
        else {{
            throw new Error(`Runtime Error: Function '{expected_method}' not found. Make sure it's defined as a global function, a method on a Solution class, or matches expected naming patterns.`);
        }}

{linked_list_output_processing}
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
    """Converts TypeScript to JavaScript with proper handling of linked‑list problems."""
    import re

    # 1.  Remove /** … */ comment blocks
    code = re.sub(r'/\*\*[\s\S]*?\*/', '', code)

    # 2. Strip generic type arguments, e.g.  Map<number,string>
    code = re.sub(r'<\s*[A-Za-z0-9_$,\s]*?>', '', code)

    # 3.  Remove return‑type annotations on free functions
    code = re.sub(
        r'function\s+([A-Za-z0-9_$]+)\s*\(\s*([^)]*?)\s*\)\s*:\s*[^{]+\{',
        lambda m: f'function {m.group(1)}({strip_param_types(m.group(2))}) {{',
        code
    )

    # 4.  Remove return‑type annotations on class/obj methods
    code = re.sub(
        r'(\s+)([A-Za-z0-9_$]+)\s*\(\s*([^)]*?)\s*\)\s*:\s*[^{]+\{',
        lambda m: f'{m.group(1)}{m.group(2)}({strip_param_types(m.group(3))}) {{',
        code
    )

    # 5.  Drop variable declarations that have a type but no initializer
    code = re.sub(
        r'(const|let|var)\s+([A-Za-z0-9_$]+)\s*:\s*[^=;]+;',
        r'\1 \2;',
        code
    )

    # 6.  Drop variable type annotations withinitializer
    code = re.sub(
        r'(const|let|var)\s+([A-Za-z0-9_$]+)\s*:\s*[^=;]+?(\s*=)',
        r'\1 \2\3',
        code
    )

    # 7.  Convert BigInt literals
    code = re.sub(r'(\d+)n', r'BigInt(\1)', code)

    # 8.  Remove “as” and non‑null assertions
    code = re.sub(r'\s+as\s+[A-Za-z0-9_$<>\[\],\s|&{}]+', '', code)
    code = re.sub(r'([A-Za-z0-9_$\.\(\)\[\]]+)!', r'\1', code)


    # Run the formatted code as JavaScript
    return format_javascript(code, test_input, expected_method)

def strip_param_types(params_str):
    """Helper function to strip type annotations from function parameters."""
    if not params_str.strip():
        return ""

    result = []
    params = params_str.split(',')

    for param in params:
        param_name = param.split(':', 1)[0].strip()
        result.append(param_name)

    return ', '.join(result)

def format_go(code, test_input, expected_method):
    """Format Go submission to handle Go's execution model with linked list support."""

    is_linked_list = is_linked_list_question(expected_method)

    # Define linked list structure and helper functions
    linked_list_code = """
// ListNode definition for linked list problems
type ListNode struct {
    Val int
    Next *ListNode
}

// Converts a slice of integers to a linked list
func sliceToLinkedList(values []int) *ListNode {
    if len(values) == 0 {
        return nil
    }

    head := &ListNode{Val: values[0]}
    current := head

    for i := 1; i < len(values); i++ {
        current.Next = &ListNode{Val: values[i]}
        current = current.Next
    }

    return head
}

// Converts a linked list back to a slice of integers
func linkedListToSlice(head *ListNode) []int {
    result := []int{}
    current := head

    for current != nil {
        result = append(result, current.Val)
        current = current.Next
    }

    return result
}
""" if is_linked_list else ""

    # Convert test_input to a Go-compatible string representation
    import json

    try:
        input_data = json.loads(test_input)
    except:
        input_data = test_input

    # Build a Go-compatible string for the input
    input_declaration = ""
    function_call = ""

    if is_linked_list and isinstance(input_data, dict):
        # Handle linked list specific inputs
        if "l1" in input_data and "l2" in input_data and expected_method.lower() == "addtwonumbers":
            # Add Two Numbers problem
            l1_values = input_data["l1"]
            l2_values = input_data["l2"]

            if isinstance(l1_values, list) and isinstance(l2_values, list):
                # Create linked lists from arrays
                input_declaration = f"""
    // Convert input arrays to linked lists
    l1Values := []int{{{', '.join(map(str, l1_values))}}}
    l2Values := []int{{{', '.join(map(str, l2_values))}}}
    l1 := sliceToLinkedList(l1Values)
    l2 := sliceToLinkedList(l2Values)
"""
                function_call = f"""
    // Call function and convert result to slice
    linkedListResult := {expected_method}(l1, l2)
    result := linkedListToSlice(linkedListResult)
"""
        elif "head" in input_data and "n" in input_data and expected_method.lower() == "removenthfromend":
            # Remove Nth From End problem
            head_values = input_data["head"]
            n_value = input_data["n"]

            if isinstance(head_values, list) and isinstance(n_value, int):
                input_declaration = f"""
    // Convert input array to linked list
    headValues := []int{{{', '.join(map(str, head_values))}}}
    head := sliceToLinkedList(headValues)
    n := {n_value}
"""
                function_call = f"""
    // Call function and convert result to slice
    linkedListResult := {expected_method}(head, n)
    result := linkedListToSlice(linkedListResult)
"""
    elif not is_linked_list:
        # Handle non-linked list inputs (your existing code)
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
            elif expected_method.lower() == "foursum" and "nums" in input_data and "target" in input_data:
                #4Sum (#18)
                nums = input_data["nums"]
                target = input_data["target"]
                if isinstance(nums, list) and all(isinstance(x, int) for x in nums):
                    input_declaration = f"nums := []int{{{', '.join(map(str, nums))}}}\ntarget := {target}"
                    function_call = f"result := fourSum(nums, target)"
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

{linked_list_code}

// User submitted code:
{code}

func main() {{
    // Set up test input
    {input_declaration}

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

def is_linked_list_question(expected_method):
    """Returns boolean indicating whether expected_method involves linked lists"""
    linked_list_questions = set(["addTwoNumbers", "removeNthFromEnd"])
    return expected_method in linked_list_questions


def needs_sorted_result(expected_method):
    """Returns boolean indicating whether expected_method requires sorted results"""
    sorted_methods = set(["threeSum", "fourSum", "twoSum", "letterCombinations"])
    return expected_method in sorted_methods