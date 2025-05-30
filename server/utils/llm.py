"""
LLM integration utilities.
"""
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from config.settings import config


def get_llm(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
) -> BaseChatModel:
    """
    Get an LLM instance with the specified configuration.
    
    Args:
        model: Optional model name, defaults to config
        temperature: Optional temperature, defaults to config
        
    Returns:
        An instance of BaseChatModel
    """
    model = model or config.llm.model
    temperature = temperature if temperature is not None else config.llm.temperature
    
    if config.llm.provider == "openai":
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=config.llm.api_key,
        )
    
    # Add support for other providers as needed
    raise ValueError(f"Unsupported LLM provider: {config.llm.provider}")


def format_conversation_history(messages: List[Dict[str, str]]) -> List[Any]:
    """
    Format conversation history for LLM consumption.
    
    Args:
        messages: List of conversation messages
        
    Returns:
        List of formatted messages for LLM
    """
    formatted_messages = []
    
    for message in messages:
        role = message.get("role", "").lower()
        content = message.get("content", "")
        
        if role == "system":
            formatted_messages.append(SystemMessage(content=content))
        elif role == "user":
            formatted_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            formatted_messages.append(AIMessage(content=content))
    
    return formatted_messages


def create_prompt_template(system_template: str, human_template: str) -> ChatPromptTemplate:
    """
    Create a chat prompt template.
    
    Args:
        system_template: System message template
        human_template: Human message template
        
    Returns:
        ChatPromptTemplate instance
    """
    return ChatPromptTemplate.from_messages([
        ("system", system_template),
        ("human", human_template),
    ])
