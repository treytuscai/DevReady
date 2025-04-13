"""Blueprint for settings."""
from flask import Blueprint, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from website.models import User
from .extensions import db
from .models import User

settings_blueprint = Blueprint('settings', __name__)

@settings_blueprint.route('/newEmail', methods=['POST'])
@login_required
def new_email():
    """Endpoint to change email."""
    email = request.form['email']

    if email == current_user.email:
        flash("No changes were made to your email.", "email_warning")
        return redirect(url_for('main.settings'))

    if not email:
        flash("All fields are required.", "email_danger")
        return redirect(url_for('main.settings'))

    if User.query.filter_by(email=email).first():
        flash("An account with that email already exists.", "email_danger")
        return redirect(url_for('main.settings'))

    current_user.email = email
    db.session.commit()
    flash("Your email has been updated successfully.", "email_success")
    return redirect(url_for('main.settings'))

@settings_blueprint.route('/newPassword', methods=['POST'])
@login_required
def new_password():
    """Endpoint to change password."""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not current_password or not new_password or not confirm_password:
        flash("All fields are required.", "password_danger")
        return redirect(url_for('main.settings'))

    if not check_password_hash(current_user.passwordHash, current_password):
        flash("Current password is incorrect.", "password_danger")
        return redirect(url_for('main.settings'))

    if new_password != confirm_password:
        flash("New passwords do not match.", "password_danger")
        return redirect(url_for('main.settings'))

    if len(new_password) > 20 or len(new_password) < 8:
        flash("Password must be between 8 and 20 characters.", "password_danger")
        return redirect(url_for('main.settings'))

    current_user.passwordHash = generate_password_hash(new_password, "pbkdf2")
    db.session.commit()
    flash("Your password has been updated successfully.", "password_success")
    return redirect(url_for('main.settings'))
