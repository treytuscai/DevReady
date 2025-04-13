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

@ab_blueprint.route('/get-ab-test-data', methods=['GET'])
def get_ab_test_data():
    # Query
    results = ABTestAnalytics.query.all()

    # Initialize the data structure to hold the required data
    ai_usage = {'A': 0, 'B': 0}
    assignments = {'A': 0, 'B': 0}
    hint_impact = {
        'A': {'hint': 0, 'noHint': 0},
        'B': {'hint': 0, 'noHint': 0}
    }

    for entry in results:
        # Count the hint usage
        if entry.usedHint:
            ai_usage[entry.group] += 1
        
        # Count assignments (total number of submissions) per group
        assignments[entry.group] += 1
        
        # Track hint impact on submission time
        if entry.usedHint:
            if entry.group == 'A':
                hint_impact['A']['hint'] += entry.timeToSubmit
            else:
                hint_impact['B']['hint'] += entry.timeToSubmit
        else:
            if entry.group == 'A':
                hint_impact['A']['noHint'] += entry.timeToSubmit
            else:
                hint_impact['B']['noHint'] += entry.timeToSubmit

    # Calculate the average time
    for group in ['A', 'B']:
        hint_impact[group]['hint'] = hint_impact[group]['hint'] / ai_usage[group] if ai_usage[group] > 0 else 0
        hint_impact[group]['noHint'] = hint_impact[group]['noHint'] / (assignments[group] - ai_usage[group]) if assignments[group] - ai_usage[group] > 0 else 0

    data = {
        'aiUsage': ai_usage,
        'assignments': assignments,
        'hintImpact': hint_impact
    }

    return jsonify(data)
