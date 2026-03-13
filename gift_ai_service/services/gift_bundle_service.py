# gift_ai_service/services/gift_bundle_service.py
"""
Gift Bundle Generation Service
FIXED: Uses GeminiDirectClient (v1 REST) instead of genai.GenerativeModel.
       Recipient-aware filtering applied before LLM call and in fallback.
"""

import os
import logging
import json
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# ── Recipient filtering ────────────────────────────────────────────────────────

MALE_ONLY_KEYWORDS  = ["men's", "mens", "male", "suit", "tie", "necktie", "cufflink", "shaving"]
FEMALE_ONLY_KEYWORDS = ["women's", "womens", "female", "saree", "kurti", "dupatta", "salwar",
                        "anarkali", "lehenga", "bra", "lipstick", "kanjivaram"]

FEMALE_RECIPIENTS = {"mom", "mother", "sister", "wife", "girlfriend", "aunt", "grandmother", "grandma"}
MALE_RECIPIENTS   = {"dad", "father", "brother", "husband", "boyfriend", "uncle", "grandfather", "grandpa"}


def _extract_recipient(text: str) -> str:
    text_lower = text.lower()
    for key in list(FEMALE_RECIPIENTS) + list(MALE_RECIPIENTS) + ["friend", "colleague", "self", "anyone"]:
        if key in text_lower:
            return key
    return "anyone"


def _is_item_appropriate(item: Dict, recipient: str) -> bool:
    combined = (item.get("title", "") + " " + item.get("description", "")).lower()
    if recipient in FEMALE_RECIPIENTS:
        if any(kw in combined for kw in MALE_ONLY_KEYWORDS):
            logger.info(f"  🚫 Filtered out '{item.get('title')}' — male item for female recipient")
            return False
    if recipient in MALE_RECIPIENTS:
        if any(kw in combined for kw in FEMALE_ONLY_KEYWORDS):
            logger.info(f"  🚫 Filtered out '{item.get('title')}' — female item for male recipient")
            return False
    return True


def _filter_items_by_recipient(items: List[Dict], user_intent: str) -> List[Dict]:
    recipient = _extract_recipient(user_intent)
    if recipient in {"anyone", "friend", "colleague", "self", ""}:
        return items
    filtered = [i for i in items if _is_item_appropriate(i, recipient)]
    logger.info(f"🎯 Recipient='{recipient}': {len(items)} items → {len(filtered)} after gender filter")
    return filtered if filtered else items


# ── Service ────────────────────────────────────────────────────────────────────

class GiftBundleService:
    """Generates gift bundles using Gemini v1 REST API"""

    def __init__(self, llm_model: str = None):
        self.preferred_model = llm_model or os.getenv("LLM_MODEL", "gemini-1.5-flash-8b")
        self.google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self._client = None

        if self.google_api_key:
            try:
                from core.gemini_client import GeminiDirectClient
                self._client = GeminiDirectClient(api_key=self.google_api_key)
                logger.info(f"✅ GiftBundleService using Gemini direct v1 REST (preferred: {self.preferred_model})")
            except Exception as e:
                logger.warning(f"⚠️ GeminiDirectClient init failed: {e}")
        else:
            logger.warning("⚠️ No Gemini API key — will use hardcoded fallback")

    async def generate_bundles(self, user_intent: str, items: List[Dict]) -> Dict[str, Any]:
        """Generate gift bundles with recipient-aware filtering"""
        logger.info(f"🎨 Generating bundles: '{user_intent}' with {len(items)} items")

        # Filter by recipient BEFORE passing to LLM
        filtered_items = _filter_items_by_recipient(items, user_intent)

        from services.gift_prompt_templates import get_gift_bundle_prompt
        prompt = get_gift_bundle_prompt(user_intent, filtered_items)

        result = None
        if self._client:
            try:
                from core.gemini_client import TEXT_MODEL_CHAIN
                # Put the preferred model first in the chain
                chain = [self.preferred_model] + [m for m in TEXT_MODEL_CHAIN if m != self.preferred_model]
                raw = await self._client.generate(prompt, max_tokens=2048, model_chain=chain)
                result = self._parse_json(raw)
            except Exception as e:
                logger.warning(f"⚠️ Gemini bundle generation failed, using fallback: {e}")

        if not result:
            # Hardcoded fallback uses filtered_items (never shows wrong-gender items)
            result = {
                "bundles": [{
                    "bundle_name": "Curated Selection",
                    "description": f"Items matching: {user_intent}",
                    "items": [
                        {"title": item["title"], "reason": "Relevant to your needs"}
                        for item in filtered_items[:3]
                    ],
                }]
            }

        if "bundles" not in result:
            result = {"bundles": []}

        # Attach totals
        for bundle in result["bundles"]:
            if "total_price" not in bundle:
                bundle["total_price"] = sum(
                    item.get("price", 0) for item in bundle.get("items", [])
                )

        return {"query": user_intent, "bundles": result["bundles"]}

    @staticmethod
    def _parse_json(text: str) -> Dict:
        """Extract JSON object from LLM response text"""
        clean = text.strip()
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0]
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0]
        import re
        match = re.search(r"\{.*\}", clean, re.DOTALL)
        if match:
            clean = match.group(0)
        return json.loads(clean.strip())