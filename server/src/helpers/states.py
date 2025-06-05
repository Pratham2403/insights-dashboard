"""
Modern state management using latest LangGraph built-in patterns.

This modernized version leverages:
- TypedDict for LangGraph compatibility
- Built-in annotations for state management
- Simplified type definitions
- Reduced code complexity through LangGraph primitives
"""

from typing import Dict, List, Optional, Any, Annotated, Sequence, TypedDict
from datetime import datetime
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import operator


class DashboardState(TypedDict):
    """
    Modern dashboard state using TypedDict for LangGraph compatibility.
    
    Key improvements:
    - Compatible with LangGraph StateGraph
    - Automatic message handling
    - Simplified state management
    - Built-in message persistence
    """
    
    # Required: messages for LangGraph compatibility
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Conversation tracking
    conversation_id: Optional[str]
    current_stage: Optional[str]
    thread_id: Optional[str]
    workflow_status: Optional[str]
    
    # User query and context
    user_query: Optional[str]
    user_context: Optional[Dict[str, Any]]
    
    # Processing data - simplified structure
    refined_query: Optional[str]
    query_context: Optional[Dict[str, Any]]
    defaults_applied: Optional[List[str]]
    
    # Data collection
    keywords: Optional[List[str]]
    filters: Optional[Dict[str, Any]]
    data_requirements: Optional[Dict[str, Any]]
    extracted_entities: Optional[List[str]]
    
    # Query generation
    boolean_query: Optional[str]
    query_metadata: Optional[Dict[str, Any]]
    
    # Tool results
    tool_results: Optional[Dict[str, Any]]
    fetched_data: Optional[List[Dict[str, Any]]]
    
    # Analysis results
    analysis_results: Optional[Dict[str, Any]]
    insights: Optional[List[str]]
    themes: Optional[List[Dict[str, Any]]]
    summary: Optional[str]
    
    # HITL verification
    hitl_summary: Optional[Dict[str, Any]]
    hitl_iteration: Optional[int]
    human_feedback: Optional[str]
    needs_human_input: Optional[bool]
    human_input_payload: Optional[Dict[str, Any]]
    awaiting_human_input: Optional[bool]
    
    # Workflow tracking
    workflow_started: Optional[str]
    current_step: Optional[str]
    current_stage: Optional[str]
    step_history: Optional[List[str]]
    
    # Error handling
    errors: Optional[List[str]]
    warnings: Optional[List[str]]


def create_initial_state(user_query: str, conversation_id: str = None) -> DashboardState:
    """Create initial state for the workflow."""
    from langchain_core.messages import HumanMessage
    import time
    
    if not conversation_id:
        conversation_id = f"conv_{int(time.time())}"
    
    return DashboardState(
        messages=[HumanMessage(content=user_query)],
        conversation_id=conversation_id,
        user_query=user_query,
        current_stage="initial",
        workflow_status="started",
        workflow_started=datetime.now().isoformat(),
        step_history=[],
        errors=[],
        warnings=[]
    )
