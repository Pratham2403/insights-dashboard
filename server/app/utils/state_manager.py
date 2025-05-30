"""
Utilities for state management in the Sprinklr Insights Dashboard application.
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import uuid4
import aiofiles
from pathlib import Path
from app.config.settings import settings


logger = logging.getLogger(__name__)


class FileSystemStateManager:
    """
    Manages state persistence using the file system.
    """
    
    def __init__(self):
        """
        Initialize the FileSystemStateManager.
        
        Creates the memory directory if it doesn't exist.
        """
        self.memory_path = Path(settings.MEMORY_PATH)
        os.makedirs(self.memory_path, exist_ok=True)
    
    async def save_state(self, conversation_id: str, state: Dict[str, Any]) -> None:
        """
        Save the state to a file.
        
        Args:
            conversation_id: The ID of the conversation.
            state: The state to save.
        """
        file_path = self.memory_path / f"{conversation_id}.json"
        
        # Add timestamp to state
        state["last_updated"] = datetime.now().isoformat()
        
        async with aiofiles.open(file_path, mode="w") as f:
            await f.write(json.dumps(state, default=self._json_serializer))
    
    async def get_state(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the state from a file.
        
        Args:
            conversation_id: The ID of the conversation.
            
        Returns:
            The state if it exists, None otherwise.
        """
        file_path = self.memory_path / f"{conversation_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            async with aiofiles.open(file_path, mode="r") as f:
                content = await f.read()
                return json.loads(content)
        except Exception as e:
            logger.error(f"Error reading state file: {e}")
            return None
    
    async def list_conversations(self) -> list:
        """
        List all conversation IDs.
        
        Returns:
            A list of conversation IDs.
        """
        return [f.stem for f in self.memory_path.glob("*.json")]
    
    async def delete_state(self, conversation_id: str) -> bool:
        """
        Delete a state file.
        
        Args:
            conversation_id: The ID of the conversation.
            
        Returns:
            True if the file was deleted, False otherwise.
        """
        file_path = self.memory_path / f"{conversation_id}.json"
        
        if file_path.exists():
            file_path.unlink()
            return True
        
        return False
    
    def _json_serializer(self, obj):
        """
        Custom JSON serializer for objects not serializable by default json code.
        
        Args:
            obj: The object to serialize.
            
        Returns:
            A serializable version of the object.
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return str(obj)


# Factory function to get the appropriate state manager
def get_state_manager():
    """
    Get the appropriate state manager based on the configuration.
    
    Returns:
        A state manager instance.
    """
    if settings.MEMORY_TYPE == "file_system":
        return FileSystemStateManager()
    # Add support for MongoDB state manager in the future
    else:
        return FileSystemStateManager()


# Helper function to create a new conversation ID
def generate_conversation_id() -> str:
    """
    Generate a new conversation ID.
    
    Returns:
        A new conversation ID.
    """
    return str(uuid4())
