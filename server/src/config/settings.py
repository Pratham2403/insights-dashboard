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
    ENVIRONMENT: str = Field(default="production", description="Application environment (development/production)")
    
    # LLM Configuration (Primary)
    GOOGLE_API_KEY: str = Field(..., description="Google API key for LLM access")
    DEFAULT_MODEL_NAME: str = Field(default="gemini-2.0-flash", description="Default LLM model name")
    TEMPERATURE: float = Field(default=0.1, description="LLM temperature setting")
    MAX_OUTPUT_TOKENS: int = Field(default=8192, description="Maximum output tokens")
    
    # LLM Router Configuration (for production)
    LLM_ROUTER_URL: str = Field(default="http://qa6-intuitionx-llm-router-v2.sprinklr.com/chat-completion", description="LLM Router API endpoint")
    LLM_ROUTER_CLIENT_ID: str = Field(default="spr-backend-interns-25", description="LLM Router client identifier")
    LLM_ROUTER_MODEL: str = Field(default="gpt-4o", description="LLM Router model name")
    
    # Knowledge Base Paths
    KNOWLEDGE_BASE_PATH: str = Field(default="./src/knowledge_base", description="Knowledge base directory")
    FILTERS_JSON_PATH: str = Field(default="./src/knowledge_base/filters.json", description="Filters JSON file path")
    USE_CASE_FILE_PATH: str = Field(default="./src/knowledge_base/completeUseCase.json", description="Complete use case JSON file path")
    QUERY_PATTERNS_PATH: str = Field(default="./src/knowledge_base/keyword_query_patterns.json", description="Query patterns file")
    
    # API Configuration
    SPRINKLR_DATA_API_URL: str = Field(
        default="https://space-p0-lst-poc.sprinklr.com/ui/rest/chatgpt/stream/get-mentions/9004/MESSAGE_STREAM_SUMMARIZATION_STREAM/",
        description="Sprinklr API endpoint"
    )
    
    # Changing headers that can be configured via environment variables
    SPRINKLR_COOKIES: str = Field(
        default="SPR_STICKINESS=1749725175.91.67.128084|e805d1f847d7d15b3586fc924e912afa; JSESSIONID=823A3DE37244F1C28716851EAE9D9017; user.env.type=ENTERPRISE; connect.sid=s%3ANiytl1zSEa7hmrYZELAeWFaUSmiam8ZZ.vgbp9TV2ua5Jh1GZojZRg7b7Asb3I7EOH0aqNUYTfH4; SPR_AT=NW5aRjFWSHhKWFhMeUNWMXhDUjBY; connect.token=eyJ2M1Nlc3Npb25VcGRhdGVkIjoidHJ1ZSIsImFjY2Vzc1Rva2VuIjoiZXlKaGJHY2lPaUpTVXpJMU5pSjkuZXlKemRXSWlPaUpCWTJObGMzTWdWRzlyWlc0Z1IyVnVaWEpoZEdWa0lFSjVJRk53Y21sdWEyeHlJaXdpWTJ4cFpXNTBTV1FpT2pFd01EQXdNRFExTURrc0lteHZaMmx1VFdWMGFHOWtJam9pVTBGTlRDSXNJbTkwWVVsa0lqb2lOamcwWVdGbVpqVTRPR1kyT1RJMU1HRXlNV0l5TjJaa0lpd2lhWE56SWpvaVUxQlNTVTVMVEZJaUxDSjBlWEFpT2lKS1YxUWlMQ0oxYzJWeVNXUWlPakV3TURBME5qSXhNellzSW5WMWFXUWlPaUl3TUdJeE56QTJNaTAyWm1ReExUUXpOREl0T1dSaVl5MDBZbVEwTnpRNVptUTVaVFk2TWpnME5URXhOVEV3TURVeU9EZ3dOeUlzSW1GMVpDSTZJbE5RVWtsT1MweFNJaXdpYm1KbUlqb3hOelE1TnpJek9UY3pMQ0p6WTI5d1pTSTZXeUpTUlVGRUlpd2lWMUpKVkVVaVhTd2ljMlZ6YzJsdmJsUnBiV1Z2ZFhRaU9qRXdNVEk0TUN3aWNHRnlkRzVsY2tsa0lqbzVNREEwTENKbGVIQWlPakUzTkRrNU9EUXpOek1zSW1GMWRHaFVlWEJsSWpvaVUxQlNYMHRGV1Y5UVFWTlRYMHhQUjBsT0lpd2lkRzlyWlc1VWVYQmxJam9pUVVORFJWTlRJaXdpYVdGMElqb3hOelE1TnpJMU1UY3pMQ0pxZEdraU9pSnpjSEpwYm10c2NpSXNJbTFwWTNKdlUyVnlkbWxqWlNJNkluTndjaUo5LkpHaWNJZlU2aFlPSkpGTF84aHFLb0VnNVk0c2Q4UjdMb3ZmeW1SRkxBcUNnNUFZSE5UVVN0MXVPMTA1a1FISEFNOFFMWVdrSG5JLVdJVGVMZzAwcUNHX2FVNFl1TUZpcFE0OXNjNGRxMHFKa3RlUHZYcEk2NFZ0Ql9xN2dEcGNiOG9nb24tYmZUbTNLc2RXejd6NE1IWkZtMTNEb2NxLVZMT2dwaV9jVVFZRE5QSVVoX2l2cHFuUHZ5S1pNY0JVRHRRZ1g4M29pZk9RbGdmeFgtZ0VPTlNFRVFHSkNTaEhiYUdaQ283UHNDMC1aeXp2RHdpMUFudTN0cFVmSjBvVmpTbjJUaVJvMkVxV3JHMWZUZm10T1l4ZGVvcmFZR01lemd2UmZWSldReHZFVFhReE8tVUxkTlpObXdQM1QwcXcxM1ZycHhCenJXaHgtcTRsNzcxTlRsQSJ9.IEMmg32vUvX3WZwla/Oxb61/cxOGT07wkiSsVBpzeF8; sess-exp-time=Fri, 13 Jun 2025 14:54:59 GMT",
        description="Sprinklr API cookies for authentication"
    )
    SPRINKLR_X_CSRF_TOKEN: str = Field(
        default="NW5aRjFWSHhKWFhMeUNWMXhDUjBY",
        description="CSRF token for Sprinklr API requests"
    )
    SPRINKLR_X_REQUEST_ID: str = Field(
        default="1749725218190",
        description="Unique request ID for Sprinklr API"
    )
    SPRINKLR_X_USER_CONTEXT: str = Field(
        default="c_9004_1000004509_1000462136",
        description="User context for Sprinklr API requests"
    )
    SPRINKLR_SENTRY_TRACE: str = Field(
        default="bec78ee0aba94d95b09e2e2f685222e7-bd47340070c6c6ff",
        description="Sentry trace ID for Sprinklr API requests"
    )
    SPRINKLR_BAGGAGE: str = Field(
        default="sentry-environment=prod0,sentry-release=20.7-2a766f5d3627bed01d9b9eaeac4cbdd5717cc0bf,sentry-public_key=24769b1761314c0f814bde1a0576c6f6,sentry-trace_id=bec78ee0aba94d95b09e2e2f685222e7",
        description="Baggage header for Sprinklr API requests"
    )

    # MongoDB Configuration for Persistence
    MONGODB_URI: str = Field(default="mongodb://localhost:27017/", description="MongoDB connection URI")
    MONGODB_DATABASE: str = Field(default="insights_dashboard", description="MongoDB database name")
    MONGODB_COLLECTION: str = Field(default="langgraph_checkpoints", description="MongoDB collection for checkpoints")

    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    @field_validator("KNOWLEDGE_BASE_PATH")
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
    def llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration dictionary"""
        return {
            "api_key": self.GOOGLE_API_KEY,
            "model_name": self.DEFAULT_MODEL_NAME,
            "temperature": self.TEMPERATURE,
            "max_output_tokens": self.MAX_OUTPUT_TOKENS
        }
    
    @property
    def llm_router_config(self) -> Dict[str, Any]:
        """Get LLM Router configuration dictionary"""
        return {
            "url": self.LLM_ROUTER_URL,
            "client_id": self.LLM_ROUTER_CLIENT_ID,
            "model": self.LLM_ROUTER_MODEL
        }

# Global settings instance
settings = Settings()
