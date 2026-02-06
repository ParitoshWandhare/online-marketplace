# # gift_ai_service/main.py
# """
# Unified Gift AI Service - Complete Integration
# ==============================================
# Combines Gift AI recommendation engine and Vision AI analysis in one service
# Port: 8001 (serves both functionalities)
# """

# # ========================================================================
# # CRITICAL: Load .env FIRST
# # ========================================================================
# import os
# import io
# import base64
# from pathlib import Path
# from dotenv import load_dotenv

# env_path = Path(__file__).parent / ".env"
# if env_path.exists():
#     load_dotenv(dotenv_path=env_path, override=True)

# # ========================================================================
# # IMPORTS
# # ========================================================================
# import logging
# import traceback
# from typing import Dict, Any, List, Optional

# from fastapi import FastAPI, UploadFile, File, HTTPException, Query
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from contextlib import asynccontextmanager
# from PIL import Image
# import google.generativeai as genai

# from core.orchestrator import GiftOrchestrator
# from core.config import settings

# # ========================================================================
# # LOGGING
# # ========================================================================
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
# )
# logger = logging.getLogger("gift_ai.main")

# # ========================================================================
# # VISION AI CLIENT
# # ========================================================================
# class VisionAIClient:
#     """Gemini Vision AI client (Ollama disabled for deployment stability)"""
    
#     def __init__(self):
#         self.gemini_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
#         self.gemini_model = None
        
#         if self.gemini_api_key:
#             try:
#                 genai.configure(api_key=self.gemini_api_key)
#                 model_names = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-pro-latest']
                
#                 for name in model_names:
#                     try:
#                         self.gemini_model = genai.GenerativeModel(name)
#                         logger.info(f"Vision AI initialized with: {name}")
#                         break
#                     except:
#                         continue
#             except Exception as e:
#                 logger.error(f"Vision AI initialization failed: {e}")
        
#         # Ollama disabled for deployment stability
#         self.ollama_available = False
#         logger.info("Ollama disabled for deployment - using Gemini only")
    
#     async def analyze_image_gemini(self, image_bytes: bytes, prompt: str) -> str:
#         if not self.gemini_model:
#             raise Exception("Gemini not configured")
        
#         image = Image.open(io.BytesIO(image_bytes))
#         response = self.gemini_model.generate_content([prompt, image])
#         return response.text
    
#     async def analyze_image(self, image_bytes: bytes, prompt: str) -> str:
#         if self.gemini_model:
#             try:
#                 return await self.analyze_image_gemini(image_bytes, prompt)
#             except Exception as e:
#                 logger.error(f"Gemini failed: {e}")
#                 raise Exception(f"Vision AI failed: {e}")
        
#         raise Exception("No vision AI provider available")

# # Helper function for JSON extraction
# def extract_json_from_response(text: str) -> Dict[str, Any]:
#     import json
#     import re
    
#     json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
#     if json_match:
#         text = json_match.group(1)
#     else:
#         json_match = re.search(r'\{.*\}', text, re.DOTALL)
#         if json_match:
#             text = json_match.group(0)
    
#     try:
#         return json.loads(text)
#     except json.JSONDecodeError:
#         logger.warning("Failed to parse JSON")
#         return {"raw_response": text}

# # ========================================================================
# # PYDANTIC MODELS
# # ========================================================================
# class GiftBundle(BaseModel):
#     bundle_name: str
#     description: str
#     items: List[Dict[str, Any]]
#     total_price: Optional[float] = None

# class ImageBundleResponse(BaseModel):
#     bundle_id: str
#     vision: Dict[str, Any]
#     intent: Dict[str, Any]
#     bundles: List[Dict[str, Any]]
#     metadata: Dict[str, Any]
#     error: Optional[str] = None

# class TextSearchResponse(BaseModel):
#     query: str
#     bundles: List[Dict[str, Any]]
#     metadata: Optional[Dict[str, Any]] = None
#     error: Optional[str] = None

# class ArtworkIndexRequest(BaseModel):
#     mongo_id: str
#     title: str
#     description: str
#     category: Optional[str] = "General"
#     price: float
#     tags: Optional[List[str]] = []

# # ========================================================================
# # GLOBAL INSTANCES
# # ========================================================================
# orchestrator: Optional[GiftOrchestrator] = None
# vision_client: Optional[VisionAIClient] = None

# # ========================================================================
# # LIFECYCLE MANAGEMENT
# # ========================================================================
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     global orchestrator, vision_client
    
#     # Startup
#     logger.info("Starting Unified Gift AI Service...")
#     logger.info(f"MongoDB: {settings.DATABASE_NAME}.{settings.COLLECTION_NAME}")
#     logger.info(f"Qdrant: {settings.QDRANT_URL}")
#     logger.info(f"LLM: {settings.LLM_MODEL}")
    
#     startup_errors = []
    
#     try:
#         # Initialize orchestrator
#         logger.info("Initializing orchestrator...")
#         orchestrator = GiftOrchestrator()
        
#         # Connect to databases
#         logger.info("Connecting to databases...")
#         await orchestrator.vector_store.connect()
#         logger.info("✅ Databases connected")
        
