# src/services/embedding_service.py - FORCE OLLAMA MODE
import google.generativeai as genai
import requests
import json
from typing import List, Optional
import time
import logging
from enum import Enum
from circuitbreaker import circuit
from src.config.settings import settings

logger = logging.getLogger(__name__)

class EmbeddingProvider(Enum):
    GEMINI = "gemini"
    OLLAMA = "ollama"

class OllamaFallbackEmbeddingService:
    """Embedding service with automatic fallback from Gemini to Ollama - FORCE OLLAMA MODE"""
    
    def __init__(self):
        # Gemini setup (kept for manual testing)
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.gemini_model = "models/embedding-001"
        
        # Ollama setup
        self.ollama_base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        self.ollama_model = getattr(settings, 'OLLAMA_EMBEDDING_MODEL', 'nomic-embed-text')
        self.ollama_timeout = getattr(settings, 'OLLAMA_TIMEOUT', 30)
        
        # FORCE OLLAMA MODE - Skip Gemini entirely for normal operations
        self.gemini_failures = 999  # High number to force fallback
        self.max_failures_before_fallback = 3
        self.last_gemini_attempt = 0
        self.gemini_cooldown_seconds = 300
        self.use_fallback = True  # FORCE OLLAMA USAGE
        self.ollama_available = False
        
        # Test Ollama availability on startup
        self._test_ollama_connection()

        # Stats
        self.stats = {
            "gemini_requests": 0,
            "gemini_successes": 0,
            "gemini_failures": 0,
            "ollama_requests": 0,
            "ollama_successes": 0,
            "ollama_failures": 0,
            "fallback_activations": 0
        }
        
        logger.info("Embedding service initialized in OLLAMA-ONLY mode (preserving Gemini quota for cultural analysis)")
    
    def _test_ollama_connection(self):
        """Test if Ollama is running and model is available"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                
                if self.ollama_model in model_names:
                    self.ollama_available = True
                    logger.info(f"Ollama connection successful. Model '{self.ollama_model}' available")
                else:
                    logger.warning(f"Ollama running but model '{self.ollama_model}' not found")
                    logger.info("Available models: " + ", ".join(model_names))
                    self.ollama_available = False
            else:
                logger.warning(f"Ollama responded with status {response.status_code}")
                self.ollama_available = False
                
        except requests.exceptions.ConnectionError:
            logger.warning("Ollama not running. Start with: ollama serve")
            self.ollama_available = False
        except Exception as e:
            logger.error(f"Error testing Ollama: {e}")
            self.ollama_available = False
    
    def _should_try_gemini(self) -> bool:
        """Always return False to force Ollama usage"""
        return False  # FORCE OLLAMA MODE
    
    @circuit(failure_threshold=3, recovery_timeout=60)
    def _try_gemini_embedding(self, text: str) -> Optional[List[float]]:
        """Attempt to get embedding from Gemini with circuit breaker - MANUAL USE ONLY"""
        try:
            self.stats["gemini_requests"] += 1
            self.last_gemini_attempt = time.time()
            
            result = genai.embed_content(
                model=self.gemini_model,
                content=text,
                request_options={
                    "timeout": getattr(settings, 'GEMINI_API_TIMEOUT', 30)
                }
            )
            
            self.stats["gemini_successes"] += 1
            self.gemini_failures = 0
            
            logger.debug(f"Gemini embedding successful: {text[:50]}...")
            return result['embedding']
            
        except Exception as e:
            self.stats["gemini_failures"] += 1
            self.gemini_failures += 1
            
            error_str = str(e).lower()
            
            if any(keyword in error_str for keyword in ['quota', '429', 'rate limit', 'exceeded']):
                # Don't log quota errors in forced Ollama mode
                pass
            else:
                logger.error(f"Gemini API error: {e}")
            
            return None
    
    def _try_ollama_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding from Ollama"""
        if not self.ollama_available:
            logger.error("Ollama not available")
            return None
            
        try:
            self.stats["ollama_requests"] += 1
            
            payload = {
                "model": self.ollama_model,
                "prompt": text
            }
            
            response = requests.post(
                f"{self.ollama_base_url}/api/embeddings",
                json=payload,
                timeout=self.ollama_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result.get('embedding')
                
                if embedding:
                    self.stats["ollama_successes"] += 1
                    logger.debug(f"Ollama embedding successful: {text[:50]}...")
                    return embedding
                else:
                    logger.error("Ollama response missing embedding")
                    self.stats["ollama_failures"] += 1
                    return None
            else:
                logger.error(f"Ollama error: {response.status_code} - {response.text}")
                self.stats["ollama_failures"] += 1
                return None
                
        except requests.exceptions.Timeout:
            logger.error("Ollama timeout")
            self.stats["ollama_failures"] += 1
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama")
            self.ollama_available = False
            self.stats["ollama_failures"] += 1
            return None
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            self.stats["ollama_failures"] += 1
            return None
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """FORCE OLLAMA MODE - Skip Gemini entirely to preserve quota"""
        if not text or not text.strip():
            logger.warning("Empty text for embedding")
            return None
        
        # SKIP ALL GEMINI LOGIC - Use Ollama directly
        logger.debug("Using Ollama for embeddings (preserving Gemini quota for cultural analysis)")
        return self._try_ollama_embedding(text)
    
    def force_gemini(self, text: str) -> Optional[List[float]]:
        """Force Gemini attempt - MANUAL TESTING ONLY"""
        logger.warning("Manual Gemini embedding call - this will consume quota!")
        return self._try_gemini_embedding(text)
    
    def force_ollama(self, text: str) -> Optional[List[float]]:
        """Force Ollama attempt"""
        return self._try_ollama_embedding(text)
    
    def reset_fallback(self):
        """Reset fallback state - DISABLED IN FORCE OLLAMA MODE"""
        logger.info("Reset fallback called, but staying in Ollama-only mode")
        # Don't actually reset - keep using Ollama
    
    def get_provider_info(self) -> dict:
        """Get current provider information"""
        return {
            "current_provider": EmbeddingProvider.OLLAMA.value,  # Always Ollama
            "gemini_available": False,  # Disabled to preserve quota
            "ollama_available": self.ollama_available,
            "ollama_model": self.ollama_model,
            "ollama_url": self.ollama_base_url,
            "fallback_active": True,  # Always in "fallback" (Ollama) mode
            "consecutive_failures": self.gemini_failures,
            "cooldown_remaining": 999,  # Always in cooldown
            "mode": "FORCE_OLLAMA_FOR_QUOTA_PRESERVATION"
        }
    
    def get_stats(self) -> dict:
        """Get detailed statistics"""
        provider_info = self.get_provider_info()
        total_requests = self.stats["gemini_requests"] + self.stats["ollama_requests"]
        
        return {
            "total_requests": total_requests,
            "provider_info": provider_info,
            "gemini_stats": {
                "requests": self.stats["gemini_requests"],
                "successes": self.stats["gemini_successes"],
                "failures": self.stats["gemini_failures"],
                "success_rate": f"{(self.stats['gemini_successes'] / max(1, self.stats['gemini_requests']) * 100):.1f}%"
            },
            "ollama_stats": {
                "requests": self.stats["ollama_requests"],
                "successes": self.stats["ollama_successes"], 
                "failures": self.stats["ollama_failures"],
                "success_rate": f"{(self.stats['ollama_successes'] / max(1, self.stats['ollama_requests']) * 100):.1f}%",
                "model": self.ollama_model,
                "available": self.ollama_available
            },
            "fallback_activations": self.stats["fallback_activations"]
        }
    
    def health_check(self) -> dict:
        """Check health of both providers - STARTUP SAFE VERSION"""
        health = {"overall_status": "healthy", "providers": {}}
        
        # DON'T make actual API calls during startup - just check configuration
        health["providers"]["gemini"] = {
            "status": "disabled_for_quota_preservation",
            "available": False,
            "note": "Disabled to preserve quota for cultural analysis"
        }
        
        # Test Ollama connection only (no API quota)
        health["providers"]["ollama"] = {
            "status": "active" if self.ollama_available else "not_available",
            "available": self.ollama_available,
            "model": self.ollama_model
        }
        
        return health

# Global instance
embedding_service = OllamaFallbackEmbeddingService()

# Backward compatible function
def get_embedding(text: str) -> Optional[List[float]]:
    """Backward compatible function - OLLAMA ONLY MODE"""
    return embedding_service.get_embedding(text)