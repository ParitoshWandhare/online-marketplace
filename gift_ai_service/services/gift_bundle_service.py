"""
Gift bundle generation service using LLMs (Gemini with Ollama fallback).
"""

import os
import logging
import json
import requests
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GiftBundleService:
    """Generates gift bundles using LLM with fallback support."""
    
    def __init__(self, llm_model: str = None):
        """
        Initialize GiftBundleService.
        
        Args:
            llm_model: LLM model to use (defaults to environment variable)
        """
        self.llm_model = llm_model or os.getenv('LLM_MODEL', 'models/gemini-2.5-flash')
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        
        if self.google_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.google_api_key)
                self.genai = genai
            except ImportError:
                logger.warning("google-generativeai not installed, Gemini functionality disabled")
                self.genai = None
        else:
            self.genai = None
        
        logger.info(f"GiftBundleService initialized with model: {self.llm_model}")

    def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        """Call Gemini API for bundle generation."""
        try:
            model = self.genai.GenerativeModel(self.llm_model)
            response = model.generate_content(prompt)
            
            # Extract JSON from response
            response_text = response.text
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0]
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0]
            
            result = json.loads(response_text.strip())
            logger.info("Successfully generated bundles using Gemini")
            return result
            
        except Exception as e:
            logger.error(f"Gemini API call failed: {str(e)}")
            raise

    def _call_ollama(self, prompt: str) -> Dict[str, Any]:
        """Call Ollama API as fallback for bundle generation."""
        try:
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'llama3.1',  # or any available model
                    'prompt': prompt,
                    'stream': False,
                    'format': 'json'
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                
                # Try to extract JSON
                try:
                    if '```json' in response_text:
                        response_text = response_text.split('```json')[1].split('```')[0]
                    bundle_data = json.loads(response_text.strip())
                    logger.info("Successfully generated bundles using Ollama")
                    return bundle_data
                except json.JSONDecodeError:
                    # If JSON parsing fails, create a simple structure
                    logger.warning("Ollama response not valid JSON, creating fallback structure")
                    return {
                        "bundles": [
                            {
                                "bundle_name": "Thoughtful Gift Set",
                                "description": f"A curated selection for {prompt.split(':')[0] if ':' in prompt else 'your needs'}",
                                "items": []
                            }
                        ]
                    }
            else:
                logger.error(f"Ollama API call failed with status: {response.status_code}")
                raise Exception(f"Ollama API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Ollama fallback also failed: {str(e)}")
            raise

    def generate_bundles(self, user_intent: str, items: List[Dict]) -> Dict[str, Any]:
        """
        Generate gift bundles using Gemini first, fallback to Ollama if fails.
        
        Args:
            user_intent: User's gift search intent
            items: List of validated items
            
        Returns:
            Dict containing query and bundles
        """
        logger.info(f"Generating bundles for intent: {user_intent} with {len(items)} items")
        
        # Import here to avoid circular imports
        from services.gift_prompt_templates import get_gift_bundle_prompt, get_fallback_prompt
        
        # Generate appropriate prompt
        prompt = get_gift_bundle_prompt(user_intent, items)
        
        try:
            # Try Gemini first
            if self.google_api_key and self.genai:
                result = self._call_gemini(prompt)
            else:
                raise Exception("No Google API key available or Gemini not configured")
                
        except Exception as e:
            logger.warning(f"Gemini failed, trying Ollama: {str(e)}")
            try:
                # Fallback to Ollama with simplified prompt
                fallback_prompt = get_fallback_prompt(user_intent, items)
                result = self._call_ollama(fallback_prompt)
            except Exception as ollama_error:
                logger.error(f"All LLM providers failed: {str(ollama_error)}")
                # Return minimal fallback result
                result = {
                    "bundles": [
                        {
                            "bundle_name": "Backup Gift Selection",
                            "description": "We've selected some great items based on your search",
                            "items": [
                                {
                                    "title": item.get('title', 'Unknown'),
                                    "reason": "Matches your interests"
                                }
                                for item in items[:2]  # Use first 2 items as fallback
                            ]
                        }
                    ]
                }
        
        # Ensure result has proper structure
        if 'bundles' not in result:
            result = {'bundles': []}
        
        final_result = {
            'query': user_intent,
            'bundles': result['bundles']
        }
        
        logger.info(f"Generated {len(final_result['bundles'])} bundles")
        return final_result