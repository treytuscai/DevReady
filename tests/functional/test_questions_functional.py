"""Functional tests for the questions API endpoints."""
import pytest
from website.models import Question, TestCase, QuestionTag
from website.extensions import db

@pytest.mark.usefixtures("sample_data")
def test_get_all_questions(client) -> None:
    """Test getting all questions endpoint."""
    response = client.get("/questions")
    assert response.status_code == 200
    data = response.json
    assert len(data) == 2

    assert data[0]["title"] == "Sum Array"
    assert data[0]["description"] == "Find the sum of array elements"
    assert data[0]["difficulty"] == "easy"
    assert data[0]["tags"] == ["arrays"]
    assert len(data[0]["sample_test_cases"]) == 1
    assert data[0]["sample_test_cases"][0]["input"] == "[1, 2, 3]"
    assert data[0]["sample_test_cases"][0]["expected_output"] == '6'

    assert data[1]["title"] == "Reverse String"
    assert data[1]["description"] == "Reverse the given string"
    assert data[1]["tags"] == ["arrays", "strings"]

@pytest.mark.usefixtures("sample_data")
def test_get_question_by_id(client) -> None:
    """Test getting a specific question by ID."""
    response = client.get("/questions/1")
    assert response.status_code == 200

    assert b"Sum Array" in response.data
    assert b"arrays" in response.data

    response = client.get("/questions/999")
    assert response.status_code == 404
    assert response.json["error"] == "Question not found"

@pytest.mark.usefixtures("sample_data")
def test_get_questions_by_tag(client) -> None:
    """Test getting questions filtered by tag."""
    response = client.get("/questions/tags?tag=arrays")
    assert response.status_code == 200

    data = response.json
    assert len(data) == 2

    response = client.get("/questions/tags?tag=strings")
    assert response.status_code == 200

    data = response.json
    assert len(data) == 1
    assert data[0]["title"] == "Reverse String"

    response = client.get("/questions/tags")
    assert response.status_code == 400
    assert response.json["error"] == "Tag parameter is required"

    response = client.get("/questions/tags?tag=nonexistent")
    assert response.status_code == 200
    assert len(response.json) == 0

@pytest.mark.usefixtures("sample_data")
def test_get_question_not_found(client) -> None:
    """Test getting a non-existent question."""
    response = client.get('/questions/999')
    assert response.status_code == 404
    assert response.json['error'] == 'Question not found'

@pytest.mark.usefixtures("sample_data")
def test_get_questions_by_tag_missing_param(client) -> None:
    """Test getting questions by tag without providing tag parameter."""
    response = client.get('/questions/tags')
    assert response.status_code == 400
    assert response.json['error'] == 'Tag parameter is required'

@pytest.mark.usefixtures("sample_data")
def test_get_questions_by_nonexistent_tag(client) -> None:
    """Test getting questions with a tag that doesn't exist."""
    response = client.get('/questions/tags?tag=nonexistent')
    assert response.status_code == 200
    assert response.json == []

@pytest.mark.usefixtures("sample_data")
def test_get_all_questions_empty_db(client, app) -> None:
    """Test getting questions when database is empty."""
    with app.app_context():
        # Clean up all test data
        db.session.query(TestCase).delete()
        db.session.query(QuestionTag).delete()
        db.session.query(Question).delete()
        db.session.commit()

        response = client.get("/questions")
        assert response.status_code == 200
        assert response.json == []

@pytest.mark.usefixtures("sample_data")
def test_get_all_questions_db_error(client, mocker):
    """Test database error handling when getting all questions."""
    mock = mocker.patch(
        'website.models.Question.query',
        new_callable=mocker.PropertyMock
    )
    mock.return_value.all.side_effect = Exception("Database error")

    response = client.get("/questions")
    assert response.status_code == 500
    assert "error" in response.json
    assert "Failed to fetch questions" in response.json["error"]

@pytest.mark.usefixtures("sample_data")
def test_get_question_by_id_db_error(client, mocker):
    """Test database error handling when getting question by ID."""
    mock = mocker.patch(
        'website.models.Question.query',
        new_callable=mocker.PropertyMock
    )
    mock.return_value.get.side_effect = Exception("Database error")

    response = client.get("/questions/1")
    assert response.status_code == 500
    assert "error" in response.json
    assert "Failed to fetch question" in response.json["error"]

@pytest.mark.usefixtures("sample_data")
def test_get_questions_by_tag_db_error(client, mocker):
    """Test database error handling when getting questions by tag."""
    mock_query = mocker.MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.side_effect = Exception("Database error")

    mocker.patch('website.questions.Question.query', mock_query)

    response = client.get("/questions/tags?tag=arrays")
    assert response.status_code == 500
    assert "error" in response.json
    assert "Failed to fetch questions by tag" in response.json["error"]

@pytest.mark.usefixtures("sample_data")
def test_get_questions_by_tag_empty_result(client) -> None:
    """Test getting questions by tag with no matching results."""
    response = client.get("/questions/tags?tag=nonexistent")
    assert response.status_code == 200
    assert response.json == []

@pytest.mark.usefixtures("sample_data")
def test_get_questions_malformed_json(client, mocker):
    """Test handling of malformed JSON in question data."""
    mocker.patch(
        'website.models.Question.to_dict',
        side_effect=Exception("JSON error")
    )
    response = client.get("/questions")
    assert response.status_code == 500
    assert "error" in response.json

@pytest.mark.usefixtures("sample_data")
def test_next_question(client):
    """Test if the main page recommends a question based on the user's weakest skill."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Reverse String" in response.data

def test_next_question_no_mastery(client, app, test_user):
    """Test if the main page recommends any question for a new user without mastery scores."""
    with app.app_context():
        user = test_user
        with client.session_transaction() as session:
            session['_user_id'] = str(user.userID)
        question1 = Question(title="Intro Question",
                             description="Solve this simple problem.",
                             difficulty="Easy")
        db.session.add(question1)
        db.session.commit()

    response = client.get('/')
    assert response.status_code == 200
    assert b"Intro Question" in response.data

@pytest.mark.usefixtures("sample_data")
def test_library_page(client):
    """Test if the library page loads and displays questions grouped by tags."""
    response = client.get("/library")

    # Ensure the page loads successfully
    assert response.status_code == 200

    # Check if tags are displayed in the UI
    assert b"arrays" in response.data
    assert b"strings" in response.data

    # Check if question titles appear in the response
    assert b"Sum Array" in response.data
    assert b"Reverse String" in response.data