#         # Initialize vision client
#         logger.info("Initializing vision client...")
#         vision_client = VisionAIClient()
#         logger.info("✅ Vision client initialized")
        
#         logger.info("🚀 Service initialized successfully")
        
#     except Exception as e:
#         error_msg = f"Startup failed: {e}"
#         logger.error(f"❌ {error_msg}")
#         startup_errors.append(error_msg)
#         traceback.print_exc()
        
#         # Continue with partial initialization for debugging
#         if not orchestrator:
#             try:
#                 orchestrator = GiftOrchestrator()
#                 logger.info("⚠️ Orchestrator initialized without database connections")
#             except Exception as e2:
#                 logger.error(f"❌ Failed to initialize orchestrator: {e2}")
        
#         if not vision_client:
#             try:
#                 vision_client = VisionAIClient()
#                 logger.info("⚠️ Vision client initialized with potential issues")
#             except Exception as e2:
#                 logger.error(f"❌ Failed to initialize vision client: {e2}")
    
#     yield
    
#     # Shutdown
#     logger.info("Shutting down...")
#     if orchestrator:
#         try:
#             await orchestrator.vector_store.close()
#             logger.info("✅ Connections closed")
#         except Exception as e:
#             logger.warning(f"Shutdown warning: {e}")

# # ========================================================================
# # FASTAPI APP
# # ========================================================================
# app = FastAPI(
#     title="Unified Gift AI Service",
#     description="Complete GenAI gift recommendation and vision analysis system",
#     version="3.0.0",
#     docs_url="/docs",
#     redoc_url="/redoc",
#     lifespan=lifespan
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ========================================================================
# # HEALTH CHECK
# # ========================================================================
# @app.get("/")
# async def root():
#     """Root endpoint for basic connectivity test"""
#     return {
#         "service": "unified-gift-ai",
#         "version": "3.0.0",
#         "status": "running",
#         "message": "Gift AI Service is operational",
#         "endpoints": [
#             "/health",
#             "/docs",
#             "/generate_gift_bundle",
#             "/search_similar_gifts",
#             "/refresh_vector_store"
#         ]
#     }

# @app.get("/health")
# async def health_check():
#     """Service health check with detailed diagnostics"""
#     health_status = {
#         "status": "healthy",
#         "service": "unified-gift-ai",
#         "version": "3.0.0",
#         "components": {
#             "orchestrator": orchestrator is not None,
#             "mongodb": False,
#             "qdrant": False,
#             "gemini_api_key": settings.GEMINI_API_KEY is not None and settings.GEMINI_API_KEY != "",
#             "vision_ai": vision_client is not None,
#             "ollama": "disabled_for_deployment"
#         },
#         "errors": []
#     }
    
#     # Test MongoDB connection
#     if orchestrator and orchestrator.vector_store.mongo_collection:
#         try:
#             # Simple ping test
#             await orchestrator.vector_store.mongo_collection.find_one({}, {"_id": 1})
#             health_status["components"]["mongodb"] = True
#         except Exception as e:
#             health_status["components"]["mongodb"] = False
#             health_status["errors"].append(f"MongoDB: {str(e)}")
    
#     # Test Qdrant connection
#     if orchestrator and orchestrator.vector_store.qdrant_client:
#         try:
#             orchestrator.vector_store.qdrant_client.get_collections()
#             health_status["components"]["qdrant"] = True
#         except Exception as e:
#             health_status["components"]["qdrant"] = False
#             health_status["errors"].append(f"Qdrant: {str(e)}")
    
#     # Test Gemini
#     if vision_client and vision_client.gemini_model:
#         try:
#             # Simple test generation
#             test_response = vision_client.gemini_model.generate_content("Say 'OK'")
#             if test_response.text:
#                 health_status["components"]["vision_ai"] = True
#         except Exception as e:
#             health_status["components"]["vision_ai"] = False
#             health_status["errors"].append(f"Gemini: {str(e)}")
    
#     # Determine overall status
#     critical_components = ["orchestrator", "mongodb", "qdrant", "gemini_api_key"]
#     if not all(health_status["components"][comp] for comp in critical_components):
#         health_status["status"] = "degraded"
    
#     if health_status["errors"]:
#         health_status["status"] = "unhealthy" if len(health_status["errors"]) > 2 else "degraded"
    
#     return health_status

# # ========================================================================
# # GIFT AI ENDPOINTS (Recommendation Engine)
# # ========================================================================

# @app.post("/generate_gift_bundle", response_model=ImageBundleResponse)
# async def generate_gift_bundle(image: UploadFile = File(...)):
#     """Image to Gift Bundle Pipeline"""
#     if not orchestrator:
#         raise HTTPException(status_code=503, detail="Service not initialized")
    
#     if not image.filename or not image.content_type.startswith("image/"):
#         raise HTTPException(status_code=400, detail="Invalid image file")
    
#     try:
#         image_bytes = await image.read()
#         if len(image_bytes) > 5 * 1024 * 1024:
#             raise HTTPException(status_code=400, detail="Image too large (max 5MB)")
        
