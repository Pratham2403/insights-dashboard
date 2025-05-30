"""
State management models for the Sprinklr Insights dashboard.
"""
from typing import Dict, List, Optional, TypedDict, Any
from enum import Enum
from pydantic import BaseModel, Field


class ConversationRole(str, Enum):
    """Roles in a conversation."""
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    """Message model for conversation history."""
    role: ConversationRole
    content: str


class UserRequirements(BaseModel):
    """User requirements for dashboard generation."""
    products: List[str] = Field(default_factory=list, description="List of products to analyze")
    channels: List[str] = Field(default_factory=list, description="List of channels to analyze")
    goals: List[str] = Field(default_factory=list, description="User goals for the dashboard")
    time_period: Optional[str] = Field(None, description="Time period for the analysis")
    additional_notes: Optional[str] = Field(None, description="Additional notes or focus areas")
    user_persona: Optional[str] = Field(None, description="User persona (e.g., Sales Manager)")
    locations: List[str] = Field(default_factory=list, description="Locations or countries to focus on")
    
    def is_complete(self) -> bool:
        """Check if all required fields are filled."""
        return (
            len(self.products) > 0 and
            len(self.channels) > 0 and
            len(self.goals) > 0 and
            self.time_period is not None
        )
    
    def get_missing_fields(self) -> List[str]:
        """Get a list of missing required fields."""
        missing = []
        if not self.products:
            missing.append("products")
        if not self.channels:
            missing.append("channels")
        if not self.goals:
            missing.append("goals")
        if not self.time_period:
            missing.append("time_period")
        return missing


class BooleanQuery(BaseModel):
    """Boolean query model for data retrieval."""
    query_text: str
    target_product: str
    target_channel: str
    target_goal: str
    time_constraint: Optional[str] = None
    location_constraint: Optional[str] = None


class Theme(BaseModel):
    """Theme model for extracted insights."""
    name: str
    keywords: List[str]
    relevance_score: float
    source_queries: List[str]
    associated_product: str
    associated_channel: str
    sentiment: Optional[float] = None


class ProjectState(TypedDict):
    """Complete project state definition."""
    conversation_id: str
    messages: List[Dict[str, str]]
    user_requirements: Dict[str, Any]  # Will be converted to/from UserRequirements
    queries: List[Dict[str, Any]]  # Will be converted to/from BooleanQuery
    extracted_data: List[Dict[str, Any]]  # Raw data from external API
    themes: List[Dict[str, Any]]  # Will be converted to/from Theme
    current_workflow_state: str
