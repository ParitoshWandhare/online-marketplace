# gift_ai_service/core/config.py
"""
Configuration Management for Gift AI Service
Loads settings from environment variables with validation
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # ========================================
    # Google AI / Gemini
    # ========================================
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", os.getenv("GEMINI_API_KEY", ""))
    
    # ========================================
    # MongoDB
    # ========================================
    MONGODB_URL: str = os.getenv("MONGODB_URL", "")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "orchid_db")
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "artworks")
    
    # ========================================
    # Qdrant Vector Database
    # ========================================
    QDRANT_URL: str = os.getenv("QDRANT_URL", "")
    QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY", None)
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "gift_items")
    
    # ========================================
    # Optional: Alternative LLM Providers
    # ========================================
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY", None)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    
    # ========================================
    # Server Configuration
    # ========================================
    PORT: int = int(os.getenv("PORT", "8001"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
    
    # ========================================
    # Feature Flags
    # ========================================
    LAZY_INITIALIZATION: bool = os.getenv("LAZY_INITIALIZATION", "true").lower() == "true"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def validate_critical_settings(self) -> list[str]:
        """Validate that critical settings are present"""
        missing = []
        
        if not self.GOOGLE_API_KEY:
            missing.append("GOOGLE_API_KEY or GEMINI_API_KEY")
        
        if not self.MONGODB_URL:
            missing.append("MONGODB_URL")
        
        if not self.QDRANT_URL:
            missing.append("QDRANT_URL")
        
        return missing

# Create global settings instance
settings = Settings()

# Validate on import (but don't fail - let lazy init handle it)
missing_vars = settings.validate_critical_settings()
if missing_vars:
    import logging
    logger = logging.getLogger("gift_ai.config")
    logger.warning(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
    logger.warning("⚠️ Some features may not work until these are configured")