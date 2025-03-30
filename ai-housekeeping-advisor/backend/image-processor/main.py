"""
Image Processor for AI Housekeeping Advisor Bot - Cloud Function Entry Point.

This module serves as the entry point for the Image Processor Cloud Function.
It processes uploaded images using Google Cloud Vision API and returns structured data.
"""
import functions_framework
from src.main import app

@functions_framework.http
def image_processor(request):
    """HTTP Cloud Function entry point."""
    return app(request)
