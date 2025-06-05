"""
Modern Sprinklr Insights Dashboard API

Clean, modern implementation using latest LangGraph patterns:
- Modern workflow orchestration
- Conversation memory management  
- Human-in-the-loop patterns
- Built-in error handling
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
from src.utils.api_helpers import (
    create_success_response,
    create_error_response,
    validate_request_data,
    handle_exceptions,
    log_endpoint_access
)

# Import modern workflow
from src.workflow import (
    process_dashboard_request,
    handle_user_feedback,
    get_workflow_history,
    SprinklrWorkflow
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

# Global modern workflow instance
modern_workflow_instance = None

def get_modern_workflow():
    """Get or initialize the modern workflow instance"""
    global modern_workflow_instance
    if modern_workflow_instance is None:
        logger.info("Initializing modern workflow instance for the first time.")
        modern_workflow_instance = SprinklrWorkflow()
    return modern_workflow_instance

@app.route('/')
def index():
    """Home page with basic API information"""
    log_endpoint_access("index")
    data = {
        "message": "Sprinklr Insights Dashboard API - Modern Implementation",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Modern LangGraph workflow",
            "Conversation memory management",
            "Human-in-the-loop verification",
            "Advanced agent orchestration"
        ]
    }
    return create_success_response(data, "Modern API is running")

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
    wf = get_modern_workflow()
    status_info = {
        "workflow_initialized": wf is not None,
        "memory_enabled": hasattr(wf, 'memory'),
        "agents_loaded": len(wf.__dict__) > 0 if wf else 0,
        "timestamp": datetime.now().isoformat()
    }
    return create_success_response(status_info, "Modern API operational")

@app.route('/api/process', methods=['POST'])
@handle_exceptions("Modern processing error")
def process_query():
    """
    Modern unified endpoint for query processing and conversation management.
    
    For new query analysis:
        - Requires 'query' parameter
        - Optional 'conversation_id' parameter
    
    For responding to existing conversation:
        - Requires 'conversation_id' and 'query' parameters
    """
    log_endpoint_access("process_query")
    
    data = request.get_json()
    if not data or 'query' not in data:
        return create_error_response("Missing query parameter", "Invalid request", 400)
    
    user_query = data['query']
    conversation_id = data.get('conversation_id')
    
    logger.info(f"Processing query: {user_query[:100]}...")
    
    # Use modern workflow for all processing
    result = asyncio.run(process_dashboard_request(user_query, conversation_id))
    
    logger.info("Query processing completed successfully")
    return create_success_response(result, "Query processed successfully")

@app.route('/api/feedback', methods=['POST'])
@handle_exceptions("Modern feedback error")
def handle_feedback():
    """
    Modern HITL feedback endpoint using interrupt patterns.
    
    Handles human-in-the-loop verification for data collection results.
    """
    log_endpoint_access("handle_feedback")
    
    data = request.get_json()
    if not data or 'conversation_id' not in data or 'feedback' not in data:
        return create_error_response("Missing required parameters", "Invalid request", 400)
    
    conversation_id = data['conversation_id']
    feedback = data['feedback']
    
    logger.info(f"Processing feedback for conversation: {conversation_id}")
    
    # Modern feedback handling
    result = asyncio.run(handle_user_feedback(conversation_id, feedback))
    
    logger.info("Feedback processed successfully")
    return create_success_response(result, "Feedback processed")

@app.route('/api/history/<conversation_id>', methods=['GET'])
@handle_exceptions("Modern history error")
def get_history(conversation_id):
    """
    Modern conversation history endpoint using built-in memory.
    
    Leverages LangGraph's automatic persistence.
    """
    log_endpoint_access("get_history")
    
    logger.info(f"Retrieving history for: {conversation_id}")
    
    # Modern history retrieval - built-in persistence
    history = asyncio.run(get_workflow_history(conversation_id))
    
    return create_success_response({
        "conversation_id": conversation_id,
        "messages": history,
        "count": len(history)
    }, "History retrieved")

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
        logger.info("Starting Modern Sprinklr Dashboard API...")
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', 8000))
        app.run(host=host, port=port, debug=True)
    except Exception as e:
        logger.critical(f"Failed to start Flask application: {e}")
        sys.exit(1)
