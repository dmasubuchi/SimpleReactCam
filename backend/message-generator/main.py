"""
Message Generator for AI Housekeeping Advisor Bot - Cloud Function Entry Point.

This module serves as the entry point for the Message Generator Cloud Function.
It generates housekeeping advice using Google Vertex AI Gemini API based on image analysis.
"""
import functions_framework
from src.main import app

@functions_framework.http
def message_generator(request):
    """HTTP Cloud Function entry point."""
    return app(request)