#         logger.info(f"Processing: {image.filename}")
#         result = await orchestrator.generate_bundle(image_bytes, image.filename)
#         logger.info(f"Bundle generated: {result['bundle_id']}")
#         return result
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Failed: {e}")
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/search_similar_gifts", response_model=TextSearchResponse)
# async def search_similar_gifts(
#     query: str = Query(..., min_length=1),
#     limit: int = Query(10, ge=1, le=50)
# ):
#     """Text Search to Gift Bundle"""
#     if not orchestrator:
#         raise HTTPException(status_code=503, detail="Service not initialized")
    
#     if not query.strip():
#         raise HTTPException(status_code=400, detail="Query cannot be empty")
    
#     try:
#         logger.info(f"Searching: '{query}'")
#         result = await orchestrator.process_gift_query(query, limit)
#         logger.info(f"Found {len(result.get('bundles', []))} bundles")
#         return result
#     except Exception as e:
#         logger.error(f"Search failed: {e}")
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=str(e))

# # Alias endpoint for backward compatibility
# @app.get("/search", response_model=TextSearchResponse)
# async def search_alias(
#     query: str = Query(..., min_length=1),
#     limit: int = Query(10, ge=1, le=50)
# ):
#     """Alias for search_similar_gifts (GET method)"""
#     return await search_similar_gifts(query, limit)

# @app.post("/refresh_vector_store")
# async def refresh_vector_store():
#     """Refresh Vector Store (Admin)"""
#     if not orchestrator:
#         raise HTTPException(status_code=503, detail="Service not initialized")
    
#     try:
#         logger.info("Starting refresh...")
#         result = await orchestrator.refresh_vector_store()
        
#         if result.get("success"):
#             logger.info("Refresh completed")
#             return {
#                 "success": True,
#                 "message": result.get("message", "Refreshed successfully"),
#                 "items_count": result.get("items_count", 0),
#                 "collection": settings.COLLECTION_NAME
#             }
#         else:
#             error_msg = result.get("error", "Unknown error")
#             step = result.get("step", "unknown")
#             logger.error(f"Refresh failed at step '{step}': {error_msg}")
#             raise HTTPException(status_code=500, detail=f"Refresh failed at {step}: {error_msg}")
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Refresh error: {e}")
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/index_artwork")
# async def index_artwork(request: ArtworkIndexRequest):
#     """Index Single Artwork"""
#     if not orchestrator:
#         raise HTTPException(status_code=503, detail="Service not initialized")
    
#     try:
#         item_dict = request.model_dump()
#         text = f"{item_dict['title']} {item_dict['description']}"
        
#         embedding = orchestrator.vector_store.generate_embedding(text)
#         if not embedding:
#             raise HTTPException(status_code=500, detail="Embedding generation failed")
        
#         if len(embedding) > 768:
#             embedding = embedding[:768]
#         elif len(embedding) < 768:
#             embedding.extend([0.0] * (768 - len(embedding)))
        
#         from qdrant_client.http.models import PointStruct
        
#         point = PointStruct(
#             id=abs(hash(item_dict['mongo_id'])) % (10 ** 8),
#             vector=embedding,
#             payload={
#                 'title': item_dict['title'],
#                 'description': item_dict['description'],
#                 'category': item_dict.get('category', 'General'),
#                 'price': item_dict['price'],
#                 'mongo_id': item_dict['mongo_id']
#             }
#         )
        
#         orchestrator.vector_store.qdrant_client.upsert(
#             collection_name=settings.COLLECTION_NAME,
#             points=[point]
#         )
        
#         logger.info(f"Indexed: {item_dict['title']}")
#         return {
#             "success": True,
#             "message": f"Indexed '{item_dict['title']}'",
#             "item_id": item_dict['mongo_id']
#         }
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Indexing failed: {e}")
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/vector_store_info")
# async def vector_store_info():
#     """Get Vector Store Information"""
#     if not orchestrator:
#         raise HTTPException(status_code=503, detail="Service not initialized")
    
#     try:
#         if orchestrator.vector_store.qdrant_client:
#             collections = orchestrator.vector_store.qdrant_client.get_collections()
#             collection_names = [col.name for col in collections.collections]
            
#             collection_info = None
#             if settings.COLLECTION_NAME in collection_names:
#                 collection_info = orchestrator.vector_store.qdrant_client.get_collection(
#                     settings.COLLECTION_NAME
#                 )
            
#             return {
#                 "connected": True,
#                 "qdrant_url": settings.QDRANT_URL,
#                 "mongodb_db": settings.DATABASE_NAME,
#                 "qdrant_collection": settings.COLLECTION_NAME,
#                 "available_collections": collection_names,
#                 "collection_info": {
#                     "vectors_count": collection_info.vectors_count if collection_info else 0,
#                     "points_count": collection_info.points_count if collection_info else 0
#                 } if collection_info else None
#             }
#         else:
#             return {"connected": False, "error": "Qdrant not initialized"}
#     except Exception as e:
#         logger.error(f"Info fetch failed: {e}")
#         return {"connected": False, "error": str(e)}

