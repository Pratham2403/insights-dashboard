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
    SPRINKLR_COOKIES: Optional[str] = Field(default="SPR_STICKINESS=1749206150.75.66.232491|82e1351007a7c3c95a47ab53204a1f03; JSESSIONID=7595036953C0E5D1FBE07014F517ABF3; user.env.type=ENTERPRISE; connect.sid=s%3AR5dMTp4OISMa5JXQibcHpDraoR0FS2Ob.eO6oApUKiX%2BPJ8uN5u50mBgw4Tya1fN%2FCtGyyY40I%2F4; SPR_AT=SUE3SFdCVG9HVno5MVdyeUNxV24y; connect.token=eyJ2M1Nlc3Npb25VcGRhdGVkIjoidHJ1ZSIsImFjY2Vzc1Rva2VuIjoiZXlKaGJHY2lPaUpTVXpJMU5pSjkuZXlKemRXSWlPaUpCWTJObGMzTWdWRzlyWlc0Z1IyVnVaWEpoZEdWa0lFSjVJRk53Y21sdWEyeHlJaXdpWTJ4cFpXNTBTV1FpT2pFd01EQXdNRFExTURrc0lteHZaMmx1VFdWMGFHOWtJam9pVTFCU1gxQkJVMU5YVDFKRVgweFBSMGxPSWl3aWIzUmhTV1FpT2lJMk9ETmhaR1UzT1RjMVl6VTRNak5pTmpVNE9ESTNZVGdpTENKcGMzTWlPaUpUVUZKSlRrdE1VaUlzSW5SNWNDSTZJa3BYVkNJc0luVnpaWEpKWkNJNk1UQXdNRFEyTWpFek5pd2lkWFZwWkNJNklqTTJNekJpTlRZM0xXTTFPREl0TkdNd1ppMWhaRE0wTFdZeU1EY3pNRFkwWWpWbU9Ub3hNelUyTmpBMU1UQTNPVEl5TWpJeElpd2lZWFZrSWpvaVUxQlNTVTVMVEZJaUxDSnVZbVlpT2pFM05Ea3lNRFU1TkRBc0luTmpiM0JsSWpwYklsSkZRVVFpTENKWFVrbFVSU0pkTENKelpYTnphVzl1VkdsdFpXOTFkQ0k2TVRBeE1qZ3dMQ0p3WVhKMGJtVnlTV1FpT2prd01EUXNJbVY0Y0NJNk1UYzBPVFEyTmpNME1Dd2lZWFYwYUZSNWNHVWlPaUpUVUZKZlMwVlpYMUJCVTFOZlRFOUhTVTRpTENKMGIydGxibFI1Y0dVaU9pSkJRME5GVTFNaUxDSnBZWFFpT2pFM05Ea3lNRGN4TkRBc0ltcDBhU0k2SW5Od2NtbHVhMnh5SWl3aWJXbGpjbTlUWlhKMmFXTmxJam9pYzNCeUluMC5WY1hoaTZycW9pbWo1dGpJR194V19EelF3TFE4OXl3ZDZYanNLVnZjRXl6eThuUFdfNmN3MS1XZEFaU3lVZDY1Q1pYem8yQUo5VnVHQXJzZG5WYjhZSmdUYU5XdkpTRFpseFdtM2t1RTRwQlBDVFlBaHlmVXZackNyRnVDN1M0SlJlVm9PcEJ2YWZMd1JWQ3lGaTRFa3JOcXpCVVZ5azVfWDg3ZHViOHJzU0UtV1Z2QkFrNTk0NFRTcVJQRFFtV083Y3gwMEpzZWRxRXdwZk93eTA5RWhKclVyWkNGOEt0Y00wbEVvR203MkI5dGVNX3M2emxCU2d6eFg5bmp3dlo4aEh2UW1vaXBXS05lVTRoZ3NRdjFlaGJkakNZZVRCYW15RDRhSjhURjI4aTJiVXFEVTdYNk1DVkMtVHVuX1I1SDVhTEdqUy1EeFlxbnpha0N6RDMtZ3cifQ.3IYsgnvWY5YyqXmsn0jjkaVLhb0PR2Ua4dcu1iUgWd8; sess-exp-time=Sat, 7 Jun 2025 15:24:22 GMT", description="Sprinklr authentication cookies")
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
