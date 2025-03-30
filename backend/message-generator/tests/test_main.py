"""
Unit tests for the message generator Cloud Function.
"""
import json
import os
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from google.cloud import secretmanager
from google.cloud import aiplatform

from src.main import (
    validate_request,
    format_analysis_result,
    construct_prompt,
    generate_advice,
    get_service_account_key,
    initialize_vertex_ai,
    generate_message,
    PROMPT_TEMPLATES,
    DEFAULT_ADVICE
)


@pytest.fixture
def app():
    """Create a Flask test app."""
    app = Flask(__name__)
    app.testing = True
    return app


@pytest.fixture
def sample_analysis_result():
    """Sample analysis result for testing."""
    return {
        "labels": [
            {"description": "Plant", "score": 0.95},
            {"description": "Houseplant", "score": 0.92},
            {"description": "Flowerpot", "score": 0.85}
        ],
        "objects": [
            {"name": "Potted plant", "score": 0.98},
            {"name": "Vase", "score": 0.75}
        ],
        "text": "Plant care instructions"
    }


@pytest.fixture
def sample_request_json(sample_analysis_result):
    """Sample request JSON for testing."""
    return {
        "scenario": "plant",
        "analysis_result": sample_analysis_result
    }


class TestValidateRequest:
    """Tests for the validate_request function."""

    def test_valid_request(self, sample_request_json):
        """Test validation of a valid request."""
        is_valid, error_message = validate_request(sample_request_json)
        assert is_valid is True
        assert error_message is None

    def test_empty_request(self):
        """Test validation of an empty request."""
        is_valid, error_message = validate_request({})
        assert is_valid is False
        assert "Missing 'scenario'" in error_message

    def test_missing_scenario(self, sample_request_json):
        """Test validation of a request with missing scenario."""
        del sample_request_json["scenario"]
        is_valid, error_message = validate_request(sample_request_json)
        assert is_valid is False
        assert "Missing 'scenario'" in error_message

    def test_invalid_scenario(self, sample_request_json):
        """Test validation of a request with an invalid scenario."""
        sample_request_json["scenario"] = "invalid"
        is_valid, error_message = validate_request(sample_request_json)
        assert is_valid is False
        assert "Invalid scenario" in error_message

    def test_missing_analysis_result(self, sample_request_json):
        """Test validation of a request with missing analysis result."""
        del sample_request_json["analysis_result"]
        is_valid, error_message = validate_request(sample_request_json)
        assert is_valid is False
        assert "Missing 'analysis_result'" in error_message


class TestFormatAnalysisResult:
    """Tests for the format_analysis_result function."""

    def test_format_complete_result(self, sample_analysis_result):
        """Test formatting of a complete analysis result."""
        formatted = format_analysis_result(sample_analysis_result)
        assert "Plant (0.95)" in formatted["labels"]
        assert "Potted plant (0.98)" in formatted["objects"]
        assert formatted["text"] == "Plant care instructions"

    def test_format_empty_result(self):
        """Test formatting of an empty analysis result."""
        formatted = format_analysis_result({})
        assert formatted["labels"] == "なし"
        assert formatted["objects"] == "なし"
        assert formatted["text"] == "なし"

    def test_format_partial_result(self):
        """Test formatting of a partial analysis result."""
        partial_result = {
            "labels": [{"description": "Plant", "score": 0.95}],
            "objects": []
        }
        formatted = format_analysis_result(partial_result)
        assert "Plant (0.95)" in formatted["labels"]
        assert formatted["objects"] == "なし"
        assert formatted["text"] == "なし"