# # ========================================================================
# # VISION AI ENDPOINTS (Image Analysis)
# # ========================================================================

# @app.post("/analyze_craft")
# async def analyze_craft(image: UploadFile = File(...)) -> Dict:
#     """Vision AI: Detect craft type"""
#     logger.info(f"Analyzing craft in {image.filename}")
    
#     try:
#         image_bytes = await image.read()
        
#         prompt = """Analyze this image and identify the type of craft or artwork shown.

# Return a JSON object with:
# {
#     "craft_type": "pottery|textile|metalwork|painting|sculpture|woodwork|jewelry|other",
#     "confidence": 0.0-1.0,
#     "details": "brief description"
# }"""
        
#         response = await vision_client.analyze_image(image_bytes, prompt)
#         result = extract_json_from_response(response)
#         result.setdefault('craft_type', 'unknown')
#         result.setdefault('confidence', 0.5)
        
#         logger.info(f"Craft detected: {result.get('craft_type')}")
#         return result
#     except Exception as e:
#         logger.error(f"Craft analysis failed: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/analyze_quality")
# async def analyze_quality(image: UploadFile = File(...)) -> Dict:
#     """Vision AI: Assess craftsmanship quality"""
#     logger.info(f"Analyzing quality of {image.filename}")
    
#     try:
#         image_bytes = await image.read()
        
#         prompt = """Analyze the quality and craftsmanship of this item.

# Return JSON:
# {
#     "quality": "high|medium|low",
#     "details": "describe finish, craftsmanship, flaws",
#     "craftsmanship_score": 0.0-1.0
# }"""
        
#         response = await vision_client.analyze_image(image_bytes, prompt)
#         result = extract_json_from_response(response)
#         result.setdefault('quality', 'medium')
#         result.setdefault('details', 'No details available')
        
#         return result
#     except Exception as e:
#         logger.error(f"Quality analysis failed: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/estimate_price")
# async def estimate_price(image: UploadFile = File(...)) -> Dict:
#     """Vision AI: Estimate price range"""
#     logger.info(f"Estimating price for {image.filename}")
    
#     try:
#         image_bytes = await image.read()
        
#         prompt = """Estimate the price range for this handmade item in Indian Rupees.

# Return JSON:
# {
#     "price_range_inr": "min-max",
#     "estimated_price": numeric_value,
#     "method": "description",
#     "factors": ["factor1", "factor2"]
# }"""
        
#         response = await vision_client.analyze_image(image_bytes, prompt)
#         result = extract_json_from_response(response)
#         result.setdefault('price_range_inr', '500-1500')
#         result.setdefault('method', 'visual estimation')
        
#         return result
#     except Exception as e:
#         logger.error(f"Price estimation failed: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/detect_fraud")
# async def detect_fraud(image: UploadFile = File(...)) -> Dict:
#     """Vision AI: Detect fraud indicators"""
#     logger.info(f"Fraud detection for {image.filename}")
    
#     try:
#         image_bytes = await image.read()
        
#         prompt = """Analyze this image for potential fraud indicators.

# Return JSON:
# {
#     "fraud_score": 0.0-1.0,
#     "is_suspicious": true|false,
#     "red_flags": ["flag1", "flag2"],
#     "authenticity_indicators": ["indicator1"]
# }"""
        
#         response = await vision_client.analyze_image(image_bytes, prompt)
#         result = extract_json_from_response(response)
#         result.setdefault('fraud_score', 0.0)
#         result.setdefault('is_suspicious', False)
        
#         return result
#     except Exception as e:
#         logger.error(f"Fraud detection failed: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/suggest_packaging")
# async def suggest_packaging(image: UploadFile = File(...)) -> Dict:
#     """Vision AI: Recommend packaging"""
#     logger.info(f"Packaging suggestions for {image.filename}")
    
#     try:
#         image_bytes = await image.read()
        
#         prompt = """Recommend packaging for this item.

# Return JSON:
# {
#     "packaging": "description",
#     "cost": estimated_cost_in_rupees,
#     "materials": ["material1", "material2"],
#     "special_requirements": ["requirement1"]
# }"""
        
#         response = await vision_client.analyze_image(image_bytes, prompt)
#         result = extract_json_from_response(response)
#         result.setdefault('packaging', 'standard eco-friendly box')
#         result.setdefault('cost', 100)
        
#         return result
#     except Exception as e:
#         logger.error(f"Packaging suggestion failed: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/detect_material")
# async def detect_material(image: UploadFile = File(...)) -> Dict:
#     """Vision AI: Identify materials"""
#     logger.info(f"Material detection for {image.filename}")
    
#     try:
#         image_bytes = await image.read()
        
#         prompt = """Identify the materials used in this item.

# Return JSON:
# {
#     "material": "primary material name",
#     "purity": 0.0-1.0,
#     "additional_materials": ["material1", "material2"],
#     "texture": "description"
# }"""
        
#         response = await vision_client.analyze_image(image_bytes, prompt)
#         result = extract_json_from_response(response)
#         result.setdefault('material', 'unknown')
#         result.setdefault('purity', 0.8)
        
