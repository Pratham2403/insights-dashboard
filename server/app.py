"""
Sprinklr Insights Dashboard API

FastAPI implementation using latest LangGraph patterns:
- Workflow orchestration
- Conversation memory management  
- Human-in-the-loop patterns
- Built-in error handling
- Automatic OpenAPI documentation
"""

import logging
import os
import sys
from datetime import datetime
import asyncio
import uuid
from typing import Dict, Any, Optional
from langgraph.types import Command

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Add the src directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
from src.utils.api_helpers import (
    create_success_response,
    create_error_response,
    log_endpoint_access
)

# Import workflow
from src.workflow import (
    get_workflow_history,
    SprinklrWorkflow
)
from src.persistence.mongodb_checkpointer import get_async_mongodb_checkpointer

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

# Initialize FastAPI app
app = FastAPI(
    title="Sprinklr Insights Dashboard API",
    description="FastAPI implementation with LangGraph workflow orchestration for intelligent dashboard generation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response validation
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000, description="User query")
    thread_id: Optional[str] = Field(None, description="Conversation thread ID")

class ApiResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str

class HealthResponse(BaseModel):
    status: str

class StatusResponse(BaseModel):
    workflow_initialized: bool
    memory_enabled: bool
    agents_loaded: int
    timestamp: str

# Global workflow instance
workflow_instance = None

@app.on_event("startup")
async def startup_event():
    global workflow_instance
    if workflow_instance is None:
        logger.info("App Startup")
        workflow_instance = SprinklrWorkflow()
        await workflow_instance.async_init()
        logger.info("Workflow instance initialized with MongoDB persistence.")

def get_workflow():
    """Get or initialize the workflow instance"""
    global workflow_instance
    if workflow_instance is None:
        raise RuntimeError("Workflow instance not initialized. Startup event should handle this.")
    return workflow_instance

@app.get("/", response_model=ApiResponse)
async def index():
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

