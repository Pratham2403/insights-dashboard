"""
Modern RouterChatModel that supports both GoogleGenerativeAI (development) 
and LLM Router (production) while maintaining full LangChain/LangGraph compatibility.
"""

import json
import requests
import logging
from typing import Any, Dict, List, Optional, Union, Iterator

from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.language_models import BaseLLM
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_google_genai import GoogleGenerativeAI

from src.config.settings import settings

logger = logging.getLogger(__name__)


class RouterChatModel(BaseLLM):
    """
    A modular ChatModel that routes between GoogleGenerativeAI and LLM Router,
    transparently supporting tool bindings, memory, interrupts, commands, etc.
    
    Automatically selects backend based on environment configuration.
    This implementation inherits from BaseLLM for full LangChain compatibility.
    """
    
    # Required for BaseLLM
    model_name: str = ""
    use_router: bool = False
    environment: str = ""
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    router_url: Optional[str] = None
    client_identifier: Optional[str] = None
    google_llm: Optional[GoogleGenerativeAI] = None
    
    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize RouterChatModel with environment-based routing.
        
        Args:
            model: LLM model name (optional, uses settings default)
            temperature: Temperature for text generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
        """
        # Initialize parent
        super().__init__(**kwargs)
        
        # Use environment configuration
        self.environment = settings.ENVIRONMENT
        self.temperature = temperature or settings.TEMPERATURE
        self.max_tokens = max_tokens or settings.MAX_OUTPUT_TOKENS
        
        # Configure based on environment
        if self.environment == "production":
            # Production: Use LLM Router
            self.use_router = True
            self.model_name = model or settings.LLM_ROUTER_MODEL
            self.router_url = settings.LLM_ROUTER_URL
            self.client_identifier = settings.LLM_ROUTER_CLIENT_ID
            self.google_llm = None
            logger.info(f"RouterChatModel initialized for PRODUCTION with LLM Router: {self.model_name}")
        else:
            # Development: Use GoogleGenerativeAI
            self.use_router = False
            self.model_name = model or settings.DEFAULT_MODEL_NAME
            self.router_url = None
            self.client_identifier = None
            
            # Initialize GoogleGenerativeAI
            self.google_llm = GoogleGenerativeAI(
                model=self.model_name,
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )
            logger.info(f"RouterChatModel initialized for DEVELOPMENT with GoogleGenerativeAI: {self.model_name}")

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate response - required by BaseLLM.
        
        Args:
            messages: Input messages
            stop: Stop sequences
            run_manager: Callback manager
            **kwargs: Additional parameters
            
        Returns:
            Generated response string
        """
        if self.use_router:
            return self._generate_with_router(messages, **kwargs)
        else:
            return self._generate_with_google(messages, **kwargs)

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Async generate response - required by BaseLLM.
        
        Args:
            messages: Input messages
            stop: Stop sequences
            run_manager: Callback manager
            **kwargs: Additional parameters
            
        Returns:
            Generated response string
        """
        # For now, delegate to sync generate
        return self._generate(messages, stop, run_manager, **kwargs)

    def invoke(self, messages: Union[List[BaseMessage], str], **kwargs) -> AIMessage:
        """
        Invoke the LLM with messages.
        
        Args:
            messages: Input messages or string
            **kwargs: Additional parameters
            
        Returns:
            Generated response as AIMessage
        """
        # Convert string to messages if needed
        if isinstance(messages, str):
            messages = [HumanMessage(content=messages)]
        
        # Generate response
        content = self._generate(messages, **kwargs)
        
        # Return as AIMessage for LangChain compatibility
        return AIMessage(content=content)

    async def ainvoke(self, messages: Union[List[BaseMessage], str], **kwargs) -> AIMessage:
        """
        Async invoke the LLM with messages.
        
        Args:
            messages: Input messages or string
            **kwargs: Additional parameters
            
        Returns:
            Generated response as AIMessage
        """
        # Convert string to messages if needed
        if isinstance(messages, str):
            messages = [HumanMessage(content=messages)]
        
        # Generate response
        content = await self._agenerate(messages, **kwargs)
        
        # Return as AIMessage for LangChain compatibility
        return AIMessage(content=content)

    def _generate_with_router(self, messages: List[BaseMessage], **kwargs) -> str:
        """Generate using LLM Router."""
        try:
            # Convert LangChain messages to router format
            router_messages = []
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    router_messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    router_messages.append({"role": "assistant", "content": msg.content})
                elif isinstance(msg, SystemMessage):
                    router_messages.append({"role": "system", "content": msg.content})
                else:
                    # Generic message handling
                    router_messages.append({"role": "user", "content": str(msg.content)})

            # Prepare router payload
            payload = {
                "model": self.model_name,
                "client_identifier": self.client_identifier,
                "messages": router_messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }

            # Make request to LLM Router
            response = requests.post(
                self.router_url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=60,  # 60 second timeout
            )
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return content
            
        except Exception as e:
            logger.error(f"LLM Router request failed: {e}")
            raise RuntimeError(f"LLM Router error: {str(e)}")

    def _generate_with_google(self, messages: List[BaseMessage], **kwargs) -> str:
        """Generate using GoogleGenerativeAI."""
        try:
            # Delegate to GoogleGenerativeAI
            result = self.google_llm.invoke(messages, **kwargs)
            
            # Handle different response formats from GoogleGenerativeAI
            if hasattr(result, 'content'):
                return result.content
            else:
                return str(result)
        except Exception as e:
            logger.error(f"GoogleGenerativeAI request failed: {e}")
            raise RuntimeError(f"GoogleGenerativeAI error: {str(e)}")

    @property
    def _llm_type(self) -> str:
        """Return LLM type identifier."""
        if self.use_router:
            return f"router_chat_model_{self.model_name}"
        else:
            return f"google_generative_ai_{self.model_name}"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Return identifying parameters."""
        params = {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "environment": self.environment,
            "use_router": self.use_router,
        }
        
        if self.use_router:
            params["router_url"] = self.router_url
            params["client_identifier"] = self.client_identifier
        
        return params


def get_router_chat_model(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    **kwargs
) -> RouterChatModel:
    """
    Factory function to create a RouterChatModel instance.
    
    Args:
        model: Model name (optional)
        temperature: Temperature setting (optional)
        max_tokens: Max tokens (optional)
        **kwargs: Additional parameters
        
    Returns:
        Configured RouterChatModel instance
    """
    return RouterChatModel(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )
