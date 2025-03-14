"""This module contains unit tests for the AI."""
from unittest import mock
import pytest
from website.ai_helper import get_openai_client, generate_response

def test_get_openai_client_success(app):
    """Test the get_openai_client function when the API key is present."""
    with app.app_context():
        mock_client = mock.Mock()
        with mock.patch('website.ai_helper.OpenAI', return_value=mock_client):
            client = get_openai_client()
            assert client == mock_client

def test_get_openai_client_no_api_key(app):
    """Test get_openai_client when the API key is missing."""
    with app.app_context():
        app.config["OPENAI_API_KEY"] = None
        with pytest.raises(ValueError):
            get_openai_client()

def test_generate_response_success(app):
    """Test the generate_response function."""
    with app.app_context():
        system_prompt = "System prompt"
        user_prompt = "User prompt"

        mock_response = mock.Mock()
        mock_message = mock.Mock(content="Hint!")
        mock_response = mock.Mock(choices=[mock.Mock(message=mock_message)])

        # Patch the get_openai_client to return a mock client
        mock_chat = mock.Mock(completions=mock.Mock(create=mock.Mock(return_value=mock_response)))
        with mock.patch('website.ai_helper.get_openai_client',
                         return_value=mock.Mock(chat=mock_chat)):
            user_hint, error = generate_response(system_prompt, user_prompt)
            assert user_hint == "Hint!"
            assert error is None

def test_generate_response_error_handling(app):
    """Test error handling for the generate_response function."""
    with app.app_context():
        system_prompt = "System prompt"
        user_prompt = "User prompt"

        with mock.patch.object(get_openai_client(), 'chat', side_effect=Exception("API error")):
            user_hint, error = generate_response(system_prompt, user_prompt)
            assert user_hint is None
            assert error == "An unexpected error occurred."
