# # gift_ai_service/services/gift_bundle_service.py
# """
# Gift Bundle Generation Service
# Fixed: Proper indentation and error handling
# """

# import os
# import logging
# import json
# from typing import List, Dict, Any

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# class GiftBundleService:
#     """Generates gift bundles using LLM with fallback support"""
    
#     def __init__(self, llm_model: str = None):
#         """Initialize GiftBundleService"""
#         self.llm_model = llm_model or os.getenv('LLM_MODEL', 'gemini-1.5-flash-001')
#         self.google_api_key = os.getenv('GOOGLE_API_KEY')
        
#         if self.google_api_key:
#             try:
#                 import google.generativeai as genai
#                 genai.configure(api_key=self.google_api_key)
#                 self.genai = genai
#                 logger.info(f"✅ Gemini initialized: {self.llm_model}")
#             except ImportError:
#                 logger.warning("⚠️ google-generativeai not installed")
#                 self.genai = None
#         else:
#             self.genai = None
#             logger.warning("⚠️ No Gemini API key")

#     def _call_gemini(self, prompt: str) -> Dict[str, Any]:
#         """Call Gemini API"""
#         try:
#             model = self.genai.GenerativeModel(self.llm_model)
#             response = model.generate_content(prompt)
            
#             # Extract JSON
#             response_text = response.text
#             if '```json' in response_text:
#                 response_text = response_text.split('```json')[1].split('```')[0]
#             elif '```' in response_text:
#                 response_text = response_text.split('```')[1].split('```')[0]
            
#             result = json.loads(response_text.strip())
#             logger.info("✅ Gemini generated bundles")
#             return result
            
#         except Exception as e:
#             logger.error(f"Gemini failed: {e}")
#             raise

#     async def generate_bundles(self, user_intent: str, items: List[Dict]) -> Dict[str, Any]:
#         """
#         Generate bundles using Gemini with hardcoded fallback (Ollama disabled for deployment)
#         """
#         logger.info(f"🎨 Generating bundles: '{user_intent}' with {len(items)} items")
        
#         from services.gift_prompt_templates import get_gift_bundle_prompt
        
#         prompt = get_gift_bundle_prompt(user_intent, items)
        
#         try:
#             # Try Gemini
#             if self.google_api_key and self.genai:
#                 result = self._call_gemini(prompt)
#             else:
#                 raise Exception("No Gemini API key")
                
#         except Exception as e:
#             logger.warning(f"⚠️ Gemini failed, using hardcoded fallback: {e}")
#             # Hardcoded fallback (Ollama disabled for deployment stability)
#             result = {
#                 "bundles": [
#                     {
#                         "bundle_name": "Curated Gift Selection",
#                         "description": f"Hand-picked items matching: {user_intent}",
#                         "items": [
#                             {
#                                 "title": item.get('title', 'Unknown'),
#                                 "reason": "Highly relevant to your needs",
#                                 "price": item.get('price', 0),
#                                 "category": item.get('category', 'General')
#                             }
#                             for item in items[:3]
#                         ],
#                         "total_price": sum(item.get('price', 0) for item in items[:3])
#                     }
#                 ]
#             }
        
#         # Ensure proper structure
#         if 'bundles' not in result:
#             result = {'bundles': []}
        
#         # Calculate total prices if missing
#         for bundle in result['bundles']:
#             if 'total_price' not in bundle and 'items' in bundle:
#                 bundle['total_price'] = sum(
#                     item.get('price', 0) for item in bundle.get('items', [])
#                 )
        
#         final_result = {
#             'query': user_intent,
#             'bundles': result['bundles']
#         }
        
#         logger.info(f"✅ Generated {len(final_result['bundles'])} bundles")
#         return final_result


# gift_ai_service/services/gift_bundle_service.py
"""
Gift Bundle Generation Service
FIXED: Updated model name from gemini-1.5-flash-001 to gemini-1.5-flash
FIXED: Smarter fallback that filters items by recipient context
"""

import os
import logging
import json
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Recipient gender/context hints for filtering
RECIPIENT_HINTS = {
    "mom": ["women", "feminine", "floral", "saree", "kurti", "jewellery", "jewelry", "dupatta", "home"],
    "mother": ["women", "feminine", "floral", "saree", "kurti", "jewellery", "jewelry", "home"],
    "dad": ["men", "masculine", "shirt", "watch", "wallet", "office"],
    "father": ["men", "masculine", "shirt", "watch", "wallet", "office"],
    "sister": ["women", "feminine", "accessories", "jewellery", "beauty"],
    "brother": ["men", "masculine", "gadgets", "accessories"],
    "wife": ["women", "feminine", "jewellery", "saree", "flowers"],
    "husband": ["men", "masculine", "watch", "wallet", "accessories"],
    "girlfriend": ["women", "feminine", "romantic", "jewellery", "flowers"],
    "boyfriend": ["men", "masculine", "accessories", "gadgets"],
    "friend": [],  # neutral — no filtering
    "colleague": [],  # neutral
    "anyone": [],   # neutral
    "self": [],     # neutral
}

