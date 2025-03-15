"""Functional tests for the auth API endpoints."""
import pytest
from werkzeug.security import check_password_hash
from website.models import User

@pytest.mark.usefixtures("test_user")
def test_login_success(client):
    """Test successful login with correct credentials."""
    response = client.post("/login", data={
        "username": "testuser",
        "password": "password123"
    })
    assert response.status_code == 302
    assert response.headers["Location"] == "/"

@pytest.mark.usefixtures("test_user")
def test_login_with_email(client):
    """Test successful login using email instead of username."""
    response = client.post("/login", data={
        "username": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 302
    assert response.headers["Location"] == "/"

@pytest.mark.usefixtures("test_user")
def test_login_wrong_password(client):
    """Test login with incorrect password."""
    response = client.post("/login", data={
        "username": "testuser",
        "password": "wrongpassword"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"The password you entered is incorrect" in response.data

@pytest.mark.usefixtures("test_user")
def test_login_nonexistent_user(client):
    """Test login with non-existent user."""
    with client:
        response = client.post("/login", data={
            "username": "nonexistent",
            "password": "password123"
        }, follow_redirects=True)
        assert response.status_code == 200
        html = response.data.decode()
        assert "We couldn&#39;t find an account with that email address." in html

@pytest.mark.usefixtures("test_user")
def test_register_success(client):
    """Test successful user registration."""
    response = client.post("/register", data={
        "username": "newuser",
        "email": "new@example.com",
        "password": "password123",
        "confirmPassword": "password123"
    })
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"

    with client.application.app_context():
        user = User.query.filter_by(username="newuser").first()
        assert user is not None
        assert user.email == "new@example.com"
        assert check_password_hash(user.passwordHash, "password123")

@pytest.mark.usefixtures("test_user")
def test_register_existing_email(client):
    """Test registration with an existing email."""
    response = client.post("/register", data={
        "username": "newuser",
        "email": "test@example.com",
        "password": "password123",
        "confirmPassword": "password123"
    })
    assert response.status_code == 302
    assert response.headers["Location"] == "/register"

@pytest.mark.usefixtures("test_user")
def test_register_existing_username(client):
    """Test registration with an existing username."""
    response = client.post("/register", data={
        "username": "testuser",
        "email": "new@example.com",
        "password": "password123",
        "confirmPassword": "password123"
    })
    assert response.status_code == 302
    assert response.headers["Location"] == "/register"

@pytest.mark.usefixtures("test_user")
def test_register_password_mismatch(client):
    """Test registration with mismatched passwords."""
    response = client.post("/register", data={
        "username": "newuser",
        "email": "new@example.com",
        "password": "password123",
        "confirmPassword": "password456"
    })
    assert response.status_code == 302
    assert response.headers["Location"] == "/register"

@pytest.mark.usefixtures("test_user")
def test_register_invalid_password_length(client):
    """Test registration with invalid password length."""
    response = client.post("/register", data={
        "username": "newuser",
        "email": "new@example.com",
        "password": "short",
        "confirmPassword": "short"
    })
    assert response.status_code == 302
    assert response.headers["Location"] == "/register"

@pytest.mark.usefixtures("test_user")
def test_logout(client):
    """Test user logout."""
    client.post("/login", data={
        "username": "testuser",
        "password": "password123"
    })
    response = client.get("/logout")
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"

def test_about_page(client):
    """Test accessing about page."""
    response = client.get("/about")
    assert response.status_code == 200
    assert b"Welcome" in response.data
    assert b"DevReady" in response.data

@pytest.mark.usefixtures("test_user")
def test_authenticated_redirects(client):
    """Test that authenticated users are redirected from auth pages."""
    client.post("/login", data={
        "username": "testuser",
        "password": "password123"
    })
    for route in ["/login", "/register", "/about"]:
        response = client.get(route)
        assert response.status_code == 302
        assert response.headers["Location"] == "/"
