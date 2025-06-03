"""
Main application logic and entry point using Flask.

Provides API endpoints for health checks, status, and query analysis.
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
import sys # Ensure sys is imported
import os  # Ensure os is imported
import importlib.util # Ensure importlib.util is imported
import logging # Ensure logging is imported

# Add the src directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
from src.utils.files_helper import import_module_from_file  

# Import workflow and configuration

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
    logger.info("Root endpoint '/' accessed.")
    return jsonify({
        "message": "Sprinklr Insights Dashboard API",
        "version": "1.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    logger.info("Health check endpoint '/api/health' accessed.")
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()}), 200

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get detailed service status"""
    logger.info("Status endpoint '/api/status' accessed.")
    try:
        wf = get_workflow()
        # Assuming workflow has a method to get its status or relevant info
        # For example, wf.get_status() or some properties
        status_info = {
            "workflow_initialized": wf is not None,
            # Add more relevant status details from the workflow if available
            # "last_activity": wf.last_activity_timestamp if hasattr(wf, 'last_activity_timestamp') else None
        }
        return jsonify({"status": "API operational", "details": status_info, "timestamp": datetime.utcnow().isoformat()}), 200
    except Exception as e:
        logger.error(f"Error getting status: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

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
    logger.info("Analyze endpoint '/api/analyze' accessed.")
    data = request.get_json()
    if not data or 'query' not in data:
        logger.warning("Analyze endpoint: Missing 'query' in request data.")
        return jsonify({"error": "Missing 'query' in request data"}), 400

    user_query = data['query']
    logger.info(f"Received query for analysis: {user_query[:100]}...") # Log a snippet of the query

    try:
        wf = get_workflow()
        # Assuming the workflow has an asynchronous method `process_query_async` or similar
        # For Flask, which is synchronous by default, you might run async code differently
        # or the workflow's process_query is synchronous.
        # If workflow_module.get_workflow().process_query is async, this needs to be handled.
        # For now, assuming it can be called directly or is handled internally.
        
        # If process_query is async, and you are in a sync Flask route:
        # result = asyncio.run(wf.process_query(user_query)) # This blocks. Not ideal in a web server.
        # Better to have the workflow expose a sync method or use Flask async support if available.
        # Given the constraints, we will assume a synchronous call path exists or is acceptable.

        # Simulating a call to a potentially complex workflow. 
        # The actual implementation of how `wf.process_query` (or equivalent) is called
        # depends on its signature (sync/async) and how it interacts with agents.
        # For this cleanup, we focus on the Flask part.

        # Placeholder: Replace with actual call to workflow for processing
        # This is a critical part; the actual call to the workflow needs to be correct.
        # For example, if the workflow has a method like `run_analysis`:
        # result = wf.run_analysis(user_query) 
        # Or if it uses the `process_query` method from the CLI example:
        # result = wf.process_query(user_query) # This might be async, see notes above.

        # Use the workflow's process_user_query method 
        # Since it's async, we need to run it using asyncio
        import asyncio
        
        # Check if we're already in an async context
        try:
            loop = asyncio.get_running_loop()
            # If we get here, we're in an async context, so we can't use asyncio.run()
            # We need to create a new thread for this
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, wf.process_user_query(user_query, data.get('context', {})))
                result = future.result()
        except RuntimeError:
            # No running event loop, safe to use asyncio.run()
            result = asyncio.run(wf.process_user_query(user_query, data.get('context', {})))
        
        # Check if the workflow is waiting for user input
        if result.get("workflow_status") == "awaiting_user_input":
            logger.info(f"Workflow is awaiting user input for query: {user_query[:100]}...")
            # Return a status indicating user input is needed
            return jsonify({
                "status": "awaiting_user_input",
                "message": "Additional information is needed to process your request",
                "workflow_status": "awaiting_user_input",
                "conversation_id": result.get("conversation_id", "unknown"),
                "current_step": result.get("current_step", "awaiting_user_verification"),
                "pending_questions": result.get("pending_questions", []),
                "thread_id": result.get("thread_id", f"workflow_{hash(user_query)}")
            }), 200

        logger.info(f"Analysis successful for query: {user_query[:100]}...")
        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error during analysis for query '{user_query[:100]}...': {e}", exc_info=True)
        return jsonify({"error": "An error occurred during analysis", "details": str(e)}), 500

