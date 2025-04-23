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
    format_go,
    is_linked_list_question,
    run_code_samples
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
    assert result["stdout"] is None
    assert result["stderr"] == ["This is not valid JSON"]

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
    assert all(r["passed"] for r in results)
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
    assert results[0]["passed"] is True
    assert results[1]["passed"] is False
    
    
def test_run_tests_with_non_json_expected():
    """
    Tests run_tests when expectedOutput is not valid JSON.
    """
    code = "class Solution:\n    def addTwoNumbers(self, l1, l2):\n        return 'hello'"
    
    test_cases = [
        TestCaseStub("[1, 2, 3]", "hello", True)
    ]
    
    with patch("website.code_execution.execute_code_with_test") as mock_exec:
        mock_exec.return_value = {
            "output": "hello",
            "stdout": [],
            "stderr": []
        }
        
        results, all_passed = run_tests(code, test_cases, "addTwoNumbers", "python")
    
    assert all_passed is True
    assert results[0]["passed"] is True
    assert results[0]["expected"] == "hello"
    
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


def test_format_javascript_linked_list():
    """
    Tests format_javascript with linked list input.
    """
    code = """
    function addTwoNumbers(l1, l2) {
        return l1 + l2;
    }
    """
    formatted = format_javascript(code, {"l1": [4,5,6], "l2": [1,2,3]}, "addTwoNumbers")
    assert "function addTwoNumbers(l1, l2)" in formatted
    assert "1, 2, 3" in formatted
    assert "4, 5, 6" in formatted

def test_format_go_linked_list():
    """
    Tests format_go with linked list input.
    """
    code = """
    func addTwoNumbers(l1, l2) int {
        return l1 + l2;
    }
    """
    formatted = format_go(code, {"l1": [4,5,6], "l2": [1,2,3]}, "addTwoNumbers")
    assert "func addTwoNumbers(l1, l2)" in formatted
    assert "4, 5, 6" in formatted

def test_is_linked_list_question_true():
    """
    Tests is_linked_list_question.
    """
    assert is_linked_list_question("addTwoNumbers") is True
    assert is_linked_list_question("removeNthFromEnd") is True
    
def test_is_linked_list_question_false():
    """
    Tests is_linked_list_question.
    """
    assert is_linked_list_question("twoSum") is False
    assert is_linked_list_question("maxArea") is False
    assert is_linked_list_question("longestPalindrome") is False
    
def test_format_go_two_sum():
    """
    Tests format_go with two sum.
    """
    code = """
    func twoSum(nums []int, target int) []int {
        for i := 0; i < len(nums); i++ {
            for j := i + 1; j < len(nums); j++ {
                if nums[i] + nums[j] == target {
                    return []int{i, j}
                }
            }
        }
        return []int{}
    }
    """
    formatted = format_go(code, {"nums": [2,7,11,15], "target": 9}, "twoSum")
    assert "func twoSum(nums []int, target int)" in formatted
    assert "2, 7, 11, 15" in formatted
    assert "9" in formatted
    
def test_format_javascript_two_sum():
    """
    Tests format_javascript with two sum.
    """
    code = """
    function twoSum(nums, target) {
        return nums.reduce((acc, num, index) => {
            const complement = target - num;
            if (acc.hasOwnProperty(complement)) {
                return [acc[complement], index];
            }
            acc[num] = index;
            return acc;
        }, {});
    }
    """
    formatted = format_javascript(code, {"nums": [2,7,11,15], "target": 9}, "twoSum")
    assert "function twoSum(nums, target)" in formatted
    assert "2, 7, 11, 15" in formatted
    assert "9" in formatted

def test_execute_typescript_as_javascript_two_sum():
    """
    Tests execute_typescript_as_javascript with two sum.
    """
    code = """
    function twoSum(nums: number[], target: number): number[] {
        const map = new Map<number, number>();
        for (let i = 0; i < nums.length; i++) {
            const complement = target - nums[i];
            if (map.has(complement)) {
                return [map.get(complement), i];
            }
            map.set(nums[i], i);
        }
        return [];
    }
    """ 
    formatted = execute_typescript_as_javascript(code, {"nums": [2,7,11,15], "target": 9}, "twoSum")
    assert "function twoSum(nums, target)" in formatted
    assert "2, 7, 11, 15" in formatted
    assert "9" in formatted

def test_format_go_basic_integer_array():
    """Tests format_go with a basic integer array input."""
    code = """
    func sumArray(nums []int) int {
        sum := 0
        for _, num := range nums {
            sum += num
        }
        return sum
    }
    """
    formatted = format_go(code, [1, 2, 3], "sumArray")
    assert "input := []int{1, 2, 3}" in formatted
    assert "result := sumArray(input)" in formatted
    assert "package main" in formatted
    assert "encoding/json" in formatted

def test_format_go_float_array():
    """Tests format_go with float array input."""
    code = """
    func average(nums []float64) float64 {
        sum := 0.0
        for _, num := range nums {
            sum += num
        }
        return sum / float64(len(nums))
    }
    """
    formatted = format_go(code, [1.5, 2.5, 3.5], "average")
    assert "input := []float64{1.5, 2.5, 3.5}" in formatted
    assert "result := average(input)" in formatted

def test_format_go_string_array():
    """Tests format_go with string array input."""
    code = """
    func joinStrings(strs []string) string {
        return strings.Join(strs, ",")
    }
    """
    formatted = format_go(code, ["hello", "world"], "joinStrings")
    assert 'input := []string{"hello", "world"}' in formatted
    assert "result := joinStrings(input)" in formatted

