"""
Configuration settings for the the Sprinklr Insights Dashboard Application.

This File consists of the all the configuration settings that are required for the application to run.
"""

import os
from typing import Dict, Optional, Any, List, Union
from pydantic import Field, field_validator, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
import time

class Settings(BaseSettings):
    """
    Provides Configuration Settings for the Sprinklr Insights Dashboard Application.
    Loaded from the environment variables or a .env file.
    """
    
    #Sprinklr API Configuration
    SPRINKLR_DATA_API_URL: str = Field(
        default="https://space-prod0.sprinklr.com/ui/rest/reports/query",
    )
    SPRINKLR_COOKIES: Optional[Dict[str, str]] = None
    
    
    
    #LLM Configuration
    GOOGLE_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    DEFAULT_MODEL: str = "gemini-2.0-flash"
    
    
    #Memory Configuration
    MEMORY_TYPE: str = "file_system"
    MEMORY_PATH: str = "./conversation_memory"


settings = Settings()
