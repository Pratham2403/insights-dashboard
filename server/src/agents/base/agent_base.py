"""
Base agent class to reduce duplication across agent implementations.
"""

import logging
from typing import Optional, Any, Dict
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Base class for all agents in the system.
    
    Provides common initialization patterns and utilities to reduce code duplication.
    """
    
    def __init__(self, agent_name: str, llm: Optional[Any] = None):
        """
        Initialize the base agent.
        
        Args:
            agent_name: Name identifier for the agent
            llm: Language model instance (optional)
        """
        self.agent_name = agent_name
        self.llm = llm
        self._setup_logging()
        logger.info(f"{self.agent_name} agent initialized")
    
    def _setup_logging(self):
        """Setup agent-specific logging."""
        self.logger = logging.getLogger(f"{__name__}.{self.agent_name}")
    
    @abstractmethod
    async def invoke(self, *args, **kwargs) -> Any:
        """
        Main agent invocation method - must be implemented by subclasses.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            Agent-specific result
        """
        pass
    
    def get_agent_info(self) -> Dict[str, str]:
        """
        Get basic information about the agent.
        
        Returns:
            Dictionary containing agent information
        """
        return {
            "name": self.agent_name,
            "class": self.__class__.__name__,
            "has_llm": self.llm is not None
        }
    
    def log_operation(self, operation: str, details: Optional[str] = None):
        """
        Log agent operations with consistent formatting.
        
        Args:
            operation: Operation being performed
            details: Additional operation details
        """
        if details:
            self.logger.info(f"{self.agent_name} - {operation}: {details}")
        else:
            self.logger.info(f"{self.agent_name} - {operation}")


class LLMAgent(BaseAgent):
    """
    Base class for agents that require LLM functionality.
    
    Provides common LLM initialization and error handling patterns.
    """
    
    def __init__(self, agent_name: str, llm: Optional[Any] = None, **llm_kwargs):
        """
        Initialize the LLM agent.
        
        Args:
            agent_name: Name identifier for the agent
            llm: Language model instance (optional)
            **llm_kwargs: Additional LLM configuration parameters
        """
        super().__init__(agent_name, llm)
        self.llm_kwargs = llm_kwargs
        
        if not self.llm:
            self._setup_default_llm()
    
    def _setup_default_llm(self):
        """
        Setup default LLM if none provided.
        
        Subclasses can override this method for agent-specific LLM setup.
        """
        try:
            from ...setup.llm_setup import get_llm
            self.llm = get_llm(self.agent_name)
            self.logger.info(f"Default LLM setup completed for {self.agent_name}")
        except Exception as e:
            self.logger.warning(f"Failed to setup default LLM for {self.agent_name}: {e}")
            self.llm = None
    
    async def safe_llm_invoke(self, messages, **kwargs) -> Optional[str]:
        """
        Safely invoke LLM with error handling.
        
        Args:
            messages: Messages to send to LLM
            **kwargs: Additional LLM parameters
            
        Returns:
            LLM response content or None if error occurred
        """
        if not self.llm:
            self.logger.error(f"No LLM available for {self.agent_name}")
            return None
        
        try:
            # Merge instance kwargs with call-specific kwargs
            final_kwargs = {**self.llm_kwargs, **kwargs}
            response = await self.llm.ainvoke(messages, **final_kwargs)
            
            if hasattr(response, 'content'):
                return response.content
            return str(response)
            
        except Exception as e:
            self.logger.error(f"LLM invocation failed for {self.agent_name}: {e}")
            return None


def create_agent_factory(agent_class, agent_name: str):
    """
    Factory function generator for creating agent instances.
    
    Args:
        agent_class: The agent class to instantiate
        agent_name: Name for the agent (not used, kept for compatibility)
        
    Returns:
        Factory function that creates agent instances
    """
    def factory(llm=None, **kwargs):
        """
        Create an agent instance.
        
        Args:
            llm: Language model instance
            **kwargs: Additional agent parameters
            
        Returns:
            Configured agent instance
        """
        # Don't pass agent_name since agents hardcode it in their super().__init__() calls
        return agent_class(llm=llm, **kwargs)
    
    factory.__name__ = f"create_{agent_name.lower()}_agent"
    factory.__doc__ = f"Factory function to create a {agent_class.__name__}."
    
    return factory
