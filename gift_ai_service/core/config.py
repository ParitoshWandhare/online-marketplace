# gift_ai_service/core/config.py
"""
Unified Configuration using Pydantic Settings
Supports both Member A and Member B requirements
"""

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # MongoDB - Primary naming
    MONGO_URI: str = "mongodb://localhost:27017/test"
    DATABASE_NAME: str = "test"
    COLLECTION_NAME: str = "artworks"
    
    # Alternative naming (auto-synced)
    MONGODB_URL: Optional[str] = None
    MONGO_DB: Optional[str] = None
    MONGO_COLLECTION: Optional[str] = None

    # LLM APIs
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gemini-1.5-flash-001"

    # Vector DB (Qdrant)
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    
    # Microservices URLs
    LANGUAGE_SERVICE_URL: str = "http://127.0.0.1:8001"
    VECTOR_SERVICE_URL: str = "http://127.0.0.1:8002"
    VISION_AI_SERVICE_URL: str = "http://127.0.0.1:8001"
    
    # App Config
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    PORT: int = 8001

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allows extra fields
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Sync MONGODB_URL ↔ MONGO_URI
        if not self.MONGODB_URL:
            self.MONGODB_URL = self.MONGO_URI
        elif self.MONGODB_URL != self.MONGO_URI:
            self.MONGO_URI = self.MONGODB_URL
            
        # Sync DATABASE_NAME ↔ MONGO_DB
        if not self.MONGO_DB:
            self.MONGO_DB = self.DATABASE_NAME
        elif self.MONGO_DB != self.DATABASE_NAME:
            self.DATABASE_NAME = self.MONGO_DB
            
        # Sync COLLECTION_NAME ↔ MONGO_COLLECTION
        if not self.MONGO_COLLECTION:
            self.MONGO_COLLECTION = self.COLLECTION_NAME
        elif self.MONGO_COLLECTION != self.COLLECTION_NAME:
            self.COLLECTION_NAME = self.MONGO_COLLECTION
            
        # Sync API keys (GOOGLE_API_KEY ↔ GEMINI_API_KEY)
        if self.GOOGLE_API_KEY and not self.GEMINI_API_KEY:
            self.GEMINI_API_KEY = self.GOOGLE_API_KEY
        elif self.GEMINI_API_KEY and not self.GOOGLE_API_KEY:
            self.GOOGLE_API_KEY = self.GEMINI_API_KEY

# Singleton instance
settings = Settings()