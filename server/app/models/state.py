"""
Models for state management in the Sprinklr Insights Dashboard application.
"""
from typing import Dict, List, Optional, TypedDict, Literal, Any, Annotated, Sequence
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import operator


class Message(BaseModel):
    """
    Represents a message in the conversation.
    """
    role: Literal["user", "assistant", "system"] = Field(
        description="The role of the message sender"
    )
    content: str = Field(
        description="The content of the message"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the message was sent"
    )


class UserRequirements(BaseModel):
    """
    Represents the user requirements for the dashboard.
    """
    products: List[str] = Field(
        default_factory=list,
        description="List of products the user is interested in"
    )
    channels: List[str] = Field(
        default_factory=list,
        description="List of channels to analyze (e.g., Twitter, Facebook)"
    )
    goals: List[str] = Field(
        default_factory=list,
        description="User's goals (e.g., Brand Awareness, Customer Satisfaction)"
    )
    time_period: Optional[str] = Field(
        default=None,
        description="Time period for analysis (e.g., Last 6 months)"
    )
    focus_areas: List[str] = Field(
        default_factory=list,
        description="Specific areas to focus on (e.g., Customer Feedback, Sentiment Analysis)"
    )
    additional_notes: Optional[str] = Field(
        default=None,
        description="Any additional notes or requirements"
    )
    user_persona: Optional[str] = Field(
        default=None,
        description="The user persona (e.g., Sales Manager)"
    )
    location: Optional[List[str]] = Field(
        default_factory=list,
        description="Geographic locations to focus on"
    )

    def is_complete(self) -> bool:
        """
        Check if all required fields are filled.

        Returns:
            bool: True if all required fields are filled, False otherwise.
        """
        required_fields = ["products", "channels", "goals", "time_period"]
        return all(bool(getattr(self, field)) for field in required_fields)

    def get_missing_fields(self) -> List[str]:
        """
        Get a list of missing required fields.

        Returns:
            List[str]: List of missing field names.
        """
        required_fields = ["products", "channels", "goals", "time_period"]
        return [
            field for field in required_fields
            if not getattr(self, field) or (isinstance(getattr(self, field), list) and not getattr(self, field))
        ]


class QueryBatch(BaseModel):
    """
    Represents a batch of Boolean keyword queries.
    """
    id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for the query batch"
    )
    queries: List[str] = Field(
        default_factory=list,
        description="List of Boolean keyword queries"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When the query batch was created"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the query batch"
    )


class SearchResult(BaseModel):
    """
    Represents a search result from the external API.
    """
    id: str = Field(
        description="Unique identifier for the search result"
    )
    content: str = Field(
        description="Content of the search result"
    )
    source: str = Field(
        description="Source of the search result (e.g., Twitter, Facebook)"
    )
    timestamp: datetime = Field(
        description="When the content was created"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the search result"
    )


class Theme(BaseModel):
    """
    Represents a theme extracted from search results.
    """
    id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for the theme"
    )
    name: str = Field(
        description="Name of the theme"
    )
    keywords: List[str] = Field(
        description="Keywords associated with the theme"
    )
    relevance_score: float = Field(
        description="Relevance score of the theme"
    )
    frequency: int = Field(
        description="Frequency of the theme in the search results"
    )
    sample_posts: List[str] = Field(
        default_factory=list,
        description="Sample posts related to the theme"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the theme"
    )


class ProjectState(TypedDict, total=False):
    """
    Represents the overall state of the project.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_input: Optional[str] # The current user input
    user_requirements: Dict[str, Any] # Store as dict
    query_batches: List[Dict[str, Any]] # Store as list of dicts
    search_results: List[Dict[str, Any]] # Store as list of dicts
    themes: List[Dict[str, Any]] # Store as list of dicts
    current_step: str
    last_updated: str # ISO format string
    all_requirements_collected: bool
    workflow_completed: bool
    conversation_id: Optional[str] # Added for clarity, usually in config
