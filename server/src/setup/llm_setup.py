"""
Modern LLM Setup with RouterChatModel for Development and Production.

This module provides a unified interface for LLM access that automatically
routes between GoogleGenerativeAI (development) and LLM Router (production)
based on environment configuration.

# LLMs supported:
- GoogleGenerativeAI: For Development (ENVIRONMENT=development)
- LLM Router: For Production (ENVIRONMENT=production)

## LLM Router API:
```bash
curl -X POST 'http://qa6-intuitionx-llm-router-v2.sprinklr.com/chat-completion' \
-H "Content-Type: application/json" \
-d '{
  "model": "gpt-4o",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "client_identifier": "spr-backend-interns-25"
}'
```
"""

from langchain_core.language_models import BaseLLM
from typing import Optional
import logging

from src.config.settings import settings
from src.setup.router_chat_model import RouterChatModel, get_router_chat_model

logger = logging.getLogger(__name__)


class LLMSetup:
    """
    Modern LLM Setup with automatic environment-based routing.
    
    Provides methods to initialize and configure LLMs that automatically
    switch between development and production backends.
    """
    
    def __init__(self):
        """Initialize LLM Setup with environment configuration."""
        self.environment = "production"
        logger.info(f"LLMSetup initialized for environment: {self.environment}")

    def get_llm(self, temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> "RouterChatModel":
        """
        Get a configured LLM instance with automatic environment routing.
        
        Args:
            temperature: Temperature for text generation (uses settings default if None)
            max_tokens: Maximum tokens to generate (uses settings default if None)
            
        Returns:
            Configured RouterChatModel instance (inherits from BaseLLM)
        """
        return get_router_chat_model(
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def get_agent_llm(self, agent_type: str) -> "RouterChatModel":
        """
        Get LLM configured for specific agent types.
        
        Args:
            agent_type: Type of agent (query_refiner, data_collector, etc.)
            
        Returns:
            RouterChatModel configured for the specific agent
        """
        logger.info(f"Getting LLM for agent type: {agent_type}")
        return self.get_llm()


# Global LLM setup instance
llm_setup = LLMSetup()


def get_llm(agent_type: str = "default") -> "RouterChatModel":
    """
    Convenience function to get LLM for agents based on type globally.
    
    Args:
        agent_type: Type of agent requesting the LLM
        
    Returns:
        Configured RouterChatModel instance with automatic environment routing
    """
    return llm_setup.get_agent_llm(agent_type)