def test_format_go_2d_integer_array():
    """Tests format_go with 2D integer array input."""
    code = """
    func matrixSum(matrix [][]int) int {
        sum := 0
        for _, row := range matrix {
            for _, val := range row {
                sum += val
            }
        }
        return sum
    }
    """
    formatted = format_go(code, [[1, 2], [3, 4]], "matrixSum")
    assert "input := [][]int{{1, 2}, {3, 4}}" in formatted
    assert "result := matrixSum(input)" in formatted

def test_format_go_linked_list():
    """Tests format_go with linked list input."""
    code = """
    func addTwoNumbers(l1 *ListNode, l2 *ListNode) *ListNode {
        return l1
    }
    """
    test_input = {"l1": [1, 2, 3], "l2": [4, 5, 6]}
    formatted = format_go(code, test_input, "addTwoNumbers")
    assert "type ListNode struct" in formatted
    assert "l1Values := []int{1, 2, 3}" in formatted
    assert "l2Values := []int{4, 5, 6}" in formatted
    assert "sliceToLinkedList" in formatted
    assert "linkedListToSlice" in formatted

def test_format_go_two_sum():
    """Tests format_go with two sum problem input."""
    code = """
    func twoSum(nums []int, target int) []int {
        return []int{0, 1}
    }
    """
    test_input = {"nums": [2, 7, 11, 15], "target": 9}
    formatted = format_go(code, test_input, "twoSum")
    assert "nums := []int{2, 7, 11, 15}" in formatted
    assert "target := 9" in formatted
    assert "result := twoSum(nums, target)" in formatted

def test_format_go_remove_nth_from_end():
    """Tests format_go with removeNthFromEnd problem."""
    code = """
    func removeNthFromEnd(head *ListNode, n int) *ListNode {
        return head
    }
    """
    test_input = {"head": [1, 2, 3, 4, 5], "n": 2}
    formatted = format_go(code, test_input, "removeNthFromEnd")
    assert "type ListNode struct" in formatted
    assert "headValues := []int{1, 2, 3, 4, 5}" in formatted
    assert "n := 2" in formatted
    assert "sliceToLinkedList" in formatted
    assert "linkedListToSlice" in formatted

def test_format_go_single_string():
    """Tests format_go with single string input."""
    code = """
    func reverseString(s string) string {
        return s
    }
    """
    formatted = format_go(code, "hello", "reverseString")
    assert 'input := "hello"' in formatted
    assert "result := reverseString(input)" in formatted

def test_format_go_find_median_sorted_arrays():
    """Tests format_go with findMedianSortedArrays problem."""
    code = """
    func findMedianSortedArrays(nums1 []int, nums2 []int) float64 {
        return 2.0
    }
    """
    test_input = {"nums1": [1, 3], "nums2": [2, 4]}
    formatted = format_go(code, test_input, "findMedianSortedArrays")
    assert "nums1 := []int{1, 3}" in formatted
    assert "nums2 := []int{2, 4}" in formatted
    assert "result := findMedianSortedArrays(nums1, nums2)" in formatted

def test_format_go_zigzag_conversion():
    """Tests format_go with convert (zigzag) problem."""
    code = """
    func convert(s string, numRows int) string {
        return s
    }
    """
    test_input = {"s": "PAYPALISHIRING", "numRows": 3}
    formatted = format_go(code, test_input, "convert")
    assert 's := "PAYPALISHIRING"' in formatted
    assert "numRows := 3" in formatted
    assert "result := convert(s, numRows)" in formatted

def test_format_go_regular_expression_matching():
    """Tests format_go with isMatch (regex) problem."""
    code = """
    func isMatch(s string, p string) bool {
        return true
    }
    """
    test_input = {"s": "aa", "p": "a*"}
    formatted = format_go(code, test_input, "isMatch")
    assert 's := "aa"' in formatted
    assert 'p := "a*"' in formatted
    assert "result := isMatch(s, p)" in formatted

def test_format_go_three_sum_closest():
    """Tests format_go with threeSumClosest problem."""
    code = """
    func threeSumClosest(nums []int, target int) int {
        return target
    }
    """
    test_input = {"nums": [-1, 2, 1, -4], "target": 1}
    formatted = format_go(code, test_input, "threeSumClosest")
    assert "nums := []int{-1, 2, 1, -4}" in formatted
    assert "target := 1" in formatted
    assert "result := threeSumClosest(nums, target)" in formatted

def test_format_go_single_integer():
    """Tests format_go with single integer input."""
    code = """
    func square(n int) int {
        return n * n
    }
    """
    test_input = {"value": 5}
    formatted = format_go(code, test_input, "square")
    assert "func square" in formatted
    assert "fmt" in formatted

def test_format_go_single_float():
    """Tests format_go with single float input."""
    code = """
    func double(n float64) float64 {
        return n * 2.0
    }
    """
    formatted = format_go(code, 3.14, "double")
    assert "input := 3.14" in formatted
    assert "result := double(input)" in formatted

def test_format_go_null_input():
    """Tests format_go with null input."""
    code = """
    func handleNull(data interface{}) interface{} {
        return nil
    }
    """
    formatted = format_go(code, None, "handleNull")
    assert "var input interface{}" in formatted
    assert "result := handleNull(input)" in formatted