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
    
    # Environment Configuration
    ENVIRONMENT: str = Field(default="development", description="Application environment (development/production)")
    
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
    USE_CASE_FILE_PATH: str = Field(default="./src/knowledge_base/completeUseCase.txt", description="Use case context file")
    QUERY_PATTERNS_PATH: str = Field(default="./src/knowledge_base/keyword_query_patterns.json", description="Query patterns file")
    
    # API Configuration
    SPRINKLR_DATA_API_URL: str = Field(
        default="https://space-prod0.sprinklr.com/ui/rest/reports/query",
        description="Sprinklr API endpoint"
    )
    SPRINKLR_COOKIES : str = Field(default="SPR_STICKINESS=1749289959.863.103.296053|935c7dcb81a00314ea56a3b1f4989107; JSESSIONID=0E96203CC106FD4BF5CFBFF40CEC41A8; user.env.type=ENTERPRISE; connect.sid=s%3A_nHvY16x_ef2qjwrhBEvdkTJuHaVIfg6.qKd2ZuYyIMpBUGDBvPLX4lUL4L93ltqk9ZdGzicEPek; SPR_AT=VUhpT0ZOd2J6dHJiT2k5REFuMnF4; connect.token=eyJ2M1Nlc3Npb25VcGRhdGVkIjoidHJ1ZSIsImFjY2Vzc1Rva2VuIjoiZXlKaGJHY2lPaUpTVXpJMU5pSjkuZXlKemRXSWlPaUpCWTJObGMzTWdWRzlyWlc0Z1IyVnVaWEpoZEdWa0lFSjVJRk53Y21sdWEyeHlJaXdpWTJ4cFpXNTBTV1FpT2pFd01EQXdNRFExTURrc0lteHZaMmx1VFdWMGFHOWtJam9pVTBGTlRDSXNJbTkwWVVsa0lqb2lOamcwTkRCaVpUTTBZakV5TkRnd01UVTVZMlF6Tm1FMElpd2lhWE56SWpvaVUxQlNTVTVMVEZJaUxDSjBlWEFpT2lKS1YxUWlMQ0oxYzJWeVNXUWlPakV3TURBME5qSXhNellzSW5WMWFXUWlPaUptT0dGa1pXTmxaQzAwTW1VeUxUUmhNRGt0WVRVeFlpMDVNRGN3WldKaU9UWTFZekE2TVRZNU9UZ3lNalEwTnpZMU9USTFJaXdpWVhWa0lqb2lVMUJTU1U1TFRGSWlMQ0p1WW1ZaU9qRTNORGt5T0RnM05UVXNJbk5qYjNCbElqcGJJbEpGUVVRaUxDSlhVa2xVUlNKZExDSnpaWE56YVc5dVZHbHRaVzkxZENJNk1UQXhNamd3TENKd1lYSjBibVZ5U1dRaU9qa3dNRFFzSW1WNGNDSTZNVGMwT1RVME9URTFOU3dpWVhWMGFGUjVjR1VpT2lKVFVGSmZTMFZaWDFCQlUxTmZURTlIU1U0aUxDSjBiMnRsYmxSNWNHVWlPaUpCUTBORlUxTWlMQ0pwWVhRaU9qRTNORGt5T0RrNU5UVXNJbXAwYVNJNkluTndjbWx1YTJ4eUlpd2liV2xqY205VFpYSjJhV05sSWpvaWMzQnlJbjAuWGZFSXFFeWVNM09ySEpDa3J1RFo4RDNhRUwtZC1mUEZhVWlTU19yQVZaRjlSS3NWbE5SdC1XRVFrcnUzM1dtZUlibEE1YWtwWDRYYXo3YkZTVmtQYjRDUDZiZEpSdDYtT3dkN3lkRG5TckJzZmZzbTRYdHJRZGs4VlJaa25ISEpJd0ZNeWVZZnVTX0x2cmVnaGsxU3RIZEc3LWNOQ3pKSTlyakdhaGlpbUFuSFZRYkE2WmRJdjk2SVV3bDRGVnVjUDEtby1CYWpkeXV1aUV4QkNELVpoUFJIU2U0Xzk1OURIeXdBcmRWTzg0bzdXMVlSdnRqZlhYbzY3UFRqOHV6YmZrTTJzbE5ySUVieUJwaGw3dS1UMWdqXzZsTXk1cTJtekVBWUp4MnN0bE9YUVRUR2M1R2F6azBlNjAtMnhBT0psNFVRbnJ6ZlZhRkt2WS1fYXZqUlZ3In0.3Ep94SMwCXBgeKzibbc+B2nXXeYz0h9dL43LGQAIRe8; sess-exp-time=Sun, 8 Jun 2025 14:03:37 GMT", description="Sprinklr API cookies for authentication")
    SPRINKLR_REQUEST_AT : str = Field(default="1749290136860", description="Timestamp for the Sprinklr API request")
    SPRINKLR_REQUEST_ID: str = Field(default="space-e6d0276f-f6de-41fd-92a0-29dc2037e1b9", description="Unique request ID for Sprinklr API")
    SPRINKLR_CSRF_TOKEN: str = Field(default="VUhpT0ZOd2J6dHJiT2k5REFuMnF4", description="CSRF token for Sprinklr API requests")
    SPRINKLR_SENTRY_TRACE: str = Field(default="ed0df10e92614c86bfef1061d68c36ee-a7c76c73531d5134", description="Sentry trace ID for Sprinklr API requests")


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
