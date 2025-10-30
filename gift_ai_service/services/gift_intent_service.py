# gift_ai_service/services/gift_intent_service.py
"""
Member B: Extract gift intent from image + vision analysis
FIXED: Use generate_text instead of generate_story
"""

from core.llm_client import LLMClient
from typing import Dict, Any
import logging
import json

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
            "recipient": "friend",
            "budget_inr": 1500,
            "sentiment": "warm",
            "interests": ["handmade", "pottery"]
        }
    """
    llm = LLMClient()
    
    # Build prompt from vision analysis
    vision_summary = []
    if vision_analysis.get('craft_type') != 'unknown':
        vision_summary.append(f"craft type: {vision_analysis.get('craft_type')}")
    if vision_analysis.get('occasion_hint') != 'any':
        vision_summary.append(f"occasion hint: {vision_analysis.get('occasion_hint')}")
    if vision_analysis.get('sentiment') != 'neutral':
        vision_summary.append(f"sentiment: {vision_analysis.get('sentiment')}")
    
    vision_text = ", ".join(vision_summary) if vision_summary else "general gift"
    
    prompt = f"""Based on this image analysis, extract gift intent in JSON format.

Vision Analysis: {vision_text}
User Request: {user_prompt or "Find suitable gift"}

Return ONLY a valid JSON object (no markdown, no explanation):
{{
    "occasion": "birthday|wedding|anniversary|diwali|housewarming|graduation|general",
    "recipient": "friend|family|colleague|partner|self|anyone",
    "budget_inr": 1000,
    "sentiment": "warm|playful|elegant|traditional|modern",
    "interests": ["handmade", "art", "decor"]
}}

Rules:
- Choose the most likely occasion based on the vision hints
- Set budget to a reasonable amount (500-2000 INR range)
- Interests should be 2-3 relevant keywords
- Return ONLY the JSON, no other text"""
    
    try:
        # Use generate_text method (not generate_story)
        result_text = await llm.generate_text(prompt)
        
        # Parse JSON from result
        # Remove markdown code blocks if present
        clean_text = result_text.strip()
        if '```json' in clean_text:
            clean_text = clean_text.split('```json')[1].split('```')[0]
        elif '```' in clean_text:
            clean_text = clean_text.split('```')[1].split('```')[0]
        
        data = json.loads(clean_text.strip())
        
        # Validate and set defaults
        data.setdefault('occasion', 'birthday')
        data.setdefault('recipient', 'friend')
        data.setdefault('budget_inr', 1000)
        data.setdefault('sentiment', 'warm')
        data.setdefault('interests', ['handmade'])
        
        logger.info(f"✅ Intent extracted: {data}")
        return data
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON parse error: {e}")
        logger.error(f"   Raw response: {result_text[:200]}")
        # Return fallback intent
        return {
            "occasion": "birthday",
            "recipient": "friend", 
            "budget_inr": 1000,
            "sentiment": "warm",
            "interests": ["handmade"]
        }
    except Exception as e:
        logger.error(f"❌ Intent extraction failed: {e}")
        import traceback
        traceback.print_exc()
        # Return fallback intent
        return {
            "occasion": "birthday",
            "recipient": "friend",
            "budget_inr": 1000,
            "sentiment": "warm",
            "interests": ["handmade"]
        }