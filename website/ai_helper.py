"""Blueprint for AI-powered coding hints and analysis."""
from flask import Blueprint, jsonify, request, current_app
from openai import OpenAI

ai_helper_blueprint = Blueprint("ai_helper", __name__)

def get_openai_client():
    """Retrieves OpenAI client using the API key from Flask config."""
    api_key = current_app.config.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Missing OpenAI API Key")
    return OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

def generate_response(system_prompt, user_prompt):
    """Helper function to generate AI responses using DeepSeek Chat API."""
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=False
        )
        return response.choices[0].message.content, None
    except Exception as error:
        current_app.logger.error("Unexpected AI Model Error: %s", str(error))
        return None, "An unexpected error occurred."

@ai_helper_blueprint.route('/hint', methods=['POST'])
def provide_hint():
    """Provides guidance on solving a coding question without revealing the answer."""
    data = request.get_json()
    question_description = data.get("question_description")
    code = data.get("code")

    if not question_description or not code:
        return jsonify({"success": False, "error": "Missing question description or code"}), 400

    system_prompt = (
        "You are a coding interviewer. Your interviewee is stuck on a Leetcode-style problem. "
        "Evaluate their code, identify mistakes, and guide them toward a solution. "
        "DO NOT GIVE AWAY THE ANSWER. Only provide a hint. Be very brief, concise and patient."
    )
    user_prompt = (
        f"I am solving the Leetcode question '{question_description}', but I'm stuck.\n"
        f"Here is my code so far:\n{code}"
    )

    user_hint, error = generate_response(system_prompt, user_prompt)

    if error:
        return jsonify({"success": False, "error": error}), 500

    return jsonify({"success": True, "hint": user_hint})

@ai_helper_blueprint.route('/analyze_submission', methods=['POST'])
def analyze_submission():
    """Analyzes submitted code, providing time/space complexity and optimization suggestions."""
    data = request.get_json()
    question_description = data.get("question_description")
    code = data.get("code")

    if not question_description or not code:
        return jsonify({"success": False, "error": "Missing question description or code"}), 400

    system_prompt = (
        "You are a CS professor specializing in algorithms. Evaluate a given solution, analyze its "
        "time/space complexity, compare it to the optimal solution, and suggest improvements. "
        "Be concise."
    )
    user_prompt = (
        f"I solved the Leetcode question '{question_description}'. Can you analyze my solution's "
        f"time/space complexity and compare it to the optimal one? Here is my code:\n{code}"
    )

    analysis, error = generate_response(system_prompt, user_prompt)

    if error:
        return jsonify({"success": False, "error": error}), 500

    return jsonify({"success": True, "analysis": analysis})
