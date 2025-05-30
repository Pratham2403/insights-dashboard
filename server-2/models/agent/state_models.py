\
from typing import List, Optional, Dict, Any
from typing_extensions import TypedDict

class ProjectState(TypedDict):
    """
    Represents the state of a project conversation and data processing.
    """
    # User Requirements
    user_persona: Optional[str]
    products: List[str]
    location: Optional[str]
    channels: List[str]
    goals: List[str]
    time_period: Optional[str]
    additional_notes: Optional[str]

    # System State
    conversation_id: str
    current_stage: str  # "collecting", "validating", "querying", "processing", "confirmation", "end"
    missing_fields: List[str]
    is_complete: bool
    requires_human_input: bool

    # Data Processing
    elasticsearch_queries: List[Dict[str, Any]]
    retrieved_data: List[Dict[str, Any]]
    processed_themes: List[Dict[str, Any]]

    # Conversation Flow
    messages: List[Dict[str, str]] # e.g., {"role": "user", "content": "Hello"} or {"role": "ai", "content": "Hi there"}
