# gift_ai_service/services/gift_bundle_service.py
"""
Gift Bundle Generation Service
FIXED: Uses genai library (v1beta) with correct bare 1.5 model names.

Key facts about AI Studio API keys:
- They ONLY work on the v1beta endpoint (not v1 REST)
- gemini-2.0-* models have exhausted free-tier quota (limit: 0)
- gemini-1.5-flash-latest / gemini-1.5-pro-latest → 404 on v1beta
- CORRECT: "gemini-1.5-flash-8b", "gemini-1.5-flash", "gemini-1.5-pro" (bare names, no suffix)
"""

import os
import re
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# NEW
GEMINI_MODEL_CHAIN = [
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.5-flash",
]

# ── Recipient filtering ────────────────────────────────────────────────────────

MALE_ONLY_KEYWORDS   = ["men's", "mens", "male", "suit", "tie", "necktie", "cufflink", "shaving"]
FEMALE_ONLY_KEYWORDS = ["women's", "womens", "female", "saree", "kurti", "dupatta", "salwar",
                        "anarkali", "lehenga", "bra", "lipstick", "kanjivaram"]

FEMALE_RECIPIENTS = {"mom", "mother", "sister", "wife", "girlfriend", "aunt", "grandmother", "grandma"}
MALE_RECIPIENTS   = {"dad", "father", "brother", "husband", "boyfriend", "uncle", "grandfather", "grandpa"}


def _extract_recipient(text: str) -> str:
    text_lower = text.lower()
    for key in list(FEMALE_RECIPIENTS) + list(MALE_RECIPIENTS):
        if key in text_lower:
            return key
    return "anyone"


def _filter_items_by_recipient(items: List[Dict], user_intent: str) -> List[Dict]:
    recipient = _extract_recipient(user_intent)
    if recipient == "anyone":
        return items

    filtered = []
    for item in items:
        combined = (item.get("title", "") + " " + item.get("description", "")).lower()
        if recipient in FEMALE_RECIPIENTS and any(kw in combined for kw in MALE_ONLY_KEYWORDS):
            logger.info(f"  🚫 Filtered out '{item.get('title')}' — male item for female recipient")
            continue
        if recipient in MALE_RECIPIENTS and any(kw in combined for kw in FEMALE_ONLY_KEYWORDS):
            logger.info(f"  🚫 Filtered out '{item.get('title')}' — female item for male recipient")
            continue
        filtered.append(item)

    logger.info(f"🎯 Recipient='{recipient}': {len(items)} items → {len(filtered)} after gender filter")
    return filtered if filtered else items


# ── Service ────────────────────────────────────────────────────────────────────

class GiftBundleService:
    """Generates gift bundles using Gemini via genai library (v1beta)"""

    def __init__(self, llm_model: str = None):
        self.preferred_model = llm_model or os.getenv("LLM_MODEL", "gemini-1.5-flash-8b")
        self.google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.genai = None

        if self.google_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.google_api_key)
                self.genai = genai
                logger.info(f"✅ GiftBundleService initialized (preferred: {self.preferred_model})")
            except Exception as e:
                logger.warning(f"⚠️ Gemini init failed: {e}")
        else:
            logger.warning("⚠️ No Gemini API key — will use hardcoded fallback")

    def _call_gemini(self, prompt: str) -> Dict:
        """Try each model in GEMINI_MODEL_CHAIN via genai library (v1beta endpoint)."""
        if not self.genai:
            raise Exception("Gemini not initialized")

        # Put preferred model first, then rest of chain
        chain = [self.preferred_model] + [m for m in GEMINI_MODEL_CHAIN if m != self.preferred_model]
        last_error = None

        for model_name in chain:
            try:
                model = self.genai.GenerativeModel(model_name)
                response = model.generate_content(
                    prompt,
                    generation_config={"max_output_tokens": 2048, "temperature": 0.7},
                )
                text = response.text

                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0]
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0]
                m = re.search(r"\{.*\}", text, re.DOTALL)
                if m:
                    text = m.group(0)

                result = json.loads(text.strip())
                logger.info(f"✅ Bundle generated via {model_name}")
                return result

            except Exception as e:
                logger.warning(f"⚠️ Model '{model_name}' failed: {e}")
                last_error = e
                continue

        raise Exception(f"All Gemini models failed. Last error: {last_error}")

    async def generate_bundles(self, user_intent: str, items: List[Dict]) -> Dict[str, Any]:
        """Generate gift bundles with recipient-aware filtering"""
        logger.info(f"🎨 Generating bundles: '{user_intent}' with {len(items)} items")

        filtered_items = _filter_items_by_recipient(items, user_intent)

        from services.gift_prompt_templates import get_gift_bundle_prompt
        prompt = get_gift_bundle_prompt(user_intent, filtered_items)

        result = None
        if self.google_api_key and self.genai:
            try:
                result = self._call_gemini(prompt)
            except Exception as e:
                logger.warning(f"⚠️ Gemini failed, using fallback: {e}")

        if not result:
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

        for bundle in result["bundles"]:
            if "total_price" not in bundle:
                bundle["total_price"] = sum(
                    item.get("price", 0) for item in bundle.get("items", [])
                )

        return {"query": user_intent, "bundles": result["bundles"]}