"""Functional tests for the code execution API."""
import pytest
from website.models import Question

@pytest.mark.usefixtures("sample_data")
def test_run_code_samples_success(client, app):
    """Test running code against sample test cases successfully."""
    with app.app_context():
        q1 = Question.query.filter_by(title="Sum Array").first()

        code = f"""class Solution:
            def {q1.expected_method}(self, args):
                return sum(args)
        """
        response = client.post(f"/run/{q1.questionID}", json={"code": code})
        data = response.get_json()

        assert response.status_code == 200
        assert data["passed"] is True
        assert len(data["results"]) == 1
        assert data["results"][0]["passed"] is True
        assert data["results"][0]["input"] == "[1, 2, 3]"
        assert data["results"][0]["expected"] == '6'

@pytest.mark.usefixtures("sample_data")
def test_run_code_samples_failure(client, app):
    """Test running incorrect code against sample test cases."""
    with app.app_context():
        q1 = Question.query.filter_by(title="Sum Array").first()

        code = f"""class Solution:
            def {q1.expected_method}(self, args):
                return sum(args) - 1
        """
        response = client.post(f"/run/{q1.questionID}", json={"code": code})
        data = response.get_json()

        assert response.status_code == 200
        assert data["passed"] is False
        assert data["results"][0]["passed"] is False

@pytest.mark.usefixtures("sample_data")
def test_submit_solution_success(client, app):
    """Test submitting a correct solution."""
    with app.app_context():
        q1 = Question.query.filter_by(title="Sum Array").first()

        code = f"""class Solution:
            def {q1.expected_method}(self, args):
                return sum(args)
        """
        response = client.post(f"/submit/{q1.questionID}", json={"code": code})
        data = response.get_json()

        assert response.status_code == 200
        assert data["passed"] is True
        assert len(data["results"]) == 2
        assert all(result["passed"] for result in data["results"])
        assert data["results"][1]["input"] == "Hidden"
        assert data["results"][1]["expected"] == "Hidden"
        assert data["results"][1]["output"] == 15

@pytest.mark.usefixtures("sample_data")
def test_code_execution_timeout(client, app):
    """Test handling of code that exceeds execution time limit."""
    with app.app_context():
        q1 = Question.query.filter_by(title="Sum Array").first()

        code = f"""class Solution:
        def {q1.expected_method}(self, args):
            x = 0
            while True:
                x += 1  # Infinite loop
        """
        response = client.post(f"/run/{q1.questionID}", json={"code": code})
        data = response.get_json()
        assert response.status_code == 500
        assert "Error running sample tests" in data["error"]

@pytest.mark.usefixtures("sample_data")
def test_missing_code(client, app):
    """Test handling of missing code in run request."""
    with app.app_context():
        q1 = Question.query.filter_by(title="Sum Array").first()
        response = client.post(f"/run/{q1.questionID}", json={})
        assert response.status_code == 400
        assert "No code provided" in response.get_json()["error"]

@pytest.mark.usefixtures("sample_data")
def test_invalid_question_id(client):
    """Test handling of non-existent question ID."""
    response = client.post("/run/999999", json={"code": "class Solution: pass"})
    assert response.status_code == 500
    assert "Error running sample tests" in response.get_json()["error"]

@pytest.mark.usefixtures("sample_data")
def test_submit_missing_code(client, app):
    """Test handling of missing code in submit request."""
    with app.app_context():
        q1 = Question.query.filter_by(title="Sum Array").first()
        response = client.post(f"/submit/{q1.questionID}", json={})
        assert response.status_code == 400
        assert "No code provided" in response.get_json()["error"]

@pytest.mark.usefixtures("sample_data")
def test_submit_solution_save_error(client, app, monkeypatch):
    """Test handling of error when saving submission."""
    with app.app_context():
        q1 = Question.query.filter_by(title="Sum Array").first()
        code = f"""class Solution:
        def {q1.expected_method}(self, args):
            return sum(args)
        """
        monkeypatch.setattr("website.extensions.db.session.commit",
                            lambda: (_ for _ in ()).throw(Exception("Commit error")))
        response = client.post(f"/submit/{q1.questionID}", json={"code": code})
        data = response.get_json()
        assert response.status_code == 500
        assert data["error"] == "Failed to save submission: Commit error"

@pytest.mark.usefixtures("sample_data")
def test_run_code_syntax_error(client, app):
    """Test handling of code with syntax error."""
    with app.app_context():
        q1 = Question.query.filter_by(title="Sum Array").first()
        code = f"""class Solution
        def {q1.expected_method}(self, args):
            return sum(args)
        """
        response = client.post(f"/run/{q1.questionID}", json={"code": code})
        data = response.get_json()
        assert response.status_code == 200
        assert data["passed"] is False

@pytest.mark.usefixtures("sample_data")
def test_run_code_unauthenticated(client, app):
    """Test that unauthenticated users cannot run code."""
    with app.app_context():
        with client.session_transaction() as sess:
            sess.clear()
        q1 = Question.query.filter_by(title="Sum Array").first()
        code = f"""class Solution:
            def {q1.expected_method}(self, args):
                return sum(args)
        """
        response = client.post(f"/run/{q1.questionID}", json={"code": code})
        assert response.status_code in (302, 401)

@pytest.mark.usefixtures("sample_data")
def test_submit_solution_unauthenticated(client, app):
    """Test that unauthenticated users cannot submit solutions."""
    with app.app_context():
        with client.session_transaction() as sess:
            sess.clear()
        q1 = Question.query.filter_by(title="Sum Array").first()
        code = f"""class Solution:
            def {q1.expected_method}(self, args):
                return sum(args)
        """
        response = client.post(f"/submit/{q1.questionID}", json={"code": code})
        assert response.status_code in (302, 401)
