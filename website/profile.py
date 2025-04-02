"""This module contains functions for retrieving user profile information."""
from website.models import User, Submission

def get_user_info(user_id):
    """Get user information."""
    return User.query.filter_by(userID=user_id).first()

def get_user_submissions(user_id):
    """Get user submissions."""
    return Submission.query.filter_by(userID=user_id).all()

