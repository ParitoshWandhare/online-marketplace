# gift_ai_service/main.py
"""
Gift AI Service - Unified API Gateway
=====================================
Complete integration of all microservices in one file
"""

# ========================================================================
# CRITICAL: Load .env FIRST before any other imports
# ========================================================================
import os
from pathlib import Path
from dotenv import load_dotenv

# Get absolute path to .env file
env_path = Path(__file__).parent / ".env"
print(f"🔍 Looking for .env at: {env_path}")
print(f"   Exists: {env_path.exists()}")

if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print("✅ .env loaded")
    
    # Verify API key immediately
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if api_key:
        print(f"✅ API Key found: {api_key[:15]}...")
    else:
        print("❌ API Key NOT found after loading .env!")
else:
    print(f"❌ .env file not found at: {env_path}")

# ========================================================================
# NOW import everything else
# ========================================================================
import logging
import traceback
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from contextlib import asynccontextmanager

from core.orchestrator import GiftOrchestrator
from core.config import settings

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("gift_ai.main")

# ========================================================================
# PYDANTIC MODELS
# ========================================================================
class GiftBundle(BaseModel):
    """Gift bundle model"""
    bundle_name: str
    description: str
    items: List[Dict[str, Any]]
    total_price: Optional[float] = None

class ImageBundleResponse(BaseModel):
    """Image upload response"""
    bundle_id: str
    vision: Dict[str, Any]
    intent: Dict[str, Any]
    bundles: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    error: Optional[str] = None

class TextSearchResponse(BaseModel):
    """Text search response"""
    query: str
    bundles: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ArtworkIndexRequest(BaseModel):
    """Single artwork index request"""
    mongo_id: str
    title: str
    description: str
    category: Optional[str] = "General"
    price: float
    tags: Optional[List[str]] = []

# Global orchestrator
orchestrator: Optional[GiftOrchestrator] = None

# ========================================================================
# LIFECYCLE MANAGEMENT (Modern FastAPI way)
# ========================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global orchestrator
    
    # Startup
    logger.info("🚀 Gift AI Service starting...")
    logger.info(f"📦 MongoDB: {settings.DATABASE_NAME}.{settings.COLLECTION_NAME}")
    logger.info(f"🔍 Qdrant: {settings.QDRANT_URL}")
    logger.info(f"🤖 LLM: {settings.LLM_MODEL}")
    logger.info(f"🔑 API Key: {'✅ Configured' if settings.GEMINI_API_KEY else '❌ MISSING'}")
    
    try:
        orchestrator = GiftOrchestrator()
        await orchestrator.vector_store.connect()
        logger.info("✅ Service initialized")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        traceback.print_exc()
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    if orchestrator:
        try:
            await orchestrator.vector_store.close()
            logger.info("✅ Connections closed")
        except Exception as e:
            logger.warning(f"⚠️ Shutdown warning: {e}")

# ========================================================================
# FASTAPI APP
# ========================================================================
app = FastAPI(
    title="Gift AI Service - Unified",
    description="Complete GenAI gift recommendation system",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan  # Use modern lifespan instead of on_event
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================================================
# ENDPOINTS
# ========================================================================

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "gift-ai-unified",
        "version": "2.0.0",
        "components": {
            "orchestrator": orchestrator is not None,
            "mongodb": settings.MONGODB_URL is not None and settings.MONGODB_URL != "",
            "qdrant": settings.QDRANT_URL is not None and settings.QDRANT_URL != "",
            "gemini_api_key": settings.GEMINI_API_KEY is not None and settings.GEMINI_API_KEY != ""
        }
    }

