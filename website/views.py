"""This module contains endpoints for DevReady"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from .questions import get_next_question, get_all_tags_with_questions, get_all_completed_questions

# Create a blueprint
main_blueprint = Blueprint('main', __name__)

@main_blueprint.route('/', methods=['GET', 'POST'])
@login_required
def main():
    """Selects a question based on user's weakest skill level."""
    question, sample_tests = get_next_question(current_user.userID)
    return render_template('index.html', user=current_user, question=question,
                            sample_tests=sample_tests)

@main_blueprint.route('/library', methods=['GET', 'POST'])
@login_required
def library():
    """Endpoint to get problem library page."""
    tag_questions = get_all_tags_with_questions()
    completed_questions = get_all_completed_questions(current_user.userID)
    return render_template('library.html', user=current_user, tag_questions=tag_questions,
                            completed_questions=completed_questions)

@main_blueprint.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Endpoint to get profile page."""
    return render_template('profile.html', user=current_user)

@main_blueprint.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Endpoint to get settings page."""
    return render_template('settings.html', user=current_user)
