"""Unit tests for code execution API."""
from website.code_execution import execute_code_with_test

def test_execute_code_with_valid_input():
    '''Mocking the test input and expected output for a valid case'''
    code = """class Solution:
    def number(self, num: int) -> int:
        return num"""
    test_input = '5'
    expected_method = "number"

    result = execute_code_with_test(code, test_input, expected_method)

    # Checking if the result has no errors in stdout or stderr
    assert result["stderr"] is None
    assert result["stdout"] is None
    assert result["output"] == 5

def test_execute_code_with_invalid_input():
    '''Mocking a case where the code raises an exception'''
    code = """class Solution:
    def number(self, num: int) -> int:
        return num"""
    test_input = 'five'
    expected_method = "square_number"

    result = execute_code_with_test(code, test_input, expected_method)

    # Checking if the error was captured in stderr
    assert result["stdout"] is None
    assert result["stderr"] is not None
    assert result["output"] is None

def test_execute_code_with_non_serializable_output():
    '''Mocking a case where the output includes non-serializable types like deque'''
    code = """class Solution:
    def number(self, num: int) -> int:
        return deque([num, 2, 3])"""

    test_input = '5'
    expected_method = "number"

    result = execute_code_with_test(code, test_input, expected_method)

    # Checking that the 'deque' was properly serialized to list
    expected_output = [5, 2, 3]
    assert result["stderr"] is None
    assert result["stdout"] is None
    assert result["output"] == expected_output
