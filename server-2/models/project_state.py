from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid

class ProjectState(BaseModel):
    """
    Represents the state of a project conversation and data processing.
    """
    # User Requirements
    user_persona: Optional[str] = None
    products: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    channels: List[str] = Field(default_factory=list)
    goals: List[str] = Field(default_factory=list)
    time_period: Optional[str] = None
    additional_notes: Optional[str] = None
    
    # System State
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    current_stage: str = "collecting"  # "collecting", "validating", "querying", "processing", "completed"
    missing_fields: List[str] = Field(default_factory=list)
    is_complete: bool = False
    requires_human_input: bool = True # Initially true to start HITL
    
    # Data Processing
    elasticsearch_queries: List[Dict[str, Any]] = Field(default_factory=list)
    retrieved_data: List[Dict[str, Any]] = Field(default_factory=list)
    processed_themes: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Conversation Flow
    messages: List[Dict[str, str]] = Field(default_factory=list) # e.g., [{"role": "user", "content": "Hello"}, {"role": "ai", "content": "Hi there!"}]

    class Config:
        arbitrary_types_allowed = True

# Example usage:
# state = ProjectState(products=["Galaxy S25"], conversation_id="test-convo-123")
# print(state.model_dump_json(indent=2))
