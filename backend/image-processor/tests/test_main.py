"""
Unit tests for the image processor function.
"""
import base64
import json
import os
import unittest
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

import sys
from unittest.mock import MagicMock

mock_vision = MagicMock()
mock_secretmanager = MagicMock()
sys.modules['google.cloud.vision'] = mock_vision
sys.modules['google.cloud.vision_v1'] = MagicMock()
sys.modules['google.cloud.secretmanager'] = mock_secretmanager

from src.main import process_image, validate_request, decode_image, analyze_image


class TestImageProcessor(unittest.TestCase):
    """Test cases for the image processor function."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.valid_image_data = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAIBAQIBAQICAgICAgICAwUDAwMDAwYEBAMFBwYHBwcGBwcICQsJCAgKCAcHCg0KCgsMDAwMBwkODw0MDgsMDAz/2wBDAQICAgMDAwYDAwYMCAcIDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAz/wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD9/KKKKAP/2Q=="
        self.mock_request = MagicMock()
        self.mock_request.method = "POST"
        self.mock_request.get_json.return_value = {"image_data": self.valid_image_data}

    def test_validate_request_valid(self):
        """Test validation with valid request."""
        request_json = {"image_data": self.valid_image_data}
        is_valid, error = validate_request(request_json)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_request_missing_image_data(self):
        """Test validation with missing image_data field."""
        request_json = {"other_field": "value"}
        is_valid, error = validate_request(request_json)
        self.assertFalse(is_valid)
        self.assertEqual(error, "Missing 'image_data' field in request")

    def test_validate_request_empty_image_data(self):
        """Test validation with empty image_data field."""
        request_json = {"image_data": ""}
        is_valid, error = validate_request(request_json)
        self.assertFalse(is_valid)
        self.assertEqual(error, "Empty 'image_data' field in request")

    def test_validate_request_empty_json(self):
        """Test validation with empty JSON."""
        request_json = {}
        is_valid, error = validate_request(request_json)
        self.assertFalse(is_valid)
        self.assertEqual(error, "Request body is empty")

    def test_decode_image_valid(self):
        """Test decoding a valid base64 image."""
        base64_str = "YQ=="  # 'a' in base64
        result = decode_image(base64_str)
        self.assertEqual(result, b'a')

    def test_decode_image_with_data_url(self):
        """Test decoding a base64 image with data URL prefix."""
        data_url = "data:image/jpeg;base64,YQ=="  # 'a' in base64 with data URL prefix
        result = decode_image(data_url)
        self.assertEqual(result, b'a')

    def test_decode_image_invalid(self):
        """Test decoding an invalid base64 string."""
        with self.assertRaises(ValueError):
            decode_image("invalid base64 string")

    @patch('src.main.vision.ImageAnnotatorClient')
    def test_analyze_image_success(self, mock_client_class):
        """Test successful image analysis."""
        mock_client = mock_client_class.return_value
        
        mock_label = MagicMock()
        mock_label.description = "Kitchen"
        mock_label.score = 0.92
        mock_label_response = MagicMock()
        mock_label_response.label_annotations = [mock_label]
        mock_client.label_detection.return_value = mock_label_response
        
        mock_object = MagicMock()
        mock_object.name = "Refrigerator"
        mock_object.score = 0.98
        mock_object_response = MagicMock()
        mock_object_response.localized_object_annotations = [mock_object]
        mock_client.object_localization.return_value = mock_object_response
        
        mock_text_annotation = MagicMock()
        mock_text_annotation.description = "Sample Text"
        mock_text_response = MagicMock()
        mock_text_response.text_annotations = [mock_text_annotation]
        mock_client.text_detection.return_value = mock_text_response
        
        result = analyze_image(b'test_image')
        
        self.assertEqual(result["labels"][0]["description"], "Kitchen")
        self.assertEqual(result["labels"][0]["score"], 0.92)
        self.assertEqual(result["objects"][0]["name"], "Refrigerator")
        self.assertEqual(result["objects"][0]["score"], 0.98)
        self.assertEqual(result["text"], "Sample Text")

    @patch('src.main.vision.ImageAnnotatorClient')
    def test_analyze_image_no_results(self, mock_client_class):
        """Test image analysis with no results."""
        mock_client = mock_client_class.return_value
        
        mock_label_response = MagicMock()
        mock_label_response.label_annotations = []
        mock_client.label_detection.return_value = mock_label_response
        
        mock_object_response = MagicMock()
        mock_object_response.localized_object_annotations = []
        mock_client.object_localization.return_value = mock_object_response
        
        mock_text_response = MagicMock()
        mock_text_response.text_annotations = []
        mock_client.text_detection.return_value = mock_text_response
        
        result = analyze_image(b'test_image')
        
        self.assertEqual(result["labels"], [])
        self.assertEqual(result["objects"], [])
        self.assertEqual(result["text"], "")

    @patch('src.main.vision.ImageAnnotatorClient')
    def test_analyze_image_error(self, mock_client_class):
        """Test image analysis with an error."""
        mock_client = mock_client_class.return_value
        mock_client.label_detection.side_effect = Exception("API Error")
        
        with self.assertRaises(Exception):
            analyze_image(b'test_image')

    @patch('src.main.get_vision_api_key')
    @patch('src.main.analyze_image')
    @patch('src.main.decode_image')
    def test_process_image_success(self, mock_decode, mock_analyze, mock_get_key):
        """Test successful image processing."""
        mock_decode.return_value = b'decoded_image'
        mock_get_key.return_value = "fake-api-key"
        mock_analyze.return_value = {
            "labels": [{"description": "Kitchen", "score": 0.92}],
            "objects": [{"name": "Refrigerator", "score": 0.98}],
            "text": "Sample Text"
        }
        
        with self.app.test_request_context(
            json={"image_data": self.valid_image_data},
            method="POST"
        ):
            with self.app.app_context():
                response = process_image(self.mock_request)
                
        response_data = json.loads(response.get_data(as_text=True))
        
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["data"]["labels"][0]["description"], "Kitchen")
        self.assertEqual(response_data["data"]["objects"][0]["name"], "Refrigerator")
        self.assertEqual(response_data["data"]["text"], "Sample Text")
        self.assertIsNone(response_data["error"])

    def test_process_image_invalid_method(self):
        """Test image processing with invalid HTTP method."""
        self.mock_request.method = "GET"
        
        with self.app.app_context():
            response = process_image(self.mock_request)
            
            response_data = json.loads(response[0].data)
            status_code = response[1]
            
            self.assertFalse(response_data["success"])
            self.assertIsNone(response_data["data"])
            self.assertEqual(response_data["error"], "Only POST requests are supported")
            self.assertEqual(status_code, 405)

    def test_process_image_invalid_request(self):
        """Test image processing with invalid request."""
        self.mock_request.get_json.return_value = {}
        
        with self.app.app_context():
            response = process_image(self.mock_request)
            
            response_data = json.loads(response[0].data)
            status_code = response[1]
            
            self.assertFalse(response_data["success"])
            self.assertIsNone(response_data["data"])
            self.assertEqual(response_data["error"], "Request body is empty")
            self.assertEqual(status_code, 400)

    @patch('src.main.decode_image')
    def test_process_image_decode_error(self, mock_decode):
        """Test image processing with decode error."""
        mock_decode.side_effect = ValueError("Invalid base64")
        
        with self.app.test_request_context(
            json={"image_data": "invalid_data"},
            method="POST"
        ):
            with self.app.app_context():
                response = process_image(self.mock_request)
                
        response_data = json.loads(response[0].data)
        status_code = response[1]
        
        self.assertFalse(response_data["success"])
        self.assertIsNone(response_data["data"])
        self.assertEqual(response_data["error"], "Invalid base64")
        self.assertEqual(status_code, 400)

    @patch('src.main.get_vision_api_key')
    @patch('src.main.decode_image')
    @patch('src.main.analyze_image')
    def test_process_image_analysis_error(self, mock_analyze, mock_decode, mock_get_key):
        """Test image processing with analysis error."""
        mock_decode.return_value = b'decoded_image'
        mock_get_key.return_value = "fake-api-key"
        mock_analyze.side_effect = Exception("API Error")
        
        with self.app.test_request_context(
            json={"image_data": self.valid_image_data},
            method="POST"
        ):
            with self.app.app_context():
                response = process_image(self.mock_request)
                
        response_data = json.loads(response[0].data)
        status_code = response[1]
        
        self.assertFalse(response_data["success"])
        self.assertIsNone(response_data["data"])
        self.assertTrue("API Error" in response_data["error"])
        self.assertEqual(status_code, 500)

    @patch('src.main.get_vision_api_key')
    @patch('src.main.decode_image')
    def test_process_image_secret_manager_error(self, mock_decode, mock_get_key):
        """Test image processing with Secret Manager error."""
        mock_decode.return_value = b'decoded_image'
        mock_get_key.side_effect = Exception("Secret Manager Error")
        
        with self.app.test_request_context(
            json={"image_data": self.valid_image_data},
            method="POST"
        ):
            response = process_image(self.mock_request)
            
        response_data = json.loads(response[0].data)
        status_code = response[1]
        
        self.assertFalse(response_data["success"])
        self.assertIsNone(response_data["data"])
        self.assertTrue("Secret Manager Error" in response_data["error"])
        self.assertEqual(status_code, 500)


if __name__ == "__main__":
    unittest.main()
