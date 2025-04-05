"""Methods for profile info"""
from flask import Blueprint
from website.models import User, Submission, Question

profile_blueprint = Blueprint("profile", __name__)

def get_solved_count(user_id):
    """Returns user's count of unique problems solved"""
    solved = Submission.query.filter_by(userID=user_id, result="Passed").all()
    return len({x.questionID for x in solved})

def get_submissions(user_id):
    """Returns user's submission history"""
    submissions = Submission.query.filter_by(userID=user_id)
    return [[x.questionID, x.result, x.runtime, x.time] for x in submissions]

def get_successful_submissions(user_id):
    """Returns user's successful submissions"""
    submissions = Submission.query.filter_by(userID=user_id, result="Passed")
    return [[x.questionID, x.result, x.runtime, x.time] for x in submissions]

def get_mastery_score(user_id):
    """Returns mocked mastery score (for now)"""
    question_count = Question.query.count()
    mastery_score = float(get_solved_count(user_id) / question_count)
    return mastery_score

def get_badges():
    """Returns mocked badges (for now)"""
    badges = 5
    return badges

def get_language_count(user_id):
    """Returns user's language count"""
    submissions = Submission.query.filter_by(userID=user_id)
    return len({x.language for x in submissions})

def get_user_info(user_id):
    """Get user information."""
    return User.query.filter_by(userID=user_id).first()

def get_user_submissions(user_id):
    """Get user submissions."""
    return Submission.query.filter_by(userID=user_id).all()
