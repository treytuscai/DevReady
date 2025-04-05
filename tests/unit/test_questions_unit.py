"""Unit tests for the problem selection algorithm."""
import pytest
from website.models import User, Question, Tag, MasteryScore, QuestionTag
from website.extensions import db
from website.views import get_next_question, get_all_tags_with_questions, get_all_completed_questions

def test_get_next_question_with_weak_skill(app):
    """Test that the function selects an unattempted question based on weakest skill."""
    with app.app_context():
        # Create test user
        user = User(username="testuser", email="test@example.com", passwordHash="hashed")
        db.session.add(user)
        db.session.commit()

        # Create a tag and a mastery score (low score = weak skill)
        tag = Tag(name="Recursion")
        db.session.add(tag)
        db.session.commit()

        mastery = MasteryScore(userID=user.userID, tagID=tag.tagID, score=1)
        db.session.add(mastery)
        db.session.commit()

        # Create questions related to the tag
        question1 = Question(title="Recursion Problem 1",
                             description="Solve this recursion problem.",
                             difficulty="Easy")
        question2 = Question(title="Recursion Problem 2",
                             description="Another recursion problem.",
                             difficulty="Medium")
        db.session.add_all([question1, question2])
        db.session.commit()

        # Link questions to tag
        db.session.add_all([
            QuestionTag(questionID=question1.questionID, tagID=tag.tagID),
            QuestionTag(questionID=question2.questionID, tagID=tag.tagID)
        ])

        question, _ = get_next_question(user.userID)
        assert question is not None
        assert question.title.startswith("Recursion Problem")

def test_get_next_question_without_mastery_scores(app):
    """Test that a user without mastery scores gets any available question."""
    with app.app_context():
        user = User(username="newuser", email="new@example.com", passwordHash="hashed")
        db.session.add(user)
        db.session.commit()

        question1 = Question(title="Intro Question",
                             description="Solve this simple problem.",
                             difficulty="Easy")
        db.session.add(question1)
        db.session.commit()

        question, _ = get_next_question(user.userID)
        assert question is not None

@pytest.mark.usefixtures("sample_data")
def test_get_all_tags_with_questions(app):
    """Test fetching all tags with their associated questions."""
    with app.app_context():
        tag_questions = get_all_tags_with_questions()

        # Check if tags exist in the dictionary
        assert "arrays" in tag_questions
        assert "strings" in tag_questions

        # Check if questions are correctly categorized
        assert len(tag_questions["arrays"]) == 2  # Two questions under 'arrays'
        assert len(tag_questions["strings"]) == 1  # One question under 'strings'

        # Check if correct questions are retrieved
        assert any(q.title == "Sum Array" for q in tag_questions["arrays"])
        assert any(q.title == "Reverse String" for q in tag_questions["arrays"])
        assert tag_questions["strings"][0].title == "Reverse String"

@pytest.mark.usefixtures("sample_data")
def test_get_all_completed_questions(app):
    """Test if get_all_completed_questions correctly fetches completed questions."""
    with app.app_context():
        completed_questions = get_all_completed_questions(1)

        # Expecting only q1 to be completed
        assert isinstance(completed_questions, set)
        assert len(completed_questions) == 1
        assert list(completed_questions)[0] > 0
