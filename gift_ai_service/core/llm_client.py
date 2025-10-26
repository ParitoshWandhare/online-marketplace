# gift_ai_service/core/llm_client.py
"""
LLM Client using Google Gemini
Fixed: Use gemini-1.5-flash-001 (2025 valid model)
"""

import google.generativeai as genai
from core.config import settings
import logging

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            # FIXED: Use valid model name
            self.model = genai.GenerativeModel('gemini-1.5-flash-001')
            logger.info("Gemini LLM client initialized with gemini-1.5-flash-001")
        else:
            logger.warning("GEMINI_API_KEY not set")
            self.model = None

    async def generate_story(self, prompt: str, image_bytes: bytes = None):
        """Generate story using Gemini"""
        if not self.model:
            return {"error": "LLM not configured"}

        try:
            contents = [prompt]
            if image_bytes:
                contents.append({
                    "mime_type": "image/jpeg",
                    "data": image_bytes
                })
            response = await self.model.generate_content_async(contents)
            return {"story": response.text}
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return {"error": str(e)}