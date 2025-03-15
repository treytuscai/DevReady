"""Methods for profile info"""
from flask import Blueprint
from website.models import Submission
from website.extensions import db

profile_blueprint = Blueprint("profile", __name__)

def get_solved_count(id):
    """Returns user's count of unique problems solved"""
    solved = Submission.query.filter_by(userID=id, result="Passed").all()
    return len(set([x.questionID for x in solved]))

def get_submissions(id):
    """Returns all user submissions"""
    submissions = Submission.query.filter_by(userID=id)
    return [[x.questionID, x.result, x.runtime, x.time] for x in submissions]

def get_mastery_score(id):
    """Returns mocked mastery score (for now)"""
    mastery_score = 80
    return mastery_score

def get_badges(id):
    """Returns mocked badges (for now)"""
    badges = 5
    return badges 
