"""This module contains functional tests for the AI."""
from unittest import mock
from flask import json

def test_provide_hint_success(client, app):
    """Test the /hint for successful hint response."""
    with app.app_context():
        with mock.patch('website.ai_helper.generate_response') as mock_generate_response:
            mock_generate_response.return_value = ("Hint!", None)

            # Send POST request to /hint
            response = client.post('/hint', json={
                "question_description": "test description",
                "code": "test code"
            })

            assert response.status_code == 200
            response_json = json.loads(response.data)
            assert response_json["success"] is True
            assert "hint" in response_json
            assert response_json["hint"] == "Hint!"

def test_provide_hint_error(client, app):
    """Test the /hint endpoint when there is an error generating the hint."""
    with app.app_context():
        with mock.patch('website.ai_helper.generate_response') as mock_generate_response:
            mock_generate_response.return_value = (None, "An unexpected error occurred.")

            # Send POST request to /hint_or_fake
            response = client.post('/hint', json={
                "question_description": "test description",
                "code": "test code"
            })

            assert response.status_code == 500
            response_json = json.loads(response.data)
            assert response_json["success"] is False
            assert response_json["error"] == "An unexpected error occurred."

def test_provide_hint_missing_desc_error(client, app):
    """Test the /hint endpoint when there is an error generating the hint due to a missing desc."""
    with app.app_context():
        with mock.patch('website.ai_helper.generate_response') as mock_generate_response:
            mock_generate_response.return_value = (None, "Missing question title or code")

            # Send POST request to /hint
            response = client.post('/hint', json={
                "question_description": None,
                "code": None
            })

            assert response.status_code == 400
            response_json = json.loads(response.data)
            assert response_json["success"] is False
            assert response_json["error"] == "Missing question title or code"

def test_analyze_success(client, app):
    """Test the /analyze_submission for successful analysis response."""
    with app.app_context():
        with mock.patch('website.ai_helper.generate_response') as mock_generate_response:
            mock_generate_response.return_value = ("Analysis!", None)

            # Send POST request to /analyze_submission
            response = client.post('/analyze_submission', json={
                "question_description": "test description",
                "code": "test code"
            })

            assert response.status_code == 200
            response_json = json.loads(response.data)
            assert response_json["success"] is True
            assert "analysis" in response_json
            assert response_json["analysis"] == "Analysis!"

def test_analyze_error(client, app):
    """Test the /analyze_submission endpoint when there is an error generating the analysis."""
    with app.app_context():
        with mock.patch('website.ai_helper.generate_response') as mock_generate_response:
            mock_generate_response.return_value = (None, "An unexpected error occurred.")

            # Send POST request to /analyze_submission
            response = client.post('/analyze_submission', json={
                "question_description": "test description",
                "code": "test code"
            })

            assert response.status_code == 500
            response_json = json.loads(response.data)
            assert response_json["success"] is False
            assert response_json["error"] == "An unexpected error occurred."

def test_analyze_missing_desc_error(client, app):
    """Test the /analyze_submission endpoint when there is an error generating the analysis."""
    with app.app_context():
        with mock.patch('website.ai_helper.generate_response') as mock_generate_response:
            mock_generate_response.return_value = (None, "Missing question title or code")

            # Send POST request to /analyze_submission
            response = client.post('/analyze_submission', json={
                "question_description": None,
                "code": None
            })

            assert response.status_code == 400
            response_json = json.loads(response.data)
            assert response_json["success"] is False
            assert response_json["error"] == "Missing question description or code"