@app.post("/generate_gift_bundle", response_model=ImageBundleResponse)
async def generate_gift_bundle(
    image: UploadFile = File(..., description="Image (JPEG/PNG, max 5MB)")
) -> ImageBundleResponse:
    """
    🎨 Image → Gift Bundle Pipeline
    
    Flow: Image → Vision AI → Intent → Retrieval → Validation → Bundle
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    if not image.filename or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid image file")
    
    try:
        image_bytes = await image.read()
        if len(image_bytes) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image too large (max 5MB)")
        
        logger.info(f"📸 Processing: {image.filename}")
        result = await orchestrator.generate_bundle(image_bytes, image.filename)
        logger.info(f"✅ Bundle generated: {result['bundle_id']}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search_similar_gifts", response_model=TextSearchResponse)
async def search_similar_gifts(
    query: str = Query(..., description="Search query", min_length=1),
    limit: int = Query(10, ge=1, le=50)
) -> TextSearchResponse:
    """
    🔍 Text Search → Gift Bundle
    
    Flow: Query → Embedding → Vector Search → Validation → Bundle
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        logger.info(f"🔍 Searching: '{query}'")
        result = await orchestrator.process_gift_query(query, limit)
        logger.info(f"✅ Found {len(result.get('bundles', []))} bundles")
        return result
    except Exception as e:
        logger.error(f"❌ Search failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/refresh_vector_store")
async def refresh_vector_store():
    """
    🔄 Refresh Vector Store (Admin)
    
    Syncs MongoDB items to Qdrant with embeddings
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        logger.info("🔄 Starting refresh...")
        result = await orchestrator.refresh_vector_store()
        
        if result.get("success"):
            logger.info("✅ Refresh completed")
            return {
                "success": True,
                "message": result.get("message", "Refreshed successfully"),
                "items_count": result.get("items_count", 0),
                "collection": settings.COLLECTION_NAME
            }
        else:
            error_msg = result.get("error", "Unknown error")
            step = result.get("step", "unknown")
            logger.error(f"❌ Refresh failed at step '{step}': {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"Refresh failed at {step}: {error_msg}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Refresh error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index_artwork")
async def index_artwork(request: ArtworkIndexRequest):
    """
    📦 Index Single Artwork
    
    Adds item to vector store immediately
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        item_dict = request.model_dump()
        text = f"{item_dict['title']} {item_dict['description']}"
        
        # Generate embedding
        embedding = orchestrator.vector_store.generate_embedding(text)
        if not embedding:
            raise HTTPException(status_code=500, detail="Embedding generation failed")
        
        # Pad to 768-dim
        if len(embedding) > 768:
            embedding = embedding[:768]
        elif len(embedding) < 768:
            embedding.extend([0.0] * (768 - len(embedding)))
        
        # Upload to Qdrant
        from qdrant_client.http.models import PointStruct
        
        point = PointStruct(
            id=abs(hash(item_dict['mongo_id'])) % (10 ** 8),
            vector=embedding,
            payload={
                'title': item_dict['title'],
                'description': item_dict['description'],
                'category': item_dict.get('category', 'General'),
                'price': item_dict['price'],
                'mongo_id': item_dict['mongo_id']
            }
        )
        
        orchestrator.vector_store.qdrant_client.upsert(
            collection_name=settings.COLLECTION_NAME,
            points=[point]
        )
        
        logger.info(f"✅ Indexed: {item_dict['title']}")
        return {
            "success": True,
            "message": f"Indexed '{item_dict['title']}'",
            "item_id": item_dict['mongo_id']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Indexing failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vector_store_info")
async def vector_store_info():
    """
    📊 Get Vector Store Info
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        if orchestrator.vector_store.qdrant_client:
            collections = orchestrator.vector_store.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            collection_info = None
            if settings.COLLECTION_NAME in collection_names:
                collection_info = orchestrator.vector_store.qdrant_client.get_collection(
                    settings.COLLECTION_NAME
                )
            
            return {
                "connected": True,
                "qdrant_url": settings.QDRANT_URL,
                "mongodb_db": settings.DATABASE_NAME,
                "qdrant_collection": settings.COLLECTION_NAME,
                "available_collections": collection_names,
                "collection_info": {
                    "vectors_count": collection_info.vectors_count if collection_info else 0,
                    "points_count": collection_info.points_count if collection_info else 0
                } if collection_info else None
            }
        else:
            return {"connected": False, "error": "Qdrant not initialized"}
    except Exception as e:
        logger.error(f"❌ Info fetch failed: {e}")
        return {"connected": False, "error": str(e)}

# ========================================================================
# RUN
# ========================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True,
        log_level="info"
    )