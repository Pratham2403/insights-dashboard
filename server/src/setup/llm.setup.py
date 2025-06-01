"""
This script sets up the LLM for the application.
It initializes the LLM and its components.

# LLMs that will be used in the application:
- GoogleGenerativeAI: For Development
- OpenAI-LLMRouter : For Production


## LLM Router Used:
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
 

# Note : For now implementing only GoogleGenerativeAI for development purposes.
# This will be used in the agents to interact with the LLM.
# Make sure to set the environment variable GOOGLE_API_KEY with your Google API key.

"""

import os
from langchain_google_genai import GoogleGenerativeAI
from langchain_core.language_models import BaseLLM
from langchain_core.outputs import LLMResult
from langchain_core.callbacks import CallbackManagerForLLMRun
from typing import Optional, List, Any
import logging

logger = logging.getLogger(__name__)

class MockLLM(BaseLLM):
    """Mock LLM for testing when no valid API key is available."""
    
    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """Generate mock responses."""
        from langchain_core.outputs import Generation
        
        # Simple mock response based on the prompt
        mock_responses = []
        for prompt in prompts:
            if "refined_query" in prompt.lower():
                response = '''{"refined_query": "Brand monitoring analysis", "suggested_filters": [{"name": "Brand Mentions", "description": "Track brand mentions"}], "suggested_themes": [{"name": "Brand Health", "description": "Overall brand health"}], "missing_information": ["products", "channels"], "confidence_score": 0.8}'''
            else:
                response = "Mock LLM response: This is a placeholder response for testing purposes."
            mock_responses.append(Generation(text=response))
        
        return LLMResult(generations=[mock_responses])
    
    def _llm_type(self) -> str:
        return "mock"
    
    async def _agenerate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """Generate mock responses asynchronously."""
        return self._generate(prompts, stop, run_manager, **kwargs)
    
    def invoke(self, prompt, **kwargs):
        """Invoke method that returns a response with content attribute."""
        from types import SimpleNamespace
        
        if isinstance(prompt, str):
            prompt_text = prompt
        else:
            prompt_text = str(prompt)
            
        if "refined_query" in prompt_text.lower():
            content = '''{"refined_query": "Brand monitoring analysis", "suggested_filters": [{"name": "Brand Mentions", "description": "Track brand mentions"}], "suggested_themes": [{"name": "Brand Health", "description": "Overall brand health"}], "missing_information": ["products", "channels"], "confidence_score": 0.8}'''
        elif "query" in prompt_text.lower() and "boolean" in prompt_text.lower():
            content = '''query: (brand AND monitor) OR (insights AND analysis)
confidence: 0.85
estimated_results: medium'''
        else:
            content = "Mock LLM response: This is a placeholder response for testing purposes."
            
        # Return an object with content attribute like real LLM responses
        return SimpleNamespace(content=content)
    
    async def ainvoke(self, prompt, **kwargs):
        """Async invoke method that returns a response with content attribute."""
        # For testing purposes, just return the same as invoke
        return self.invoke(prompt, **kwargs)

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
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
        
        # Check if API key is valid (not placeholder)
        if not self.api_key or self.api_key == "<gemini-api-key>" or self.api_key == "your_gemini_api_key_here":
            logger.warning("No valid GEMINI_API_KEY found. Using mock LLM for testing.")
            self.use_mock = True
        else:
            self.use_mock = False
    
    def get_llm(self, temperature: float = 0.7, max_tokens: Optional[int] = None) -> BaseLLM:
        """
        Get a configured LLM instance.
        
        Args:
            temperature: Temperature for text generation (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Configured LLM instance
        """
        try:
            if self.use_mock:
                # Return a mock LLM for testing
                return MockLLM()
            
            llm = GoogleGenerativeAI(
                model=self.model,
                google_api_key=self.api_key,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            logger.info(f"Successfully initialized {self.model} LLM")
            return llm
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise
    
    def get_agent_llm(self, agent_type: str) -> BaseLLM:
        """
        Get LLM configured for specific agent types.
        
        Args:
            agent_type: Type of agent (query_refiner, data_collector, etc.)
            
        Returns:
            LLM configured for the specific agent
        """
        # Different agents may need different temperature settings
        agent_configs = {
            "query_refiner": {"temperature": 0.3},  # More deterministic for query refinement
            "data_collector": {"temperature": 0.5}, # Balanced for interaction
            "hitl_verification": {"temperature": 0.2}, # Very deterministic for verification
            "query_generator": {"temperature": 0.1}, # Very precise for query generation
            "data_analyzer": {"temperature": 0.4}, # Balanced for analysis
        }
        
        config = agent_configs.get(agent_type, {"temperature": 0.7})
        return self.get_llm(**config)

# Global LLM setup instance
llm_setup = LLMSetup()

def get_llm(agent_type: str = "default") -> BaseLLM:
    """
    Convenience function to get LLM for agents.
    
    Args:
        agent_type: Type of agent requesting the LLM
        
    Returns:
        Configured LLM instance
    """
    return llm_setup.get_agent_llm(agent_type)
