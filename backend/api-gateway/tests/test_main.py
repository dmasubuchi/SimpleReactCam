"""
Unit tests for the API Gateway Cloud Function.

This module contains tests for the API Gateway Cloud Function,
which orchestrates calls to the image-processor and message-generator functions.
"""
import json
import os
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from src.main import (
    api_gateway,
    validate_request,
    call_image_processor,
    call_message_generator,
    handle_cors
)


@pytest.fixture
def app():
    """Create a Flask test app."""
    app = Flask(__name__)
    return app
    return app


@pytest.fixture
def valid_request_json():
    """Return a valid request JSON."""
    return {
        "scenario": "plant",
        "image_data": "base64_encoded_image_data"
    }


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set mock environment variables."""
    monkeypatch.setenv("IMAGE_PROCESSOR_URL", "http://image-processor-url")
    monkeypatch.setenv("MESSAGE_GENERATOR_URL", "http://message-generator-url")


class TestValidateRequest:
    """Tests for the validate_request function."""

    def test_valid_request(self, valid_request_json):
        """Test validation with a valid request."""
        is_valid, error_message = validate_request(valid_request_json)
        assert is_valid is True
        assert error_message is None

    def test_empty_request(self):
        """Test validation with an empty request."""
        is_valid, error_message = validate_request({})
        assert is_valid is False
        assert "Request body is empty" in error_message

    def test_missing_scenario(self):
        """Test validation with missing scenario."""
        is_valid, error_message = validate_request({"image_data": "data"})
        assert is_valid is False
        assert "Missing 'scenario'" in error_message

    def test_invalid_scenario(self):
        """Test validation with invalid scenario."""
        is_valid, error_message = validate_request({
            "scenario": "invalid",
            "image_data": "data"
        })
        assert is_valid is False
        assert "Invalid 'scenario'" in error_message

    def test_missing_image_data(self):
        """Test validation with missing image data."""
        is_valid, error_message = validate_request({"scenario": "plant"})
        assert is_valid is False
        assert "Missing 'image_data'" in error_message

    def test_empty_image_data(self):
        """Test validation with empty image data."""
        is_valid, error_message = validate_request({
            "scenario": "plant",
            "image_data": ""
        })
        assert is_valid is False
        assert "Empty 'image_data'" in error_message


class TestCallImageProcessor:
    """Tests for the call_image_processor function."""

    def test_successful_call(self, mock_env_vars, requests_mock):
        """Test successful call to image processor."""
        requests_mock.post(
            "http://image-processor-url",
            json={
                "success": True,
                "data": {
                    "labels": [{"description": "Plant", "score": 0.9}],
                    "objects": [{"name": "Flower pot", "score": 0.8}],
                    "text": "Plant care instructions"
                },
                "error": None
            },
            status_code=200
        )

        success, analysis_result, error = call_image_processor("base64_image_data")

        assert success is True
        assert "labels" in analysis_result
        assert "objects" in analysis_result
        assert "text" in analysis_result
        assert error is None

    def test_http_error(self, mock_env_vars, requests_mock):
        """Test HTTP error from image processor."""
        requests_mock.post(
            "http://image-processor-url",
            json={"success": False, "error": "Internal server error"},
            status_code=500
        )

        success, analysis_result, error = call_image_processor("base64_image_data")

        assert success is False
        assert analysis_result == {}
        assert "Image processor error" in error

    def test_success_false_in_response(self, mock_env_vars, requests_mock):
        """Test success=false in response from image processor."""
        requests_mock.post(
            "http://image-processor-url",
            json={"success": False, "error": "Invalid image data", "data": None},
            status_code=200
        )

        success, analysis_result, error = call_image_processor("base64_image_data")

        assert success is False
        assert analysis_result == {}
        assert "Image processor error" in error

    def test_request_exception(self, mock_env_vars, requests_mock):
        """Test request exception when calling image processor."""
        requests_mock.post(
            "http://image-processor-url",
            exc=Exception("Connection error")
        )

        success, analysis_result, error = call_image_processor("base64_image_data")

        assert success is False
        assert analysis_result == {}
        assert "Error communicating with image processor" in error

    def test_missing_url(self, monkeypatch):
        """Test missing image processor URL."""
        monkeypatch.delenv("IMAGE_PROCESSOR_URL", raising=False)

        success, analysis_result, error = call_image_processor("base64_image_data")

        assert success is False
        assert analysis_result == {}
        assert "Image processor URL not configured" in error


class TestCallMessageGenerator:
    """Tests for the call_message_generator function."""

    def test_successful_call(self, mock_env_vars, requests_mock):
        """Test successful call to message generator."""
        requests_mock.post(
            "http://message-generator-url",
            json={
                "success": True,
                "advice": "Here is some advice for your plant.",
                "error": None
            },
            status_code=200
        )

        analysis_result = {
            "labels": [{"description": "Plant", "score": 0.9}],
            "objects": [{"name": "Flower pot", "score": 0.8}],
            "text": "Plant care instructions"
        }

        success, advice, error = call_message_generator("plant", analysis_result)

        assert success is True
        assert advice == "Here is some advice for your plant."
        assert error is None

    def test_http_error(self, mock_env_vars, requests_mock):
        """Test HTTP error from message generator."""
        requests_mock.post(
            "http://message-generator-url",
            json={"success": False, "error": "Internal server error"},
            status_code=500
        )

        analysis_result = {
            "labels": [{"description": "Plant", "score": 0.9}]
        }

        success, advice, error = call_message_generator("plant", analysis_result)

        assert success is False
        assert advice == ""
        assert "Message generator error" in error

    def test_success_false_in_response(self, mock_env_vars, requests_mock):
        """Test success=false in response from message generator."""
        requests_mock.post(
            "http://message-generator-url",
            json={"success": False, "error": "Failed to generate advice", "advice": None},
            status_code=200
        )

        analysis_result = {
            "labels": [{"description": "Plant", "score": 0.9}]
        }

        success, advice, error = call_message_generator("plant", analysis_result)

        assert success is False
        assert advice == ""
        assert "Message generator error" in error

    def test_request_exception(self, mock_env_vars, requests_mock):
        """Test request exception when calling message generator."""
        requests_mock.post(
            "http://message-generator-url",
            exc=Exception("Connection error")
        )

        analysis_result = {
            "labels": [{"description": "Plant", "score": 0.9}]
        }

        success, advice, error = call_message_generator("plant", analysis_result)

        assert success is False
        assert advice == ""
        assert "Error communicating with message generator" in error

    def test_missing_url(self, monkeypatch):
        """Test missing message generator URL."""
        monkeypatch.delenv("MESSAGE_GENERATOR_URL", raising=False)

        analysis_result = {
            "labels": [{"description": "Plant", "score": 0.9}]
        }

        success, advice, error = call_message_generator("plant", analysis_result)

        assert success is False
        assert advice == ""
        assert "Message generator URL not configured" in error


class TestHandleCors:
    """Tests for the handle_cors function."""

    def test_handle_cors_with_origin(self, app):
        """Test CORS handling with Origin header."""
        with app.test_request_context(headers={"Origin": "http://localhost:5173"}):
            response = handle_cors(app.test_request_context().request, {"success": True})

            assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
            assert "POST, OPTIONS" in response.headers["Access-Control-Allow-Methods"]
            assert "Content-Type" in response.headers["Access-Control-Allow-Headers"]
            assert response.headers["Access-Control-Allow-Credentials"] == "true"

    def test_handle_cors_without_origin(self, app):
        """Test CORS handling without Origin header."""
        with app.test_request_context():
            response = handle_cors(app.test_request_context().request, {"success": True})

            assert response.headers["Access-Control-Allow-Origin"] == "*"
            assert "POST, OPTIONS" in response.headers["Access-Control-Allow-Methods"]
            assert "Content-Type" in response.headers["Access-Control-Allow-Headers"]
            assert response.headers["Access-Control-Allow-Credentials"] == "true"

    def test_handle_cors_with_status_code(self, app):
        """Test CORS handling with status code."""
        with app.test_request_context():
            response = handle_cors(app.test_request_context().request, ({"success": False}, 400))

            assert response.status_code == 400
            assert "Access-Control-Allow-Origin" in response.headers


class TestApiGateway:
    """Tests for the api_gateway function."""

    def test_options_request(self, app):
        """Test handling of OPTIONS request."""
        with app.test_request_context(method="OPTIONS"):
            response = api_gateway(app.test_request_context().request)

            assert response.status_code == 204
            assert "Access-Control-Allow-Origin" in response.headers
            assert "Access-Control-Allow-Methods" in response.headers
            assert "Access-Control-Allow-Headers" in response.headers

    def test_invalid_method(self, app):
        """Test handling of invalid HTTP method."""
        with app.test_request_context(method="GET"):
            response = api_gateway(app.test_request_context().request)

            assert response.status_code == 405
            json_response = json.loads(response.data)
            assert json_response["success"] is False
            assert "Only POST requests are supported" in json_response["error"]

    @patch("src.main.validate_request")
    def test_invalid_request(self, mock_validate, app):
        """Test handling of invalid request."""
        mock_validate.return_value = (False, "Invalid request")

        with app.test_request_context(
            method="POST",
            json={"scenario": "invalid", "image_data": "data"}
        ):
            response = api_gateway(app.test_request_context().request)

            assert response.status_code == 400
            json_response = json.loads(response.data)
            assert json_response["success"] is False
            assert "Invalid request" in json_response["error"]

    @patch("src.main.validate_request")
    @patch("src.main.call_image_processor")
    def test_image_processor_error(self, mock_call_image, mock_validate, app, valid_request_json):
        """Test handling of image processor error."""
        mock_validate.return_value = (True, None)
        mock_call_image.return_value = (False, {}, "Image processor error")

        with app.test_request_context(
            method="POST",
            json=valid_request_json
        ):
            response = api_gateway(app.test_request_context().request)

            assert response.status_code == 502
            json_response = json.loads(response.data)
            assert json_response["success"] is False
            assert "Image processor error" in json_response["error"]

    @patch("src.main.validate_request")
    @patch("src.main.call_image_processor")
    @patch("src.main.call_message_generator")
    def test_message_generator_error(self, mock_call_message, mock_call_image, mock_validate, app, valid_request_json):
        """Test handling of message generator error."""
        mock_validate.return_value = (True, None)
        mock_call_image.return_value = (True, {"labels": []}, None)
        mock_call_message.return_value = (False, "", "Message generator error")

        with app.test_request_context(
            method="POST",
            json=valid_request_json
        ):
            response = api_gateway(app.test_request_context().request)

            assert response.status_code == 502
            json_response = json.loads(response.data)
            assert json_response["success"] is False
            assert "Message generator error" in json_response["error"]

    @patch("src.main.validate_request")
    @patch("src.main.call_image_processor")
    @patch("src.main.call_message_generator")
    def test_successful_request(self, mock_call_message, mock_call_image, mock_validate, app, valid_request_json):
        """Test handling of successful request."""
        mock_validate.return_value = (True, None)
        mock_call_image.return_value = (True, {"labels": []}, None)
        mock_call_message.return_value = (True, "Here is some advice", None)

        with app.test_request_context(
            method="POST",
            json=valid_request_json
        ):
            response = api_gateway(app.test_request_context().request)

            assert response.status_code == 200
            json_response = json.loads(response.data)
            assert json_response["success"] is True
            assert json_response["advice"] == "Here is some advice"

    @patch("src.main.validate_request")
    def test_unexpected_exception(self, mock_validate, app, valid_request_json):
        """Test handling of unexpected exception."""
        mock_validate.side_effect = Exception("Unexpected error")

        with app.test_request_context(
            method="POST",
            json=valid_request_json
        ):
            response = api_gateway(app.test_request_context().request)

            assert response.status_code == 500
            json_response = json.loads(response.data)
            assert json_response["success"] is False
            assert "Internal server error" in json_response["error"]