#         return result
#     except Exception as e:
#         logger.error(f"Material detection failed: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/analyze_sentiment")
# async def analyze_sentiment(image: UploadFile = File(...)) -> Dict:
#     """Vision AI: Analyze sentiment and aesthetic appeal"""
#     logger.info(f"Sentiment analysis for {image.filename}")
    
#     try:
#         image_bytes = await image.read()
        
#         prompt = """Analyze the emotional sentiment and aesthetic appeal of this item.

# Return JSON:
# {
#     "sentiment": "warm|playful|elegant|traditional|modern|rustic",
#     "emotion": "joyful|peaceful|energetic|nostalgic|sophisticated",
#     "appeal_score": 0.0-1.0,
#     "target_audience": "description"
# }"""
        
#         response = await vision_client.analyze_image(image_bytes, prompt)
#         result = extract_json_from_response(response)
#         result.setdefault('sentiment', 'neutral')
#         result.setdefault('emotion', 'pleasant')
        
#         return result
#     except Exception as e:
#         logger.error(f"Sentiment analysis failed: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/detect_occasion")
# async def detect_occasion(image: UploadFile = File(...)) -> Dict:
#     """Vision AI: Detect suitable occasions"""
#     logger.info(f"Occasion detection for {image.filename}")
    
#     try:
#         image_bytes = await image.read()
        
#         prompt = """Identify suitable occasions for gifting this item.

# Return JSON:
# {
#     "occasion": "birthday|wedding|diwali|housewarming|anniversary|general",
#     "confidence": 0.0-1.0,
#     "suitable_occasions": ["occasion1", "occasion2"],
#     "cultural_significance": "if any"
# }"""
        
#         response = await vision_client.analyze_image(image_bytes, prompt)
#         result = extract_json_from_response(response)
#         result.setdefault('occasion', 'general')
#         result.setdefault('confidence', 0.7)
        
#         return result
#     except Exception as e:
#         logger.error(f"Occasion detection failed: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# # ========================================================================
# # RUN SERVER
# # ========================================================================
# # ========================================================================
# # RUN SERVER
# # ========================================================================
# if __name__ == "__main__":
#     import uvicorn
#     import os
    
#     port = int(os.getenv("PORT", 8001))
    
#     uvicorn.run(
#         "main:app",
#         host="0.0.0.0",
#         port=port,
#         reload=True,
#         log_level="info"
#     )


# gift_ai_service/main.py
"""
Unified Gift AI Service - ALL Vision AI endpoints fixed
=======================================================
FIXED: All vision AI endpoints now use direct client calls (no internal HTTP)
NO HARDCODED VALUES: All analysis comes from Gemini Vision API
Port: 8001
"""

# ========================================================================
# CRITICAL: Load .env FIRST
# ========================================================================
import os
import io
import base64
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)

# ========================================================================
# IMPORTS
# ========================================================================
import logging
import traceback
import json
import re
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from PIL import Image
import google.generativeai as genai

from core.orchestrator import GiftOrchestrator
from core.config import settings

# ========================================================================
# LOGGING
# ========================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("gift_ai.main")

# ========================================================================
# VISION AI CLIENT
# ========================================================================
class VisionAIClient:
    """Gemini Vision AI client for all vision endpoints"""
    
    def __init__(self):
        self.gemini_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.gemini_model = None
        
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                
                # Try multiple model versions - use correct model names
                model_names = [
                    'gemini-1.5-flash-latest',
                    'gemini-1.5-flash',
                    'gemini-1.5-pro-latest',
                    'gemini-1.5-pro',
                    'gemini-pro-vision'
                ]
                
                for name in model_names:
                    try:
                        self.gemini_model = genai.GenerativeModel(name)
                        logger.info(f"✅ Vision AI initialized with model: {name}")
                        break
                    except Exception as e:
                        logger.debug(f"Model {name} not available: {e}")
                        continue
                        
                if not self.gemini_model:
                    logger.error("❌ No suitable Gemini model available")
            except Exception as e:
                logger.error(f"❌ Vision AI initialization failed: {e}")
                self.gemini_model = None
        else:
            logger.error("❌ No Gemini API key found in environment")
        
        # Ollama disabled
        self.ollama_available = False
    
    async def analyze_image(self, image_bytes: bytes, prompt: str) -> str:
        """Analyze image using Gemini Vision"""
        if not self.gemini_model:
            raise Exception("Gemini Vision not configured - check GOOGLE_API_KEY or GEMINI_API_KEY in .env")
        
        try:
            image = Image.open(io.BytesIO(image_bytes))
            response = self.gemini_model.generate_content([prompt, image])
            
            if not response or not response.text:
                raise Exception("Empty response from Gemini Vision")
            
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini Vision API error: {e}")
            raise Exception(f"Vision analysis failed: {str(e)}")

# ========================================================================
# HELPER FUNCTIONS
# ========================================================================
def extract_json_from_response(text: str) -> Dict[str, Any]:
    """Extract and parse JSON from LLM response"""
    # Remove markdown code blocks
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        text = json_match.group(1)
    elif '```' in text:
        # Remove any markdown blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    
    # Find JSON object
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        text = json_match.group(0)
    
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed: {e}")
        logger.warning(f"Raw text: {text[:300]}")
        raise Exception(f"Failed to parse JSON response: {str(e)}")

