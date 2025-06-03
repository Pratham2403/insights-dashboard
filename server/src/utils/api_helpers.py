"""
API utility functions for standardizing responses, error handling, and request validation.
"""

import logging
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional, Tuple, Union
from flask import jsonify, request

logger = logging.getLogger(__name__)


def create_success_response(data: Any, message: str = "Success", status_code: int = 200):
    """
    Create a standardized success response.
    
    Args:
        data: The response data
        message: Success message
        status_code: HTTP status code
        
    Returns:
        Flask response tuple
    """
    response = {
        "status": "success",
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    return jsonify(response), status_code


def create_error_response(
    error: Union[str, Exception], 
    message: str = "An error occurred",
    status_code: int = 500,
    details: Optional[Any] = None
):
    """
    Create a standardized error response.
    
    Args:
        error: The error message or exception
        message: User-friendly error message
        status_code: HTTP status code
        details: Additional error details
        
    Returns:
        Flask response tuple
    """
    error_str = str(error)
    
    response = {
        "status": "error",
        "message": message,
        "error": error_str,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if details:
        response["details"] = details
    
    # Log the error
    logger.error(f"{message}: {error_str}")
    
    return jsonify(response), status_code


def validate_request_data(required_fields: list, data: Optional[Dict] = None):
    """
    Validate that required fields are present in request data.
    
    Args:
        required_fields: List of required field names
        data: Request data (defaults to request.get_json())
        
    Returns:
        Error response tuple if validation fails, None if validation passes
    """
    if data is None:
        data = request.get_json()
    
    if not data:
        return create_error_response(
            "No JSON data provided", 
            "Invalid request: Missing JSON data",
            400
        )
    
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return create_error_response(
            f"Missing required fields: {', '.join(missing_fields)}",
            "Invalid request: Missing required fields",
            400,
            {"missing_fields": missing_fields}
        )
    
    return None


def handle_exceptions(default_message: str = "An unexpected error occurred"):
    """
    Decorator for handling exceptions in API endpoints.
    
    Args:
        default_message: Default error message for unhandled exceptions
        
    Usage:
        @handle_exceptions("Error processing request")
        def my_endpoint():
            # endpoint logic
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValueError as e:
                return create_error_response(e, "Invalid input", 400)
            except KeyError as e:
                return create_error_response(e, "Missing required data", 400)
            except Exception as e:
                return create_error_response(e, default_message, 500)
        return wrapper
    return decorator


def log_endpoint_access(endpoint_name: str, additional_info: str = ""):
    """
    Log endpoint access with standardized format.
    
    Args:
        endpoint_name: Name of the endpoint
        additional_info: Additional information to log
    """
    info_str = f"Endpoint '{endpoint_name}' accessed"
    if additional_info:
        info_str += f" - {additional_info}"
    logger.info(info_str)


def extract_pagination_params(default_page: int = 0, default_size: int = 100) -> Dict[str, int]:
    """
    Extract pagination parameters from request args.
    
    Args:
        default_page: Default page number
        default_size: Default page size
        
    Returns:
        Dictionary with 'page' and 'size' keys
    """
    try:
        page = int(request.args.get('page', default_page))
        size = int(request.args.get('size', default_size))
        
        # Ensure reasonable limits
        page = max(0, page)
        size = min(max(1, size), 1000)  # Cap at 1000 items per page
        
        return {"page": page, "size": size}
    except ValueError:
        return {"page": default_page, "size": default_size}
