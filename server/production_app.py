#!/usr/bin/env python3
"""
Production-ready Flask application for Sprinklr Insights Dashboard
Integrates modern LangGraph workflow with performance monitoring
"""

import logging
import os
import sys
import asyncio
import time
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps

from flask import Flask, request, jsonify, g
from flask_cors import CORS

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Import configuration
from production_config import ProductionConfig

# Import API helpers
from src.utils.api_helpers import (
    create_success_response,
    create_error_response,
    validate_request_data,
    handle_exceptions,
    log_endpoint_access
)

# Configure logging for production
logging.basicConfig(
    level=getattr(logging, ProductionConfig.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(ProductionConfig.LOG_FILE)
    ]
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global variables for lazy initialization
modern_workflow_instance = None
workflow_initialized = False
initialization_error = None

def initialize_modern_workflow():
    """Initialize the modern workflow with error handling"""
    global modern_workflow_instance, workflow_initialized, initialization_error
    
    if workflow_initialized:
        return modern_workflow_instance
    
    try:
        logger.info("🚀 Initializing Modern Sprinklr Workflow...")
        start_time = time.time()
        
        # Import workflow functions
        from src.complete_modern_workflow import (
            process_dashboard_request,
            handle_user_feedback,
            get_workflow_history,
            get_modern_workflow_status,
            modern_workflow
        )
        
        # Set up the workflow functions
        modern_workflow_instance = {
            'process_dashboard_request': process_dashboard_request,
            'handle_user_feedback': handle_user_feedback,
            'get_workflow_history': get_workflow_history,
            'get_status': get_modern_workflow_status,
            'workflow_instance': modern_workflow
        }
        
        initialization_time = time.time() - start_time
        logger.info(f"✅ Modern Workflow initialized in {initialization_time:.2f}s")
        
        workflow_initialized = True
        initialization_error = None
        
        return modern_workflow_instance
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Modern Workflow: {e}")
        logger.error(traceback.format_exc())
        initialization_error = str(e)
        workflow_initialized = False
        return None

def require_workflow(f):
    """Decorator to ensure workflow is initialized"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not workflow_initialized:
            workflow = initialize_modern_workflow()
            if not workflow:
                return create_error_response(
                    f"Workflow initialization failed: {initialization_error}",
                    "Service temporarily unavailable",
                    503
                )
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def before_request():
    """Set up request context"""
    g.request_start_time = time.time()

@app.after_request  
def after_request(response):
    """Log request performance"""
    if hasattr(g, 'request_start_time'):
        duration = time.time() - g.request_start_time
        if duration > 1.0:  # Log slow requests
            logger.warning(f"Slow request: {request.path} took {duration:.2f}s")
    return response

# Health check endpoints
@app.route('/')
def index():
    """Home page with API information"""
    return create_success_response({
        "service": "Sprinklr Insights Dashboard API",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "Modern LangGraph workflow",
            "Lazy loading for performance",
            "Thread-based conversation memory",
            "HITL verification patterns",
            "Production-ready monitoring"
        ]
    }, "API is running")

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Sprinklr Insights Dashboard"
    })

@app.route('/api/health', methods=['GET'])
def detailed_health_check():
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "workflow_initialized": workflow_initialized,
        "initialization_error": initialization_error,
        "config": ProductionConfig.get_config()
    }
    
    # Check workflow status if initialized
    if workflow_initialized and modern_workflow_instance:
        try:
            workflow_status = modern_workflow_instance['get_status']()
            health_status["workflow_status"] = workflow_status
        except Exception as e:
            health_status["workflow_status"] = {"error": str(e)}
    
    return create_success_response(health_status, "Health check completed")

# Modern workflow endpoints
@app.route('/api/v2/process', methods=['POST'])
@require_workflow
@handle_exceptions("Modern processing error")
def modern_process_query():
    """
    Modern endpoint for processing dashboard queries
    """
    log_endpoint_access("modern_process_query")
    
    data = request.get_json()
    if not data or 'query' not in data:
        return create_error_response("Missing query parameter", "Invalid request", 400)
    
    user_query = data['query']
    conversation_id = data.get('conversation_id')
    
    logger.info(f"Processing modern query: {user_query[:100]}...")
    
    try:
        # Run the async workflow
        result = asyncio.run(modern_workflow_instance['process_dashboard_request'](
            user_query, conversation_id
        ))
        
        logger.info("Modern processing completed successfully")
        return create_success_response(result, "Query processed successfully")
        
    except Exception as e:
        logger.error(f"Modern processing error: {e}")
        return create_error_response(str(e), "Processing failed", 500)

@app.route('/api/v2/feedback', methods=['POST'])
@require_workflow
@handle_exceptions("Modern feedback error")
def modern_handle_feedback():
    """
    Modern HITL feedback endpoint
    """
    log_endpoint_access("modern_handle_feedback")
    
    data = request.get_json()
    if not data or 'conversation_id' not in data or 'feedback' not in data:
        return create_error_response("Missing required parameters", "Invalid request", 400)
    
    conversation_id = data['conversation_id']
    feedback = data['feedback']
    
    logger.info(f"Processing feedback for conversation: {conversation_id}")
    
    try:
        result = asyncio.run(modern_workflow_instance['handle_user_feedback'](
            conversation_id, feedback
        ))
        
        logger.info("Feedback processed successfully")
        return create_success_response(result, "Feedback processed")
        
    except Exception as e:
        logger.error(f"Feedback processing error: {e}")
        return create_error_response(str(e), "Feedback processing failed", 500)

@app.route('/api/v2/history/<conversation_id>', methods=['GET'])
@require_workflow
@handle_exceptions("Modern history error")
def modern_get_history(conversation_id):
    """
    Get conversation history
    """
    log_endpoint_access("modern_get_history")
    
    logger.info(f"Retrieving history for: {conversation_id}")
    
    try:
        history = asyncio.run(modern_workflow_instance['get_workflow_history'](conversation_id))
        
        return create_success_response({
            "conversation_id": conversation_id,
            "messages": history,
            "count": len(history)
        }, "History retrieved successfully")
        
    except Exception as e:
        logger.error(f"History retrieval error: {e}")
        return create_error_response(str(e), "History retrieval failed", 500)

@app.route('/api/v2/status', methods=['GET'])
def modern_status():
    """
    Modern status endpoint with detailed system information
    """
    try:
        status_info = {
            "status": "operational",
            "version": "2.0.0", 
            "timestamp": datetime.now().isoformat(),
            "workflow_initialized": workflow_initialized,
            "initialization_error": initialization_error,
            "features": [
                "Modern LangGraph workflow",
                "Built-in memory management",
                "Advanced HITL patterns", 
                "Lazy loading optimization",
                "Production monitoring"
            ],
            "performance": {
                "lazy_loading_enabled": ProductionConfig.LAZY_LOADING_ENABLED,
                "max_concurrent_workflows": ProductionConfig.MAX_CONCURRENT_WORKFLOWS,
                "workflow_timeout": ProductionConfig.WORKFLOW_TIMEOUT
            }
        }
        
        # Add workflow status if available
        if workflow_initialized and modern_workflow_instance:
            try:
                workflow_status = modern_workflow_instance['get_status']()
                status_info["workflow_details"] = workflow_status
            except Exception as e:
                status_info["workflow_error"] = str(e)
        
        return create_success_response(status_info, "Status retrieved successfully")
        
    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        return create_error_response(str(e), "Status retrieval failed", 500)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    logger.warning(f"404 Not Found: {request.url}")
    return create_error_response("Endpoint not found", "Not Found", 404)

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 Internal Server Error: {request.url}")
    return create_error_response("Internal server error", "Internal Server Error", 500)

@app.errorhandler(503)
def service_unavailable_error(error):
    """Handle 503 errors"""
    logger.error(f"503 Service Unavailable: {request.url}")
    return create_error_response("Service temporarily unavailable", "Service Unavailable", 503)

if __name__ == "__main__":
    try:
        logger.info("🚀 Starting Sprinklr Insights Dashboard API...")
        logger.info(f"Configuration: {ProductionConfig.get_config()}")
        
        # Initialize workflow on startup for better performance
        if ProductionConfig.LAZY_LOADING_ENABLED:
            logger.info("Lazy loading enabled - workflow will initialize on first request")
        else:
            logger.info("Pre-initializing workflow...")
            initialize_modern_workflow()
        
        # Start Flask app
        app.run(
            host=ProductionConfig.FLASK_HOST,
            port=ProductionConfig.FLASK_PORT,
            debug=ProductionConfig.FLASK_DEBUG,
            threaded=True
        )
        
    except Exception as e:
        logger.critical(f"Failed to start application: {e}")
        sys.exit(1)
