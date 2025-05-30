"""
State management utilities.
"""
import json
import uuid
import os
from typing import Dict, Any, Optional
from pathlib import Path

from models.state import ProjectState, UserRequirements, BooleanQuery, Theme


def generate_conversation_id() -> str:
    """
    Generate a unique conversation ID.
    
    Returns:
        Unique conversation ID
    """
    return str(uuid.uuid4())


def initialize_state(conversation_id: Optional[str] = None) -> ProjectState:
    """
    Initialize a new project state.
    
    Args:
        conversation_id: Optional conversation ID
        
    Returns:
        Initialized ProjectState
    """
    conversation_id = conversation_id or generate_conversation_id()
    
    return {
        "conversation_id": conversation_id,
        "messages": [],
        "user_requirements": UserRequirements().dict(),
        "queries": [],
        "extracted_data": [],
        "themes": [],
        "current_workflow_state": "START"
    }


def save_state(state: ProjectState, data_dir: Path) -> None:
    """
    Save project state to a file.
    
    Args:
        state: Project state to save
        data_dir: Directory to save state file
    """
    conversation_id = state["conversation_id"]
    state_file = data_dir / f"{conversation_id}.json"
    
    os.makedirs(data_dir, exist_ok=True)
    
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)


def load_state(conversation_id: str, data_dir: Path) -> Optional[ProjectState]:
    """
    Load project state from a file.
    
    Args:
        conversation_id: Conversation ID
        data_dir: Directory containing state files
        
    Returns:
        Loaded ProjectState or None if not found
    """
    state_file = data_dir / f"{conversation_id}.json"
    
    if not state_file.exists():
        return None
    
    with open(state_file, "r") as f:
        state = json.load(f)
    
    return state


def update_user_requirements(state: ProjectState, requirements_update: Dict[str, Any]) -> ProjectState:
    """
    Update user requirements in the project state.
    
    Args:
        state: Current project state
        requirements_update: Updates to apply to user requirements
        
    Returns:
        Updated project state
    """
    current_requirements = UserRequirements.parse_obj(state["user_requirements"])
    
    # Update each field that is provided
    for field, value in requirements_update.items():
        if hasattr(current_requirements, field):
            setattr(current_requirements, field, value)
    
    # Update the state with the modified requirements
    state["user_requirements"] = current_requirements.dict()
    
    return state


def add_message(state: ProjectState, role: str, content: str) -> ProjectState:
    """
    Add a message to the conversation history.
    
    Args:
        state: Current project state
        role: Message role ('user' or 'assistant')
        content: Message content
        
    Returns:
        Updated project state
    """
    state["messages"].append({
        "role": role,
        "content": content
    })
    
    return state