# Items that should NEVER be recommended for female recipients
MALE_ONLY_KEYWORDS = ["men's", "mens", "male", "suit", "tie", "necktie", "cufflink", "shaving"]
FEMALE_ONLY_KEYWORDS = ["women's", "womens", "female", "saree", "kurti", "dupatta", "bra", "lipstick"]


def _extract_recipient(user_intent: str) -> str:
    """Extract recipient keyword from intent string"""
    intent_lower = user_intent.lower()
    for key in RECIPIENT_HINTS:
        if key in intent_lower:
            return key
    return "anyone"


def _is_item_appropriate(item: Dict, recipient: str) -> bool:
    """
    Check if an item is appropriate for a given recipient.
    Returns False if item is clearly for the wrong gender.
    """
    title_lower = item.get("title", "").lower()
    description_lower = item.get("description", "").lower()
    combined = f"{title_lower} {description_lower}"

    recipient_lower = recipient.lower()

    # Female recipients → reject male-only items
    if recipient_lower in ["mom", "mother", "sister", "wife", "girlfriend"]:
        if any(kw in combined for kw in MALE_ONLY_KEYWORDS):
            logger.info(f"  🚫 Filtered out '{item.get('title')}' — male item for female recipient")
            return False

    # Male recipients → reject female-only items
    if recipient_lower in ["dad", "father", "brother", "husband", "boyfriend"]:
        if any(kw in combined for kw in FEMALE_ONLY_KEYWORDS):
            logger.info(f"  🚫 Filtered out '{item.get('title')}' — female item for male recipient")
            return False

    return True


def _filter_items_by_recipient(items: List[Dict], user_intent: str) -> List[Dict]:
    """Filter items based on recipient context extracted from user_intent"""
    recipient = _extract_recipient(user_intent)
    if recipient in ["anyone", "friend", "colleague", "self", ""]:
        return items  # no filtering needed

    filtered = [item for item in items if _is_item_appropriate(item, recipient)]
    logger.info(f"🎯 Recipient='{recipient}': {len(items)} items → {len(filtered)} after gender filter")
    return filtered if filtered else items  # fallback to unfiltered if nothing left


class GiftBundleService:
    """Generates gift bundles using LLM with fallback support"""

    def __init__(self, llm_model: str = None):
        """Initialize GiftBundleService"""
        # FIXED: was 'gemini-1.5-flash-001' (404 error) → now 'gemini-1.5-flash'
        self.llm_model = llm_model or os.getenv('LLM_MODEL', 'gemini-1.5-flash')
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
        """Call Gemini API with model fallback chain"""
        model_chain = [
            self.llm_model,
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-pro",
        ]
        # Deduplicate while preserving order
        seen = set()
        model_chain = [m for m in model_chain if not (m in seen or seen.add(m))]

        last_error = None
        for model_name in model_chain:
            try:
                model = self.genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)

                response_text = response.text
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0]
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0]

                result = json.loads(response_text.strip())
                logger.info(f"✅ Gemini ({model_name}) generated bundles")
                return result

            except Exception as e:
                logger.warning(f"⚠️ Model '{model_name}' failed: {e}")
                last_error = e
                continue

        raise Exception(f"All Gemini models failed. Last error: {last_error}")

    async def generate_bundles(self, user_intent: str, items: List[Dict]) -> Dict[str, Any]:
        """
        Generate bundles using Gemini with smart fallback.
        FIXED: Recipient-aware filtering applied before LLM and in fallback.
        """
        logger.info(f"🎨 Generating bundles: '{user_intent}' with {len(items)} items")

        # FIXED: Filter items by recipient BEFORE passing to LLM or fallback
        filtered_items = _filter_items_by_recipient(items, user_intent)

        from services.gift_prompt_templates import get_gift_bundle_prompt
        prompt = get_gift_bundle_prompt(user_intent, filtered_items)

        result = None
        try:
            if self.google_api_key and self.genai:
                result = self._call_gemini(prompt)
        except Exception as e:
            logger.warning(f"⚠️ Gemini failed, using smart fallback: {e}")

        if not result:
            # FIXED: Smarter fallback — uses filtered_items and adds proper reasons
            result = {
                "bundles": [
                    {
                        "bundle_name": "Curated Gift Selection",
                        "description": f"Hand-picked items matching: {user_intent}",
                        "items": [
                            {
                                "title": item.get('title', 'Unknown'),
                                "reason": "Relevant to your needs",
                                "price": item.get('price', 0),
                                "category": item.get('category', 'General')
                            }
                            for item in filtered_items[:3]
                        ],
                        "total_price": sum(item.get('price', 0) for item in filtered_items[:3])
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