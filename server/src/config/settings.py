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
    SPRINKLR_COOKIES : str = Field(default="SPR_STICKINESS=1749430640.602.65.801359|935c7dcb81a00314ea56a3b1f4989107; JSESSIONID=06FD6301C147227584DF186F3850676C; user.env.type=ENTERPRISE; connect.sid=s%3ADmz-vx8noYOsFeTqKLrCH-xrlvZoBv47.5eiIxFeaG80W2alf%2BLnqSu9bRTeFdhTYfzW5ZXOmMnI; SPR_AT=OGgyaHVFMDM4R1RVQkZocTRmT2p2; connect.token=eyJ2M1Nlc3Npb25VcGRhdGVkIjoidHJ1ZSIsImFjY2Vzc1Rva2VuIjoiZXlKaGJHY2lPaUpTVXpJMU5pSjkuZXlKemRXSWlPaUpCWTJObGMzTWdWRzlyWlc0Z1IyVnVaWEpoZEdWa0lFSjVJRk53Y21sdWEyeHlJaXdpWTJ4cFpXNTBTV1FpT2pFd01EQXdNRFExTURrc0lteHZaMmx1VFdWMGFHOWtJam9pVTBGTlRDSXNJbTkwWVVsa0lqb2lOamcwTmpNeE5tRXpZakJpWTJNMk5UaGlZbVV4WTJGbUlpd2lhWE56SWpvaVUxQlNTVTVMVEZJaUxDSjBlWEFpT2lKS1YxUWlMQ0oxYzJWeVNXUWlPakV3TURBME5qSXhNellzSW5WMWFXUWlPaUl3WkRjME16TTJNUzB6TnpKbExUUTNOall0WWpZd1ppMDNZamM0TkdKallUVXpabVU2TWpRNU9EZ3lORGM1TXpVM05qZzRJaXdpWVhWa0lqb2lVMUJTU1U1TFRGSWlMQ0p1WW1ZaU9qRTNORGswTWprME16VXNJbk5qYjNCbElqcGJJbEpGUVVRaUxDSlhVa2xVUlNKZExDSnpaWE56YVc5dVZHbHRaVzkxZENJNk1UQXhNamd3TENKd1lYSjBibVZ5U1dRaU9qa3dNRFFzSW1WNGNDSTZNVGMwT1RZNE9UZ3pOU3dpWVhWMGFGUjVjR1VpT2lKVFVGSmZTMFZaWDFCQlUxTmZURTlIU1U0aUxDSjBiMnRsYmxSNWNHVWlPaUpCUTBORlUxTWlMQ0pwWVhRaU9qRTNORGswTXpBMk16VXNJbXAwYVNJNkluTndjbWx1YTJ4eUlpd2liV2xqY205VFpYSjJhV05sSWpvaWMzQnlJbjAuZHVKMkVtbllWaVBIbi1mVkduZV9YNVRxS3FfbGYwNzB5alEtNEx2emRiUHF6V2hzeUpETk13Tm9qX2RVeXJQLXotbUtHeGJHdWUwM1lCby1OT2tiVjZmQXlER0lDQ0lVWno0SVdsSGNSeTM4YnQzRXBFOXRBZzV1M0lHNGxLNVpRaVdqaGd4ZHZlUGo4MUZNTkpmbUwtZkZ3Y3N6bXpWalNtVTFNREQwSHcxLWx5S0p2T1FGSWdxc214Y3FCOHlfOWpadlJIUF9pOVBoemg4bllWc3NGSVdZN2s2M3RUcS0xNWJ2bm01eUQ4WDF6cWdtOHVBdTVpenN2cUlodzM4N3JlY0hfbm5NbVpXM3lLdkZ6MURkcHJFYmRwdjd0QXNOY2ZvaUJDT0g5NkFWVXdVWUh3anNVMGdUY1NudGhIMlJ2R1N1RE1IYnd3SkkxYUxsN1NsbjhnIn0.R885+9Xg+tXunXAUgVtRinKUC2E14tl+c72je7wskho; sess-exp-time=Tue, 10 Jun 2025 05:08:17 GMT", description="Sprinklr API cookies for authentication")
    SPRINKLR_REQUEST_AT : str = Field(default="1749430817365", description="Timestamp for the Sprinklr API request")
    SPRINKLR_REQUEST_ID: str = Field(default="space-a34b39b9-e20c-4900-b32e-0ad138162c14", description="Unique request ID for Sprinklr API")
    SPRINKLR_CSRF_TOKEN: str = Field(default="OGgyaHVFMDM4R1RVQkZocTRmT2p2", description="CSRF token for Sprinklr API requests")
    SPRINKLR_SENTRY_TRACE: str = Field(default="4a1ef890c8e52537e4b36ecce331f79e-a2f6df7b75e9286c", description="Sentry trace ID for Sprinklr API requests")


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
