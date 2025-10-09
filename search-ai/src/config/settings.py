from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import logging

class Settings(BaseSettings):
    # API Keys
    GEMINI_API_KEY: str
    QDRANT_API_KEY: str
    
    # Database URLs
    QDRANT_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Collection Settings
    COLLECTION_NAME: str = "artisans"
    VECTOR_SIZE: int = 768  # Gemini embedding dimension
    
    # Performance Settings
    EMBEDDING_CACHE_TTL: int = 3600  # 1 hour in seconds
    SEARCH_CACHE_TTL: int = 300      # 5 minutes in seconds
    QUERY_EXPANSION_CACHE_TTL: int = 1800  # 30 minutes
    
    # API Rate Limiting
    GEMINI_MAX_REQUESTS_PER_MINUTE: int = 60
    GEMINI_API_TIMEOUT: int = 30
    QDRANT_TIMEOUT: int = 10
    
    # Search Performance
    MAX_SEARCH_RESULTS: int = 50
    DEFAULT_SEARCH_LIMIT: int = 10
    MAX_QUERY_EXPANSIONS: int = 3
    MAX_RERANK_CANDIDATES: int = 10
    
    # Connection Pooling
    REDIS_MAX_CONNECTIONS: int = 20
    QDRANT_MAX_CONNECTIONS: int = 10
    
    # Monitoring
    ENABLE_PERFORMANCE_LOGGING: bool = True
    LOG_LEVEL: str = "INFO"
    ENABLE_METRICS: bool = True
    
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text:latest"
    OLLAMA_TIMEOUT: int = 30
    # Circuit Breaker Settings
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60
    
    # Optional: Development Settings
    DEBUG: bool = False
    ENABLE_CACHE: bool = True
    MOCK_EXTERNAL_APIS: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore unknown env vars
    )

    def get_log_level(self) -> int:
        """Convert string log level to logging constant"""
        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        return levels.get(self.LOG_LEVEL.upper(), logging.INFO)

settings = Settings()