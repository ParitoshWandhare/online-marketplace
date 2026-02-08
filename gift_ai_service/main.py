# gift_ai_service/main.py
"""
UNIFIED GIFT AI SERVICE - Single File Deployment
=================================================
Combines ALL functionality:
- Gift Bundle Generation (image → bundles)
- Text Search (query → bundles)  
- Vision AI Analysis (all 8 endpoints)
- Vector Store Management

Port: 8001
Deployment: Single service, all endpoints accessible
"""

# ========================================================================
# CRITICAL: Load .env FIRST
# ========================================================================
import os
import io
import json
import re
import logging
import traceback
import uuid
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)

# ========================================================================
# IMPORTS
# ========================================================================
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from PIL import Image
import google.generativeai as genai

# Import core components
from core.config import settings
from core.llm_client import LLMClient

# ========================================================================
# LOGGING
# ========================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("gift_ai.main")

# ========================================================================
# VISION AI CLIENT (Direct - No HTTP)
# ========================================================================
class VisionAIClient:
    """Unified Vision AI client using Gemini"""
    
    def __init__(self):
        self.gemini_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.gemini_model = None
        
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                
                # Try different models
                model_names = [
                    'gemini-2.5-flash',
                    'gemini-2.0-flash', 
                    'gemini-pro-latest',
                    'gemini-flash-latest',
                ]
                
                for name in model_names:
                    try:
                        self.gemini_model = genai.GenerativeModel(name)
                        logger.info(f"✅ Vision AI initialized with: {name}")
                        break
                    except:
                        continue
                        
            except Exception as e:
                logger.error(f"❌ Vision AI initialization failed: {e}")
        else:
            logger.warning("⚠️ No Gemini API key found")
    
    async def analyze_image(self, image_bytes: bytes, prompt: str) -> str:
        """Analyze image using Gemini Vision"""
        if not self.gemini_model:
            raise Exception("Gemini Vision not configured - check API key")
        
        try:
            image = Image.open(io.BytesIO(image_bytes))
            response = self.gemini_model.generate_content([prompt, image])
            
            if not response or not response.text:
                raise Exception("Empty response from Gemini")
            
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini Vision error: {e}")
            raise Exception(f"Vision analysis failed: {str(e)}")

# ========================================================================
# VECTOR STORE (Embedded)
# ========================================================================
from motor.motor_asyncio import AsyncIOMotorClient
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
import requests