class TestConstructPrompt:
    """Tests for the construct_prompt function."""

    def test_construct_plant_prompt(self, sample_analysis_result):
        """Test construction of a plant scenario prompt."""
        prompt = construct_prompt("plant", sample_analysis_result)
        assert "植物ケアの専門家です" in prompt
        assert "Plant (0.95)" in prompt
        assert "Potted plant (0.98)" in prompt
        assert "Plant care instructions" in prompt

    def test_construct_closet_prompt(self, sample_analysis_result):
        """Test construction of a closet scenario prompt."""
        prompt = construct_prompt("closet", sample_analysis_result)
        assert "整理収納の専門家です" in prompt
        assert "Plant (0.95)" in prompt
        assert "Potted plant (0.98)" in prompt
        assert "Plant care instructions" in prompt

    def test_construct_fridge_prompt(self, sample_analysis_result):
        """Test construction of a fridge scenario prompt."""
        prompt = construct_prompt("fridge", sample_analysis_result)
        assert "食品管理と冷蔵庫整理の専門家です" in prompt
        assert "Plant (0.95)" in prompt
        assert "Potted plant (0.98)" in prompt
        assert "Plant care instructions" in prompt

    def test_invalid_scenario(self, sample_analysis_result):
        """Test construction of a prompt with an invalid scenario."""
        with pytest.raises(ValueError, match="Invalid scenario"):
            construct_prompt("invalid", sample_analysis_result)


class TestGetServiceAccountKey:
    """Tests for the get_service_account_key function."""

    @patch.dict(os.environ, {"PROJECT_ID": "test-project"})
    @patch("src.main.secretmanager.SecretManagerServiceClient")
    def test_get_service_account_key_success(self, mock_client):
        """Test successful retrieval of service account key."""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_response = MagicMock()
        mock_response.payload.data.decode.return_value = "test-key"
        mock_client_instance.access_secret_version.return_value = mock_response

        key = get_service_account_key()

        assert key == "test-key"
        mock_client_instance.access_secret_version.assert_called_once()

    @patch.dict(os.environ, {"PROJECT_ID": ""})
    @patch("src.main.secretmanager.SecretManagerServiceClient")
    def test_get_service_account_key_no_project_id(self, mock_client):
        """Test retrieval of service account key with no project ID."""
        with pytest.raises(ValueError, match="Project ID not found"):
            get_service_account_key()

    @patch.dict(os.environ, {"PROJECT_ID": "test-project"})
    @patch("src.main.secretmanager.SecretManagerServiceClient")
    def test_get_service_account_key_error(self, mock_client):
        """Test error during retrieval of service account key."""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.access_secret_version.side_effect = Exception("Test error")

        with pytest.raises(Exception, match="Test error"):
            get_service_account_key()


class TestInitializeVertexAI:
    """Tests for the initialize_vertex_ai function."""

    @patch("src.main.aiplatform.init")
    @patch("builtins.open", new_callable=MagicMock)
    @patch("os.remove")
    def test_initialize_vertex_ai_success(self, mock_remove, mock_open, mock_init):
        """Test successful initialization of Vertex AI."""
        initialize_vertex_ai("test-key")

        mock_open.assert_called_once()
        mock_init.assert_called_once()
        mock_remove.assert_called_once_with("/tmp/service_account_key.json")

    @patch("src.main.aiplatform.init")
    @patch("builtins.open", new_callable=MagicMock)
    @patch("os.remove")
    @patch("os.path.exists", return_value=True)
    def test_initialize_vertex_ai_error(self, mock_exists, mock_remove, mock_open, mock_init):
        """Test error during initialization of Vertex AI."""
        mock_init.side_effect = Exception("Test error")

        with pytest.raises(Exception, match="Test error"):
            initialize_vertex_ai("test-key")

        mock_remove.assert_called_once_with("/tmp/service_account_key.json")


