"""
Configuration settings for the Sprinklr Insights Dashboard application.
"""
import os
from typing import Dict, List, Optional, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import validator, AnyHttpUrl, Field
import time


class Settings(BaseSettings):
    """
    Application configuration settings, loaded from environment variables.
    Provides defaults for development environment.
    """
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Sprinklr Insights Dashboard"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = Field(
        default=["http://localhost:3000", "http://localhost:8080"]
    )
    
    # LLM Configuration
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    DEFAULT_MODEL_NAME: str = "gemini-2.0-flash"
    
    # External API Configuration
    EXTERNAL_API_URL: Optional[str] = Field(
        default="https://api.example.com/search"
    )
    EXTERNAL_API_KEY: Optional[str] = None

    CURRENT_TIMESTAMP: int = Field(default_factory=lambda: int(time.time()))

    # Timeout Configuration
    EXTERNAL_API_TIMEOUT: int = 30  # seconds
    
    # Memory Configuration
    MEMORY_TYPE: str = "file_system"  # Options: "file_system", "mongodb"
    MEMORY_PATH: str = "./conversation_memory"
    MONGODB_URI: Optional[str] = None
    MONGODB_DB_NAME: str = "sprinklr_insights"
    
    # Query Configuration
    MAX_QUERY_TOKENS: int = 500
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """
        Parse CORS origins from comma-separated string to list.
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