async def call_vision_ai_comprehensive(image_bytes: bytes, analysis_type: str, prompt: str) -> Dict[str, Any]:
    """
    Universal vision AI caller - NO HTTP, direct client usage
    NO HARDCODED VALUES: All data from Gemini Vision
    """
    logger.info(f"🎨 {analysis_type} - Using direct Gemini Vision client")
    
    if not vision_client:
        raise HTTPException(status_code=503, detail="Vision client not initialized")
    
    if not vision_client.gemini_model:
        raise HTTPException(
            status_code=503, 
            detail="Gemini Vision not configured - check API key in environment"
        )
    
    try:
        # Call vision API directly
        response_text = await vision_client.analyze_image(image_bytes, prompt)
        
        # Parse JSON response
        result = extract_json_from_response(response_text)
        
        logger.info(f"✅ {analysis_type} completed successfully")
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ {analysis_type} JSON parse error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"{analysis_type} returned invalid JSON: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ {analysis_type} failed: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"{analysis_type} error: {str(e)}"
        )

# ========================================================================
# PYDANTIC MODELS
# ========================================================================
class GiftBundle(BaseModel):
    bundle_name: str
    description: str
    items: List[Dict[str, Any]]
    total_price: Optional[float] = None

class ImageBundleResponse(BaseModel):
    bundle_id: str
    vision: Dict[str, Any]
    intent: Dict[str, Any]
    bundles: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    error: Optional[str] = None

class TextSearchResponse(BaseModel):
    query: str
    bundles: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# ========================================================================
# GLOBAL INSTANCES
# ========================================================================
orchestrator: Optional[GiftOrchestrator] = None
vision_client: Optional[VisionAIClient] = None

# ========================================================================
# LIFECYCLE MANAGEMENT
# ========================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator, vision_client
    
    # Startup
    logger.info("🚀 Starting Unified Gift AI Service...")
    logger.info(f"📦 MongoDB: {settings.DATABASE_NAME}.{settings.COLLECTION_NAME}")
    logger.info(f"🔍 Qdrant: {settings.QDRANT_URL}")
    logger.info(f"🤖 LLM: {settings.LLM_MODEL}")
    
    try:
        # Initialize vision client first
        logger.info("Initializing vision client...")
        vision_client = VisionAIClient()
        
        if vision_client.gemini_model:
            logger.info("✅ Vision client ready")
        else:
            logger.warning("⚠️ Vision client initialized but Gemini not available")
        
        # Initialize orchestrator
        logger.info("Initializing orchestrator...")
        orchestrator = GiftOrchestrator()
        
        # Connect databases
        logger.info("Connecting to databases...")
        await orchestrator.vector_store.connect()
        logger.info("✅ Databases connected")
        
        logger.info("🎉 Service fully initialized")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        traceback.print_exc()
        
        # Partial initialization
        if not vision_client:
            vision_client = VisionAIClient()
        if not orchestrator:
            orchestrator = GiftOrchestrator()
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    if orchestrator:
        try:
            await orchestrator.vector_store.close()
            logger.info("✅ Connections closed")
        except Exception as e:
            logger.warning(f"Shutdown warning: {e}")

# ========================================================================
# FASTAPI APP
# ========================================================================
app = FastAPI(
    title="Unified Gift AI Service",
    description="Complete GenAI gift recommendation and vision analysis system",
    version="3.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================================================
# HEALTH & INFO ENDPOINTS
# ========================================================================
@app.get("/")
async def root():
    return {
        "service": "unified-gift-ai",
        "version": "3.1.0",
        "status": "running",
        "message": "Gift AI Service with direct Vision AI integration"
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "service": "unified-gift-ai",
        "version": "3.1.0",
        "components": {
            "orchestrator": orchestrator is not None,
            "mongodb": False,
            "qdrant": False,
            "gemini_configured": bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")),
            "vision_ai": vision_client is not None and vision_client.gemini_model is not None,
        },
        "errors": []
    }
    
    # Test MongoDB
    if orchestrator and orchestrator.vector_store.mongo_collection:
        try:
            await orchestrator.vector_store.mongo_collection.find_one({}, {"_id": 1})
            health_status["components"]["mongodb"] = True
        except Exception as e:
            health_status["errors"].append(f"MongoDB: {str(e)}")
    
    # Test Qdrant
    if orchestrator and orchestrator.vector_store.qdrant_client:
        try:
            orchestrator.vector_store.qdrant_client.get_collections()
            health_status["components"]["qdrant"] = True
        except Exception as e:
            health_status["errors"].append(f"Qdrant: {str(e)}")
    
    # Determine overall status
    critical = ["orchestrator", "mongodb", "qdrant", "gemini_configured"]
    if not all(health_status["components"][c] for c in critical):
        health_status["status"] = "degraded"
    
    if health_status["errors"]:
        health_status["status"] = "unhealthy" if len(health_status["errors"]) > 2 else "degraded"
    
    return health_status

# ========================================================================
# GIFT AI ENDPOINTS
# ========================================================================

@app.post("/generate_gift_bundle", response_model=ImageBundleResponse)
async def generate_gift_bundle(image: UploadFile = File(...)):
    """Image to Gift Bundle Pipeline"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    if not image.filename or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid image file")
    
    try:
        image_bytes = await image.read()
        if len(image_bytes) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image too large (max 5MB)")
        
        logger.info(f"Processing image: {image.filename}")
        result = await orchestrator.generate_bundle(image_bytes, image.filename)
        logger.info(f"Bundle generated: {result['bundle_id']}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bundle generation failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search_similar_gifts", response_model=TextSearchResponse)
async def search_similar_gifts(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50)
):
    """Text Search to Gift Bundle"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        logger.info(f"Text search: '{query}'")
        result = await orchestrator.process_gift_query(query, limit)
        return result
    except Exception as e:
        logger.error(f"Search failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search", response_model=TextSearchResponse)
async def search_alias(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50)
):
    """Alias for search_similar_gifts"""
    return await search_similar_gifts(query, limit)

