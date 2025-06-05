"""
Modern base agent classes using latest LangGraph patterns for minimal code duplication.
"""

import logging
from typing import Optional, Any, Dict
from abc import ABC, abstractmethod
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

class ModernBaseAgent(ABC):
    """
    Modern base class for all agents using latest LangGraph patterns.
    
    Leverages built-in LangGraph features for state management and tool integration.
    Key improvements:
    - Agents are callable functions (not classes with invoke methods)
    - Built-in message handling with MessagesState compatibility
    - Simplified state management
    - Modern async/await patterns
    """
    
    def __init__(self, agent_name: str, llm: Optional[Any] = None):
        """Initialize with minimal setup - let LangGraph handle the heavy lifting."""
        self.agent_name = agent_name
        self.llm = llm or self._get_default_llm()
        self.logger = logging.getLogger(f"agents.{agent_name}")
        self.logger.info(f"Modern {agent_name} agent initialized")
    
    def _get_default_llm(self):
        """Get default LLM using modern pattern."""
        try:
            from ...setup.llm_setup import get_llm
            return get_llm()
        except Exception as e:
            self.logger.warning(f"Default LLM setup failed: {e}")
            return None
    
    @abstractmethod
    async def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Modern callable pattern - agents are functions in LangGraph.
        
        Args:
            state: Current graph state (MessagesState compatible)
            
        Returns:
            State updates dictionary
        """
        pass

    async def add_message(self, content: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Add AI message to state using modern pattern."""
        message = AIMessage(content=content, name=self.agent_name)
        return {"messages": [message]}

    async def safe_llm_call(self, messages, **kwargs) -> Optional[str]:
        """Simplified LLM call with error handling."""
        if not self.llm:
            self.logger.error(f"No LLM available for {self.agent_name}")
            return None
        
        try:
            response = await self.llm.ainvoke(messages, **kwargs)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            self.logger.error(f"LLM call failed for {self.agent_name}: {e}")
            return None


class ModernLLMAgent(ModernBaseAgent):
    """
    Modern LLM agent with built-in patterns for common operations.
    
    Uses latest LangGraph patterns for minimal code and maximum functionality.
    """
    
    def __init__(self, agent_name: str, llm: Optional[Any] = None, **llm_kwargs):
        super().__init__(agent_name, llm)
        self.llm_kwargs = llm_kwargs

    async def process_with_llm(self, state: Dict[str, Any], prompt_template: str, **kwargs) -> str:
        """
        Common pattern for LLM processing with state.
        
        Args:
            state: Current state
            prompt_template: Prompt template string
            **kwargs: Template variables
            
        Returns:
            LLM response content
        """
        messages = state.get("messages", [])
        
        # Format prompt with state and kwargs
        formatted_prompt = prompt_template.format(
            messages=messages,
            agent_name=self.agent_name,
            **kwargs
        )
        
        return await self.safe_llm_call([{"role": "user", "content": formatted_prompt}], **self.llm_kwargs)


def create_modern_agent(agent_class):
    """
    Modern factory pattern for LangGraph agents.
    
    Returns a callable function that can be used directly in LangGraph.
    """
    async def agent_function(state: Dict[str, Any]) -> Dict[str, Any]:
        """Agent function for LangGraph graph."""
        agent = agent_class()
        return await agent(state)
    
    agent_function.__name__ = agent_class.__name__.lower()
    return agent_function