class TestGenerateAdvice:
    """Tests for the generate_advice function."""

    @patch("src.main.aiplatform.GenerativeModel")
    def test_generate_advice_success(self, mock_model_class):
        """Test successful generation of advice."""
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model
        mock_response = MagicMock()
        mock_response.text = "Test advice"
        mock_model.generate_content.return_value = mock_response

        success, advice, error = generate_advice("Test prompt")

        assert success is True
        assert advice == "Test advice"
        assert error is None
        mock_model.generate_content.assert_called_once()

    @patch("src.main.aiplatform.GenerativeModel")
    def test_generate_advice_safety_error(self, mock_model_class):
        """Test generation of advice with safety error."""
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model
        mock_model.generate_content.side_effect = Exception("Safety settings blocked")

        success, advice, error = generate_advice("Test prompt")

        assert success is False
        assert advice == DEFAULT_ADVICE
        assert "safety settings" in error.lower()

    @patch("src.main.aiplatform.GenerativeModel")
    def test_generate_advice_general_error(self, mock_model_class):
        """Test generation of advice with general error."""
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model
        mock_model.generate_content.side_effect = Exception("Test error")

        success, advice, error = generate_advice("Test prompt")

        assert success is False
        assert advice == DEFAULT_ADVICE
        assert "Test error" in error


class TestGenerateMessage:
    """Tests for the generate_message function."""

    @patch("src.main.get_service_account_key")
    @patch("src.main.initialize_vertex_ai")
    @patch("src.main.construct_prompt")
    @patch("src.main.generate_advice")
    def test_generate_message_success(self, mock_generate_advice, mock_construct_prompt,
                                     mock_initialize_vertex_ai, mock_get_service_account_key,
                                     app, sample_request_json):
        """Test successful generation of message."""
        mock_get_service_account_key.return_value = "test-key"
        mock_construct_prompt.return_value = "Test prompt"
        mock_generate_advice.return_value = (True, "Test advice", None)

        with app.test_request_context(
            json=sample_request_json,
            method="POST"
        ):
            response = generate_message(app.request)
            response_data = json.loads(response.data)

            assert response.status_code == 200
            assert response_data["success"] is True
            assert response_data["advice"] == "Test advice"
            assert response_data["error"] is None

    def test_generate_message_invalid_method(self, app):
        """Test generation of message with invalid method."""
        with app.test_request_context(method="GET"):
            response = generate_message(app.request)
            response_data = json.loads(response.data)

            assert response.status_code == 405
            assert response_data["success"] is False
            assert "Only POST requests" in response_data["error"]

    def test_generate_message_invalid_request(self, app):
        """Test generation of message with invalid request."""
        with app.test_request_context(
            json={},
            method="POST"
        ):
            response = generate_message(app.request)
            response_data = json.loads(response.data)

            assert response.status_code == 400
            assert response_data["success"] is False
            assert "Missing 'scenario'" in response_data["error"]

    @patch("src.main.get_service_account_key")
    def test_generate_message_secret_manager_error(self, mock_get_service_account_key, app, sample_request_json):
        """Test generation of message with Secret Manager error."""
        mock_get_service_account_key.side_effect = Exception("Secret Manager error")

        with app.test_request_context(
            json=sample_request_json,
            method="POST"
        ):
            response = generate_message(app.request)
            response_data = json.loads(response.data)

            assert response.status_code == 500
            assert response_data["success"] is False
            assert "Secret Manager error" in response_data["error"]
            assert response_data["advice"] == DEFAULT_ADVICE

    @patch("src.main.get_service_account_key")
    @patch("src.main.initialize_vertex_ai")
    @patch("src.main.construct_prompt")
    @patch("src.main.generate_advice")
    def test_generate_message_gemini_api_error(self, mock_generate_advice, mock_construct_prompt,
                                              mock_initialize_vertex_ai, mock_get_service_account_key,
                                              app, sample_request_json):
        """Test generation of message with Gemini API error."""
        mock_get_service_account_key.return_value = "test-key"
        mock_construct_prompt.return_value = "Test prompt"
        mock_generate_advice.return_value = (False, DEFAULT_ADVICE, "Gemini API error")

        with app.test_request_context(
            json=sample_request_json,
            method="POST"
        ):
            response = generate_message(app.request)
            response_data = json.loads(response.data)

            assert response.status_code == 200
            assert response_data["success"] is False
            assert response_data["advice"] == DEFAULT_ADVICE
            assert "Gemini API error" in response_data["error"]
