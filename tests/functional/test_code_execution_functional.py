# test_code_execution_unit.py

import pytest
import json
from unittest.mock import patch, MagicMock

from website.code_execution import (
    execute_code_with_test,
    run_tests,
    format_python,
    format_javascript,
    execute_typescript_as_javascript,
    format_go
)
from collections import namedtuple

TestCaseStub = namedtuple("TestCaseStub", ["inputData", "expectedOutput", "isSample"])

@pytest.fixture
def mock_requests_post():
    """
    A pytest fixture that patches requests.post and returns a mock object.
    You can control the .json() return value and the .status_code, etc.
    """
    with patch("website.code_execution.requests.post") as mock_post:
        yield mock_post

def test_execute_code_with_test_python_success(mock_requests_post):
    """
    Tests a successful Python code execution where the service
    returns valid JSON with result, stdout, stderr.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "output": json.dumps({
            "result": 42,
            "stdout": "some standard output",
            "stderr": ""
        })
    }
    mock_requests_post.return_value = mock_response

    code = "class Solution:\n    def testMethod(self, x):\n        return x * 2"
    result = execute_code_with_test(code, "21", "testMethod", "python")
    
    assert result["output"] == 42
    assert result["stdout"] == ["some standard output"]
    assert result["stderr"] == [] or result["stderr"] is None

def test_execute_code_with_test_javascript_success(mock_requests_post):
    """
    Tests a successful JavaScript code execution.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "output": json.dumps({
            "result": "JS Output",
            "stdout": "",
            "stderr": ""
        })
    }
    mock_requests_post.return_value = mock_response

    code = "function testMethod(x){ return 'JS Output'; }"
    result = execute_code_with_test(code, "\"test input\"", "testMethod", "javascript")

    assert result["output"] == "JS Output"
    assert result["stderr"] == [] or result["stderr"] is None
    assert result["stdout"] == [] or result["stdout"] is None

def test_execute_code_with_test_typescript_success(mock_requests_post):
    """
    Tests a successful TypeScript code execution (run as stripped JS).
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "output": json.dumps({
            "result": "TS Output",
            "stdout": "",
            "stderr": ""
        })
    }
    mock_requests_post.return_value = mock_response

    ts_code = """
    function testMethod(x: string): string {
        return 'TS Output';
    }
    """
    result = execute_code_with_test(ts_code, "\"test input\"", "testMethod", "typescript")

    assert result["output"] == "TS Output"

def test_execute_code_with_test_go_success(mock_requests_post):
    """
    Tests a successful Go code execution.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "output": json.dumps({
            "result": "Go Output",
            "stdout": "",
            "stderr": ""
        })
    }
    mock_requests_post.return_value = mock_response

    go_code = """
    func testMethod(x int) int {
        return x + 1
    }
    """
    result = execute_code_with_test(go_code, "41", "testMethod", "go")

    assert result["output"] == "Go Output"
    assert result["stderr"] == [] or result["stderr"] is None
    assert result["stdout"] == [] or result["stdout"] is None

def test_execute_code_with_test_unsupported_language():
    """
    Tests that an unsupported language returns a dict with an error in 'stderr'.
    """
    code = "function test(){ return 1; }"
    result = execute_code_with_test(code, "{}", "testMethod", "rust")
    assert result["output"] is None
    assert "Language 'rust' is not supported yet" in result["stderr"][0]

def test_execute_code_with_test_non_200_response(mock_requests_post):
    """
    Tests handling a non-200 response status from the remote code executor.
    """
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal server error"
    mock_requests_post.return_value = mock_response

    code = "class Solution:\n    def testMethod(self, x):\n        return x"
    result = execute_code_with_test(code, "123", "testMethod", "python")

    assert result["output"] is None
    assert result["stdout"] is None
    assert "Code execution service error: Internal server error" in result["stderr"][0]

def test_execute_code_with_test_non_json_output(mock_requests_post):
    """
    Tests handling a response that is 200 but not valid JSON in the "output" field.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "output": "This is not valid JSON"
    }
    mock_requests_post.return_value = mock_response

    code = "class Solution:\n    def testMethod(self, x):\n        return x"
    result = execute_code_with_test(code, "123", "testMethod", "python")

    assert result["output"] is None
    assert result["stdout"] == ["This is not valid JSON"]
    assert result["stderr"] is None 

def test_run_tests_all_passed():
    """
    Tests run_tests when all test cases pass.
    """
    code = "class Solution:\n    def sumArray(self, arr):\n        return sum(arr)"
    with patch("website.code_execution.execute_code_with_test") as mock_exec:
        mock_exec.return_value = {
            "output": 6, 
            "stdout": [], 
            "stderr": []
        }
        test_cases = [
            TestCaseStub("[1, 2, 3]", "6", True),
            TestCaseStub("[4, 2]", "6", False)
        ]
        results, all_passed = run_tests(code, test_cases, "sumArray", "python")
    
    assert all_passed is True
    assert all(r["Passed"] for r in results)
    assert len(results) == 2

def test_run_tests_some_failed():
    """
    Tests run_tests when one test fails.
    """
    code = "class Solution:\n    def sumArray(self, arr):\n        return sum(arr)"
    def side_effect(*args, **kwargs):
        input_data = args[1]
        if input_data == "[1, 2, 3]":
            return {"output": 6, "stdout": [], "stderr": []}
        else:
            return {"output": 100, "stdout": [], "stderr": []}

    with patch("website.code_execution.execute_code_with_test", side_effect=side_effect):
        test_cases = [
            TestCaseStub("[1, 2, 3]", "6", True),
            TestCaseStub("[4, 5]", "9", False)
        ]
        results, all_passed = run_tests(code, test_cases, "sumArray", "python")
    
    assert all_passed is False
    assert results[0]["Passed"] is True
    assert results[1]["Passed"] is False

def test_format_python():
    """
    Tests format_python.
    """
    code = "class Solution:\n    def foo(self, x): return x"
    formatted = format_python(code, "123", "foo")
    assert "class Solution:" in formatted
    assert "foo" in formatted
    assert "123" in formatted
    assert "redirect_stdout" in formatted

def test_format_javascript():
    """
    Tests format_javascript.
    """
    code = "function foo(x){ return x + 1; }"
    formatted = format_javascript(code, "5", "foo")
    assert "function foo(x){ return x + 1; }" in formatted
    assert "foo" in formatted
    assert "JSON.parse(\"5\")" in formatted

def test_execute_typescript_as_javascript():
    """
    Tests execute_typescript_as_javascript.
    """
    ts_code = """
    function foo(x: number): number {
        return x + 1;
    }
    """
    formatted = execute_typescript_as_javascript(ts_code, "5", "foo")
    assert "number" not in formatted
    assert "foo" in formatted

def test_format_go():
    """
    Tests format_go.
    """
    go_code = """
    func foo(arr []int) int {
        sum := 0
        for _, val := range arr {
            sum += val
        }
        return sum
    }
    """
    formatted = format_go(go_code, "[1,2,3]", "foo")
    assert "func foo(arr []int)" in formatted
    assert "1, 2, 3" in formatted
    assert "json.Marshal(result)" in formatted
    assert "resultJSON" in formatted
