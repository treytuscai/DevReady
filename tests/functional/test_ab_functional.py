"""This module contains functional tests for AB testing."""
import pytest
from website.models import ABTestAnalytics

def test_track_ab_test(client):
    """Test the /track-ab-test endpoint to ensure data is added correctly."""
    data = {
        "questionID": 3,
        "group": "A",
        "usedHint": True,
        "timeToSubmit": 20
    }

    # Send a POST request to track A/B test data
    client.post('/track-ab-test', json=data)

    # Check if the data is in the database
    ab_entry = ABTestAnalytics.query.filter_by(questionID=3, group='A').first()
    assert ab_entry is not None
    assert ab_entry.usedHint == True
    assert ab_entry.timeToSubmit == 20

@pytest.mark.usefixtures("sample_data")
def test_get_ab_test_data(client):
    """Test the /get-ab-test-data endpoint to ensure data is returned correctly."""
    # Send a GET request to fetch A/B test data
    response = client.get('/get-ab-test-data')
    data = response.json

    # Verify that data contains the correct values (based on the sample data added in fixture)
    assert data['aiUsage']['A'] == 1
    assert data['aiUsage']['B'] == 0
    assert data['assignments']['A'] == 1
    assert data['assignments']['B'] == 1
    assert data['hintImpact']['A']['hint'] == 15
    assert data['hintImpact']['A']['noHint'] == 0
    assert data['hintImpact']['B']['hint'] == 0
    assert data['hintImpact']['B']['noHint'] == 10
