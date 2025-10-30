# gift_ai_service/core/vector_store.py
"""
Unified Vector Store: Member B's embedding logic + Member A's async structure
- Real embedding generation (Gemini → Ollama → Simple fallback)
- Async MongoDB operations
- Qdrant vector search
FIXED: Removed mock data fallback - always use real MongoDB
"""

import logging
import uuid
import requests
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from core.config import settings

logger = logging.getLogger(__name__)

class VectorStore:
    """Unified vector store with real embeddings and async operations"""
    
    def __init__(self):
        # MongoDB (async)
        self.mongo_client = None
        self.mongo_db = None
        self.mongo_collection = None
        
        # Qdrant
        self.qdrant_client = None
        self.collection_name = settings.COLLECTION_NAME
        
        # Embedding config
        self.google_api_key = settings.GOOGLE_API_KEY
        self.genai = None
        self.ollama_available = False
        
        logger.info(f"VectorStore initialized with collection: {self.collection_name}")

    async def connect(self):
        """Connect to MongoDB and Qdrant"""
        # MongoDB connection
        try:
            self.mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
            self.mongo_db = self.mongo_client[settings.DATABASE_NAME]
            self.mongo_collection = self.mongo_db[settings.COLLECTION_NAME]
            logger.info(f"✅ MongoDB connected: {settings.DATABASE_NAME}.{settings.COLLECTION_NAME}")
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise Exception(f"MongoDB connection required but failed: {e}")

        # Qdrant connection
        try:
            if settings.QDRANT_URL and settings.QDRANT_API_KEY:
                self.qdrant_client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY
                )
                logger.info("✅ Qdrant connected")
            else:
                logger.warning("⚠️ Qdrant not configured - checking if using local instance")
                # Try local Qdrant without API key
                try:
                    self.qdrant_client = QdrantClient(url=settings.QDRANT_URL)
                    # Test the connection
                    self.qdrant_client.get_collections()
                    logger.info("✅ Qdrant connected (local instance)")
                except Exception as e:
                    logger.error(f"❌ Qdrant connection failed: {e}")
                    raise Exception(f"Qdrant connection required but failed: {e}")
        except Exception as e:
            logger.error(f"❌ Qdrant connection failed: {e}")
            raise Exception(f"Qdrant connection required but failed: {e}")
            
        # Initialize Gemini for embeddings
        if self.google_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.google_api_key)
                self.genai = genai
                logger.info("✅ Gemini embeddings configured")
            except ImportError:
                logger.warning("⚠️ google-generativeai not installed")
                
        # Test Ollama availability
        self.ollama_available = self._test_ollama_connection()

    def _test_ollama_connection(self) -> bool:
        """Test if Ollama is available at localhost:11434"""
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            if response.status_code == 200:
                logger.info("✅ Ollama available as fallback")
                return True
        except:
            logger.warning("⚠️ Ollama not available")
        return False

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embeddings with fallback chain:
        1. Gemini (768-dim, best quality)
        2. Ollama nomic-embed-text (768-dim, local)
        3. Simple TF-IDF-like (128-dim, always works)
        """
        # Try Gemini first
        if self.genai:
            try:
                result = self.genai.embed_content(
                    model='models/embedding-001',
                    content=text,
                    task_type="retrieval_document"
                )
                embedding = result['embedding']
                logger.debug("Generated embedding using Gemini")
                return embedding
            except Exception as e:
                logger.warning(f"Gemini embedding failed: {e}, trying Ollama...")
        
        # Fallback to Ollama
        if self.ollama_available:
            try:
                response = requests.post(
                    'http://localhost:11434/api/embeddings',
                    json={'model': 'nomic-embed-text', 'prompt': text},
                    timeout=30
                )
                if response.status_code == 200:
                    embedding = response.json()['embedding']
                    logger.debug("Generated embedding using Ollama")
                    return embedding
            except Exception as e:
                logger.warning(f"Ollama embedding failed: {e}, using simple fallback...")
        
        # Final fallback: simple local embedding
        return self._generate_simple_embedding(text)

    def _generate_simple_embedding(self, text: str) -> List[float]:
        """
        Simple TF-IDF-like embedding (128-dim) for demo/fallback
        """
        text = text.lower()
        embedding = [0.0] * 128
        
        # Character-based features
        for i, char in enumerate(text[:128]):
            embedding[i] = (ord(char) % 100) / 100.0
        
        # Keyword-based features
        keywords = {
            'art': 0.1, 'painting': 0.2, 'decorative': 0.3, 'home': 0.4,
            'office': 0.5, 'gift': 0.6, 'diwali': 0.7, 'family': 0.8,
            'birthday': 0.9, 'anniversary': 1.0, 'handmade': 0.15, 'craft': 0.25
        }
        
        for keyword, value in keywords.items():
            if keyword in text:
                embedding.append(value)
        
        # Normalize to 128-dim
        if len(embedding) < 128:
            embedding.extend([0.0] * (128 - len(embedding)))
        else:
            embedding = embedding[:128]
        
        logger.debug("Generated simple fallback embedding")
        return embedding

    async def close(self):
        """Close MongoDB connection"""
        if self.mongo_client:
            self.mongo_client.close()
            logger.info("MongoDB connection closed")

    async def get_mongo_items(self, limit: int = 100) -> List[Dict]:
        """
        Fetch items from MongoDB asynchronously
        FIXED: Removed mock data fallback - raises error if MongoDB not connected
        """
        if self.mongo_collection is None:
            error_msg = "MongoDB not connected - cannot fetch items"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        try:
            # Query for published artworks only
            cursor = self.mongo_collection.find(
                {
                    "status": "published",
                    "title": {"$exists": True},
                    "description": {"$exists": True}
                }
            ).limit(limit)
            
            items = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                # Ensure required fields
                doc.setdefault('title', 'Unknown Item')
                doc.setdefault('description', 'No description')
                doc.setdefault('category', 'General')
                doc.setdefault('price', 0)
                items.append(doc)
            
            logger.info(f"📦 Retrieved {len(items)} published artworks from MongoDB")
            
            if len(items) == 0:
                logger.warning("⚠️ No published artworks found in MongoDB!")
                logger.warning("   Please create some artworks with status='published'")
            
            return items
            
        except Exception as e:
            logger.error(f"❌ Error fetching MongoDB items: {e}")
            raise

    async def setup_collection(self, collection_name: str = None) -> bool:
        """Create Qdrant collection if it doesn't exist"""
        if self.qdrant_client is None:
            error_msg = "Qdrant not connected - cannot setup collection"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
            
        collection_name = collection_name or self.collection_name
        
        try:
            # Check if exists
            collections = self.qdrant_client.get_collections()
            exists = any(col.name == collection_name for col in collections.collections)
            
            if exists:
                logger.info(f"✅ Collection '{collection_name}' already exists")
                return True
            
            # Create new collection (768-dim for Gemini/Ollama, auto-pads if needed)
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
            logger.info(f"✅ Created Qdrant collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Collection setup failed: {e}")
            raise

    async def upload_items(self, items: List[Dict], collection_name: str = None) -> bool:
        """Upload items to Qdrant with real embeddings"""
        if self.qdrant_client is None:
            error_msg = "Qdrant not connected - cannot upload items"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
            
        if not items:
            logger.warning("⚠️ No items to upload")
            return False
            
        collection_name = collection_name or self.collection_name
        
        try:
            points = []
            for index, item in enumerate(items):
                # Generate embedding from title + description
                text = f"{item.get('title', '')} {item.get('description', '')}"
                embedding = self.generate_embedding(text)
                
                if not embedding:
                    logger.warning(f"⚠️ Skipping item {index}: no embedding generated")
                    continue
                
                # Pad/truncate to 768-dim (Qdrant collection size)
                if len(embedding) > 768:
                    embedding = embedding[:768]
                elif len(embedding) < 768:
                    embedding.extend([0.0] * (768 - len(embedding)))
                
                # Create point
                point_id = index + 1  # Simple sequential ID
                point = PointStruct(
                    id=point_id,
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
                logger.debug(f"  ✓ Prepared: {item.get('title', 'Unknown')}")
            
            if points:
                self.qdrant_client.upsert(collection_name=collection_name, points=points)
                logger.info(f"✅ Uploaded {len(points)} items to Qdrant")
                return True
            else:
                logger.warning("⚠️ No valid points to upload")
                return False
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def search_related_items(self, text: str, collection_name: str = None, limit: int = 10) -> List[Dict]:
        """
        Search Qdrant for similar items
        FIXED: Removed mock data fallback - raises error if Qdrant not connected
        """
        if self.qdrant_client is None:
            error_msg = "Qdrant not connected - cannot search"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
            
        collection_name = collection_name or self.collection_name
        
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(text)
            if not query_embedding:
                logger.error("❌ Failed to generate query embedding")
                return []
            
            # Pad/truncate to 768-dim
            if len(query_embedding) > 768:
                query_embedding = query_embedding[:768]
            elif len(query_embedding) < 768:
                query_embedding.extend([0.0] * (768 - len(query_embedding)))
            
            # Search Qdrant
            results = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit
            )
            
            # Format results
            items = []
            for result in results:
                items.append({
                    'id': str(result.id),
                    'title': result.payload.get('title', ''),
                    'description': result.payload.get('description', ''),
                    'category': result.payload.get('category', ''),
                    'price': result.payload.get('price', 0),
                    'score': result.score,
                    'mongo_id': result.payload.get('mongo_id', '')
                })
            
            logger.info(f"🔍 Found {len(items)} similar items for query: '{text}'")
            return items
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            import traceback
            traceback.print_exc()
            raise