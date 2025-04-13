"""This module contains unit tests for AB testing."""
import pytest
from flask import json
from website.models import ABTestAnalytics

def test_track_ab_test(client, app):
    """Test the /track-ab-test endpoint."""
    data = {
        "questionID": 3,
        "group": "A",
        "usedHint": True,
        "timeToSubmit": 20
    }

    # Send a POST request to track A/B test data
    response = client.post('/track-ab-test', json=data)

    # Check if the response status is success
    assert response.status_code == 201
    assert response.json['status'] == 'success'

@pytest.mark.usefixtures("sample_data")
def test_get_ab_test_data(client, app):
    """Test the /get-ab-test-data endpoint."""
    # Send a GET request to fetch A/B test data
    response = client.get('/get-ab-test-data')

    # Check if the response status is OK
    assert response.status_code == 200

    # Parse the returned data
    data = response.json

    # Verify the structure of the response
    assert 'aiUsage' in data
    assert 'assignments' in data
    assert 'hintImpact' in data