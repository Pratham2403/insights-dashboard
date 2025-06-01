"""
This module contains the main application logic and entry point if using the flask framework and working with API
"""

import os
import sys
import logging
import asyncio
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
import json

# Add the src directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Import workflow and configuration
import importlib.util

def import_module_from_file(filepath, module_name):
    """Helper function to import modules with dots in filenames"""
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

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
        workflow_instance = workflow_module.get_workflow()
    return workflow_instance

@app.route('/')
def index():
    """Home page with basic API information"""
    return jsonify({
        "service": "Sprinklr Listening Dashboard API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "POST /api/analyze": "Analyze user query and generate themes",
            "GET /api/status": "Get service status",
            "GET /api/health": "Health check endpoint"
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        return jsonify({
            "status": "healthy",
            "service": "Sprinklr Dashboard API",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "workflow": "operational",
                "agents": "operational",
                "database": "operational"
            }
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get detailed service status"""
    try:
        workflow = get_workflow()
        
        return jsonify({
            "status": "operational",
            "service": "Sprinklr Listening Dashboard",
            "version": "1.0.0",
            "uptime": "operational",
            "components": {
                "query_refiner": "ready",
                "query_generator": "ready", 
                "data_collector": "ready",
                "data_analyzer": "ready",
                "hitl_verification": "ready",
                "workflow_engine": "ready"
            },
            "capabilities": [
                "Query refinement",
                "Boolean query generation",
                "Data analysis",
                "Theme categorization",
                "HITL verification"
            ],
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_query():
    """
    Main endpoint to analyze user queries and generate themes.
    
    Expected JSON payload:
    {
        "query": "User's natural language query",
        "context": {
            "user_preferences": {},
            "session_data": {},
            "analysis_options": {}
        }
    }
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Request must be JSON",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required field: 'query'",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        user_query = data['query'].strip()
        if not user_query:
            return jsonify({
                "success": False,
                "error": "Query cannot be empty",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        user_context = data.get('context', {})
        
        logger.info(f"Received analysis request for query: {user_query[:100]}...")
        
        # Process the query asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            workflow = get_workflow()
            result = loop.run_until_complete(
                workflow.process_user_query(user_query, user_context)
            )
        finally:
            loop.close()
        
        # Format response
        response = {
            "success": result.get("success", False),
            "status": result.get("status", "unknown"),
            "current_step": result.get("current_step", "unknown"),
            "query": {
                "original": user_query,
                "refined": result.get("refined_query", ""),
                "boolean": result.get("boolean_query", "")
            },
            "themes": result.get("themes", []),
            "analysis_summary": result.get("analysis_summary", {}),
            "errors": result.get("errors", []),
            "processing_time": result.get("processing_time", datetime.now().isoformat()),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Analysis completed - Status: {response['status']}, Themes: {len(response['themes'])}")
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "status": "failed",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/workflow/status/<thread_id>', methods=['GET'])
def get_workflow_status(thread_id):
    """Get the status of a specific workflow execution"""
    try:
        workflow = get_workflow()
        status = workflow.get_workflow_status(thread_id)
        
        return jsonify({
            "success": True,
            "thread_id": thread_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting workflow status: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/themes/validate', methods=['POST'])
def validate_themes():
    """Validate and provide feedback on generated themes"""
    try:
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Request must be JSON"
            }), 400
        
        data = request.get_json()
        themes = data.get('themes', [])
        feedback = data.get('feedback', {})
        
        # Process validation (placeholder for now)
        validated_themes = []
        for theme in themes:
            validated_theme = theme.copy()
            validated_theme['validated'] = True
            validated_theme['validation_score'] = 0.8  # Mock score
            validated_themes.append(validated_theme)
        
        return jsonify({
            "success": True,
            "validated_themes": validated_themes,
            "validation_summary": {
                "total_themes": len(themes),
                "validated_count": len(validated_themes),
                "average_score": 0.8
            },
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating themes: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "message": "The requested endpoint does not exist",
        "timestamp": datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "message": "An unexpected error occurred",
        "timestamp": datetime.now().isoformat()
    }), 500

def create_app():
    """Application factory function"""
    try:
        # Initialize workflow on startup
        get_workflow()
        logger.info("Application initialized successfully")
        return app
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        # Initialize the application
        app = create_app()
        
        # Get configuration from environment variables
        host = os.getenv('FLASK_HOST', '0.0.0.0')
        port = int(os.getenv('FLASK_PORT', 5000))
        debug = os.getenv('FLASK_ENV') == 'development'
        
        logger.info(f"Starting Sprinklr Dashboard API server on {host}:{port}")
        logger.info(f"Debug mode: {debug}")
        
        # Start the Flask development server
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        sys.exit(1)