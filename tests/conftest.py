"""Configuration for pytest fixtures."""
import pytest
from datetime import datetime
from werkzeug.security import generate_password_hash
from website import create_app, db
from website.models import User, Tag, Question, QuestionTag, TestCase, MasteryScore, Submission

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    testing_app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test'
    })

    with testing_app.app_context():
        db.create_all()
        yield testing_app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client(use_cookies=True)

@pytest.fixture
def mock_subprocess_run(mocker):
    """Fixture to mock subprocess.run for safe code execution testing."""
    return mocker.patch("subprocess.run")

@pytest.fixture
def sample_data(client, app):
    """Create a test user and log them in before running tests."""
    with app.app_context():
        test_user = User(
            username="testuser",
            email="test@example.com",
            passwordHash=generate_password_hash("password")
        )
        db.session.add(test_user)
        db.session.commit()

        client.post("/login", data={"username": "testuser", "password": "password"})

        tag1 = Tag(name="arrays")
        tag2 = Tag(name="strings")
        db.session.add_all([tag1, tag2])
        db.session.commit()

        mastery = MasteryScore(userID=test_user.userID, tagID=tag2.tagID, score=1)  # Low mastery
        db.session.add(mastery)
        db.session.commit()

        q1 = Question(title="Sum Array",
                      description="Find the sum of array elements",
                      difficulty="easy",
                      expected_method="sumArray")
        q2 = Question(title="Reverse String",
                      description="Reverse the given string",
                      difficulty="easy",
                      expected_method="reverseString")
        db.session.add_all([q1, q2])
        db.session.commit()

        qt1 = QuestionTag(questionID=q1.questionID, tagID=tag1.tagID)
        qt2 = QuestionTag(questionID=q2.questionID, tagID=tag1.tagID)
        qt3 = QuestionTag(questionID=q2.questionID, tagID=tag2.tagID)
        db.session.add_all([qt1, qt2, qt3])
        db.session.commit()

        tc1 = TestCase(questionID=q1.questionID,
                       inputData="[1, 2, 3]",
                       expectedOutput=6,
                       isSample=True)
        tc2 = TestCase(questionID=q1.questionID,
                       inputData="[4, 5, 6]",
                       expectedOutput=15,
                       isSample=False)
        db.session.add_all([tc1, tc2])
        db.session.commit()

        submission1 = Submission(
            userID=test_user.userID,
            questionID=q1.questionID,
            code="def sumArray(arr): return sum(arr)",
            result="passed",
            runtime=12,
            language="python3",
            time=datetime.utcnow()
        )
        db.session.add(submission1)
        db.session.commit()

        yield

@pytest.fixture
def test_user(app):
    """Create a test user for authentication tests."""
    with app.app_context():
        user = User(
            username="testuser",
            email="test@example.com",
            passwordHash=generate_password_hash("password123")
        )
        db.session.add(user)
        db.session.commit()
        yield user
