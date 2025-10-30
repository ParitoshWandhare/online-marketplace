# gift_ai_service/core/orchestrator.py
"""
Unified Orchestrator combining Member A's Vision AI pipeline + Member B's text search
- Image-to-bundle: Vision AI → Intent → Retrieval → Bundle
- Text-to-bundle: Intent → Retrieval → Bundle
FIXED: Proper None checks for Motor collections + Lenient validation
"""

import logging
import uuid
import traceback
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

    # ========================================================================
    # ADMIN: Refresh Vector Store
    # ========================================================================
    async def refresh_vector_store(self) -> Dict[str, Any]:
        """
        Refresh Qdrant with latest MongoDB items
        Returns dict with detailed status for better error reporting
        """
        try:
            logger.info("🔄 Starting vector store refresh...")
            
            # Step 1: Check MongoDB connection - FIXED: Compare with None
            if self.vector_store.mongo_collection is None:
                error_msg = "MongoDB not connected"
                logger.error(f"❌ {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "step": "mongodb_check"
                }
            
            # Step 2: Get items from MongoDB
            logger.info("📦 Fetching items from MongoDB...")
            try:
                items = await self.vector_store.get_mongo_items(limit=100)
                logger.info(f"✅ Fetched {len(items)} items from MongoDB")
            except Exception as e:
                error_msg = f"MongoDB fetch failed: {str(e)}"
                logger.error(f"❌ {error_msg}")
                traceback.print_exc()
                return {
                    "success": False,
                    "error": error_msg,
                    "step": "mongodb_fetch"
                }
            
            if not items:
                error_msg = "No items found in MongoDB"
                logger.warning(f"⚠️ {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "step": "mongodb_empty"
                }
            
            # Step 3: Check Qdrant connection - FIXED: Compare with None
            if self.vector_store.qdrant_client is None:
                error_msg = "Qdrant not connected"
                logger.error(f"❌ {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "step": "qdrant_check"
                }
            
            # Step 4: Setup Qdrant collection
            logger.info("🔧 Setting up Qdrant collection...")
            try:
                collection_ok = await self.vector_store.setup_collection()
                if not collection_ok:
                    error_msg = "Qdrant collection setup returned False"
                    logger.error(f"❌ {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "step": "qdrant_setup"
                    }
                logger.info("✅ Qdrant collection ready")
            except Exception as e:
                error_msg = f"Qdrant setup failed: {str(e)}"
                logger.error(f"❌ {error_msg}")
                traceback.print_exc()
                return {
                    "success": False,
                    "error": error_msg,
                    "step": "qdrant_setup"
                }
            
            # Step 5: Upload items to Qdrant
            logger.info(f"📤 Uploading {len(items)} items to Qdrant...")
            try:
                upload_ok = await self.vector_store.upload_items(items)
                if not upload_ok:
                    error_msg = "Qdrant upload returned False"
                    logger.error(f"❌ {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "step": "qdrant_upload",
                        "items_attempted": len(items)
                    }
                logger.info(f"✅ Successfully uploaded {len(items)} items")
            except Exception as e:
                error_msg = f"Qdrant upload failed: {str(e)}"
                logger.error(f"❌ {error_msg}")
                traceback.print_exc()
                return {
                    "success": False,
                    "error": error_msg,
                    "step": "qdrant_upload",
                    "items_attempted": len(items)
                }
            
            # Success!
            logger.info(f"✅ Vector store refresh completed successfully")
            return {
                "success": True,
                "message": f"Refreshed vector store with {len(items)} items",
                "items_count": len(items)
            }
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"❌ {error_msg}")
            traceback.print_exc()
            return {
                "success": False,
                "error": error_msg,
                "step": "unknown"
            }

    # ========================================================================
    # MEMBER A PIPELINE: Image → Full Bundle (Vision AI)
    # ========================================================================
