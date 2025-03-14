"""This module handles the endpoints and functions related to questions."""
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from .models import Question, QuestionTag, MasteryScore, Submission, Tag
from .extensions import db

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
        examples = [{
            "input": tc.inputData,
            "output": tc.expectedOutput
        } for tc in question.testCases if tc.isSample]

        total_submissions = Submission.query.filter_by(questionID=question_id).count()
        successful_submissions = Submission.query.filter_by(
            questionID=question_id, result="Passed"
        ).count()
        success_rate = round((successful_submissions / total_submissions * 100)
                           if total_submissions > 0 else 0)

        return render_template('question.html',
                             question=question,
                             examples=examples,
                             success_rate=success_rate,
                             user=current_user)
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
    """Fetch the next question based on the user's weakest skill."""
    # Find the weakest skill (tag with lowest mastery score)
    weakest_tag = (
        db.session.query(MasteryScore)
        .filter_by(userID=user_id)
        .order_by(MasteryScore.score.asc())
        .first()
    )

    if weakest_tag:
        # Get an unattempted question for this tag
        question = (
            db.session.query(Question)
            .join(QuestionTag, QuestionTag.questionID == Question.questionID)
            .filter(QuestionTag.tagID == weakest_tag.tagID)
            .outerjoin(
                Submission,
                (Submission.questionID == Question.questionID) & (Submission.userID == user_id)
            )
            .filter(Submission.submissionID == None)
            .order_by(Question.difficulty)
            .first()
        )
    else:
        # Default: Get any question if no mastery score exists yet
        question = db.session.query(Question).order_by(Question.difficulty).first()

    sample_tests = [test for test in question.testCases if test.isSample]
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
