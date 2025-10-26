# gift_ai_service/main.py
"""
Gift AI Service - Public API Gateway
Exposes 2 endpoints:
1. /generate_gift_bundle  → Upload image → Get AI gift bundle (Vision + Intent + Retrieval)
2. /search_similar_gifts → Text query → Get similar gifts
"""

import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from core.orchestrator import GiftOrchestrator

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("gift_ai.main")

# ------------------------------------------------------------------
# RESPONSE MODELS (For Swagger Docs)
# ------------------------------------------------------------------
class GiftBundle(BaseModel):
    id: Optional[str] = None
    title: str
    price: float
    story: str
    packaging: str
    similarity: float

    class Config:
        schema_extra = {
            "example": {
                "id": "g123",
                "title": "Handmade Terracotta Diya",
                "price": 850.0,
                "story": "A warm glow for Diwali nights...",
                "packaging": "Eco-box with ribbon",
                "similarity": 0.94
            }
        }

class BundleResponse(BaseModel):
    bundle_id: str
    vision: Dict[str, Any]
    intent: Dict[str, Any]
    bundles: List[GiftBundle]
    metadata: Dict[str, Any]
    error: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "bundle_id": "b789",
                "vision": {"craft_type": "pottery", "quality": "high"},
                "intent": {"occasion": "birthday", "recipient": "sister"},
                "bundles": [...],
                "metadata": {"valid_count": 3}
            }
        }

class SearchResponse(BaseModel):
    bundles: List[GiftBundle]
    metadata: Dict[str, Any]
    error: Optional[str] = None

# ------------------------------------------------------------------
# FastAPI App
# ------------------------------------------------------------------
app = FastAPI(
    title="Gift AI Service",
    description="GenAI-powered gift recommendation with Vision AI, Intent, and Semantic Search",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ------------------------------------------------------------------
# Initialize Orchestrator
# ------------------------------------------------------------------
orchestrator = GiftOrchestrator()

# ------------------------------------------------------------------
# Startup / Shutdown (Async)
# ------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    logger.info("Gift AI Service starting up...")
    try:
        await orchestrator.vector_store.connect()
        logger.info("Connected to MongoDB & Qdrant")
    except Exception as e:
        logger.error(f"Startup failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Gift AI Service shutting down...")
    try:
        await orchestrator.vector_store.close()
        logger.info("MongoDB connection closed")
    except Exception as e:
        logger.warning(f"Shutdown error: {e}")

# ------------------------------------------------------------------
# Health Check
# ------------------------------------------------------------------
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "gift-ai"}

# ------------------------------------------------------------------
# ENDPOINT 1: Generate Gift Bundle (Image Upload)
# ------------------------------------------------------------------
@app.post("/generate_gift_bundle", response_model=BundleResponse)
async def generate_gift_bundle(
    image: UploadFile = File(
        ...,
        description="Inspiration image (JPEG/PNG, max 5MB)"
    )
) -> BundleResponse:
    """
    FULL GENAI PIPELINE:
    1. Vision AI (8 parallel endpoints)
    2. Intent Extraction (Gemini)
    3. Semantic Retrieval (Qdrant)
    4. Bundle Generation
    5. Validation
    """
    if not image.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        image_bytes = await image.read()
        if len(image_bytes) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image too large (max 5MB)")

        logger.info(f"Processing image: {image.filename}")

        # FULL PIPELINE: Vision → Intent → Retrieval → Bundle
        result = await orchestrator.generate_bundle(image_bytes, image.filename)

        logger.info("Gift bundle generated successfully")
        return result

    except Exception as e:
        logger.error(f"Bundle generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

# ------------------------------------------------------------------
# ENDPOINT 2: Search Similar Gifts (Text Query)
# ------------------------------------------------------------------
@app.post("/search_similar_gifts", response_model=SearchResponse)
async def search_similar_gifts(
    query: str = Query(..., description="Gift search query"),
    limit: int = Query(5, ge=1, le=20, description="Number of results")
) -> SearchResponse:
    """
    Text-based semantic search using vector store.
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    logger.info(f"Searching gifts for: {query}")
    result = await orchestrator.process_gift_query(user_intent=query, limit=limit)
    return result