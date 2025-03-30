"""
API Gateway for AI Housekeeping Advisor Bot.

This module serves as the entry point for the API Gateway Cloud Function.
It handles HTTP requests from the frontend, orchestrates calls to other functions,
and returns the final response.
"""
import json
import logging
import os
from typing import Dict, Any, Optional, Tuple

import functions_framework
from flask import Request, jsonify, make_response
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IMAGE_PROCESSOR_URL = os.environ.get("IMAGE_PROCESSOR_URL", "")
MESSAGE_GENERATOR_URL = os.environ.get("MESSAGE_GENERATOR_URL", "")

VALID_SCENARIOS = ["plant", "closet", "fridge"]


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
    
    if "scenario" not in request_json:
        return False, "Missing 'scenario' field in request"
    
    if request_json["scenario"] not in VALID_SCENARIOS:
        return False, f"Invalid 'scenario' value. Must be one of: {', '.join(VALID_SCENARIOS)}"
    
    if "image_data" not in request_json:
        return False, "Missing 'image_data' field in request"
    
    if not request_json["image_data"]:
        return False, "Empty 'image_data' field in request"
    
    return True, None


def call_image_processor(image_data: str) -> Tuple[bool, Dict[str, Any], Optional[str]]:
    """
    Call the image-processor function with the provided image data.
    
    Args:
        image_data: Base64 encoded image string.
        
    Returns:
        Tuple[bool, Dict[str, Any], Optional[str]]: A tuple containing:
            - A boolean indicating if the call was successful
            - The analysis result data (or empty dict if failed)
            - An optional error message (if failed)
    """
    if not IMAGE_PROCESSOR_URL:
        logger.error("IMAGE_PROCESSOR_URL environment variable not set")
        return False, {}, "Image processor URL not configured"
    
    try:
        logger.info(f"Calling image-processor at {IMAGE_PROCESSOR_URL}")
        
        response = requests.post(
            IMAGE_PROCESSOR_URL,
            json={"image_data": image_data},
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"Image processor returned status code {response.status_code}: {response.text}")
            return False, {}, f"Image processor error: {response.text}"
        
        response_data = response.json()
        
        if not response_data.get("success", False):
            error_msg = response_data.get("error", "Unknown error")
            logger.error(f"Image processor returned error: {error_msg}")
            return False, {}, f"Image processor error: {error_msg}"
        
        analysis_result = response_data.get("data", {})
        logger.info("Successfully received analysis result from image-processor")
        
        return True, analysis_result, None
    
    except requests.RequestException as e:
        logger.error(f"Error calling image-processor: {str(e)}")
        return False, {}, f"Error communicating with image processor: {str(e)}"


def call_message_generator(scenario: str, analysis_result: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
    """
    Call the message-generator function with the scenario and analysis result.
    
    Args:
        scenario: The scenario identifier (plant, closet, or fridge).
        analysis_result: The analysis result from the image-processor.
        
    Returns:
        Tuple[bool, str, Optional[str]]: A tuple containing:
            - A boolean indicating if the call was successful
            - The generated advice (or empty string if failed)
            - An optional error message (if failed)
    """
    if not MESSAGE_GENERATOR_URL:
        logger.error("MESSAGE_GENERATOR_URL environment variable not set")
        return False, "", "Message generator URL not configured"
    
    try:
        logger.info(f"Calling message-generator at {MESSAGE_GENERATOR_URL}")
        
        response = requests.post(
            MESSAGE_GENERATOR_URL,
            json={
                "scenario": scenario,
                "analysis_result": analysis_result
            },
            timeout=60  # Longer timeout for Gemini API calls
        )
        
        if response.status_code != 200:
            logger.error(f"Message generator returned status code {response.status_code}: {response.text}")
            return False, "", f"Message generator error: {response.text}"
        
        response_data = response.json()
        
        if not response_data.get("success", False):
            error_msg = response_data.get("error", "Unknown error")
            logger.error(f"Message generator returned error: {error_msg}")
            return False, "", f"Message generator error: {error_msg}"
        
        advice = response_data.get("advice", "")
        logger.info("Successfully received advice from message-generator")
        
        return True, advice, None
    
    except requests.RequestException as e:
        logger.error(f"Error calling message-generator: {str(e)}")
        return False, "", f"Error communicating with message generator: {str(e)}"


def handle_cors(request: Request, response: Any) -> Any:
    """
    Add CORS headers to the response.
    
    Args:
        request: The HTTP request object.
        response: The response object.
        
    Returns:
        The response object with CORS headers added.
    """
    origin = request.headers.get("Origin", "*")
    
    if isinstance(response, tuple):
        data, status_code = response
        response = make_response(data, status_code)
    else:
        response = make_response(response)
    
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    
    return response


@functions_framework.http
def api_gateway(request: Request) -> Any:
    """
    Cloud Function entry point for the API Gateway.
    
    Args:
        request: The HTTP request object.
        
    Returns:
        The HTTP response object.
    """
    if request.method == "OPTIONS":
        logger.info("Handling OPTIONS request (CORS preflight)")
        response = make_response("")
        return handle_cors(request, (response, 204))
    
    if request.method != "POST":
        logger.error(f"Invalid request method: {request.method}")
        return handle_cors(
            request,
            (jsonify({
                "success": False,
                "error": "Only POST requests are supported"
            }), 405)
        )
    
    try:
        request_json = request.get_json(silent=True)
        
        is_valid, error_message = validate_request(request_json)
        if not is_valid:
            logger.error(f"Invalid request: {error_message}")
            return handle_cors(
                request,
                (jsonify({
                    "success": False,
                    "error": error_message
                }), 400)
            )
        
        scenario = request_json["scenario"]
        image_data = request_json["image_data"]
        
        logger.info(f"Processing request for scenario: {scenario}")
        
        success, analysis_result, error = call_image_processor(image_data)
        if not success:
            return handle_cors(
                request,
                (jsonify({
                    "success": False,
                    "error": error
                }), 502)
            )
        
        success, advice, error = call_message_generator(scenario, analysis_result)
        if not success:
            return handle_cors(
                request,
                (jsonify({
                    "success": False,
                    "error": error
                }), 502)
            )
        
        logger.info("Request processed successfully")
        return handle_cors(
            request,
            jsonify({
                "success": True,
                "advice": advice
            })
        )
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return handle_cors(
            request,
            (jsonify({
                "success": False,
                "error": f"Internal server error: {str(e)}"
            }), 500)
        )


if __name__ == "__main__":
    from flask import Flask, request as flask_request
    
    app = Flask(__name__)
    
    @app.route("/chat", methods=["POST", "OPTIONS"])
    def chat():
        return api_gateway(flask_request)
    
    app.run(host="0.0.0.0", port=8080, debug=True)