# Only replace the generate_bundle method in your orchestrator.py
# Keep everything else the same, especially process_gift_query

    async def generate_bundle(self, image_bytes: bytes, filename: str = "upload.jpg") -> Dict[str, Any]:
        """
        Full GenAI pipeline for image-based gift recommendations
        Flow: Image → Vision AI → Intent → Retrieval → Validation → Bundle
        FIXED: Pass vector_store instance to retrieve_similar
        """
        bundle_id = str(uuid.uuid4())
        logger.info(f"🎁 Starting image bundle generation: {bundle_id}")

        # Default fallback response (prevents Pydantic errors)
        fallback = {
            "bundle_id": bundle_id,
            "vision": {"status": "failed", "error": "Vision AI unavailable"},
            "intent": {"status": "failed", "error": "Intent extraction failed"},
            "bundles": [],
            "metadata": {"total_retrieved": 0, "valid_count": 0, "invalid_count": 0},
            "error": None
        }

        try:
            # Step 1: Vision AI Analysis (8 parallel endpoints)
            logger.info("📸 Step 1: Vision AI analysis...")
            vision = await self._step_vision_analysis(image_bytes)
            fallback["vision"] = vision

            # Step 2: Intent Extraction
            logger.info("🧠 Step 2: Extracting intent...")
            intent = await extract_intent(image_bytes, vision)
            fallback["intent"] = intent

            # Step 3: Semantic Retrieval (FIXED: Pass vector_store instance)
            logger.info("🔍 Step 3: Retrieving similar gifts...")
            try:
                similar_gifts = await retrieve_similar(
                    intent, 
                    top_k=5,
                    vector_store=self.vector_store  # Pass the connected instance
                )
                fallback["metadata"]["total_retrieved"] = len(similar_gifts)
                
                if not similar_gifts:
                    fallback["error"] = "No items found in vector store. Please run refresh_vector_store first."
                    logger.error("❌ No items retrieved from vector store")
                    logger.error("   → Check if Qdrant is running and has data")
                    logger.error("   → Run: POST /refresh_vector_store to sync MongoDB → Qdrant")
                    return fallback
                    
            except Exception as retrieval_error:
                fallback["error"] = f"Retrieval failed: {str(retrieval_error)}"
                logger.error(f"❌ Retrieval error: {retrieval_error}")
                logger.error("   → Is Qdrant running?")
                logger.error("   → Run: POST /refresh_vector_store to initialize")
                import traceback
                traceback.print_exc()
                return fallback

            # Step 4: Validation (More lenient budget checking)
            logger.info("✅ Step 4: Validating items...")
            
            # Only apply budget if it's explicitly high AND user-specified
            # For image-based search, ignore the AI-extracted budget (too unreliable)
            budget = intent.get("budget_inr")
            
            # Don't apply budget filter for image-based searches
            # The AI often sets unrealistic low budgets like ₹1000
            max_budget = None
            logger.info(f"💰 Budget filter: Disabled for image-based search (AI estimated: ₹{budget})")
            
            valid_gifts, invalid_gifts = validate_items(
                similar_gifts, 
                max_budget=max_budget,
                min_quality_score=0.0  # Accept all similarity scores
            )
            fallback["metadata"]["valid_count"] = len(valid_gifts)
            fallback["metadata"]["invalid_count"] = len(invalid_gifts)

            if not valid_gifts:
                fallback["error"] = "No valid gifts found after validation. Items may be missing required fields."
                logger.warning("⚠️ No valid gifts after validation")
                if invalid_gifts:
                    logger.info("Invalid items details:")
                    for inv in invalid_gifts[:3]:  # Show first 3
                        logger.info(f"  - {inv.get('reason', 'Unknown reason')}")
                return fallback

            # Step 5: Bundle Generation
            logger.info("🎨 Step 5: Generating bundles...")
            try:
                result = await self.bundle_service.generate_bundles(str(intent), valid_gifts)
                fallback["bundles"] = result.get("bundles", [])
                
                if not fallback["bundles"]:
                    fallback["error"] = "Bundle generation succeeded but produced no bundles"
                    logger.warning("⚠️ No bundles generated from valid gifts")
                else:
                    logger.info(f"✅ Bundle {bundle_id} generated successfully with {len(fallback['bundles'])} bundles")
                    fallback.pop("error", None)
                    
            except Exception as bundle_error:
                fallback["error"] = f"Bundle generation failed: {str(bundle_error)}"
                logger.error(f"❌ Bundle generation error: {bundle_error}")
                
            return fallback

        except Exception as e:
            logger.error(f"❌ Bundle generation failed: {e}")
            traceback.print_exc()
            fallback["error"] = f"Processing failed: {str(e)}"
            return fallback

    async def _step_vision_analysis(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Call Vision AI service (Member A's 8 parallel endpoints)
        """
        vision_base_url = settings.VISION_AI_SERVICE_URL
        endpoints = [
            "/analyze_craft", "/analyze_quality", "/estimate_price",
            "/detect_fraud", "/suggest_packaging", "/detect_material",
            "/analyze_sentiment", "/detect_occasion"
        ]

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                files = {"image": ("upload.jpg", image_bytes, "image/jpeg")}
                tasks = [
                    client.post(f"{vision_base_url}{ep}", files=files)
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

    # ========================================================================
    # MEMBER B PIPELINE: Text → Bundle (Simple Search)
    # ========================================================================
    async def process_gift_query(self, user_intent: str, limit: int = 10) -> Dict[str, Any]:
        """
        Text-based gift search pipeline
        Flow: Text → Retrieval → Validation → Bundle
        """
        logger.info(f"🔍 Processing text query: '{user_intent}'")

        try:
            # Step 1: Retrieve from vector store
            logger.info("Step 1: Retrieving similar items...")
            items = await self.vector_store.search_related_items(
                text=user_intent,
                collection_name=None,  # Use default
                limit=limit
            )

            if not items:
                logger.warning("⚠️ No items found")
                return {
                    'query': user_intent,
                    'bundles': [],
                    'error': 'No matching items found. Please refresh vector store first.'
                }

            # Step 2: Validate (FIXED: No budget limit for text search)
            logger.info("Step 2: Validating items...")
            valid_items, invalid_items = validate_items(
                items,
                max_budget=None,  # No budget limit for text search
                min_quality_score=0.0  # Accept all similarity scores
            )

            if not valid_items:
                logger.warning("⚠️ No valid items")
                return {
                    'query': user_intent,
                    'bundles': [],
                    'error': 'No valid items available',
                    'invalid_items': invalid_items
                }

            # Step 3: Generate bundles
            logger.info("Step 3: Generating bundles...")
            result = await self.bundle_service.generate_bundles(user_intent, valid_items)

            # Add metadata
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
            return {
                'query': user_intent,
                'bundles': [],
                'error': f'Processing failed: {str(e)}'
            }