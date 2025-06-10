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
    ENVIRONMENT: str = Field(default=os.getenv("ENVIROMENT"), description="Application environment (development/production)")
    
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
    SPRINKLR_COOKIES : str = Field(default="SPR_STICKINESS=1749511218.679.68.934870|935c7dcb81a00314ea56a3b1f4989107; JSESSIONID=26F3384C4EE461D6CF2B5327AB09EF40; user.env.type=ENTERPRISE; SPR_AT=bm5yOE1mQkpCdGFlb0hmNVpIWWJD; connect.token=eyJ2M1Nlc3Npb25VcGRhdGVkIjoidHJ1ZSIsImFjY2Vzc1Rva2VuIjoiZXlKaGJHY2lPaUpTVXpJMU5pSjkuZXlKemRXSWlPaUpCWTJObGMzTWdWRzlyWlc0Z1IyVnVaWEpoZEdWa0lFSjVJRk53Y21sdWEyeHlJaXdpWTJ4cFpXNTBTV1FpT2pFd01EQXdNRFExTURrc0lteHZaMmx1VFdWMGFHOWtJam9pVTFCU1gxQkJVMU5YVDFKRVgweFBSMGxPSWl3aWIzUmhTV1FpT2lJMk9EUTNObU15WldZd05qazJNVFEwWlRCbFl6STJNVGtpTENKcGMzTWlPaUpUVUZKSlRrdE1VaUlzSW5SNWNDSTZJa3BYVkNJc0luVnpaWEpKWkNJNk1UQXdNRFEyTWpFek5pd2lkWFZwWkNJNklqUTBORFEwWlRSbExXRTFZVEl0TkRBd1ppMWhOVGc1TFdFNFpEazFPVFZqTVRWbE9Eb3hNamN6TWpBd05qTXhPVEl6TnlJc0ltRjFaQ0k2SWxOUVVrbE9TMHhTSWl3aWJtSm1Jam94TnpRNU5URXdNREUwTENKelkyOXdaU0k2V3lKU1JVRkVJaXdpVjFKSlZFVWlYU3dpYzJWemMybHZibFJwYldWdmRYUWlPakV3TVRJNE1Dd2ljR0Z5ZEc1bGNrbGtJam81TURBMExDSmxlSEFpT2pFM05EazNOekEwTVRRc0ltRjFkR2hVZVhCbElqb2lVMUJTWDB0RldWOVFRVk5UWDB4UFIwbE9JaXdpZEc5clpXNVVlWEJsSWpvaVFVTkRSVk5USWl3aWFXRjBJam94TnpRNU5URXhNakUwTENKcWRHa2lPaUp6Y0hKcGJtdHNjaUlzSW0xcFkzSnZVMlZ5ZG1salpTSTZJbk53Y2lKOS5aLTNEQ1pZeW42RkEzVEphQlBoNHFEQWI1dmhKMHhYbkpIQ2tvejJva3hyWGV1QkZiNWlOLTg3VE9PNWpiWDdTMG5SNFJwZlRERlBNOEExd01aZll0Nmc4YV9ESThNYVVtZ0pnUmpyUXFubFNnTDUyclJSRjFsaUpTeFZ4cVlMMEMxY3FweC13UWRLMGZBakVSeWpValZLRFVFVldPQ2h5ME42TjhldUF0bnJhZ2RHQmI5RGJ6aEIxR0xBY3VGWTJrNXd5OTFiaDZDazVPMF9oVnVlNkVpZ2Y0alJuT3N0cFBhSmtURzZDR2o2a3Bac0FDckVlcXMyOXFLZXVIRkMxUDk3Q0RmYTdDUU9saTMzNjNxLWsxSjFzcURBSzczendwdzVlX1oySlo5VzhnYTRjNnVkLUdUSTNzRVRvT0pLM042RTJnUUJ4RHJNQ0EydVJKMHlhNEEifQ.fKeHtUSEejLsit/ak7CBslxj0czYgRZIlx5c95RVx/8; connect.sid=s%3ADWpT_8tk4OzRThIKQY2-1S9QZRPiGDE-.Dk88x5OXgePqrT1oOEjXDoooZghxGWkG10EtvG9zI3I; sess-exp-time=Wed, 11 Jun 2025 05:25:15 GMT", description="Sprinklr API cookies for authentication")
    SPRINKLR_REQUEST_AT : str = Field(default="1749518235212", description="Timestamp for the Sprinklr API request")
    SPRINKLR_REQUEST_ID: str = Field(default="space-75900045-2647-4d14-b347-5226e059c47b", description="Unique request ID for Sprinklr API")
    SPRINKLR_CSRF_TOKEN: str = Field(default="bm5yOE1mQkpCdGFlb0hmNVpIWWJD", description="CSRF token for Sprinklr API requests")
    SPRINKLR_SENTRY_TRACE: str = Field(default="12f7b8d965654154ae1a5b6e72dbcd92-84d7f94084e7713e", description="Sentry trace ID for Sprinklr API requests")

    # MongoDB Configuration for Persistence
    MONGODB_URI: str = Field(default="mongodb://localhost:27017", description="MongoDB connection URI")
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
