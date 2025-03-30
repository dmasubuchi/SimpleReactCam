"""
API Gateway for AI Housekeeping Advisor Bot - Cloud Function Entry Point.

This module serves as the entry point for the API Gateway Cloud Function.
It handles HTTP requests from the frontend, orchestrates calls to other functions,
and returns the final response.
"""
import functions_framework
from src.main import app

@functions_framework.http
def api_gateway(request):
    """HTTP Cloud Function entry point."""
    return app(request)
