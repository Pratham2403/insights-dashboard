"""
This script sets up the LLM for the application.
It initializes the LLM and its components.

# LLMs that will be used in the application:
- GoogleGenerativeAI: For Development
- OpenAI-LLMRouter : For Production


## LLM Router Used:
```bash
curl -X POST \'http://qa6-intuitionx-llm-router-v2.sprinklr.com/chat-completion\' \\
-H "Content-Type: application/json" \\
-d \'{
  "model": "gpt-4o",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "client_identifier": "spr-backend-interns-25"
}\'
```
 

# Note : For now implementing only GoogleGenerativeAI for development purposes.
# This will be used in the agents to interact with the LLM.
# Make sure to set the environment variable GOOGLE_API_KEY with your Google API key.

"""

from langchain_google_genai import GoogleGenerativeAI
from langchain_core.language_models import BaseLLM
from langchain_core.outputs import LLMResult
from langchain_core.callbacks import CallbackManagerForLLMRun
from typing import Optional, List, Any
import logging

logger = logging.getLogger(__name__)

class LLMSetup:
    """
    Sets up and manages LLM instances for the application.
    
    Provides methods to initialize and configure LLMs for different use cases
    in the multi-agent system.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash"):
        """
        Initialize the LLM setup.
        
        Args:
            api_key: Google API key. If None, will try to get from environment
            model: Model name to use
        """
        self.api_key = api_key or "AIzaSyDM34NaNIGN1krgNgSGE5mBzameZyY3NUE"
        self.model = model
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY not found. LLM functionality will be limited.")
        logger.info(f"LLMSetup initialized with model: {self.model}")

    def get_llm(self, temperature: float = 0.1, max_tokens: Optional[int] = None) -> BaseLLM:
        """
        Get a configured LLM instance.
        
        Args:
            temperature: Temperature for text generation (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Configured LLM instance
        """
        if not self.api_key:
            logger.error("Cannot create LLM: GOOGLE_API_KEY is not configured.")
            raise ValueError("GOOGLE_API_KEY is not configured, cannot create LLM instance.")

        llm_params = {"model": self.model, "temperature": temperature}
        if max_tokens:
            llm_params["max_output_tokens"] = max_tokens
        
        return GoogleGenerativeAI(google_api_key=self.api_key, **llm_params)
    
    def get_agent_llm(self, agent_type: str) -> BaseLLM:
        """
        Get LLM configured for specific agent types.
        
        Args:
            agent_type: Type of agent (query_refiner, data_collector, etc.)
            
        Returns:
            LLM configured for the specific agent
        """
        logger.info(f"Getting LLM for agent type: {agent_type}")
        return self.get_llm()


# Import centralized config
from src.config.settings import settings

llm_setup = LLMSetup(api_key=settings.GOOGLE_API_KEY, model=settings.DEFAULT_MODEL_NAME)


def get_llm(agent_type: str = "default") -> BaseLLM:
    """
    Convenience function to get LLM for agents based on type globally.
    
    Args:
        agent_type: Type of agent requesting the LLM
        
    Returns:
        Configured LLM instance
    """
    return llm_setup.get_agent_llm(agent_type)
