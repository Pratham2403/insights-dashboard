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
    State structure matching multi_agent_system_project_state from PROMPT.md
    
    This structure follows the exact requirements from PROMPT.md:
    - query: List of queries for conversation history
    - refined_query: String containing the refined query
    - keywords: List of extracted keywords
    - filters: Dict containing filter mappings
    - boolean_query: Generated boolean query string
    - themes: List of generated themes with boolean queries
    """
    
    # Core fields as per PROMPT.md
    query: Annotated[List[str], operator.add]  # List of queries for conversation ### IMPORTANT
    refined_query: Optional[str]  # Refined query string ### IMPORTANT
    keywords: Optional[List[str]]  # Extracted keywords list ### IMPORTANT
    filters: Optional[Dict[str, Any]]  # Filter mappings ### IMPORTANT
    boolean_query: Optional[str]  # Generated boolean query ### IMPORTANT
    themes: Optional[List[Dict[str, Any]]]  # Generated themes with boolean queries ### IMPORTANT
    
    # LangGraph compatibility (required)
    messages: Annotated[Sequence[BaseMessage], add_messages] ### IMPORTANT
    
    # Additional tracking fields
    thread_id: Optional[str] ### IMPORTANT
    current_stage: Optional[str]
    workflow_status: Optional[str]
    workflow_started: Optional[str]

    # Metadata for tracking by Grok - matching helper_hitl_demo_code.py
    hitl_step: Optional[int]  ### IMPORTANT - tracks HITL step progression
    user_input: Optional[str]  ### IMPORTANT - current user input
    next_node: Optional[str]   ### IMPORTANT - next node to route to
    reason: Optional[str]      ### IMPORTANT - reason for HITL trigger (e.g., "clarification_needed")
    
    # Processing metadata
    extracted_entities: Optional[List[str]]
    defaults_applied: Optional[List[str]]
    data_requirements: Optional[List[str]] ### IMPORTANT
    
    # HITL verification
    human_feedback: Optional[str]
    needs_human_input: Optional[bool]
    
    # Workflow tracking
    step_history: Optional[List[str]]
    errors: Optional[List[str]]
    warnings: Optional[List[str]]
    
    # Tool and analysis results (simplified)
    tool_results: Optional[Dict[str, Any]]
    analysis_results: Optional[Dict[str, Any]]


def create_initial_state(user_query: str, thread_id: str = None) -> DashboardState:
    """Create initial state for the workflow matching PROMPT.md structure."""
    from langchain_core.messages import HumanMessage
    import time
    
    if not thread_id:
        thread_id = f"conv_{int(time.time())}"
    
    return DashboardState(
        # Core fields as per PROMPT.md
        query=[user_query],  # List of queries
        refined_query=None,
        keywords=None,
        filters=None,
        boolean_query=None,
        themes=None,
        
        # LangGraph compatibility
        messages=[HumanMessage(content=user_query)],
        
        # Tracking fields
        thread_id=thread_id,
        current_stage="initial",
        workflow_status="started",
        workflow_started=datetime.now().isoformat(),
        step_history=[],
        errors=[],
        warnings=[],
        extracted_entities=[],
        defaults_applied=[],
        data_requirements=[],
        
        # HITL state matching helper_hitl_demo_code.py
        hitl_step=0,
        user_input=None,
        next_node=None,
        reason=None
    )
