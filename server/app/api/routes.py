"""
API routes for the Sprinklr Insights Dashboard application.
"""
from typing import Dict, List, Any, Optional, Union
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
import logging
from app.workflows.insights_dashboard_workflow import process_message, create_or_load_conversation
from app.utils.state_manager import get_state_manager, generate_conversation_id
from uuid import UUID
from datetime import datetime


logger = logging.getLogger(__name__)
router = APIRouter()
state_manager = get_state_manager()


class ChatMessage(BaseModel):
    """
    A chat message in the conversation.
    """
    role: str = Field(..., description="The role of the message sender (user or assistant)")
    content: str = Field(..., description="The content of the message")
    timestamp: Optional[datetime] = Field(None, description="When the message was sent")


class ChatRequest(BaseModel):
    """
    Request for the chat endpoint.
    """
    conversation_id: Optional[str] = Field(None, description="The ID of the conversation")
    message: str = Field(..., description="The user message")


class ChatResponse(BaseModel):
    """
    Response from the chat endpoint.
    """
    conversation_id: str = Field(..., description="The ID of the conversation")
    messages: List[ChatMessage] = Field(..., description="The conversation messages")
    user_requirements: Dict[str, Any] = Field({}, description="The user requirements")
    themes: List[Dict[str, Any]] = Field([], description="The extracted themes")
    current_step: Optional[str] = Field(None, description="The current step in the workflow")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint for the Sprinklr Insights Dashboard.
    
    Args:
        request: The chat request.
        
    Returns:
        The chat response.
    """
    try:
        # Process message
        result = await process_message(request.conversation_id, request.message)
        
        # Extract data from result
        conversation_id = result["conversation_id"]
        state = result["state"]
        
        # Convert messages to ChatMessage objects
        messages = [
            ChatMessage(
                role=msg["role"],
                content=msg["content"],
                timestamp=datetime.fromisoformat(msg.get("timestamp", datetime.now().isoformat())) 
                if "timestamp" in msg else datetime.now()
            )
            for msg in state.get("messages", [])
        ]
        
        # Create response
        response = ChatResponse(
            conversation_id=conversation_id,
            messages=messages,
            user_requirements=state.get("user_requirements", {}),
            themes=state.get("themes", []),
            current_step=state.get("current_step")
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")


@router.get("/conversations", response_model=List[str])
async def list_conversations():
    """
    List all conversations.
    
    Returns:
        List of conversation IDs.
    """
    try:
        conversations = await state_manager.list_conversations()
        return conversations
        
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing conversations: {str(e)}")


@router.get("/state/{conversation_id}", response_model=Dict[str, Any])
async def get_state(conversation_id: str):
    """
    Get the state of a conversation.
    
    Args:
        conversation_id: The ID of the conversation.
        
    Returns:
        The conversation state.
    """
    try:
        state = await state_manager.get_state(conversation_id)
        
        if not state:
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
        
        return state
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting state: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting state: {str(e)}")


@router.delete("/state/{conversation_id}")
async def delete_state(conversation_id: str):
    """
    Delete a conversation state.
    
    Args:
        conversation_id: The ID of the conversation.
        
    Returns:
        Success message.
    """
    try:
        deleted = await state_manager.delete_state(conversation_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
        
        return {"status": "success", "message": f"Conversation {conversation_id} deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting state: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting state: {str(e)}")


class MockSearchRequest(BaseModel):
    """
    Request for the mock search endpoint.
    """
    query: str = Field(..., description="The search query")
    limit: int = Field(10, description="The maximum number of results to return")


@router.post("/mock-search", response_model=Dict[str, Any])
async def mock_search(request: MockSearchRequest):
    """
    Mock search endpoint for testing.
    
    Args:
        request: The search request.
        
    Returns:
        Mock search results.
    """
    try:
        # Create a data processing agent to generate mock results
        from app.agents.data_processing_agent import DataProcessingAgent
        
        agent = DataProcessingAgent()
        results = agent._simulate_search_results(request.query)
        
        # Limit results if needed
        if len(results) > request.limit:
            results = results[:request.limit]
        
        return {"results": results}
        
    except Exception as e:
        logger.error(f"Error in mock search: {e}")
        raise HTTPException(status_code=500, detail=f"Error in mock search: {str(e)}")
