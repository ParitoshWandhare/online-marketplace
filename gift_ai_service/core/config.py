# gift_ai_service/core/config.py
"""
Pydantic v2 + pydantic-settings configuration
"""

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # MongoDB
    MONGODB_URL: str
    DATABASE_NAME: str = "test"
    COLLECTION_NAME: str = "artworks"

    # LLM
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Vector DB (Qdrant)
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    LANGUAGE_SERVICE_URL: str = "http://127.0.0.1:8001"
    VECTOR_SERVICE_URL: str = "http://127.0.0.1:8002"
    # App
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False

# Singleton
settings = Settings()