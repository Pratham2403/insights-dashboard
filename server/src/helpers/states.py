"""
This module consists of the Different States of the Multi-Agent System.

It can contain States of Specific Agent, or the Overall State of the Multi-Agent System or the Orchestration State of the Multi-Agent System.
This is used to maintain the state of the Multi-Agent System and the agents in the system.

# Purpose of this module:
- To define the states used by various agents in the application.
- To provide a centralized location for managing states, making it easier to update and maintain them.
- To maintain consistency, modularity, and reusability of states across different agents.


"""




from typing import Dict, List, Optional, TypedDict, Literal, Any,Annotated, Sequence
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID, uuid4
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import operator


# Add more States as needed for the Multi-Agent System.

class AgentState(BaseModel):
    """
    Represents the State of the Multi-Agent System.
    It contains the State of the Multi-Agent System.
    
    """
    
    
    messages: Annotated[Sequence[BaseMessage], add_messages]
    refined_query: str
    #There can be many more fields in the future.
    