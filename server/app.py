"""
Main application logic and entry point using Flask.

Provides API endpoints for health checks, status, and query analysis.
"""

import logging
import os
import sys
from datetime import datetime
import asyncio

from flask import Flask, request, jsonify
from flask_cors import CORS

# Add the src directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
from src.utils.files_helper import import_module_from_file
from src.utils.api_helpers import (
    create_success_response,
    create_error_response,
    validate_request_data,
    handle_exceptions,
    log_endpoint_access
)

# Import workflow
workflow_module = import_module_from_file(
    os.path.join(os.path.dirname(__file__), 'src', 'workflow.py'),
    'workflow'
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('sprinklr_dashboard_api.log')
    ]
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global workflow instance
workflow_instance = None

def get_workflow():
    """Get or initialize the workflow instance"""
    global workflow_instance
    if workflow_instance is None:
        logger.info("Initializing workflow instance for the first time.")
        workflow_instance = workflow_module.get_workflow()
    return workflow_instance

@app.route('/')
def index():
    """Home page with basic API information"""
    log_endpoint_access("index")
    data = {
        "message": "Sprinklr Insights Dashboard API",
        "version": "1.0",
        "status": "running"
    }
    return create_success_response(data, "API is running")

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    log_endpoint_access("health_check")
    return create_success_response({"status": "healthy"}, "Service is healthy")

@app.route('/api/status', methods=['GET'])
@handle_exceptions("Error getting service status")
def get_status():
    """Get detailed service status"""
    log_endpoint_access("get_status")
    wf = get_workflow()
    # Assuming workflow has a method to get its status or relevant info
    # For example, wf.get_status() or some properties
    status_info = {
        "workflow_initialized": wf is not None,
        # Add more relevant status details from the workflow if available
        # "last_activity": wf.last_activity_timestamp if hasattr(wf, 'last_activity_timestamp') else None
    }
    return create_success_response(status_info, "API operational")

@app.route('/api/process', methods=['POST'])
@handle_exceptions("Error processing request")
def process_query():
    """
    Unified endpoint to handle both query analysis and user responses.
    
    For new query analysis:
        - Requires 'query' parameter
    
    For responding to existing conversation:
        - Requires 'thread_id' and 'query' parameters
    """
    log_endpoint_access("process_query")
    
    data = request.get_json()
    if not data:
        return create_error_response(
            "No JSON data provided", 
            "Invalid request: Missing JSON data",
            400
        )
    
    # Validate that 'query' field is always present
    validation_error = validate_request_data(['query'], data)
    if validation_error:
        return validation_error
    
    user_query = data['query']
    thread_id = data.get('thread_id')
    
    if thread_id:
        # Handle user response to existing conversation
        logger.info(f"Received response for thread {thread_id}: {user_query}...")
        wf = get_workflow()
        # Invoke the async process_user_response synchronously
        result = asyncio.run(wf.process_user_response(thread_id, user_query))
        logger.info(f"Response processed successfully for thread {thread_id}")
        return create_success_response(result, "Response processed successfully")
    
    else:
        # Handle new query analysis
        logger.info(f"Received query for analysis: {user_query}...")

        wf = get_workflow()
        result = wf.analyze(user_query, data.get('context', {}))
        logger.info(f"Analysis successful for query: {user_query}...")
        return create_success_response(result, "Query analyzed successfully")

@app.route('/api/workflow/status/<thread_id>', methods=['GET'])
@handle_exceptions("Error getting workflow status")
def get_workflow_status(thread_id):
    """Get the status of a specific workflow execution"""
    log_endpoint_access("get_workflow_status", f"thread_id: {thread_id}")
    wf = get_workflow()
    # Retrieve workflow status using the proper method
    status = wf.get_workflow_status(thread_id)
    if status:
        return create_success_response(status, "Workflow status retrieved successfully")
    return create_error_response(
        f"No status found for thread_id: {thread_id}",
        "Status not found for the given thread_id",
        404
    )

@app.route('/api/themes/validate', methods=['POST'])
@handle_exceptions("Error during theme validation")
def validate_themes():
    """Validate and provide feedback on generated themes"""
    log_endpoint_access("validate_themes")
    
    # Validate request data
    validation_error = validate_request_data(['themes'])
    if validation_error:
        return validation_error
    
    data = request.get_json()
    themes_to_validate = data['themes']
    logger.info(f"Received themes for validation: {str(themes_to_validate)}...")

    wf = get_workflow()
    validation_result = wf.validate_themes(themes_to_validate)
    logger.info("Theme validation successful.")
    return create_success_response(validation_result, "Themes validated successfully")

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    logger.warning(f"404 Not Found: {request.url} (Error: {error})")
    return create_error_response(str(error), "Not Found", 404)

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 Internal Server Error: {request.url}")
    return create_error_response(str(error), "Internal Server Error", 500)


if __name__ == "__main__":
    try:
        logger.info("Starting Flask development server.")
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', 8000))
        app.run(host=host, port=port, debug=True)
    except Exception as e:
        logger.critical(f"Failed to start Flask application: {e}")
        sys.exit(1)