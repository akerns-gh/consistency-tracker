"""
API Response formatting utilities for Lambda functions.
"""

import json
from typing import Any, Dict, Optional


def success_response(
    data: Any = None,
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Create a successful API Gateway response.

    Args:
        data: Response data (will be JSON serialized)
        status_code: HTTP status code (default: 200)
        headers: Additional headers to include

    Returns:
        API Gateway response dictionary
    """
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",  # Will be restricted in API Gateway
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    }

    if headers:
        default_headers.update(headers)

    response_body = {"success": True}
    if data is not None:
        response_body["data"] = data

    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": json.dumps(response_body, default=str),
    }


def error_response(
    message: str,
    status_code: int = 400,
    error_code: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Create an error API Gateway response.

    Args:
        message: Error message
        status_code: HTTP status code (default: 400)
        error_code: Optional error code for client handling
        headers: Additional headers to include

    Returns:
        API Gateway response dictionary
    """
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",  # Will be restricted in API Gateway
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    }

    if headers:
        default_headers.update(headers)

    response_body = {
        "success": False,
        "error": {
            "message": message,
        },
    }

    if error_code:
        response_body["error"]["code"] = error_code

    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": json.dumps(response_body, default=str),
    }


def cors_preflight_response() -> Dict[str, Any]:
    """
    Create a CORS preflight (OPTIONS) response.

    Returns:
        API Gateway response dictionary for OPTIONS requests
    """
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        },
        "body": "",
    }