@app.get("/api/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint"""
    log_endpoint_access("health_check")
    return create_success_response({"status": "healthy"}, "Service is healthy")

@app.get("/api/status", response_model=Dict[str, Any])
async def get_status():
    """Get detailed service status"""
    log_endpoint_access("get_status")
    try:
        wf = get_workflow()
        status_info = {
            "workflow_initialized": wf is not None,
            "memory_enabled": hasattr(wf, 'memory'),
            "agents_loaded": len(wf.__dict__) > 0 if wf else 0,
            "timestamp": datetime.now().isoformat()
        }
        return create_success_response(status_info, "API operational")
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting service status: {str(e)}")

@app.post("/api/process", response_model=Dict[str, Any])
async def process_query(query_request: QueryRequest):
    """    
    Simplified payload structure:
    
    For new conversation:
        {
            "query": "<User Query>"
        }
    
    For continuing conversation:
        {
            "query": "<User's Response>",
            "thread_id": "<thread_id>"
        }
    
    Features:
    - Unified approach - no explicit tracking of new vs existing
    - Uses streaming with interrupt() like helper demo
    - Automatic conversation state management
    - Proper async task handling to prevent task destruction
    """
    log_endpoint_access("process_query")
    
    user_query = query_request.query.strip()
    thread_id = query_request.thread_id
    
    # Log the request details
    logger.info(f"🔍 Processing query: {user_query[:100]}...")
    
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    if len(user_query) > 10000:
        raise HTTPException(status_code=400, detail="Query too long (max 10000 characters)")
    
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
            
            logger.info(f"📜 Starting workflow with inputs: {inputs} and config: {config}")




            # Stream the workflow execution
            async for event in workflow.workflow.astream(inputs, config=config):
                logger.info(f"📨 Completed Streamed event: {list(event.keys())}")

                # Check for interrupt (HITL) following modern LangGraph pattern
                if "__interrupt__" in event:
                    logger.info(f"🛑 Workflow interrupted - getting state for details")
                    
                    # Extract data directly from the interrupt event
                    # The __interrupt__ contains a tuple with the Interrupt object as its first element
                    interrupt_obj = event.get("__interrupt__")[0]  # Access the first element of the tuple
                    interrupt_value = interrupt_obj.value
                    
                    # Initialize defaults
                    message = "Human input required"
                    interrupt_data = {}
                    
                    # Extract interrupt question and instructions if available
                    question = interrupt_value.get("question", "Please review the analysis below and approve to continue:")
                    instructions = interrupt_value.get("instructions", "Reply 'yes' to approve or provide feedback to refine")


                    current_state = await workflow.workflow.aget_state(config=config)
                    # Get current state to extract additional information
                    logger.info(f"📍 Current state during interrupt: {current_state}")


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
                            defaults_applied = state_values.get('defaults_applied', {})
                            entities = state_values.get('entities', [])
                            use_case = state_values.get('use_case', 'General Use Case')
                            industry = state_values.get('industry', '')
                            sub_vertical = state_values.get('sub_vertical', '')
                            conversation_summary = state_values.get('conversation_summary', '')

                            # Combine interrupt event data with state values
                            interrupt_data = {
                                "question": question,
                                "step": interrupt_value.get("step", 1),
                                "refined_query": refined_query,
                                "keywords": keywords if keywords else [],
                                "filters": filters,
                                "data_requirements": data_requirements if data_requirements else [],
                                "defaults_applied": defaults_applied if defaults_applied else {},
                                "entities": entities if entities else [],
                                "use_case": use_case,
                                "industry": industry,
                                "sub_vertical": sub_vertical,
                                "conversation_summary": conversation_summary,
                                "instructions": instructions
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
                    # analyzer_result = event["data_analyzer"]
                    current_state = await workflow.workflow.aget_state(config=config)

                    serialized_result = {
                        "query": current_state.values.get("query", []),
                        "refined_query": current_state.values.get("refined_query", ""),
                        "keywords": current_state.values.get("keywords", []),
                        "filters": current_state.values.get("filters", {}),
                        "data_requirements": current_state.values.get("data_requirements", []),
                        "defaults_applied": current_state.values.get("defaults_applied", {}),
                        "entities": current_state.values.get("entities", []),
                        "use_case": current_state.values.get("use_case", "General Use Case"),
                        "industry": current_state.values.get("industry", ""),
                        "sub_vertical": current_state.values.get("sub_vertical", ""),
                        "conversation_summary": current_state.values.get("conversation_summary", ""),
                        "boolean_query": current_state.values.get("boolean_query", ""),
                        "themes": current_state.values.get("themes", []),
                    }
                    return {
                        "status": "completed",
                        "result": serialized_result,
                        "thread_id": thread_id
                    }
            

            current_state = await workflow.workflow.aget_state(config=config)
            logger.info("✅ Workflow completed - returning current state")
            serialized_result = {
                "query": current_state.values.get("query", []),
                "refined_query": current_state.values.get("refined_query", ""),
                "keywords": current_state.values.get("keywords", []),
                "filters": current_state.values.get("filters", {}),
                "data_requirements": current_state.values.get("data_requirements", []),
                "defaults_applied": current_state.values.get("defaults_applied", {}),
                "entities": current_state.values.get("entities", []),
                "use_case": current_state.values.get("use_case", "General Use Case"),
                "industry": current_state.values.get("industry", ""),
                "sub_vertical": current_state.values.get("sub_vertical", ""),
                "conversation_summary": current_state.values.get("conversation_summary", ""),
                "boolean_query": current_state.values.get("boolean_query", ""),
                "themes": current_state.values.get("themes", []),
            }
            
            return {
                "status": "completed-explicitly",
                "result": serialized_result,
                "thread_id": thread_id
            }

        result = await run_workflow_stream()
        return create_success_response(result, "Query processed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error processing query: {str(e)}")
        logger.error(f"📝 Query was: {user_query[:200]}...")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
                            
@app.get("/api/history/{thread_id}", response_model=Dict[str, Any])
async def get_history(thread_id: str):
    """
    Modern conversation history endpoint using built-in memory.
    
    Leverages LangGraph's automatic persistence.
    """
    log_endpoint_access("get_history")
    
    logger.info(f"Retrieving history for: {thread_id}")
    
    try:
        # Modern history retrieval - built-in persistence
        history = await get_workflow_history(thread_id)
        
        return create_success_response({
            "thread_id": thread_id,
            "messages": history,
            "count": len(history)
        }, "History retrieved")
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")

# Global exception handler
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    logger.warning(f"404 Not Found: {request.url}")
    return JSONResponse(
        status_code=404,
        content=create_error_response("Not Found", "Resource not found", 404)
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors"""
    logger.error(f"500 Internal Server Error: {request.url}")
    return JSONResponse(
        status_code=500,
        content=create_error_response("Internal Server Error", "Internal server error", 500)
    )
