# gift_ai_service/core/orchestrator.py
"""
Unified Orchestrator - Fixed for merged service
"""

import logging
import uuid
import traceback  # ✅ ADDED
import asyncio
import httpx
from typing import Dict, Any, List
from core.vector_store import VectorStore
from core.llm_client import LLMClient
from core.config import settings
from services.gift_bundle_service import GiftBundleService
from services.gift_intent_service import extract_intent
from services.gift_retrieval_service import retrieve_similar
from services.gift_validation_service import validate_items

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GiftOrchestrator:
    """Main orchestrator supporting both image and text-based gift recommendations"""
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.llm_client = LLMClient()
        self.bundle_service = GiftBundleService()
        logger.info("✅ GiftOrchestrator initialized")

    async def refresh_vector_store(self) -> Dict[str, Any]:
        """Refresh Qdrant with latest MongoDB items"""
        try:
            logger.info("🔄 Starting vector store refresh...")
            
            if self.vector_store.mongo_collection is None:
                return {"success": False, "error": "MongoDB not connected", "step": "mongodb_check"}
            
            logger.info("📦 Fetching items from MongoDB...")
            try:
                items = await self.vector_store.get_mongo_items(limit=100)
                logger.info(f"✅ Fetched {len(items)} items from MongoDB")
            except Exception as e:
                logger.error(f"❌ MongoDB fetch failed: {str(e)}")
                traceback.print_exc()
                return {"success": False, "error": f"MongoDB fetch failed: {str(e)}", "step": "mongodb_fetch"}
            
            if not items:
                return {"success": False, "error": "No items found in MongoDB", "step": "mongodb_empty"}
            
            if self.vector_store.qdrant_client is None:
                return {"success": False, "error": "Qdrant not connected", "step": "qdrant_check"}
            
            logger.info("🔧 Setting up Qdrant collection...")
            try:
                collection_ok = await self.vector_store.setup_collection()
                if not collection_ok:
                    return {"success": False, "error": "Qdrant collection setup failed", "step": "qdrant_setup"}
                logger.info("✅ Qdrant collection ready")
            except Exception as e:
                logger.error(f"❌ Qdrant setup failed: {str(e)}")
                traceback.print_exc()
                return {"success": False, "error": f"Qdrant setup failed: {str(e)}", "step": "qdrant_setup"}
            
            logger.info(f"📤 Uploading {len(items)} items to Qdrant...")
            try:
                upload_ok = await self.vector_store.upload_items(items)
                if not upload_ok:
                    return {"success": False, "error": "Qdrant upload failed", "step": "qdrant_upload"}
                logger.info(f"✅ Successfully uploaded {len(items)} items")
            except Exception as e:
                logger.error(f"❌ Qdrant upload failed: {str(e)}")
                traceback.print_exc()
                return {"success": False, "error": f"Qdrant upload failed: {str(e)}", "step": "qdrant_upload"}
            
            logger.info(f"✅ Vector store refresh completed successfully")
            return {"success": True, "message": f"Refreshed vector store with {len(items)} items", "items_count": len(items)}
            
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            traceback.print_exc()
            return {"success": False, "error": f"Unexpected error: {str(e)}", "step": "unknown"}

    async def generate_bundle(self, image_bytes: bytes, filename: str = "upload.jpg") -> Dict[str, Any]:
        """Full GenAI pipeline for image-based gift recommendations"""
        bundle_id = str(uuid.uuid4())
        logger.info(f"🎁 Starting image bundle generation: {bundle_id}")

        fallback = {
            "bundle_id": bundle_id,
            "vision": {"status": "failed", "error": "Vision AI unavailable"},
            "intent": {"status": "failed", "error": "Intent extraction failed"},
            "bundles": [],
            "metadata": {"total_retrieved": 0, "valid_count": 0, "invalid_count": 0},
            "error": None
        }

        try:
            # Step 1: Vision AI Analysis
            logger.info("📸 Step 1: Vision AI analysis...")
            vision = await self._step_vision_analysis(image_bytes)
            fallback["vision"] = vision

            # Step 2: Intent Extraction
            logger.info("🧠 Step 2: Extracting intent...")
            intent = await extract_intent(image_bytes, vision)
            fallback["intent"] = intent

            # Step 3: Semantic Retrieval
            logger.info("🔍 Step 3: Retrieving similar gifts...")
            try:
                similar_gifts = await retrieve_similar(intent, top_k=5, vector_store=self.vector_store)
                fallback["metadata"]["total_retrieved"] = len(similar_gifts)
                
                if not similar_gifts:
                    fallback["error"] = "No items found in vector store"
                    logger.error("❌ No items retrieved")
                    return fallback
                    
            except Exception as retrieval_error:
                fallback["error"] = f"Retrieval failed: {str(retrieval_error)}"
                logger.error(f"❌ Retrieval error: {retrieval_error}")
                traceback.print_exc()
                return fallback

            # Step 4: Validation
            logger.info("✅ Step 4: Validating items...")
            budget = intent.get("budget_inr")
            max_budget = None  # Disabled for image-based search
            logger.info(f"💰 Budget filter: Disabled (AI estimated: ₹{budget})")
            
            valid_gifts, invalid_gifts = validate_items(similar_gifts, max_budget=max_budget, min_quality_score=0.0)
            fallback["metadata"]["valid_count"] = len(valid_gifts)
            fallback["metadata"]["invalid_count"] = len(invalid_gifts)

            if not valid_gifts:
                fallback["error"] = "No valid gifts found after validation"
                logger.warning("⚠️ No valid gifts")
                return fallback

            # Step 5: Bundle Generation
            logger.info("🎨 Step 5: Generating bundles...")
            try:
                result = await self.bundle_service.generate_bundles(str(intent), valid_gifts)
                fallback["bundles"] = result.get("bundles", [])
                
                if not fallback["bundles"]:
                    fallback["error"] = "Bundle generation succeeded but produced no bundles"
                else:
                    logger.info(f"✅ Bundle generated with {len(fallback['bundles'])} bundles")
                    fallback.pop("error", None)
            except Exception as bundle_error:
                fallback["error"] = f"Bundle generation failed: {str(bundle_error)}"
                logger.error(f"❌ Bundle error: {bundle_error}")
                
            return fallback

        except Exception as e:
            logger.error(f"❌ Bundle generation failed: {e}")
            traceback.print_exc()
            fallback["error"] = f"Processing failed: {str(e)}"
            return fallback

    async def _step_vision_analysis(self, image_bytes: bytes) -> Dict[str, Any]:
        """Call Vision AI service (now on same port 8001)"""
        # ✅ FIXED: Use settings.VISION_AI_SERVICE_URL which now points to localhost:8001
        vision_base_url = settings.VISION_AI_SERVICE_URL
        endpoints = [
            "/analyze_craft", "/analyze_quality", "/estimate_price",
            "/detect_fraud", "/suggest_packaging", "/detect_material",
            "/analyze_sentiment", "/detect_occasion"
        ]

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:  # Increased timeout
                files = {"image": ("upload.jpg", image_bytes, "image/jpeg")}
                tasks = [client.post(f"{vision_base_url}{ep}", files={"image": ("upload.jpg", image_bytes, "image/jpeg")}) for ep in endpoints]
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
            traceback.print_exc()
            return {"status": "failed", "error": str(e)}

    async def process_gift_query(self, user_intent: str, limit: int = 10) -> Dict[str, Any]:
        """Text-based gift search pipeline"""
        logger.info(f"🔍 Processing text query: '{user_intent}'")

        try:
            logger.info("Step 1: Retrieving similar items...")
            items = await self.vector_store.search_related_items(text=user_intent, collection_name=None, limit=limit)

            if not items:
                return {'query': user_intent, 'bundles': [], 'error': 'No matching items found'}

            logger.info("Step 2: Validating items...")
            valid_items, invalid_items = validate_items(items, max_budget=None, min_quality_score=0.0)

            if not valid_items:
                return {'query': user_intent, 'bundles': [], 'error': 'No valid items available'}

            logger.info("Step 3: Generating bundles...")
            result = await self.bundle_service.generate_bundles(user_intent, valid_items)
            result['metadata'] = {
                'total_items_retrieved': len(items),
                'valid_items_count': len(valid_items),
                'invalid_items_count': len(invalid_items)
            }

            logger.info(f"✅ Generated {len(result['bundles'])} bundles")
            return result

        except Exception as e:
            logger.error(f"❌ Query processing failed: {e}")
            traceback.print_exc()
            return {'query': user_intent, 'bundles': [], 'error': f'Processing failed: {str(e)}'}