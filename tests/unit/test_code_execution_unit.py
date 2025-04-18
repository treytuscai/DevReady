"""Unit tests for code execution API."""
from website.code_execution import execute_code_with_test
from unittest.mock import patch
import json

@patch('requests.post')
def test_execute_code_with_valid_input(mock_post):
    '''Mocking the test input and expected output for a valid case'''
    mock_response = type('MockResponse', (), {
        'status_code': 200,
        'json': lambda self: {"output": json.dumps({"result": 5, "stdout": None, "stderr": None})}
    })()
    mock_post.return_value = mock_response
    code = """class Solution:
    def number(self, num: int) -> int:
        return num"""
    test_input = '5'
    expected_method = "number"
    language = "python"

    result = execute_code_with_test(code, test_input, expected_method, language)

    # Checking if the result has no errors in stdout or stderr
    assert result["stderr"] is None
    assert result["stdout"] is None
    assert result["output"] == 5

@patch('requests.post')
def test_execute_code_with_invalid_input(mock_post):
    '''Mocking a case where the code raises an exception'''
    mock_response = type('MockResponse', (), {
        'status_code': 200,
        'json': lambda self: {"output": json.dumps({"result": None, "stdout": None, "stderr": ["Error: Method not found"]})}
    })()
    mock_post.return_value = mock_response

    code = """class Solution:
    def number(self, num: int) -> int:
        return num"""
    test_input = 'five'
    expected_method = "square_number"
    language = "python"

    result = execute_code_with_test(code, test_input, expected_method, language)

    # Checking if the error was captured in stderr
    assert result["stdout"] is None
    assert result["stderr"] is not None
    assert result["output"] is None

@patch('requests.post')
def test_execute_code_with_non_serializable_output(mock_post):
    '''Mocking a case where the output includes non-serializable types like deque'''
    mock_response = type('MockResponse', (), {
        'status_code': 200,
        'json': lambda self: {"output": json.dumps({"result": [5, 2, 3], "stdout": None, "stderr": None})}
    })()
    mock_post.return_value = mock_response

    code = """class Solution:
    def number(self, num: int) -> int:
        return deque([num, 2, 3])"""

    test_input = '5'
    expected_method = "number"
    language = "python"

    result = execute_code_with_test(code, test_input, expected_method, language)

    # Checking that the 'deque' was properly serialized to list
    expected_output = [5, 2, 3]
    assert result["stderr"] is None
    assert result["stdout"] is None
    assert result["output"] == expected_output
