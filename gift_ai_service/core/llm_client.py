"""
LLM Client - Gemini + Ollama Fallback
"""
import os
import logging
import google.generativeai as genai
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class LLMClient:
    """Unified LLM client with Gemini primary and Ollama fallback"""
    
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
        
        # FIXED: Try multiple sources for API key
        self.api_key = (
            os.getenv("GOOGLE_API_KEY") or 
            os.getenv("GEMINI_API_KEY") or
            os.environ.get("GOOGLE_API_KEY") or
            os.environ.get("GEMINI_API_KEY")
        )
        
        # Debug logging
        if self.api_key:
            logger.info(f"🔑 API Key loaded: {self.api_key[:15]}...")
        else:
            logger.error("❌ NO API KEY FOUND - Checked: GOOGLE_API_KEY, GEMINI_API_KEY")
            logger.error(f"   Environment vars: {list(os.environ.keys())[:10]}...")
        
        # Initialize Gemini
        self.gemini_model = None
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                
                # Try different model names
                model_names = [
                    'gemini-2.5-flash',
                    'gemini-2.0-flash',
                    'gemini-pro-latest',
                    'gemini-flash-latest',
                    'gemini-2.5-pro',
                ]
                
                for name in model_names:
                    try:
                        self.gemini_model = genai.GenerativeModel(name)
                        logger.info(f"✅ Gemini initialized with: {name}")
                        self.model_name = name
                        break
                    except Exception as e:
                        logger.debug(f"Failed to init {name}: {e}")
                        continue
                
                if not self.gemini_model:
                    logger.warning("⚠️ No suitable Gemini model found")
                    
            except Exception as e:
                logger.error(f"Gemini init failed: {e}")
                self.gemini_model = None
        else:
            logger.warning("⚠️ No Gemini API key")
        
        # Check Ollama availability
        self.ollama_available = self._check_ollama()
        
        logger.info(f"Gemini LLM client initialized with {self.model_name}")
    
    def _check_ollama(self) -> bool:
        """Check if Ollama is available with llama3.2:3b"""
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                # Check for llama3.2 specifically
                has_llama = any(
                    'llama3.2' in m.get('name', '').lower() 
                    for m in models
                )
                if has_llama:
                    logger.info("✅ Ollama llama3.2 available as fallback")
                    return True
                else:
                    available = [m.get('name') for m in models]
                    logger.warning(f"⚠️ llama3.2 not found. Available: {available}")
        except Exception as e:
            logger.debug(f"Ollama check failed: {e}")
        
        return False
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text with Gemini → Ollama fallback
        """
        # Try Gemini first
        if self.gemini_model:
            try:
                response = self.gemini_model.generate_content(prompt)
                return response.text
            except Exception as e:
                logger.warning(f"⚠️ Gemini failed, trying Ollama: {e}")
        else:
            logger.warning("⚠️ Gemini failed, trying Ollama: No Gemini API key")
        
        # Fallback to Ollama
        if self.ollama_available:
            try:
                return self._generate_ollama(prompt)
            except Exception as e:
                logger.error(f"Ollama failed: {e}")
                raise Exception(f"❌ All LLMs failed: {e}")
        
        raise Exception("No LLM available")
    
    def _generate_ollama(self, prompt: str) -> str:
        """Generate text using Ollama llama3.2:3b"""
        try:
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'llama3.2:3b',  # ✅ FIXED: Use correct model name
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': 0.7,
                        'top_p': 0.9,
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                raise Exception(f"Ollama error: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            raise Exception("Ollama timeout (60s)")
        except requests.exceptions.ConnectionError:
            raise Exception("Ollama not running (connection refused)")
        except Exception as e:
            raise Exception(f"Ollama error: {str(e)}")