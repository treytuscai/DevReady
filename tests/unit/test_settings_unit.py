import pytest
from werkzeug.security import generate_password_hash
from website.models import User
from website.extensions import db

@pytest.fixture
def login_test_user(client, test_user):
    """Log in the test user."""
    client.post("/login", data={"username": "testuser", "password": "password123"})
    return test_user

def test_change_email_success(client, app, login_test_user):
    response = client.post("/newEmail", data={"email": "new@example.com"}, follow_redirects=True)
    assert b"Your email has been updated successfully." in response.data

def test_change_email_same(client, app, login_test_user):
    response = client.post("/newEmail", data={"email": "test@example.com"}, follow_redirects=True)
    assert b"No changes were made to your email." in response.data

def test_change_email_duplicate(client, app, login_test_user):
    with app.app_context():
        db.session.add(User(
            username="otheruser",
            email="duplicate@example.com",
            passwordHash=generate_password_hash("irrelevant")
        ))
        db.session.commit()

    response = client.post("/newEmail", data={"email": "duplicate@example.com"}, follow_redirects=True)
    assert b"An account with that email already exists." in response.data

def test_change_password_success(client, app, login_test_user):
    response = client.post("/newPassword", data={
        "current_password": "password123",
        "new_password": "newsecurepass",
        "confirm_password": "newsecurepass"
    }, follow_redirects=True)
    assert b"Your password has been updated successfully." in response.data

def test_change_password_mismatch(client, app, login_test_user):
    response = client.post("/newPassword", data={
        "current_password": "password123",
        "new_password": "abc12345",
        "confirm_password": "abc54321"
    }, follow_redirects=True)
    assert b"New passwords do not match." in response.data

def test_change_password_wrong_current(client, app, login_test_user):
    response = client.post("/newPassword", data={
        "current_password": "wrongpassword",
        "new_password": "abc12345",
        "confirm_password": "abc12345"
    }, follow_redirects=True)
    assert b"Current password is incorrect." in response.data

def test_change_password_invalid_length(client, app, login_test_user):
    response = client.post("/newPassword", data={
        "current_password": "password123",
        "new_password": "short",
        "confirm_password": "short"
    }, follow_redirects=True)
    assert b"Password must be between 8 and 20 characters." in response.data