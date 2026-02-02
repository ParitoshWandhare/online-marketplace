# gift_ai_service/services/gift_bundle_service.py
"""
Gift Bundle Generation Service
Fixed: Proper indentation and error handling
"""

import os
import logging
import json
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GiftBundleService:
    """Generates gift bundles using LLM with fallback support"""
    
    def __init__(self, llm_model: str = None):
        """Initialize GiftBundleService"""
        self.llm_model = llm_model or os.getenv('LLM_MODEL', 'gemini-1.5-flash-001')
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        
        if self.google_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.google_api_key)
                self.genai = genai
                logger.info(f"✅ Gemini initialized: {self.llm_model}")
            except ImportError:
                logger.warning("⚠️ google-generativeai not installed")
                self.genai = None
        else:
            self.genai = None
            logger.warning("⚠️ No Gemini API key")

    def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        """Call Gemini API"""
        try:
            model = self.genai.GenerativeModel(self.llm_model)
            response = model.generate_content(prompt)
            
            # Extract JSON
            response_text = response.text
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0]
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0]
            
            result = json.loads(response_text.strip())
            logger.info("✅ Gemini generated bundles")
            return result
            
        except Exception as e:
            logger.error(f"Gemini failed: {e}")
            raise

    async def generate_bundles(self, user_intent: str, items: List[Dict]) -> Dict[str, Any]:
        """
        Generate bundles using Gemini with hardcoded fallback (Ollama disabled for deployment)
        """
        logger.info(f"🎨 Generating bundles: '{user_intent}' with {len(items)} items")
        
        from services.gift_prompt_templates import get_gift_bundle_prompt
        
        prompt = get_gift_bundle_prompt(user_intent, items)
        
        try:
            # Try Gemini
            if self.google_api_key and self.genai:
                result = self._call_gemini(prompt)
            else:
                raise Exception("No Gemini API key")
                
        except Exception as e:
            logger.warning(f"⚠️ Gemini failed, using hardcoded fallback: {e}")
            # Hardcoded fallback (Ollama disabled for deployment stability)
            result = {
                "bundles": [
                    {
                        "bundle_name": "Curated Gift Selection",
                        "description": f"Hand-picked items matching: {user_intent}",
                        "items": [
                            {
                                "title": item.get('title', 'Unknown'),
                                "reason": "Highly relevant to your needs",
                                "price": item.get('price', 0),
                                "category": item.get('category', 'General')
                            }
                            for item in items[:3]
                        ],
                        "total_price": sum(item.get('price', 0) for item in items[:3])
                    }
                ]
            }
        
        # Ensure proper structure
        if 'bundles' not in result:
            result = {'bundles': []}
        
        # Calculate total prices if missing
        for bundle in result['bundles']:
            if 'total_price' not in bundle and 'items' in bundle:
                bundle['total_price'] = sum(
                    item.get('price', 0) for item in bundle.get('items', [])
                )
        
        final_result = {
            'query': user_intent,
            'bundles': result['bundles']
        }
        
        logger.info(f"✅ Generated {len(final_result['bundles'])} bundles")
        return final_result