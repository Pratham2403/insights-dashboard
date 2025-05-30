"""
Configuration module for the Sprinklr Insights dashboard.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


class LLMConfig(BaseModel):
    """Configuration for LLM services."""
    provider: str = Field(default="openai", description="LLM provider (openai, anthropic, etc.)")
    model: str = Field(default="gpt-4o", description="Model name")
    temperature: float = Field(default=0.7, description="Temperature for generation")
    api_key: str = Field(default="", description="API key for the LLM service")


class APIConfig(BaseModel):
    """Configuration for API services."""
    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    debug: bool = Field(default=False, description="Debug mode")


class ExternalAPIConfig(BaseModel):
    """Configuration for external API services."""
    elasticsearch_url: str = Field(default="", description="Elasticsearch URL")
    mock_data: bool = Field(default=True, description="Use mock data instead of real API")
    timeout: int = Field(default=30, description="Timeout for API requests in seconds")


class AppConfig(BaseModel):
    """Main application configuration."""
    app_name: str = Field(default="Sprinklr Insights Dashboard", description="Application name")
    environment: str = Field(default="development", description="Environment (development, production)")
    llm: LLMConfig = Field(default_factory=LLMConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    external_api: ExternalAPIConfig = Field(default_factory=ExternalAPIConfig)
    query_patterns_file: str = Field(default=str(DATA_DIR / "keyword_query_patterns.json"), 
                                    description="Path to query patterns file")


def get_app_config() -> AppConfig:
    """Get application configuration from environment variables."""
    config = AppConfig(
        app_name=os.getenv("APP_NAME", "Sprinklr Insights Dashboard"),
        environment=os.getenv("ENVIRONMENT", "development"),
        llm=LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            model=os.getenv("LLM_MODEL", "gpt-4o"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            api_key=os.getenv("OPENAI_API_KEY", ""),
        ),
        api=APIConfig(
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=int(os.getenv("API_PORT", "8000")),
            debug=os.getenv("API_DEBUG", "False").lower() == "true",
        ),
        external_api=ExternalAPIConfig(
            elasticsearch_url=os.getenv("ELASTICSEARCH_URL", ""),
            mock_data=os.getenv("USE_MOCK_DATA", "True").lower() == "true",
            timeout=int(os.getenv("API_TIMEOUT", "30")),
        ),
        query_patterns_file=os.getenv("QUERY_PATTERNS_FILE", str(DATA_DIR / "keyword_query_patterns.json")),
    )
    return config


# Global configuration instance
config = get_app_config()
