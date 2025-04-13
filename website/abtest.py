from flask import Blueprint, request, jsonify
from website.extensions import db
from website.models import ABTestAnalytics

ab_blueprint = Blueprint('abtest', __name__)

@ab_blueprint.route('/track-ab-test', methods=['POST'])
def track_ab_test():
    data = request.get_json()

    new_entry = ABTestAnalytics(
        questionID=data.get('questionID'),
        group=data.get('group'),
        usedHint=data.get('usedHint', False),
        timeToSubmit=data.get('timeToSubmit')
    )

    db.session.add(new_entry)
    db.session.commit()

    return jsonify({'status': 'success'}), 201
