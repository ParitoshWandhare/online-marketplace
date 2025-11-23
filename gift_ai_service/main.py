# gift_ai_service/main.py
"""
Unified Gift AI Service - Complete Integration
==============================================
Combines Gift AI recommendation engine and Vision AI analysis in one service
Port: 8001 (serves both functionalities)
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
    """Gemini Vision AI client with Ollama fallback"""
    
    def __init__(self):
        self.gemini_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.gemini_model = None
        
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                model_names = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-pro-latest']
                
                for name in model_names:
                    try:
                        self.gemini_model = genai.GenerativeModel(name)
                        logger.info(f"Vision AI initialized with: {name}")
                        break
                    except:
                        continue
            except Exception as e:
                logger.error(f"Vision AI initialization failed: {e}")
        
        self.ollama_available = self._check_ollama()
    
    def _check_ollama(self) -> bool:
        try:
            import requests
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return any('llava' in m.get('name', '').lower() for m in models)
        except:
            pass
        return False
    
    async def analyze_image_gemini(self, image_bytes: bytes, prompt: str) -> str:
        if not self.gemini_model:
            raise Exception("Gemini not configured")
        
        image = Image.open(io.BytesIO(image_bytes))
        response = self.gemini_model.generate_content([prompt, image])
        return response.text
    
    async def analyze_image_ollama(self, image_bytes: bytes, prompt: str) -> str:
        if not self.ollama_available:
            raise Exception("Ollama not available")
        
        import requests
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={'model': 'llava', 'prompt': prompt, 'images': [base64_image], 'stream': False},
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()['response']
        raise Exception(f"Ollama error: {response.status_code}")
    
    async def analyze_image(self, image_bytes: bytes, prompt: str) -> str:
        if self.gemini_model:
            try:
                return await self.analyze_image_gemini(image_bytes, prompt)
            except Exception as e:
                logger.warning(f"Gemini failed: {e}, trying Ollama...")
        
        if self.ollama_available:
            try:
                return await self.analyze_image_ollama(image_bytes, prompt)
            except Exception as e:
                logger.error(f"Ollama failed: {e}")
        
        raise Exception("No vision AI provider available")

# Helper function for JSON extraction
def extract_json_from_response(text: str) -> Dict[str, Any]:
    import json
    import re
    
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        text = json_match.group(1)
    else:
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            text = json_match.group(0)
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON")
        return {"raw_response": text}

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

class ArtworkIndexRequest(BaseModel):
    mongo_id: str
    title: str
    description: str
    category: Optional[str] = "General"
    price: float
    tags: Optional[List[str]] = []

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
    logger.info("Starting Unified Gift AI Service...")
    logger.info(f"MongoDB: {settings.DATABASE_NAME}.{settings.COLLECTION_NAME}")
    logger.info(f"Qdrant: {settings.QDRANT_URL}")
    logger.info(f"LLM: {settings.LLM_MODEL}")
    
    try:
        orchestrator = GiftOrchestrator()
        await orchestrator.vector_store.connect()
        vision_client = VisionAIClient()
        logger.info("Service initialized successfully")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        traceback.print_exc()
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    if orchestrator:
        try:
            await orchestrator.vector_store.close()
            logger.info("Connections closed")
        except Exception as e:
            logger.warning(f"Shutdown warning: {e}")

# ========================================================================
# FASTAPI APP
# ========================================================================
app = FastAPI(
    title="Unified Gift AI Service",
    description="Complete GenAI gift recommendation and vision analysis system",
    version="3.0.0",
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
# HEALTH CHECK
# ========================================================================
@app.get("/health")
async def health_check():
    """Service health check"""
    return {
        "status": "healthy",
        "service": "unified-gift-ai",
        "version": "3.0.0",
        "components": {
            "orchestrator": orchestrator is not None,
            "mongodb": settings.MONGODB_URL is not None and settings.MONGODB_URL != "",
            "qdrant": settings.QDRANT_URL is not None and settings.QDRANT_URL != "",
            "gemini_api_key": settings.GEMINI_API_KEY is not None and settings.GEMINI_API_KEY != "",
            "vision_ai": vision_client is not None and vision_client.gemini_model is not None,
        }
    }

# ========================================================================
# GIFT AI ENDPOINTS (Recommendation Engine)
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
        
        logger.info(f"Processing: {image.filename}")
        result = await orchestrator.generate_bundle(image_bytes, image.filename)
        logger.info(f"Bundle generated: {result['bundle_id']}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed: {e}")
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
    
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        logger.info(f"Searching: '{query}'")
        result = await orchestrator.process_gift_query(query, limit)
        logger.info(f"Found {len(result.get('bundles', []))} bundles")
        return result
    except Exception as e:
        logger.error(f"Search failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/refresh_vector_store")
async def refresh_vector_store():
    """Refresh Vector Store (Admin)"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        logger.info("Starting refresh...")
        result = await orchestrator.refresh_vector_store()
        
        if result.get("success"):
            logger.info("Refresh completed")
            return {
                "success": True,
                "message": result.get("message", "Refreshed successfully"),
                "items_count": result.get("items_count", 0),
                "collection": settings.COLLECTION_NAME
            }
        else:
            error_msg = result.get("error", "Unknown error")
            step = result.get("step", "unknown")
            logger.error(f"Refresh failed at step '{step}': {error_msg}")
            raise HTTPException(status_code=500, detail=f"Refresh failed at {step}: {error_msg}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refresh error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index_artwork")
