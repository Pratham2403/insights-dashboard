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
        default="https://space-prod0.sprinklr.com/ui/rest/reports/query",
        description="Sprinklr API endpoint"
    )
    SPRINKLR_COOKIES : str = Field(default="SPR_STICKINESS=1749621537.848.68.373109|935c7dcb81a00314ea56a3b1f4989107; JSESSIONID=2552D3D6587DEE68616AB16E127ABAAC; user.env.type=ENTERPRISE; connect.token=eyJ2M1Nlc3Npb25VcGRhdGVkIjoidHJ1ZSIsImFjY2Vzc1Rva2VuIjoiZXlKaGJHY2lPaUpTVXpJMU5pSjkuZXlKemRXSWlPaUpCWTJObGMzTWdWRzlyWlc0Z1IyVnVaWEpoZEdWa0lFSjVJRk53Y21sdWEyeHlJaXdpWTJ4cFpXNTBTV1FpT2pFd01EQXdNRFExTURrc0lteHZaMmx1VFdWMGFHOWtJam9pVTBGTlRDSXNJbTkwWVVsa0lqb2lOamcwT0RBMU4yVXlPV1l4WXpnMk5UWTVaREk0WmpVNElpd2lhWE56SWpvaVUxQlNTVTVMVEZJaUxDSjBlWEFpT2lKS1YxUWlMQ0oxYzJWeVNXUWlPakV3TURBME5qSXhNellzSW5WMWFXUWlPaUkzWWpKaFlUbGpOQzA1TkdRNExUUTVOalV0T0RVeU5TMHlaVFZpT0dFME9XTmpPVE02TVRBMk1UQTJOakUyTmpnNE5ESTBJaXdpWVhWa0lqb2lVMUJTU1U1TFRGSWlMQ0p1WW1ZaU9qRTNORGsxTkRreU5qTXNJbk5qYjNCbElqcGJJbEpGUVVRaUxDSlhVa2xVUlNKZExDSnpaWE56YVc5dVZHbHRaVzkxZENJNk1UQXhNamd3TENKd1lYSjBibVZ5U1dRaU9qa3dNRFFzSW1WNGNDSTZNVGMwT1Rnd09UWTJNeXdpWVhWMGFGUjVjR1VpT2lKVFVGSmZTMFZaWDFCQlUxTmZURTlIU1U0aUxDSjBiMnRsYmxSNWNHVWlPaUpCUTBORlUxTWlMQ0pwWVhRaU9qRTNORGsxTlRBME5qTXNJbXAwYVNJNkluTndjbWx1YTJ4eUlpd2liV2xqY205VFpYSjJhV05sSWpvaWMzQnlJbjAuVWhkZzlIZUcwT093OWhNYlFMRmdOcElpblhMbjd2VFIwa2J0LXdBUzRhMXpQYXZyYjZjdjF2T1E0dHVrZFdocGpWVHZFTndBaVpVQmJFRVRXb2lvckZrNG9Idng4MVEwRllOVTc2U3FEbHdGVkZCakNoRjhKa1BCMllHa0pLeFJhS01oNXNmYm00b09OcmoyYVplVVl4dmVQSHhESktteHgtaEdZNUFzMzlXRDZFYUFBdGIyQ0ZWTlJfMnYwaTRCN3R4MjJqNTRldHdnX3RWZXBRMU1TS1RYbVRhWTRHdkloNElTS21ZOHdlOVlfLXR0OGxpNm8xQ1Brc0d1Slp6d2ZhZmNseVNadWQtQVA0SUxwcGVub3JoX1FNZHF1S1ctWkUzVk1STHVVLXpOZEM2NDJqNG1YYW1Ub3NLV09BZE5qOW9aeUxLcHVJQXRKaFRlb1AydVNnIn0.BNdq1y8/3hydsiCLwre5zRumpCvo7PnS0BgfuWIFRg8; SPR_AT=d0V5SmFhMG5xT1ZGdzVVR212aVdN; connect.sid=s%3AlIAfTTGJuCi_SkjO8Zcjf-3id4-Me-np.Jkz4gjPQfBEXdSxRsRZzK4HN74zCBRfNf%2BnnOxKeBE4; sess-exp-time=Thu, 12 Jun 2025 14:34:02 GMT", description="Sprinklr API cookies for authentication")
    SPRINKLR_REQUEST_AT : str = Field(default="1749637562791", description="Timestamp for the Sprinklr API request")
    SPRINKLR_REQUEST_ID: str = Field(default="space-cdc1df87-fbac-42f0-89fe-ecb0f0ba2007", description="Unique request ID for Sprinklr API")
    SPRINKLR_CSRF_TOKEN: str = Field(default="d0V5SmFhMG5xT1ZGdzVVR212aVdN", description="CSRF token for Sprinklr API requests")
    SPRINKLR_SENTRY_TRACE: str = Field(default="f78fe4611d08667f91ac92f6d5e6e0b2-80c993c32d637e3f", description="Sentry trace ID for Sprinklr API requests")

    # MongoDB Configuration for Persistence
    MONGODB_URI: str = Field(default="mongodb://localhost:27017/insights_dashboard", description="MongoDB connection URI")
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
