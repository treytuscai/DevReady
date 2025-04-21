"""This module handles the endpoints and functions related to questions."""
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from .models import Question, QuestionTag, MasteryScore, Submission, Tag
from .extensions import db
import random

questions_blueprint = Blueprint("questions", __name__)

@questions_blueprint.route("/questions", methods=["GET"])
@login_required
def get_questions():
    """Get all questions from the database, with sample test cases."""
    try:
        questions = Question.query.all()
        return jsonify([{
            **question.to_dict(),
            "tags": [tag.name for tag in question.tags],
            "sample_test_cases": [
                {"input": tc.inputData, "expected_output": tc.expectedOutput}
                for tc in question.testCases
                if tc.isSample
            ]
        } for question in questions])
    except Exception as e:
        return jsonify({"error": "Failed to fetch questions", "details": str(e)}), 500

@questions_blueprint.route("/questions/<int:question_id>", methods=["GET"])
@login_required
def get_question_by_id(question_id):
    """Get a question by its ID and render the question template."""
    try:
        question = Question.query.get(question_id)
        if not question:
            return jsonify({"error": "Question not found"}), 404
        sample_tests = [test for test in question.testCases if test.isSample]
        acceptance_rate = get_acceptance_rate(question_id)

        return render_template('question.html',
                             question=question,
                             sample_tests=sample_tests,
                             user=current_user,
                             acceptance_rate=acceptance_rate)
    except Exception as e:
        return jsonify({"error": "Failed to fetch question", "details": str(e)}), 500

@questions_blueprint.route("/questions/tags", methods=["GET"])
@login_required
def get_questions_by_tag():
    """Get questions, with sample test cases, by a specific tag."""
    try:
        tag = request.args.get("tag")
        if not tag:
            return jsonify({"error": "Tag parameter is required"}), 400

        questions = Question.query.join(QuestionTag).filter(
            QuestionTag.tag.has(name=tag)
        ).all()
        return jsonify([{
            **question.to_dict(),
            "tags": [tag.name for tag in question.tags],
            "sample_test_cases": [
                {"input": tc.inputData, "expected_output": tc.expectedOutput}
                for tc in question.testCases
                if tc.isSample
            ]
        } for question in questions])
    except Exception as e:
        return jsonify({"error": "Failed to fetch questions by tag", "details": str(e)}), 500

def get_next_question(user_id):
    """Get the easiest unpassed question from the tag where the user has passed the fewest questions."""
    
    # Step 1: Get all tags (initialize tag completion count with 0 for each tag)
    all_tags = db.session.query(Tag.tagID, Tag.name).all()
    tag_completion_count = {tag_id: 0 for tag_id, _ in all_tags}

    # Step 2: Get all passed question IDs by the user
    passed_ids_list = (
        db.session.query(Submission.questionID)
        .filter_by(userID=user_id, result="Passed")
        .distinct()
        .all()
    )
    passed_ids_list = [q[0] for q in passed_ids_list]
    
    # Step 3: Get all tags associated with the passed questions
    passed_question_tags = (
        db.session.query(QuestionTag.tagID, QuestionTag.questionID)
        .filter(QuestionTag.questionID.in_(passed_ids_list))  # Only consider passed questions
        .all()
    )

    # Step 4: Increment the count for tags associated with the passed questions
    for tag_id, _ in passed_question_tags:
        if tag_id in tag_completion_count:
            tag_completion_count[tag_id] += 1

    # Step 5: Find the minimum completion count
    min_completion_count = min(tag_completion_count.values(), default=None)

    # Step 6: Filter tags that have the minimum completion count
    lowest_tags = [tag_id for tag_id, count in tag_completion_count.items() if count == min_completion_count]

    # Step 7: Randomly select one of the lowest tags
    lowest_tag_id = random.choice(lowest_tags) if lowest_tags else None

    # Step 8: Get an easy question with the tag that has the fewest passed questions
    question = (
        db.session.query(Question)
        .join(QuestionTag, QuestionTag.questionID == Question.questionID)
        .filter(QuestionTag.tagID == lowest_tag_id)
        .filter(~Question.questionID.in_(passed_ids_list))  # Exclude already passed questions
        .order_by(Question.difficulty.asc())
        .first()
    )

    # If no question found, return a default question
    if not question:
        question = db.session.query(Question).order_by(Question.difficulty.asc()).first()

    # Step 9: Return the question along with its sample test cases
    sample_tests = [test for test in question.testCases if test.isSample] if question else []
    return question, sample_tests

def get_all_tags_with_questions():
    """Fetch all tags with their associated questions."""
    # Fetch all tags and their associated questions in one optimized query
    tag_questions = {}

    tags_with_questions = (
        db.session.query(Tag.name, Question)
        .join(QuestionTag, Tag.tagID == QuestionTag.tagID)
        .join(Question, Question.questionID == QuestionTag.questionID)
        .order_by(Tag.name, Question.difficulty)
        .all()
    )

    # Group questions under their respective tags
    for tag_name, question in tags_with_questions:
        if tag_name not in tag_questions:
            tag_questions[tag_name] = []
        tag_questions[tag_name].append(question)

    return tag_questions

def get_all_completed_questions(user_id):
    '''Get all completed question IDs for a user'''
    completed_question_ids = set(
        db.session.query(Submission.questionID)
        .filter(Submission.userID == user_id, Submission.result == "Passed")
        .distinct()
        .all()
    )
    completed_question_ids = {qid[0] for qid in completed_question_ids}
    return completed_question_ids


def get_acceptance_rate(question_id):
    """Get the acceptance rate of a given question."""
    total_submissions = Submission.query.filter_by(questionID=question_id).count()
    successful_submissions = Submission.query.filter_by(
        questionID=question_id, result="Passed"
    ).count()
    return round((successful_submissions / total_submissions * 100) if total_submissions > 0 else 0)
