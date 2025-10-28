# gift_ai_service/services/gift_intent_service.py
"""
Member B: Extract gift intent from image + vision analysis
"""

from core.llm_client import LLMClient
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

async def extract_intent(
    image_bytes: bytes,
    vision_analysis: Dict[str, Any],
    user_prompt: str = None
) -> Dict[str, Any]:
    """
    Extract gift intent using Gemini + vision clues.
    
    Returns:
        {
            "occasion": "birthday",
            "recipient": "sister",
            "budget_inr": 1500,
            "sentiment": "warm",
            "interests": ["handmade", "pottery"]
        }
    """
    llm = LLMClient()
    
    prompt = f"""
    Analyze this image and vision data to extract gift intent.
    
    Vision: {vision_analysis}
    User: {user_prompt or "No prompt"}
    
    Return JSON:
    {{
        "occasion": "...",
        "recipient": "...",
        "budget_inr": 1500,
        "sentiment": "warm|playful|elegant",
        "interests": ["...", "..."]
    }}
    """
    
    try:
        result = await llm.generate_story(prompt, image_bytes)
        # Parse JSON from result['story']
        import json
        data = json.loads(result['story'])
        logger.info(f"Intent extracted: {data}")
        return data
    except Exception as e:
        logger.error(f"Intent extraction failed: {e}")
        return {
            "occasion": "birthday",
            "recipient": "friend",
            "budget_inr": 1000,
            "sentiment": "warm",
            "interests": ["handmade"]
        }