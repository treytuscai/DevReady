import pytest
from flask import session
from website.models import User
from website.extensions import db
from werkzeug.security import check_password_hash


def login(client):
    """Helper function to log in the user."""
    return client.post("/login", data={"username": "testuser", 
                                       "password": "password123"}, 
                                       follow_redirects=True)

def test_change_email_success(client, app, sample_data):
    """tests a change email success"""
    login(client)
    response = client.post("/newEmail", data=
                           {"email": "newemail@example.com"},
                           follow_redirects=True)

    assert b"Your email has been updated successfully." in response.data
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        assert user.email == "newemail@example.com"

def test_change_email_same_as_current(client, app, sample_data):
    """test if the new email is the same as current"""
    login(client)
    response = client.post("/newEmail", data={"email": "test@example.com"}, follow_redirects=True)
    assert b"No changes were made to your email." in response.data

def test_change_email_blank(client, app, sample_data):
    """tests if the new email is blank"""
    login(client)
    response = client.post("/newEmail", data={"email": ""}, follow_redirects=True)
    assert b"All fields are required." in response.data

def test_change_password_blank(client, app, sample_data):
    """tests if the new password is blank"""
    login(client)
    response = client.post("/newPassword", data={
        "current_password": "password123",
        "new_password": "",
        "confirm_password": ""
        }, follow_redirects=True)

    assert b"All fields are required" in response.data

def test_change_email_duplicate(client, app, sample_data):
    """tests if the new email is already used"""
    with app.app_context():
        db.session.add(User(username="other", email="taken@example.com", passwordHash="..."))
        db.session.commit()

    login(client)
    response = client.post("/newEmail", data={"email": "taken@example.com"}, follow_redirects=True)
    assert b"An account with that email already exists." in response.data

def test_change_password_success(client, app, sample_data):
    """tests if he password was changed succesfully"""
    login(client)
    response = client.post("/newPassword", data={
        "current_password": "password",
        "new_password": "newpassword123",
        "confirm_password": "newpassword123"
    }, follow_redirects=True)
    assert b"Your password has been updated successfully." in response.data
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        assert check_password_hash(user.passwordHash, "newpassword123")

def test_change_password_wrong_current(client, sample_data):
    """tests if the current password entered is incorrect"""
    login(client)
    response = client.post("/newPassword", data={
        "current_password": "wrongpass",
        "new_password": "newpassword123",
        "confirm_password": "newpassword123"
    }, follow_redirects=True)
    assert b"Current password is incorrect." in response.data

def test_change_password_mismatch(client, sample_data):
    """tests if the confirm password is different"""
    login(client)
    response = client.post("/newPassword", data={
        "current_password": "password",
        "new_password": "abc12345",
        "confirm_password": "xyz98765"
    }, follow_redirects=True)
    assert b"New passwords do not match." in response.data

def test_change_password_length_invalid(client, sample_data):
    """tests if the new password is not the right"""
    login(client)
    response = client.post("/newPassword", data={
        "current_password": "password",
        "new_password": "short",
        "confirm_password": "short"
    }, follow_redirects=True)
    assert b"Password must be between 8 and 20 characters." in response.data
    