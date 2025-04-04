import pytest
from website.profile import (
    get_solved_count,
    get_submissions,
    get_successful_submissions,
    get_mastery_score,
    get_badges,
    get_language_count,
    get_user_info,
    get_user_submissions
)
from website.models import User

def test_get_solved_count(sample_data, app):
    """Test the get_solved_count function."""
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        solved_count = get_solved_count(user.userID)
        assert solved_count == 1 

def test_get_submissions(sample_data, app):
    """Test the get_submissions function."""
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        submissions = get_submissions(user.userID)
        assert len(submissions) == 1
        assert submissions[0][1] == "Passed"

def test_get_successful_submissions(sample_data, app):
    """Test the get_successful_submissions function."""
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        successful_submissions = get_successful_submissions(user.userID)
        assert len(successful_submissions) == 1
        assert successful_submissions[0][1] == "Passed"

def test_get_mastery_score(sample_data, app):
    """Test the get_mastery_score function."""
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        mastery_score = get_mastery_score(user.userID)
        assert mastery_score == 0.5

def test_get_badges(sample_data, app):
    """Test the get_badges function."""
    with app.app_context():
        badges = get_badges()
        assert badges == 5

def test_get_language_count(sample_data, app):
    """Test the get_language_count function."""
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        language_count = get_language_count(user.userID)
        assert language_count == 1

def test_get_user_info(sample_data, app):
    """Test the get_user_info function."""
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        user_info = get_user_info(user.userID)
        assert user_info.username == "testuser"
        assert user_info.email == "test@example.com"

def test_get_user_submissions(sample_data, app):
    """Test the get_user_submissions function."""
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        user_submissions = get_user_submissions(user.userID)
        assert len(user_submissions) == 1
        assert user_submissions[0].result == "Passed"