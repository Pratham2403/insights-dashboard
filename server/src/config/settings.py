"""
Modern Configuration settings for the Sprinklr Insights Dashboard Application.
Uses Pydantic settings with proper .env file integration.
"""

import os
from typing import Dict, Optional, Any, List, Union
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

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
    SPRINKLR_COOKIES: Optional[str] = Field(default="SPR_STICKINESS=1749112027.877.27.666754|935c7dcb81a00314ea56a3b1f4989107; JSESSIONID=23DD6229A0580F7D0AEAB4B4A470A159; user.env.type=ENTERPRISE; SPR_AT=SGFWNkNhbDJSVWRlOGkzdjhxSUox; connect.token=eyJ2M1Nlc3Npb25VcGRhdGVkIjoidHJ1ZSIsImFjY2Vzc1Rva2VuIjoiZXlKaGJHY2lPaUpTVXpJMU5pSjkuZXlKemRXSWlPaUpCWTJObGMzTWdWRzlyWlc0Z1IyVnVaWEpoZEdWa0lFSjVJRk53Y21sdWEyeHlJaXdpWTJ4cFpXNTBTV1FpT2pFd01EQXdNRFExTURrc0lteHZaMmx1VFdWMGFHOWtJam9pVTBGTlRDSXNJbTkwWVVsa0lqb2lOamd6Wm1VMFptUTFNalU0WW1VMFkyRTFORGc0TnpFM0lpd2lhWE56SWpvaVUxQlNTVTVMVEZJaUxDSjBlWEFpT2lKS1YxUWlMQ0oxYzJWeVNXUWlPakV3TURBME5qSXhNellzSW5WMWFXUWlPaUl6Wm1Oak5UZ3hZeTFpWlRRMExUUTBORE10WWpJM1lTMDRaakkyTkdGa05EZGlZakU2TXpVNE5EazVORGswTlRJeU1URTVJaXdpWVhWa0lqb2lVMUJTU1U1TFRGSWlMQ0p1WW1ZaU9qRTNORGt3TVRZMk5UUXNJbk5qYjNCbElqcGJJbEpGUVVRaUxDSlhVa2xVUlNKZExDSnpaWE56YVc5dVZHbHRaVzkxZENJNk1UQXhNamd3TENKd1lYSjBibVZ5U1dRaU9qa3dNRFFzSW1WNGNDSTZNVGMwT1RJM056QTFOQ3dpWVhWMGFGUjVjR1VpT2lKVFVGSmZTMFZaWDFCQlUxTmZURTlIU1U0aUxDSjBiMnRsYmxSNWNHVWlPaUpCUTBORlUxTWlMQ0pwWVhRaU9qRTNORGt3TVRjNE5UUXNJbXAwYVNJNkluTndjbWx1YTJ4eUlpd2liV2xqY205VFpYSjJhV05sSWpvaWMzQnlJbjAuWTBlMEpIcTliSTlWYklBcjc1OEZKQWZEWDBoQ0M1WUt1WGJ0TlY0cTNzTVBUaXlMS3lNS2dHbmpIOW96Uk5jVVZORFFFRWdVTWZjRGNYN0h3ZXRTS1RBbjNTcTUxa19meWs0cmtyU0RXZ2l0WGx5R05NSWVMUXE0Z3FIT0VlN1F0cHQ2aTVpSGVSeTYxSFZTRklLeFlpR0l0WU1nYnE3U3AwbXpnblBiTU1Ea1lFMndZSU8xNTNMcjhsREtfU3c1dzhYeVNqMWE0R1BUUWVkMElMOE4zU1U0X1prNHAwZkszOEl6Ni05MTM4bFBXS3d2eEtidXhCYjhpUkZBSTN3amJiMzZBS05KTU1nZDZqZVdUczlYc1RSdHRlX2pRbWdUTUtHbnM4eE0yUzRfU3liUG1jX2N2eUNWRkdIY1ZtM0VkZ24xaUNNTjloWGNwQVVMOURTMTBnIn0.SMn78Zk16EI8adB5wQZeysvoDeoZd6YXcfCzIHzSoCc; connect.sid=s%3A8I_FMb_JHwEK6FDfZduWvnwx9QU9XqlD.eW20oYz20VVnYs24eMQLE02WbqMwlQqRDGbwLRO8Ulo; sess-exp-time=Fri, 6 Jun 2025 12:50:02 GMT", description="Sprinklr authentication cookies")
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