@app.route('/api/workflow/status/<thread_id>', methods=['GET'])
def get_workflow_status(thread_id):
    """Get the status of a specific workflow execution"""
    logger.info(f"Workflow status endpoint for thread_id '{thread_id}' accessed.")
    try:
        wf = get_workflow()
        # Use the workflow's get_workflow_status method 
        status = wf.get_workflow_status(thread_id)
        if status:
            return jsonify(status), 200
        else:
            logger.warning(f"No status found for thread_id: {thread_id}")
            return jsonify({"error": "Status not found for the given thread_id"}), 404

    except Exception as e:
        logger.error(f"Error getting workflow status for thread_id '{thread_id}': {e}", exc_info=True)
        return jsonify({"error": "An error occurred while fetching workflow status", "details": str(e)}), 500

@app.route('/api/themes/validate', methods=['POST'])
def validate_themes():
    """Validate and provide feedback on generated themes"""
    logger.info("Validate themes endpoint '/api/themes/validate' accessed.")
    data = request.get_json()
    if not data or 'themes' not in data:
        logger.warning("Validate themes: Missing 'themes' in request data.")
        return jsonify({"error": "Missing 'themes' in request data"}), 400

    themes_to_validate = data['themes']
    logger.info(f"Received themes for validation: {str(themes_to_validate)[:200]}...")

    try:
        wf = get_workflow()
        if hasattr(wf, 'validate_themes_external'): # Assuming a method name
            validation_result = wf.validate_themes_external(themes_to_validate)
            logger.info("Theme validation successful.")
            return jsonify(validation_result), 200
        else:
            logger.error("Workflow does not have a method for theme validation.")
            return jsonify({"error": "Theme validation not configured in workflow"}), 501

    except Exception as e:
        logger.error(f"Error during theme validation: {e}", exc_info=True)
        return jsonify({"error": "An error occurred during theme validation", "details": str(e)}), 500

@app.route('/api/respond', methods=['POST'])
def respond_to_query():
    """
    Endpoint to handle user responses to pending questions.
    
    Expected JSON payload:
    {
        "thread_id": "workflow_12345", 
        "response": "User's response to the pending question",
        "conversation_id": "optional-conversation-id"
    }
    """
    logger.info("Respond endpoint '/api/respond' accessed.")
    data = request.get_json()
    if not data or 'response' not in data:
        logger.warning("Respond endpoint: Missing 'response' in request data.")
        return jsonify({"error": "Missing 'response' in request data"}), 400
    
    thread_id = data.get('thread_id')
    if not thread_id:
        logger.warning("Respond endpoint: Missing 'thread_id' in request data.")
        return jsonify({"error": "Missing 'thread_id' in request data"}), 400
        
    user_response = data['response']
    logger.info(f"Received response for thread {thread_id}: {user_response[:100]}...")
    
    try:
        wf = get_workflow()
        
        # Use asyncio to call the async method
        import asyncio
        
        # Check if we're already in an async context
        try:
            loop = asyncio.get_running_loop()
            # If we get here, we're in an async context, so we can't use asyncio.run()
            # We need to create a new thread for this
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, wf.process_user_response(thread_id, user_response))
                result = future.result()
        except RuntimeError:
            # No running event loop, safe to use asyncio.run()
            result = asyncio.run(wf.process_user_response(thread_id, user_response))
        
        logger.info(f"Response processed successfully for thread {thread_id}")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error processing response for thread {thread_id}: {e}", exc_info=True)
        return jsonify({"error": "An error occurred while processing your response", "details": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    logger.warning(f"404 Not Found: {request.url} (Error: {error})")
    return jsonify({"error": "Not Found", "message": str(error)}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 Internal Server Error: {request.url} (Error: {error})", exc_info=True)
    return jsonify({"error": "Internal Server Error", "message": str(error)}), 500

# Removed create_app() as it's not strictly necessary if app is created directly.
# The prompt implies focusing on web-server paths, and `app` is already the Flask app instance.
# If create_app was used for specific configurations or extensions, that logic would need to be merged
# into the main app setup or kept if it's essential for the web server operation.
# For now, assuming direct `app` usage is sufficient for the web server path.

if __name__ == "__main__":
    # This block is typically for development server. 
    # In production, a WSGI server like Gunicorn or uWSGI would be used.
    # The prompt focuses on web-server code paths, so this is relevant for local running.
    try:
        logger.info("Starting Flask development server.")
        # Fetch host and port from environment variables or use defaults
        # Consistent with .env.example (PORT=8000, HOST=0.0.0.0)
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', 8000))
        app.run(host=host, port=port, debug=True) # debug=False for production-like logging
    except Exception as e:
        logger.critical(f"Failed to start Flask application: {e}", exc_info=True)
        sys.exit(1) # Exit if the server can't start