async def index_artwork(request: ArtworkIndexRequest):
    """Index Single Artwork"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        item_dict = request.model_dump()
        text = f"{item_dict['title']} {item_dict['description']}"
        
        embedding = orchestrator.vector_store.generate_embedding(text)
        if not embedding:
            raise HTTPException(status_code=500, detail="Embedding generation failed")
        
        if len(embedding) > 768:
            embedding = embedding[:768]
        elif len(embedding) < 768:
            embedding.extend([0.0] * (768 - len(embedding)))
        
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
        
        logger.info(f"Indexed: {item_dict['title']}")
        return {
            "success": True,
            "message": f"Indexed '{item_dict['title']}'",
            "item_id": item_dict['mongo_id']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vector_store_info")
async def vector_store_info():
    """Get Vector Store Information"""
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
        logger.error(f"Info fetch failed: {e}")
        return {"connected": False, "error": str(e)}

# ========================================================================
# VISION AI ENDPOINTS (Image Analysis)
# ========================================================================

@app.post("/analyze_craft")
async def analyze_craft(image: UploadFile = File(...)) -> Dict:
    """Vision AI: Detect craft type"""
    logger.info(f"Analyzing craft in {image.filename}")
    
    try:
        image_bytes = await image.read()
        
        prompt = """Analyze this image and identify the type of craft or artwork shown.

Return a JSON object with:
{
    "craft_type": "pottery|textile|metalwork|painting|sculpture|woodwork|jewelry|other",
    "confidence": 0.0-1.0,
    "details": "brief description"
}"""
        
        response = await vision_client.analyze_image(image_bytes, prompt)
        result = extract_json_from_response(response)
        result.setdefault('craft_type', 'unknown')
        result.setdefault('confidence', 0.5)
        
        logger.info(f"Craft detected: {result.get('craft_type')}")
        return result
    except Exception as e:
        logger.error(f"Craft analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze_quality")
async def analyze_quality(image: UploadFile = File(...)) -> Dict:
    """Vision AI: Assess craftsmanship quality"""
    logger.info(f"Analyzing quality of {image.filename}")
    
    try:
        image_bytes = await image.read()
        
        prompt = """Analyze the quality and craftsmanship of this item.

Return JSON:
{
    "quality": "high|medium|low",
    "details": "describe finish, craftsmanship, flaws",
    "craftsmanship_score": 0.0-1.0
}"""
        
        response = await vision_client.analyze_image(image_bytes, prompt)
        result = extract_json_from_response(response)
        result.setdefault('quality', 'medium')
        result.setdefault('details', 'No details available')
        
        return result
    except Exception as e:
        logger.error(f"Quality analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/estimate_price")
async def estimate_price(image: UploadFile = File(...)) -> Dict:
    """Vision AI: Estimate price range"""
    logger.info(f"Estimating price for {image.filename}")
    
    try:
        image_bytes = await image.read()
        
        prompt = """Estimate the price range for this handmade item in Indian Rupees.

