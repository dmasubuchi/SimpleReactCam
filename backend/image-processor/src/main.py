"""
Image Processor for AI Advisor Bot.

This module processes images using Google Cloud Vision API and returns structured data.
It serves as a generic image analysis service for multi-scenario advisor bots.
"""
import base64
import json
import logging
import os
from typing import Dict, Any, List, Optional, Tuple, Union

import functions_framework
from flask import Request, jsonify
from google.cloud import vision
from google.cloud import secretmanager
from google.cloud.vision_v1 import types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SECRET_NAME = "vision-api-key"
MIN_CONFIDENCE_SCORE = 0.6  # Minimum confidence score for labels and objects


def get_vision_api_key() -> str:
    """
    Retrieve the Vision API key from Secret Manager.
    
    Returns:
        str: The API key as a string.
        
    Raises:
        Exception: If there's an error retrieving the API key.
    """
    try:
        logger.info("Retrieving Vision API key from Secret Manager")
        
        client = secretmanager.SecretManagerServiceClient()
        
        project_id = os.environ.get("PROJECT_ID", "")
        if not project_id:
            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
            
        if not project_id:
            raise ValueError("Project ID not found in environment variables")
            
        name = f"projects/{project_id}/secrets/{SECRET_NAME}/versions/latest"
        
        response = client.access_secret_version(request={"name": name})
        
        api_key = response.payload.data.decode("UTF-8")
        logger.info("Successfully retrieved Vision API key")
        
        return api_key
    except Exception as e:
        logger.error(f"Error retrieving Vision API key: {str(e)}")
        raise


def decode_image(image_data: str) -> bytes:
    """
    Decode base64 encoded image data.
    
    Args:
        image_data: Base64 encoded image string.
        
    Returns:
        bytes: Decoded image bytes.
        
    Raises:
        ValueError: If the image data is invalid.
    """
    try:
        if "base64," in image_data:
            image_data = image_data.split("base64,")[1]
            
        image_bytes = base64.b64decode(image_data)
        return image_bytes
    except Exception as e:
        logger.error(f"Error decoding image: {str(e)}")
        raise ValueError(f"Invalid image data: {str(e)}")


def analyze_image(image_bytes: bytes, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze an image using Google Cloud Vision API.
    
    Args:
        image_bytes: The image bytes to analyze.
        api_key: Optional API key. If not provided, uses ADC.
        
    Returns:
        Dict[str, Any]: A dictionary containing the analysis results.
        
    Raises:
        Exception: If there's an error during image analysis.
    """
    try:
        client = vision.ImageAnnotatorClient()
        
        image = vision.Image(content=image_bytes)
        
        label_response = client.label_detection(image=image)
        
        object_response = client.object_localization(image=image)
        
        text_response = client.text_detection(image=image)
        
        labels = []
        if label_response.label_annotations:
            for label in label_response.label_annotations:
                if label.score >= MIN_CONFIDENCE_SCORE:
                    labels.append({
                        "description": label.description,
                        "score": round(label.score, 2)
                    })
        
        objects = []
        if object_response.localized_object_annotations:
            for obj in object_response.localized_object_annotations:
                if obj.score >= MIN_CONFIDENCE_SCORE:
                    objects.append({
                        "name": obj.name,
                        "score": round(obj.score, 2)
                    })
        
        text = ""
        if text_response.text_annotations and len(text_response.text_annotations) > 0:
            text = text_response.text_annotations[0].description
        
        logger.info(f"Image analysis complete. Found {len(labels)} labels, {len(objects)} objects, and {'text' if text else 'no text'}")
        
        return {
            "labels": labels,  # List of label objects with description and score
            "objects": objects,  # List of object objects with name and score
            "text": text  # String containing detected text, empty if none
        }
    except Exception as e:
        logger.error(f"Error analyzing image: {str(e)}")
        raise


def validate_request(request_json: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate the request JSON.
    
    Args:
        request_json: The request JSON to validate.
        
    Returns:
        Tuple[bool, Optional[str]]: A tuple containing a boolean indicating if the request is valid,
                                   and an optional error message.
    """
    if not request_json:
        return False, "Request body is empty"
    
    if "image_data" not in request_json:
        return False, "Missing 'image_data' field in request"
    
    if not request_json["image_data"]:
        return False, "Empty 'image_data' field in request"
    
    return True, None


@functions_framework.http
def process_image(request: Request) -> Dict[str, Any]:
    """
    Cloud Function entry point for processing images.
    
    Args:
        request: The HTTP request object.
        
    Returns:
        Dict[str, Any]: A JSON response containing the analysis results or error details.
    """
    logger.info(f"Image processor function invoked with method: {request.method}")
    
    if request.method != "POST":
        logger.error(f"Invalid request method: {request.method}")
        return jsonify({
            "success": False,
            "data": None,
            "error": "Only POST requests are supported"
        }), 405
    
    try:
        request_json = request.get_json(silent=True)
        
        is_valid, error_message = validate_request(request_json)
        if not is_valid:
            logger.error(f"Invalid request: {error_message}")
            return jsonify({
                "success": False,
                "data": None,
                "error": error_message
            }), 400
        
        image_data = request_json["image_data"]
        image_bytes = decode_image(image_data)
        
        api_key = get_vision_api_key()
        analysis_results = analyze_image(image_bytes, api_key)
        
        return jsonify({
            "success": True,
            "data": analysis_results,
            "error": None
        })
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({
            "success": False,
            "data": None,
            "error": str(e)
        }), 400
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            "success": False,
            "data": None,
            "error": f"Internal server error: {str(e)}"
        }), 500


if __name__ == "__main__":
    from flask import Flask, request as flask_request
    
    app = Flask(__name__)
    
    @app.route("/process", methods=["POST"])
    def process():
        return process_image(flask_request)
    
    app.run(host="0.0.0.0", port=8081, debug=True)