@app.post("/refresh_vector_store")
async def refresh_vector_store():
    """Refresh Vector Store"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        result = await orchestrator.refresh_vector_store()
        if result.get("success"):
            return {
                "success": True,
                "message": result.get("message"),
                "items_count": result.get("items_count", 0)
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Refresh failed at {result.get('step')}: {result.get('error')}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refresh error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================================================
# VISION AI ENDPOINTS - ALL FIXED WITH DIRECT CLIENT
# ========================================================================

@app.post("/analyze_craft")
async def analyze_craft(image: UploadFile = File(...)) -> Dict:
    """
    FIXED: Analyze craft type using direct vision client
    NO HARDCODED VALUES
    """
    image_bytes = await image.read()
    
    prompt = """Analyze this image to identify the type of craft or artwork.

Return ONLY valid JSON (no markdown, no extra text):
{
    "craft_type": "specific category: pottery|textile|metalwork|painting|sculpture|woodwork|jewelry|decorative|other",
    "confidence": 0.0-1.0,
    "subcategory": "more specific type if applicable",
    "details": "brief visual description",
    "cultural_origin": "if identifiable from visual style"
}

Base your analysis on:
- Visual characteristics and techniques visible
- Materials and construction methods evident
- Traditional craft patterns or styles
- Functional vs decorative nature"""
    
    return await call_vision_ai_comprehensive(image_bytes, "Craft Type Analysis", prompt)

@app.post("/analyze_quality")
async def analyze_quality(image: UploadFile = File(...)) -> Dict:
    """
    FIXED: Assess quality using direct vision client
    NO HARDCODED VALUES
    """
    image_bytes = await image.read()
    
    prompt = """Analyze the quality and craftsmanship of this handmade item.

Return ONLY valid JSON (no markdown):
{
    "quality": "high|medium|low",
    "craftsmanship_score": 0.0-1.0,
    "finish_quality": "description of surface finish and polish",
    "attention_to_detail": "assessment of fine details and precision",
    "professional_level": "hobbyist|intermediate|professional|master",
    "quality_indicators": ["specific observable quality features"],
    "flaws_noted": ["any visible imperfections if present"]
}

Assess based on:
- Surface finish and smoothness
- Symmetry and proportions
- Detail work and precision
- Material treatment
- Overall professional appearance"""
    
    return await call_vision_ai_comprehensive(image_bytes, "Quality Assessment", prompt)

@app.post("/estimate_price")
async def estimate_price(image: UploadFile = File(...)) -> Dict:
    """
    FIXED: Estimate price using direct vision client
    NO HARDCODED VALUES
    """
    image_bytes = await image.read()
    
    prompt = """Estimate the price range for this handmade item in Indian Rupees based on visual analysis.

Return ONLY valid JSON:
{
    "price_range_inr": "min-max format like 500-1500",
    "estimated_price": numeric_value_in_rupees,
    "confidence": 0.0-1.0,
    "pricing_factors": ["factors affecting price"],
    "market_segment": "budget|mid-range|premium|luxury",
    "size_estimate": "small|medium|large based on visual cues",
    "complexity": "simple|moderate|complex|highly_intricate"
}

Consider in your estimate:
- Apparent size and scale
- Material quality visible
- Craftsmanship level
- Detail and complexity
- Finish quality
- Indian handmade craft market standards
- Time investment apparent in creation"""
    
    return await call_vision_ai_comprehensive(image_bytes, "Price Estimation", prompt)

@app.post("/detect_fraud")
async def detect_fraud(image: UploadFile = File(...)) -> Dict:
    """
    FIXED: Detect fraud indicators using direct vision client
    NO HARDCODED VALUES
    """
    image_bytes = await image.read()
    
    prompt = """Analyze this image for authenticity and fraud indicators.

Return ONLY valid JSON:
{
    "fraud_score": 0.0-1.0 (0=authentic, 1=highly suspicious),
    "is_suspicious": true|false,
    "authenticity_confidence": 0.0-1.0,
    "red_flags": ["specific suspicious elements if any"],
    "authenticity_indicators": ["signs of genuine handmade work"],
    "assessment": "brief overall authenticity assessment"
}

