from abc import ABC, abstractmethod
from typing import Any, Dict

from server.models.project_state import ProjectState

class Agent(ABC):
    """Abstract base class for all agents."""

    @abstractmethod
    async def invoke(self, state: ProjectState) -> ProjectState:
        """Invokes the agent with the current project state and returns the updated state."""
        pass
