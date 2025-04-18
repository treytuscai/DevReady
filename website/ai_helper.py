"""Blueprint for AI-powered coding hints and analysis."""
import json

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
    """Analyzes submitted code, providing time/space complexity"""
    data = request.get_json()
    code = data.get("code")
    question_description = data.get("question_description")

    if not question_description or not code:
        return jsonify({"success": False, "error": "Missing question description or code"}), 400

    system_prompt = (
        "You are a CS professor specializing in algorithms."
        "You perfectly analyze student algorithm submission against their known optimal worst-case time complexity"
        "These are the complexity classes you can choose from: O(1), O(logn), O(n), O(nlogn), O(n^2), O(n^m), O(2^n), O(n!)"
        "You always respond in json bodies and only JSON bodies"
        "Your response starts with { and ends with }"
        "Your response is a JSON object that looks like the following: "
        "{user_time_complexity: [time complexity] ,"
        "optimal_time_complexity: [optimal time complexity] ,"
        "user_space_complexity: [space complexity] ,"
        "optimal_space_complexity: [optimal space complexity]}"
    )
    
    user_prompt = (
        f"I solved a Leetcode question with this description: '{question_description}'. Can you analyze my solution's "
        f"time/space complexity and compare it to the optimal one? Here is my code:\n{code}"
    )
    
    analysis, error = generate_response(system_prompt, user_prompt)

    if error:
        return jsonify({"success": False, "error": error}), 500

    # Clean the response to extract only JSON content
    try:
        # Find the first { and last }
        start_idx = analysis.find('{')
        end_idx = analysis.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            return jsonify({"success": False, "error": "Invalid JSON response format"}), 500
            
        # Extract just the JSON portion
        json_str = analysis[start_idx:end_idx]
        
        # Parse the JSON to validate and get the complexities
        complexity_data = json.loads(json_str)
        
        # Format response for frontend
        response = {
            "timeComplexity": complexity_data.get("user_time_complexity", "Unknown"),
            "spaceComplexity": complexity_data.get("user_space_complexity", "Unknown"),
            "explanation": f"Your solution runs in {complexity_data.get('user_time_complexity', 'Unknown')} time and uses "
                         f"{complexity_data.get('user_space_complexity', 'Unknown')} space. "
                         f"The optimal solution runs in {complexity_data.get('optimal_time_complexity', 'Unknown')} time and uses "
                         f"{complexity_data.get('optimal_space_complexity', 'Unknown')} space."
        }
        print("THis is response: ", response)
    except json.JSONDecodeError:
        return jsonify({"success": False, "error": "Failed to parse complexity analysis"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"Error processing analysis: {str(e)}"}), 500
    return jsonify({"success": True, "analysis": response})

