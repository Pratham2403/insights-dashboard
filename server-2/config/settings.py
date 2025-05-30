import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from pydantic import Field, SecretStr, HttpUrl

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sprinklr Insights Dashboard Backend"
    PROJECT_VERSION: str = "0.1.0"

    # LLM Router settings
    LLM_ROUTER_BASE_URL: HttpUrl = Field(default=HttpUrl('http://qa6-intuitionx-llm-router-v2.sprinklr.com/chat-completion'))
    LLM_ROUTER_CLIENT_IDENTIFIER: str = Field(default='spr-backend-interns-25')
    DEFAULT_LLM_MODEL: str = Field(default='gpt-4o')

    # Elasticsearch configuration (placeholders - not actively used by dummy service yet)
    ELASTICSEARCH_HOST: str = "http://localhost:9200"
    ELASTICSEARCH_INDEX_NAME: str = "sprinklr_insights_data" # Example

    # State persistence configuration
    # Currently using LangGraph's in-memory MemorySaver.
    # For persistent storage, you might add:
    # MONGO_CONNECTION_STRING: Optional[str] = None 
    # MONGO_DATABASE_NAME: Optional[str] = "insights_dashboard_state"
    # STATE_FILE_PATH: str = "./project_states.json" 
    STATE_PERSISTENCE_TYPE: str = "in_memory" # "mongodb", "file"

    # LangGraph / Agent settings - LLM models
    QUERY_GENERATION_LLM_MODEL: str = "gpt-4o" # Using a more capable model for queries
    DATA_PROCESSING_LLM_MODEL: str = "gpt-3.5-turbo" # Can be same as default or specialized
    MAX_CONVERSATION_HISTORY_IN_STATE: int = 50 # Max messages stored in ProjectState.messages

    # Logging configuration
    LOG_LEVEL: str = "INFO" # e.g., DEBUG, INFO, WARNING, ERROR

    # CORS settings
    CORS_ALLOW_ORIGINS: List[str] = ["*"] # Allow all for dev, restrict in prod
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # model_config allows pydantic-settings to load from .env file
    # It will override defaults if variables are found in the .env file or environment
    model_config = SettingsConfigDict(env_file=".env", extra='ignore', case_sensitive=False)


settings = Settings()
