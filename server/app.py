"""
Sprinklr Insights Dashboard API

Implementation using latest LangGraph patterns:
- Workflow orchestration
- Conversation memory management  
- Human-in-the-loop patterns
- Built-in error handling
"""

import logging
import os
import sys
from datetime import datetime
import asyncio
import uuid
from langgraph.types import Command


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

# Import workflow
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

# Global workflow instance
workflow_instance = None

def get_workflow():
    """Get or initialize the workflow instance"""
    global workflow_instance
    if workflow_instance is None:
        logger.info("Initializing workflow instance for the first time.")
        workflow_instance = SprinklrWorkflow()
    return workflow_instance

@app.route('/')
def index():
    """Home page with basic API information"""
    log_endpoint_access("index")
    data = {
        "message": "Sprinklr Insights Dashboard API",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "LangGraph workflow",
            "Conversation memory management",
            "Human-in-the-loop verification",
            "Advanced agent orchestration"
        ]
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
    status_info = {
        "workflow_initialized": wf is not None,
        "memory_enabled": hasattr(wf, 'memory'),
        "agents_loaded": len(wf.__dict__) > 0 if wf else 0,
        "timestamp": datetime.now().isoformat()
    }
    return create_success_response(status_info, "API operational")

@app.route('/api/process', methods=['POST'])
@handle_exceptions("Processing error")
def process_query():
    """    
    Simplified payload structure:
    
    For new conversation:
        {
            "query": "<User Query>"
        }
    
    For continuing conversation:
        {
            "query": "<User's Response>",
            "thread_id": "<conversation_id>"
        }
    
    Features:
    - Unified approach - no explicit tracking of new vs existing
    - Uses streaming with interrupt() like helper demo
    - Automatic conversation state management
    - Proper async task handling to prevent task destruction
    """
    log_endpoint_access("process_query")
    
    data = request.get_json()
    if not data or 'query' not in data:
        return create_error_response("Missing query parameter", "Invalid request", 400)
    
    user_query = data['query'].strip()
    thread_id = data.get('thread_id')
    
    # Log the request details
    logger.info(f"🔍 Processing query: {user_query[:100]}...")
    
    if not user_query:
        return create_error_response("Query cannot be empty", "Invalid request", 400)
    
    if len(user_query) > 10000:
        return create_error_response("Query too long (max 10000 characters)", "Invalid request", 400)
    
    try:
        workflow = get_workflow()
        
        if thread_id is None:
            thread_id = str(uuid.uuid4())
            inputs = {"query": [user_query]}
            logger.info(f"🆕 Starting new conversation: {thread_id}")
        else:
            inputs = None  
            logger.info(f"🔄 Continuing conversation: {thread_id} with input: {user_query}")
        
        # Prepare configuration for the workflow
        config = {"configurable": {"thread_id": thread_id}}
        
        # Use asyncio to handle the async stream properly

        
        async def run_workflow_stream():
            """Run the workflow stream in an async context to handle streaming and interrupts"""
            
            # For continuing conversations, use Command pattern 
            # Thread ID Present but the inputs are None
            if thread_id and inputs is None:
                # Get current state of the Graph
                current_state = await workflow.workflow.aget_state(config=config)
                logger.info(f"📍 Current state before resume: hitl_step={current_state}")
                
                # Use Command(resume=...) pattern 
                # The HITL verification node will handle the user input directly through yield interrupt()
                logger.info(f"🔄 Resuming workflow with Command(resume='{user_query}')")
                await workflow.workflow.ainvoke(Command(resume=user_query), config=config)
            
            # Stream the workflow execution
            async for event in workflow.workflow.astream(inputs, config=config):
                logger.info(f"📨 Completed Streamed event: {list(event.keys())}")
                # Check for interrupt (HITL) following modern LangGraph pattern
                if "__interrupt__" in event:
                    logger.info(f"🛑 Workflow interrupted - getting state for details")
                    
                    # Get current state to extract interrupt information
                    current_state = await workflow.workflow.aget_state(config=config)
                    
                    message = "Human input required"
                    interrupt_data = {}
                    
                    # Try to get interrupt data from the state's values
                    if hasattr(current_state, 'values') and current_state.values:
                        state_values = current_state.values
                        logger.info(f"📜 Current state values: {state_values}")
                        # Check if we have HITL data in the state
                        if 'refined_query' in state_values:
                            refined_query = state_values.get('refined_query', '')
                            keywords = state_values.get('keywords', [])
                            filters = state_values.get('filters', {})
                            data_requirements = state_values.get('data_requirements', [])
                            
                            interrupt_data = {
                                "question": "Please review the analysis below and approve to continue:",
                                "step": 1,
                                "refined_query": refined_query,
                                "keywords": keywords[:5] if keywords else [],
                                "filters": filters,
                                "data_requirements": data_requirements if data_requirements else [],
                                "instructions": "Reply 'yes' to approve or provide feedback to refine"
                            }
                            message = f"Review analysis: {refined_query[:100]}..."
                    
                    return {
                        "status": "waiting_for_input",
                        "message": message,
                        "thread_id": thread_id,
                        "interrupt_data": interrupt_data
                    }
                
                # Check if final node output is present (completion)
                elif event.get("data_analyzer"):  # Final node in our workflow
                    logger.info("✅ Workflow completed successfully")
                    
                    # Serialize the data_analyzer result to handle AIMessage objects
                    analyzer_result = event["data_analyzer"]
                    serialized_result = workflow._serialize_state_for_json(analyzer_result)
                    
                    return {
                        "status": "completed",
                        "result": serialized_result,
                        "thread_id": thread_id
                    }
            
            # If stream ends without explicit completion, get current state
            current_state = await workflow.workflow.aget_state(config=config)
            state_values = current_state.values if current_state else {}
            logger.info("✅ Workflow completed - returning current state")
            
            # Use the workflow's serialization method to handle AIMessage objects
            serialized_state = workflow._serialize_state_for_json(state_values)
            
            return {
                "status": "completed",
                "result": serialized_state,
                "thread_id": thread_id
            }

        
        def run_async_workflow():
            """Wrapper to run async workflow in Flask context"""
            try:
                # Check if there's already an event loop
                try:
                    loop = asyncio.get_running_loop()
                    logger.warning("Event loop already running - cannot use asyncio.run")
                    # If we're in an existing loop, we need to handle differently
                    # This shouldn't happen in Flask normally, but let's be safe
                    raise RuntimeError("Cannot use asyncio.run in existing loop")
                except RuntimeError:
                    # No loop running - this is the normal Flask case
                    return asyncio.run(run_workflow_stream())
            except Exception as e:
                logger.error(f"❌ Async workflow error: {e}")
                raise
        
        result = run_async_workflow()
        return create_success_response(result, "Query processed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error processing query: {str(e)}")
        logger.error(f"📝 Query was: {user_query[:200]}...")
        return create_error_response(f"Processing failed: {str(e)}", "Processing error", 500)


@app.route('/api/history/<thread_id>', methods=['GET'])
@handle_exceptions("Modern history error")
def get_history(thread_id):
    """
    Modern conversation history endpoint using built-in memory.
    
    Leverages LangGraph's automatic persistence.
    """
    log_endpoint_access("get_history")
    
    logger.info(f"Retrieving history for: {thread_id}")
    
    # Modern history retrieval - built-in persistence
    history = asyncio.run(get_workflow_history(thread_id))
    
    return create_success_response({
        "thread_id": thread_id,
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
