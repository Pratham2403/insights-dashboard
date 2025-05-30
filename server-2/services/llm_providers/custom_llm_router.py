# filepath: /Users/pratham.aggarwal/Documents/insights-dashboard/server/services/llm_providers/custom_llm_router.py
import httpx
import json
from typing import Any, List, Dict, Optional, AsyncIterator, Iterator, cast
from langchain_core.callbacks.manager import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, HumanMessage, SystemMessage, ToolMessage, ChatMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from pydantic import Field, SecretStr, HttpUrl

from ...config.settings import settings # Corrected import path

class CustomChatLLM(BaseChatModel):
    """
    Custom Chat LLM that routes requests to a specified LLM router.
    """
    model_name: str = Field(default=settings.DEFAULT_LLM_MODEL)
    temperature: float = 0.7 
    base_url: HttpUrl = Field(default=settings.LLM_ROUTER_BASE_URL)
    client_identifier: str = Field(default=settings.LLM_ROUTER_CLIENT_IDENTIFIER)
    # Add other parameters like max_tokens, top_p etc. if needed by the router or for customization

    @property
    def _llm_type(self) -> str:
        return "custom-chat-llm-router"

    def _map_lc_message_to_router_format(self, message: BaseMessage) -> Dict[str, Any]:
        """Maps LangChain message to the format expected by the LLM router."""
        if isinstance(message, HumanMessage):
            return {"role": "user", "content": message.content}
        elif isinstance(message, AIMessage):
            return {"role": "assistant", "content": message.content}
        elif isinstance(message, SystemMessage):
            return {"role": "system", "content": message.content}
        elif isinstance(message, ToolMessage):
            return {"role": "tool", "tool_call_id": message.tool_call_id, "content": message.content}
        elif isinstance(message, ChatMessage): # Generic ChatMessage
             return {"role": message.role, "content": message.content}
        else:
            raise ValueError(f"Unsupported message type: {type(message)}")

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Synchronous generation of chat completions."""
        
        router_messages = [self._map_lc_message_to_router_format(m) for m in messages]
        
        payload = {
            "client_identifier": self.client_identifier,
            "model": self.model_name,
            "messages": router_messages,
            "temperature": self.temperature,
            **kwargs
        }
        if stop:
            payload["stop"] = stop

        try:
            with httpx.Client() as client:
                response = client.post(
                    str(self.base_url), 
                    json=payload,
                    timeout=60.0 
                )
                response.raise_for_status() 
            
            router_response_data = response.json()

            if not router_response_data.get("choices") or not router_response_data["choices"][0].get("message"):
                raise ValueError("Invalid response structure from LLM router.")

            choice = router_response_data["choices"][0]
            content = choice["message"].get("content", "")
            ai_message = AIMessage(content=content)
            
            llm_output = {
                "token_usage": router_response_data.get("usage"),
                "finish_reason": choice.get("finish_reason"),
                "model_name": self.model_name 
            }

            return ChatResult(generations=[ChatGeneration(message=ai_message, generation_info=llm_output)])

        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            print(f"Request error occurred: {e}")
            raise
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON response: {e}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise


    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Asynchronous generation of chat completions."""
        router_messages = [self._map_lc_message_to_router_format(m) for m in messages]
        
        payload = {
            "client_identifier": self.client_identifier,
            "model": self.model_name,
            "messages": router_messages,
            "temperature": self.temperature,
            **kwargs
        }
        if stop:
            payload["stop"] = stop

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    str(self.base_url),
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
            
            router_response_data = response.json()

            if not router_response_data.get("choices") or not router_response_data["choices"][0].get("message"):
                raise ValueError("Invalid response structure from LLM router for async.")

            choice = router_response_data["choices"][0]
            content = choice["message"].get("content", "")
            ai_message = AIMessage(content=content)
            
            llm_output = {
                "token_usage": router_response_data.get("usage"),
                "finish_reason": choice.get("finish_reason"),
                "model_name": self.model_name
            }

            return ChatResult(generations=[ChatGeneration(message=ai_message, generation_info=llm_output)])

        except httpx.HTTPStatusError as e:
            print(f"Async HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            print(f"Async request error occurred: {e}")
            raise
        except json.JSONDecodeError as e:
            print(f"Async failed to decode JSON response: {e}")
            raise
        except Exception as e:
            print(f"An async unexpected error occurred: {e}")
            raise

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get the identifying parameters."""
        return {
            "model_name": self.model_name,
            "base_url": str(self.base_url),
            "client_identifier": self.client_identifier,
            "temperature": self.temperature,
        }