Return JSON:
{
    "price_range_inr": "min-max",
    "estimated_price": numeric_value,
    "method": "description",
    "factors": ["factor1", "factor2"]
}"""
        
        response = await vision_client.analyze_image(image_bytes, prompt)
        result = extract_json_from_response(response)
        result.setdefault('price_range_inr', '500-1500')
        result.setdefault('method', 'visual estimation')
        
        return result
    except Exception as e:
        logger.error(f"Price estimation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect_fraud")
async def detect_fraud(image: UploadFile = File(...)) -> Dict:
    """Vision AI: Detect fraud indicators"""
    logger.info(f"Fraud detection for {image.filename}")
    
    try:
        image_bytes = await image.read()
        
        prompt = """Analyze this image for potential fraud indicators.

Return JSON:
{
    "fraud_score": 0.0-1.0,
    "is_suspicious": true|false,
    "red_flags": ["flag1", "flag2"],
    "authenticity_indicators": ["indicator1"]
}"""
        
        response = await vision_client.analyze_image(image_bytes, prompt)
        result = extract_json_from_response(response)
        result.setdefault('fraud_score', 0.0)
        result.setdefault('is_suspicious', False)
        
        return result
    except Exception as e:
        logger.error(f"Fraud detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/suggest_packaging")
async def suggest_packaging(image: UploadFile = File(...)) -> Dict:
    """Vision AI: Recommend packaging"""
    logger.info(f"Packaging suggestions for {image.filename}")
    
    try:
        image_bytes = await image.read()
        
        prompt = """Recommend packaging for this item.

Return JSON:
{
    "packaging": "description",
    "cost": estimated_cost_in_rupees,
    "materials": ["material1", "material2"],
    "special_requirements": ["requirement1"]
}"""
        
        response = await vision_client.analyze_image(image_bytes, prompt)
        result = extract_json_from_response(response)
        result.setdefault('packaging', 'standard eco-friendly box')
        result.setdefault('cost', 100)
        
        return result
    except Exception as e:
        logger.error(f"Packaging suggestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect_material")
async def detect_material(image: UploadFile = File(...)) -> Dict:
    """Vision AI: Identify materials"""
    logger.info(f"Material detection for {image.filename}")
    
    try:
        image_bytes = await image.read()
        
        prompt = """Identify the materials used in this item.

Return JSON:
{
    "material": "primary material name",
    "purity": 0.0-1.0,
    "additional_materials": ["material1", "material2"],
    "texture": "description"
}"""
        
        response = await vision_client.analyze_image(image_bytes, prompt)
        result = extract_json_from_response(response)
        result.setdefault('material', 'unknown')
        result.setdefault('purity', 0.8)
        
        return result
    except Exception as e:
        logger.error(f"Material detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze_sentiment")
async def analyze_sentiment(image: UploadFile = File(...)) -> Dict:
    """Vision AI: Analyze sentiment and aesthetic appeal"""
    logger.info(f"Sentiment analysis for {image.filename}")
    
    try:
        image_bytes = await image.read()
        
        prompt = """Analyze the emotional sentiment and aesthetic appeal of this item.

Return JSON:
{
    "sentiment": "warm|playful|elegant|traditional|modern|rustic",
    "emotion": "joyful|peaceful|energetic|nostalgic|sophisticated",
    "appeal_score": 0.0-1.0,
    "target_audience": "description"
}"""
        
        response = await vision_client.analyze_image(image_bytes, prompt)
        result = extract_json_from_response(response)
        result.setdefault('sentiment', 'neutral')
        result.setdefault('emotion', 'pleasant')
        
        return result
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect_occasion")
async def detect_occasion(image: UploadFile = File(...)) -> Dict:
    """Vision AI: Detect suitable occasions"""
    logger.info(f"Occasion detection for {image.filename}")
    
    try:
        image_bytes = await image.read()
        
        prompt = """Identify suitable occasions for gifting this item.

Return JSON:
{
    "occasion": "birthday|wedding|diwali|housewarming|anniversary|general",
    "confidence": 0.0-1.0,
    "suitable_occasions": ["occasion1", "occasion2"],
    "cultural_significance": "if any"
}"""
        
        response = await vision_client.analyze_image(image_bytes, prompt)
        result = extract_json_from_response(response)
        result.setdefault('occasion', 'general')
        result.setdefault('confidence', 0.7)
        
        return result
    except Exception as e:
        logger.error(f"Occasion detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================================================
# RUN SERVER
# ========================================================================
# ========================================================================
# RUN SERVER
# ========================================================================
if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.getenv("PORT", 8001))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )