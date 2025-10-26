# gift_ai_service/core/orchestrator.py
"""
Orchestrator with FULL error fallbacks
All required fields in response → No Pydantic crash!
"""

import logging
from typing import Dict, Any, List
import uuid
import traceback
import asyncio
import httpx
from core.vector_store import VectorStore
from core.llm_client import LLMClient
from services.gift_bundle_service import GiftBundleService
from services.gift_intent_service import extract_intent
from services.gift_retrieval_service import retrieve_similar
from services.gift_validation_service import validate_items

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GiftOrchestrator:
    def __init__(self):
        self.vector_store = VectorStore()
        self.llm_client = LLMClient()
        self.bundle_service = GiftBundleService(llm_client=self.llm_client)
        logger.info("GiftOrchestrator initialized successfully")

    async def refresh_vector_store(self) -> bool:
        try:
            logger.info("Starting vector store refresh")
            if not await self.vector_store.setup_collection():
                logger.error("Failed to setup Qdrant collection")
                return False
            items = await self.vector_store.get_mongo_items(limit=100)
            if not items:
                logger.warning("No items in MongoDB")
                return False
            success = await self.vector_store.upload_items(items)
            if success:
                logger.info(f"Uploaded {len(items)} items to Qdrant")
            return success
        except Exception as e:
            logger.error(f"Refresh failed: {e}")
            traceback.print_exc()
            return False

    # ------------------------------------------------------------------
    # MAIN: Image → Full Bundle (SAFE!)
    # ------------------------------------------------------------------
    async def generate_bundle(self, image_bytes: bytes, filename: str = "upload.jpg") -> Dict[str, Any]:
        bundle_id = str(uuid.uuid4())
        logger.info(f"Starting bundle {bundle_id} for {filename}")

        # DEFAULT FALLBACK (prevents Pydantic crash)
        fallback = {
            "bundle_id": bundle_id,
            "vision": {"status": "failed", "error": "Vision AI unavailable"},
            "intent": {"status": "failed", "error": "Intent extraction failed"},
            "bundles": [],
            "metadata": {"total_retrieved": 0, "valid_count": 0, "invalid_count": 0},
            "error": None
        }

        try:
            # Step 1: Vision AI
            vision = await self._step_vision_analysis(image_bytes)
            fallback["vision"] = vision

            # Step 2: Intent
            intent = await extract_intent(image_bytes, vision)
            fallback["intent"] = intent

            # Step 3: Retrieval
            similar_gifts = await retrieve_similar(intent, top_k=5)
            fallback["metadata"]["total_retrieved"] = len(similar_gifts)

            # Step 4: Validation
            # In generate_bundle()
            valid_gifts, invalid_gifts = validate_items( similar_gifts, max_budget=intent.get("budget_inr", 1000))
            fallback["metadata"]["valid_count"] = len(valid_gifts)
            fallback["metadata"]["invalid_count"] = len(invalid_gifts)

            if not valid_gifts:
                fallback["error"] = "No valid gifts found after validation"
                logger.warning("No valid gifts")
                return fallback

            # Step 5: Bundle
            result = self.bundle_service.generate_bundles(str(intent), valid_gifts)
            fallback["bundles"] = result.get("bundles", [])

            logger.info(f"Bundle {bundle_id} generated successfully")
            fallback.pop("error", None)
            return fallback

        except Exception as e:
            logger.error(f"Bundle generation failed: {e}")
            traceback.print_exc()
            fallback["error"] = f"Processing failed: {str(e)}"
            return fallback

    # ------------------------------------------------------------------
    # Vision AI Call (Real HTTP)
    # ------------------------------------------------------------------
    async def _step_vision_analysis(self, image_bytes: bytes) -> Dict[str, Any]:
        endpoints = [
            "/analyze_craft", "/analyze_quality", "/estimate_price",
            "/detect_fraud", "/suggest_packaging", "/detect_material",
            "/analyze_sentiment", "/detect_occasion"
        ]

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                files = {"image": ("upload.jpg", image_bytes, "image/jpeg")}
                tasks = [
                    client.post(f"http://127.0.0.1:8004{ep}", files=files)
                    for ep in endpoints
                ]
                responses = await asyncio.gather(*tasks, return_exceptions=True)

            results = []
            for r in responses:
                if isinstance(r, Exception):
                    results.append({"error": str(r)})
                else:
                    results.append(r.json())

            return {
                "craft_type": results[0].get("craft_type", "unknown"),
                "quality": results[1].get("quality", "unknown"),
                "price_range": results[2].get("price_range_inr", "unknown"),
                "fraud_score": results[3].get("fraud_score", 1.0),
                "packaging": results[4].get("packaging", "standard box"),
                "material": results[5].get("material", "unknown"),
                "sentiment": results[6].get("sentiment", "neutral"),
                "occasion_hint": results[7].get("occasion", "any")
            }
        except Exception as e:
            logger.error(f"Vision AI failed: {e}")
            return {"status": "failed", "error": str(e)}

    # ------------------------------------------------------------------
    # Legacy Text Search
    # ------------------------------------------------------------------
    async def process_gift_query(self, user_intent: str, limit: int = 10) -> Dict[str, Any]:
        items = await self.vector_store.search_related_items(text=user_intent, limit=limit)
        valid_items, invalid_items = validate_items(items)
        result = self.bundle_service.generate_bundles(user_intent, valid_items)
        result['metadata'] = {
            'total_items_retrieved': len(items),
            'valid_items_count': len(valid_items),
            'invalid_items_count': len(invalid_items)
        }
        return result