class VectorStore:
    """Embedded Vector Store with real embeddings"""
    
    def __init__(self):
        self.mongo_client = None
        self.mongo_db = None
        self.mongo_collection = None
        self.qdrant_client = None
        self.collection_name = settings.COLLECTION_NAME
        self.google_api_key = settings.GOOGLE_API_KEY
        self.genai = None
        
    async def connect(self):
        """Connect to MongoDB and Qdrant"""
        # MongoDB
        try:
            self.mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
            self.mongo_db = self.mongo_client[settings.DATABASE_NAME]
            self.mongo_collection = self.mongo_db[settings.COLLECTION_NAME]
            logger.info(f"✅ MongoDB connected: {settings.DATABASE_NAME}.{settings.COLLECTION_NAME}")
        except Exception as e:
            logger.error(f"❌ MongoDB failed: {e}")
            raise
        
        # Qdrant
        try:
            self.qdrant_client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
            )
            logger.info("✅ Qdrant connected")
        except Exception as e:
            logger.error(f"❌ Qdrant failed: {e}")
            raise
        
        # Gemini for embeddings
        if self.google_api_key:
            try:
                genai.configure(api_key=self.google_api_key)
                self.genai = genai
                logger.info("✅ Gemini embeddings ready")
            except:
                pass
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Gemini"""
        if self.genai:
            try:
                result = self.genai.embed_content(
                    model='models/embedding-001',
                    content=text,
                    task_type="retrieval_document"
                )
                return result['embedding']
            except:
                pass
        
        # Fallback: simple embedding
        embedding = [0.0] * 768
        for i, char in enumerate(text[:768]):
            embedding[i] = (ord(char) % 100) / 100.0
        return embedding
    
    async def get_mongo_items(self, limit: int = 100) -> List[Dict]:
        """Fetch published items from MongoDB"""
        if not self.mongo_collection:
            raise Exception("MongoDB not connected")
        
        cursor = self.mongo_collection.find(
            {"status": "published"}
        ).limit(limit)
        
        items = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            items.append(doc)
        
        logger.info(f"📦 Retrieved {len(items)} items from MongoDB")
        return items
    
    async def setup_collection(self) -> bool:
        """Create Qdrant collection if needed"""
        try:
            collections = self.qdrant_client.get_collections()
            exists = any(col.name == self.collection_name for col in collections.collections)
            
            if not exists:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
                )
                logger.info(f"✅ Created collection: {self.collection_name}")
            
            return True
        except Exception as e:
            logger.error(f"❌ Collection setup failed: {e}")
            raise
    
    async def upload_items(self, items: List[Dict]) -> bool:
        """Upload items to Qdrant"""
        if not items:
            return False
        
        points = []
        for idx, item in enumerate(items):
            text = f"{item.get('title', '')} {item.get('description', '')}"
            embedding = self.generate_embedding(text)
            
            # Pad to 768
            if len(embedding) < 768:
                embedding.extend([0.0] * (768 - len(embedding)))
            elif len(embedding) > 768:
                embedding = embedding[:768]
            
            point = PointStruct(
                id=idx + 1,
                vector=embedding,
                payload={
                    'title': item.get('title', ''),
                    'description': item.get('description', ''),
                    'category': item.get('category', ''),
                    'price': item.get('price', 0),
                    'mongo_id': str(item.get('_id', ''))
                }
            )
            points.append(point)
        
        self.qdrant_client.upsert(collection_name=self.collection_name, points=points)
        logger.info(f"✅ Uploaded {len(points)} items")
        return True
    
    async def search_related_items(self, text: str, limit: int = 10) -> List[Dict]:
        """Search similar items"""
        query_embedding = self.generate_embedding(text)
        
        if len(query_embedding) < 768:
            query_embedding.extend([0.0] * (768 - len(query_embedding)))
        elif len(query_embedding) > 768:
            query_embedding = query_embedding[:768]
        
        results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit
        )
        
        items = []
        for result in results:
            items.append({
                'title': result.payload.get('title', ''),
                'description': result.payload.get('description', ''),
                'category': result.payload.get('category', ''),
                'price': result.payload.get('price', 0),
                'score': result.score,
                'mongo_id': result.payload.get('mongo_id', '')
            })
        
        return items
    
    async def close(self):
        """Close connections"""
        if self.mongo_client:
            self.mongo_client.close()

# ========================================================================
# GIFT AI SERVICES (Embedded)
# ========================================================================

async def extract_intent(image_bytes: bytes, vision_analysis: Dict) -> Dict:
    """Extract gift intent from vision analysis"""
    llm = LLMClient()
    
    vision_text = f"craft: {vision_analysis.get('craft_type')}, occasion: {vision_analysis.get('occasion_hint')}"
    
    prompt = f"""Extract gift intent from vision analysis: {vision_text}

Return ONLY valid JSON:
{{
    "occasion": "birthday|wedding|diwali|general",
    "recipient": "friend|family|anyone",
    "budget_inr": 1000,
    "sentiment": "warm|elegant|playful",
    "interests": ["handmade", "decor"]
}}"""
    
    try:
        result = await llm.generate_text(prompt)
        clean = result.strip()
        if '```json' in clean:
            clean = clean.split('```json')[1].split('```')[0]
        
        data = json.loads(clean.strip())
        data.setdefault('occasion', 'birthday')
        data.setdefault('budget_inr', 1000)
        return data
    except:
        return {
            "occasion": "birthday",
            "recipient": "friend",
            "budget_inr": 1000,
            "sentiment": "warm",
            "interests": ["handmade"]
        }

def validate_items(items: List[Dict], max_budget: float = None) -> Tuple[List[Dict], List[Dict]]:
    """Validate items"""
    valid = []
    invalid = []
    
    for item in items:
        if not item.get('title'):
            invalid.append({'item': item, 'reason': 'No title'})
            continue
        
        if max_budget and item.get('price', 0) > max_budget:
            invalid.append({'item': item, 'reason': 'Over budget'})
            continue
        
        valid.append(item)
    
    return valid, invalid

class GiftBundleService:
    """Generate gift bundles using LLM"""
    
    def __init__(self):
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.genai = None
        
        if self.google_api_key:
            try:
                genai.configure(api_key=self.google_api_key)
                self.genai = genai
            except:
                pass
    
    async def generate_bundles(self, user_intent: str, items: List[Dict]) -> Dict:
        """Generate bundles"""
        items_str = "\n".join([
            f"- {item.get('title')}: ₹{item.get('price')} ({item.get('category')})"
            for item in items[:10]
        ])
        
        prompt = f"""Create 3 gift bundles for: {user_intent}

