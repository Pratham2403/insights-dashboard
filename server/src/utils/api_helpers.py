"""
API utility functions for standardizing responses, error handling, and request validation.
FastAPI compatible version.
"""

import asyncio
import logging
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional, Tuple, Union

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def create_success_response(data: Any, message: str = "Success", status_code: int = 200) -> Dict[str, Any]:
    """
    Create a standardized success response for FastAPI.
    
    Args:
        data: The response data
        message: Success message
        status_code: HTTP status code (included for consistency but not used in FastAPI response)
        
    Returns:
        Dictionary response
    """
    response = {
        "status": "success",
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    return response


def create_error_response(
    error: Union[str, Exception], 
    message: str = "An error occurred",
    status_code: int = 500,
    details: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response for FastAPI.
    
    Args:
        error: The error message or exception
        message: User-friendly error message
        status_code: HTTP status code (included for consistency but not used in FastAPI response)
        details: Additional error details
        
    Returns:
        Dictionary response
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
    
    return response


def validate_request_data(required_fields: list, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Validate that required fields are present in request data for FastAPI.
    
    Args:
        required_fields: List of required field names
        data: Request data dictionary (from Pydantic model)
        
    Returns:
        Error response dict if validation fails, None if validation passes
    """
    if not data:
        return create_error_response(
            "No data provided", 
            "Invalid request: Missing data",
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
    Decorator for handling exceptions in FastAPI endpoints.
    
    Args:
        default_message: Default error message for unhandled exceptions
        
    Usage:
        @handle_exceptions("Error processing request")
        async def my_endpoint():
            # endpoint logic
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except ValueError as e:
                logger.error(f"ValueError in {func.__name__}: {e}")
                raise HTTPException(status_code=400, detail=str(e))
            except KeyError as e:
                logger.error(f"KeyError in {func.__name__}: {e}")
                raise HTTPException(status_code=400, detail=f"Missing required data: {e}")
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                raise HTTPException(status_code=500, detail=default_message)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValueError as e:
                logger.error(f"ValueError in {func.__name__}: {e}")
                raise HTTPException(status_code=400, detail=str(e))
            except KeyError as e:
                logger.error(f"KeyError in {func.__name__}: {e}")
                raise HTTPException(status_code=400, detail=f"Missing required data: {e}")
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                raise HTTPException(status_code=500, detail=default_message)
        
        # Return the appropriate wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
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


