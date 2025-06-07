"""
Modern Configuration settings for the Sprinklr Insights Dashboard Application.
Uses Pydantic settings with proper .env file integration.
"""

import os
from typing import Dict, Optional, Any, List, Union
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file if it exists



class Settings(BaseSettings):
    """
    Modern Configuration Settings for the Sprinklr Insights Dashboard Application.
    Automatically loaded from environment variables or .env file.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # LLM Configuration (Primary)
    GOOGLE_API_KEY: str = Field(..., description="Google API key for LLM access")
    DEFAULT_MODEL_NAME: str = Field(default="gemini-2.0-flash-exp", description="Default LLM model name")
    TEMPERATURE: float = Field(default=0.1, description="LLM temperature setting")
    MAX_OUTPUT_TOKENS: int = Field(default=8192, description="Maximum output tokens")
    
    # Memory and Persistence Configuration
    MEMORY_TYPE: str = Field(default="sqlite", description="Memory backend type")
    MEMORY_PATH: str = Field(default="./conversation_memory", description="Path for memory storage")
    ENABLE_CONVERSATION_MEMORY: bool = Field(default=True, description="Enable conversation memory")
    
    # Knowledge Base Paths
    KNOWLEDGE_BASE_PATH: str = Field(default="./src/knowledge_base", description="Knowledge base directory")
    FILTERS_JSON_PATH: str = Field(default="./src/knowledge_base/filters.json", description="Filters JSON file path")
    USE_CASE_FILE_PATH: str = Field(default="./src/knowledge_base/completeUseCase.txt", description="Use case context file")
    QUERY_PATTERNS_PATH: str = Field(default="./src/knowledge_base/keyword_query_patterns.json", description="Query patterns file")
    
    # Default Query Parameters
    DEFAULT_DURATION_DAYS: int = Field(default=30, description="Default query duration in days")
    DEFAULT_SOURCES: List[str] = Field(default=["Twitter", "Instagram"], description="Default social media sources")
    DEFAULT_LANGUAGE: str = Field(default="English", description="Default language filter")
    DEFAULT_REGION: str = Field(default="Asia", description="Default region filter")
    
    # API Configuration
    SPRINKLR_DATA_API_URL: str = Field(
        default="https://space-prod0.sprinklr.com/ui/rest/reports/query",
        description="Sprinklr API endpoint"
    )
    SPRINKLR_COOKIES: Optional[str] = Field(default="SPR_STICKINESS", description="Sprinklr authentication cookies")
    SPRINKLR_CSRF_TOKEN: Optional[str] = Field(default=None, description="CSRF token")
    
    # Workflow Configuration
    MAX_HITL_ITERATIONS: int = Field(default=3, description="Maximum HITL verification iterations")
    ENABLE_HITL_VERIFICATION: bool = Field(default=True, description="Enable human-in-the-loop verification")
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    ENABLE_DEBUG_LOGGING: bool = Field(default=False, description="Enable debug logging")
    
    @field_validator("KNOWLEDGE_BASE_PATH", "MEMORY_PATH")
    @classmethod
    def validate_paths(cls, v: str) -> str:
        """Ensure paths exist or can be created"""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)
    
    @property
    def filters_json_path(self) -> Path:
        """Get absolute path to filters JSON file"""
        return Path(self.FILTERS_JSON_PATH).resolve()
    
    @property
    def use_case_file_path(self) -> Path:
        """Get absolute path to use case file"""
        return Path(self.USE_CASE_FILE_PATH).resolve()
        
    @property
    def memory_config(self) -> Dict[str, Any]:
        """Get memory configuration dictionary"""
        return {
            "type": self.MEMORY_TYPE,
            "path": self.MEMORY_PATH,
            "enabled": self.ENABLE_CONVERSATION_MEMORY
        }
    
    @property
    def llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration dictionary"""
        return {
            "api_key": self.GOOGLE_API_KEY,
            "model_name": self.DEFAULT_MODEL_NAME,
            "temperature": self.TEMPERATURE,
            "max_output_tokens": self.MAX_OUTPUT_TOKENS
        }

# Global settings instance
settings = Settings()