Available items:
{items_str}

Return ONLY valid JSON:
{{
    "bundles": [
        {{
            "bundle_name": "Creative name",
            "description": "Why this works",
            "items": [
                {{
                    "title": "exact title from list",
                    "reason": "why included"
                }}
            ]
        }}
    ]
}}"""
        
        try:
            if self.genai:
                model = self.genai.GenerativeModel('gemini-1.5-flash-001')
                response = model.generate_content(prompt)
                text = response.text
                
                if '```json' in text:
                    text = text.split('```json')[1].split('```')[0]
                
                result = json.loads(text.strip())
            else:
                # Fallback
                result = {
                    "bundles": [{
                        "bundle_name": "Curated Selection",
                        "description": f"Items matching: {user_intent}",
                        "items": [{"title": item['title'], "reason": "Relevant"} for item in items[:3]]
                    }]
                }
        except:
            result = {
                "bundles": [{
                    "bundle_name": "Curated Selection",
                    "description": f"Items matching: {user_intent}",
                    "items": [{"title": item['title'], "reason": "Relevant"} for item in items[:3]]
                }]
            }
        
        # Calculate prices
        for bundle in result.get('bundles', []):
            total = 0
            for bundle_item in bundle.get('items', []):
                for item in items:
                    if item['title'] == bundle_item['title']:
                        bundle_item['price'] = item.get('price', 0)
                        total += item.get('price', 0)
                        break
            bundle['total_price'] = total
        
        return {'query': user_intent, 'bundles': result.get('bundles', [])}

# ========================================================================
# ORCHESTRATOR (Embedded)
# ========================================================================
class GiftOrchestrator:
    """Main orchestrator"""
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.bundle_service = GiftBundleService()
    
    async def refresh_vector_store(self) -> Dict:
        """Refresh vector store"""
        try:
            items = await self.vector_store.get_mongo_items(limit=100)
            if not items:
                return {"success": False, "error": "No items in MongoDB"}
            
            await self.vector_store.setup_collection()
            await self.vector_store.upload_items(items)
            
            return {"success": True, "items_count": len(items)}
        except Exception as e:
            logger.error(f"Refresh failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_bundle(self, image_bytes: bytes, filename: str) -> Dict:
        """Generate gift bundle from image"""
        bundle_id = str(uuid.uuid4())
        
        try:
            # Step 1: Vision analysis (direct client)
            vision = await self._vision_analysis(image_bytes)
            
            # Step 2: Extract intent
            intent = await extract_intent(image_bytes, vision)
            
            # Step 3: Retrieve items
            query = f"{intent.get('occasion')} gift {' '.join(intent.get('interests', []))}"
            items = await self.vector_store.search_related_items(query, limit=10)
            
            if not items:
                return {
                    "bundle_id": bundle_id,
                    "vision": vision,
                    "intent": intent,
                    "bundles": [],
                    "error": "No items found"
                }
            
            # Step 4: Validate
            valid_items, _ = validate_items(items)
            
            # Step 5: Generate bundles
            result = await self.bundle_service.generate_bundles(str(intent), valid_items)
            
            return {
                "bundle_id": bundle_id,
                "vision": vision,
                "intent": intent,
                "bundles": result.get('bundles', []),
                "metadata": {"total_retrieved": len(items), "valid_count": len(valid_items)}
            }
            
        except Exception as e:
            logger.error(f"Bundle generation failed: {e}")
            traceback.print_exc()
            return {
                "bundle_id": bundle_id,
                "bundles": [],
                "error": str(e)
            }
    
    async def _vision_analysis(self, image_bytes: bytes) -> Dict:
        """Direct vision analysis - NO HTTP calls"""
        if not vision_client or not vision_client.gemini_model:
            return {"status": "unavailable", "error": "Vision AI not configured"}
        
        prompt = """Analyze this craft/artwork image.

Return ONLY valid JSON:
{
    "craft_type": "pottery|textile|metalwork|painting|other",
    "quality": "high|medium|low",
    "price_range": "500-1500",
    "estimated_price": 1000,
    "occasion_hint": "birthday|wedding|general",
    "sentiment": "warm|elegant|playful"
}"""
        
        try:
            response = await vision_client.analyze_image(image_bytes, prompt)
            clean = response.strip()
            if '```json' in clean:
                clean = clean.split('```json')[1].split('```')[0]
            
            data = json.loads(clean.strip())
            data['status'] = 'success'
            return data
        except Exception as e:
            logger.error(f"Vision failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def process_gift_query(self, query: str, limit: int = 10) -> Dict:
        """Text search"""
        try:
            items = await self.vector_store.search_related_items(query, limit)
            if not items:
                return {'query': query, 'bundles': [], 'error': 'No items found'}
            
            valid_items, _ = validate_items(items)
            result = await self.bundle_service.generate_bundles(query, valid_items)
            
            return result
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {'query': query, 'bundles': [], 'error': str(e)}

# ========================================================================
# HELPER FUNCTIONS
# ========================================================================
def extract_json_from_response(text: str) -> Dict:
    """Extract JSON from LLM response"""
    if '```json' in text:
        text = text.split('```json')[1].split('```')[0]
    elif '```' in text:
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        text = json_match.group(0)
    
    try:
        return json.loads(text.strip())
    except:
        return {"raw_response": text}

async def call_vision_direct(image_bytes: bytes, prompt: str) -> Dict:
    """Direct vision call - used by all vision endpoints"""
    if not vision_client or not vision_client.gemini_model:
        raise HTTPException(503, "Vision AI not configured")
    
    try:
        response = await vision_client.analyze_image(image_bytes, prompt)
        return extract_json_from_response(response)
    except Exception as e:
        logger.error(f"Vision call failed: {e}")
        raise HTTPException(500, str(e))

# ========================================================================
# PYDANTIC MODELS
# ========================================================================
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
# LIFECYCLE
# ========================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator, vision_client
    
    logger.info("🚀 Starting Unified Gift AI Service...")
    
    try:
        # Initialize vision client
        vision_client = VisionAIClient()
        
        # Initialize orchestrator
        orchestrator = GiftOrchestrator()
        await orchestrator.vector_store.connect()
        
        logger.info("✅ Service initialized")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        traceback.print_exc()
    
    yield
    
    if orchestrator:
        await orchestrator.vector_store.close()

# ========================================================================
# FASTAPI APP
# ========================================================================
app = FastAPI(
    title="Unified Gift AI Service",
    version="4.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================================================
# CORE ENDPOINTS
# ========================================================================

@app.get("/")
async def root():
    return {
        "service": "unified-gift-ai",
        "version": "4.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "components": {
            "orchestrator": orchestrator is not None,
            "vision_ai": vision_client is not None and vision_client.gemini_model is not None,
            "gemini_configured": bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))
        }
    }

# ========================================================================
# GIFT AI ENDPOINTS
# ========================================================================

@app.post("/generate_gift_bundle", response_model=ImageBundleResponse)
async def generate_gift_bundle(image: UploadFile = File(...)):
    """Image → Gift Bundles"""
    if not orchestrator:
        raise HTTPException(503, "Service not initialized")
    
    try:
        image_bytes = await image.read()
        if len(image_bytes) > 5 * 1024 * 1024:
            raise HTTPException(400, "Image too large (max 5MB)")
        
        result = await orchestrator.generate_bundle(image_bytes, image.filename)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bundle generation failed: {e}")
        raise HTTPException(500, str(e))

@app.post("/search_similar_gifts", response_model=TextSearchResponse)
async def search_similar_gifts(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50)
):
    """Text Search → Bundles"""
    if not orchestrator:
        raise HTTPException(503, "Service not initialized")
    
    try:
        result = await orchestrator.process_gift_query(query, limit)
        return result
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(500, str(e))

@app.get("/search", response_model=TextSearchResponse)
async def search_alias(query: str = Query(...), limit: int = Query(10)):
    """Alias for search_similar_gifts"""
    return await search_similar_gifts(query, limit)

@app.post("/refresh_vector_store")
async def refresh_vector_store():
    """Refresh Vector Store"""
    if not orchestrator:
        raise HTTPException(503, "Service not initialized")
    
    result = await orchestrator.refresh_vector_store()
    if result.get("success"):
        return {"success": True, "items_count": result.get("items_count", 0)}
    else:
        raise HTTPException(500, result.get("error", "Unknown error"))

# ========================================================================
# VISION AI ENDPOINTS (All Direct - No HTTP)
# ========================================================================

@app.post("/analyze_craft")
async def analyze_craft(image: UploadFile = File(...)):
    """Detect craft type"""
    image_bytes = await image.read()
    
    prompt = """Analyze craft type. Return ONLY JSON:
{"craft_type": "pottery|textile|metalwork|painting|other", "confidence": 0.0-1.0, "details": "brief description"}"""
    
    result = await call_vision_direct(image_bytes, prompt)
    result.setdefault('craft_type', 'unknown')
    return result

@app.post("/analyze_quality")
async def analyze_quality(image: UploadFile = File(...)):
    """Assess quality"""
    image_bytes = await image.read()
    
    prompt = """Analyze quality. Return ONLY JSON:
{"quality": "high|medium|low", "craftsmanship_score": 0.0-1.0, "details": "description"}"""
    
    result = await call_vision_direct(image_bytes, prompt)
    result.setdefault('quality', 'medium')
    return result

@app.post("/estimate_price")
async def estimate_price(image: UploadFile = File(...)):
    """Estimate price"""
    image_bytes = await image.read()
    
    prompt = """Estimate price in INR. Return ONLY JSON:
{"price_range_inr": "500-1500", "estimated_price": 1000, "factors": ["list"]}"""
    
    result = await call_vision_direct(image_bytes, prompt)
    result.setdefault('estimated_price', 1000)
    return result

@app.post("/detect_fraud")
async def detect_fraud(image: UploadFile = File(...)):
    """Detect fraud"""
    image_bytes = await image.read()
    
    prompt = """Detect fraud indicators. Return ONLY JSON:
{"fraud_score": 0.0-1.0, "is_suspicious": false, "red_flags": []}"""
    
    result = await call_vision_direct(image_bytes, prompt)
    result.setdefault('fraud_score', 0.0)
    return result

@app.post("/suggest_packaging")
async def suggest_packaging(image: UploadFile = File(...)):
    """Suggest packaging"""
    image_bytes = await image.read()
    
    prompt = """Recommend packaging. Return ONLY JSON:
{"packaging": "description", "cost": 100, "materials": []}"""
    
    result = await call_vision_direct(image_bytes, prompt)
    result.setdefault('packaging', 'eco-friendly box')
    return result

@app.post("/detect_material")
async def detect_material(image: UploadFile = File(...)):
    """Identify materials"""
    image_bytes = await image.read()
    
    prompt = """Identify materials. Return ONLY JSON:
{"material": "primary material", "purity": 0.8, "additional_materials": []}"""
    
    result = await call_vision_direct(image_bytes, prompt)
    result.setdefault('material', 'mixed')
    return result

@app.post("/analyze_sentiment")
async def analyze_sentiment(image: UploadFile = File(...)):
    """Analyze sentiment"""
    image_bytes = await image.read()
    
    prompt = """Analyze sentiment. Return ONLY JSON:
{"sentiment": "warm|elegant|playful", "emotion": "joyful|peaceful", "appeal_score": 0.0-1.0}"""
    
    result = await call_vision_direct(image_bytes, prompt)
    result.setdefault('sentiment', 'warm')
    return result

@app.post("/detect_occasion")
async def detect_occasion(image: UploadFile = File(...)):
    """Detect occasion"""
    image_bytes = await image.read()
    
    prompt = """Detect suitable occasions. Return ONLY JSON:
{"occasion": "birthday|wedding|general", "confidence": 0.7, "suitable_occasions": []}"""
    
    result = await call_vision_direct(image_bytes, prompt)
    result.setdefault('occasion', 'general')
    return result

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