Check for:
- Stock photo characteristics (perfect studio lighting, watermarks, professional staging)
- AI-generated image artifacts (unnatural textures, impossible geometry, blending errors)
- Mass production indicators (perfect repetition, mold marks, industrial finish)
- Handmade authenticity signs (slight irregularities, tool marks, natural variations)
- Image manipulation signs (color banding, clone stamp patterns, resolution inconsistencies)"""
    
    return await call_vision_ai_comprehensive(image_bytes, "Fraud Detection", prompt)

@app.post("/suggest_packaging")
async def suggest_packaging(image: UploadFile = File(...)) -> Dict:
    """
    FIXED: Suggest packaging using direct vision client
    NO HARDCODED VALUES
    """
    image_bytes = await image.read()
    
    prompt = """Recommend appropriate packaging for this handmade item based on visual assessment.

Return ONLY valid JSON:
{
    "packaging_type": "specific packaging recommendation",
    "estimated_cost": numeric_value_in_rupees,
    "materials": ["packaging materials needed"],
    "protection_level": "minimal|moderate|high|fragile",
    "presentation_style": "simple|elegant|premium|traditional",
    "special_requirements": ["any special packaging needs"],
    "eco_friendly_option": "eco-friendly alternative if applicable"
}

Base recommendations on:
- Item fragility assessment
- Apparent size and weight
- Surface delicacy
- Presentation value expected
- Protection needs during transport
- Gift-worthiness and presentation appeal"""
    
    return await call_vision_ai_comprehensive(image_bytes, "Packaging Suggestion", prompt)

@app.post("/detect_material")
async def detect_material(image: UploadFile = File(...)) -> Dict:
    """
    FIXED: Identify materials using direct vision client
    NO HARDCODED VALUES
    """
    image_bytes = await image.read()
    
    prompt = """Identify the materials used in this handmade item from visual analysis.

Return ONLY valid JSON:
{
    "primary_material": "main material identified",
    "material_purity": 0.0-1.0 (quality/purity estimate),
    "secondary_materials": ["other materials visible"],
    "material_quality": "low|medium|high|premium",
    "texture_description": "surface texture characteristics",
    "finish_type": "matte|glossy|satin|textured|natural",
    "identification_confidence": 0.0-1.0
}

Identify materials from:
- Visual texture patterns
- Color and reflectivity
- Surface characteristics
- Construction techniques visible
- Material interaction at joints/edges
- Finish and treatment appearance"""
    
    return await call_vision_ai_comprehensive(image_bytes, "Material Identification", prompt)

@app.post("/analyze_sentiment")
async def analyze_sentiment(image: UploadFile = File(...)) -> Dict:
    """
    FIXED: Analyze sentiment using direct vision client
    NO HARDCODED VALUES
    """
    image_bytes = await image.read()
    
    prompt = """Analyze the emotional sentiment and aesthetic appeal of this handmade item.

Return ONLY valid JSON:
{
    "sentiment": "primary aesthetic feeling: warm|playful|elegant|traditional|modern|rustic|minimalist|bold",
    "emotion": "emotional quality: joyful|peaceful|energetic|nostalgic|sophisticated|calming|romantic",
    "appeal_score": 0.0-1.0,
    "aesthetic_style": "overall design aesthetic",
    "color_mood": "emotional impact of color palette",
    "target_demographic": "who would appreciate this aesthetically",
    "emotional_keywords": ["emotional/aesthetic descriptors"]
}

Assess based on:
- Design language and style
- Color palette emotional impact
- Form and proportion feeling
- Cultural aesthetic elements
- Contemporary vs traditional appeal
- Visual harmony and balance"""
    
    return await call_vision_ai_comprehensive(image_bytes, "Sentiment Analysis", prompt)

@app.post("/detect_occasion")
async def detect_occasion(image: UploadFile = File(...)) -> Dict:
    """
    FIXED: Detect suitable occasions using direct vision client
    NO HARDCODED VALUES
    """
    image_bytes = await image.read()
    
    prompt = """Identify suitable gifting occasions for this handmade item based on design elements.

Return ONLY valid JSON:
{
    "primary_occasion": "best fit: birthday|wedding|diwali|holi|anniversary|housewarming|graduation|raksha_bandhan|eid|christmas|general",
    "confidence": 0.0-1.0,
    "suitable_occasions": ["all applicable occasions"],
    "occasion_reasoning": "why these occasions fit",
    "cultural_significance": "if design has cultural/festival relevance",
    "age_suitability": "appropriate age groups",
    "formality_level": "casual|semi-formal|formal|ceremonial"
}

Determine based on:
- Design motifs and symbolism
- Cultural/traditional elements
- Color significance in Indian context
- Formality and presentation level
- Functional vs decorative nature
- Festival/celebration associations"""
    
    return await call_vision_ai_comprehensive(image_bytes, "Occasion Detection", prompt)

# ========================================================================
# RUN SERVER
# ========================================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )