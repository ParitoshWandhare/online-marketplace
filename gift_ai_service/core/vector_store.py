# gift_ai_service/core/vector_store.py
"""
Unified Vector Store: Member B's embedding logic + Member A's async structure
- Real embedding generation (Gemini → Ollama → Simple fallback)
- Async MongoDB operations
- Qdrant vector search
FIXED: Removed mock data fallback - always use real MongoDB
FIXED: Removed boolean truth-value check on Qdrant collection response objects
"""

import logging
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

        # ── MongoDB ──────────────────────────────────────────────────────────
        try:
            self.mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
            self.mongo_db = self.mongo_client[settings.DATABASE_NAME]
            self.mongo_collection = self.mongo_db[settings.COLLECTION_NAME]
            logger.info(
                f"✅ MongoDB connected: {settings.DATABASE_NAME}.{settings.COLLECTION_NAME}"
            )
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise Exception(f"MongoDB connection required but failed: {e}")

        # ── Qdrant ───────────────────────────────────────────────────────────
        try:
            if settings.QDRANT_URL and settings.QDRANT_API_KEY:
                self.qdrant_client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY,
                )
            else:
                # Try without API key (local instance)
                self.qdrant_client = QdrantClient(url=settings.QDRANT_URL)

            # ✅ FIX: test connection by fetching collection names as a list
            # Never do `if response:` — Qdrant objects don't support bool()
            collections_response = self.qdrant_client.get_collections()
            _ = [col.name for col in collections_response.collections]  # just validate
            logger.info("✅ Qdrant connected")

        except Exception as e:
            logger.error(f"❌ Qdrant connection failed: {e}")
            raise Exception(f"Qdrant connection required but failed: {e}")

        # ── Gemini embeddings ─────────────────────────────────────────────────
        if self.google_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.google_api_key)
                self.genai = genai
                logger.info("✅ Gemini embeddings configured")
            except ImportError:
                logger.warning("⚠️ google-generativeai not installed")

        # ── Ollama (optional local fallback) ──────────────────────────────────
        self.ollama_available = self._test_ollama_connection()

    # ─────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _test_ollama_connection(self) -> bool:
        """Test if Ollama is available at localhost:11434"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Ollama available as fallback")
                return True
        except Exception:
            logger.warning("⚠️ Ollama not available")
        return False

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embeddings with fallback chain:
        1. Gemini  (768-dim, best quality)
        2. Ollama  nomic-embed-text (768-dim, local)
        3. Simple  TF-IDF-like (128-dim padded to 768, always works)
        """
        # 1. Gemini
        if self.genai:
            try:
                result = self.genai.embed_content(
                    model="models/embedding-001",
                    content=text,
                    task_type="retrieval_document",
                )
                embedding = result["embedding"]
                logger.debug("Generated embedding using Gemini")
                return embedding
            except Exception as e:
                logger.warning(f"Gemini embedding failed: {e}, trying Ollama…")

        # 2. Ollama
        if self.ollama_available:
            try:
                response = requests.post(
                    "http://localhost:11434/api/embeddings",
                    json={"model": "nomic-embed-text", "prompt": text},
                    timeout=30,
                )
                if response.status_code == 200:
                    embedding = response.json()["embedding"]
                    logger.debug("Generated embedding using Ollama")
                    return embedding
            except Exception as e:
                logger.warning(f"Ollama embedding failed: {e}, using simple fallback…")

        # 3. Simple fallback
        return self._generate_simple_embedding(text)

    def _generate_simple_embedding(self, text: str) -> List[float]:
        """Simple character-based 768-dim fallback embedding"""
        text = text.lower()
        embedding = [0.0] * 128

        for i, char in enumerate(text[:128]):
            embedding[i] = (ord(char) % 100) / 100.0

        keywords = {
            "art": 0.1, "painting": 0.2, "decorative": 0.3, "home": 0.4,
            "office": 0.5, "gift": 0.6, "diwali": 0.7, "family": 0.8,
            "birthday": 0.9, "anniversary": 1.0, "handmade": 0.15, "craft": 0.25,
        }
        for keyword, value in keywords.items():
            if keyword in text:
                embedding.append(value)

        # Normalise to exactly 768 dims
        if len(embedding) < 768:
            embedding.extend([0.0] * (768 - len(embedding)))
        else:
            embedding = embedding[:768]

        logger.debug("Generated simple fallback embedding")
        return embedding

    # ─────────────────────────────────────────────────────────────────────────
    # Public async API
    # ─────────────────────────────────────────────────────────────────────────

    async def close(self):
        """Close MongoDB connection"""
        if self.mongo_client:
            self.mongo_client.close()
            logger.info("MongoDB connection closed")

    async def get_mongo_items(self, limit: int = 100) -> List[Dict]:
        """
        Fetch published items from MongoDB asynchronously.
        Raises if MongoDB is not connected.
        """
        if self.mongo_collection is None:
            raise Exception("MongoDB not connected - cannot fetch items")

        try:
            cursor = self.mongo_collection.find(
                {
                    "status": "published",
                    "title": {"$exists": True},
                    "description": {"$exists": True},
                }
            ).limit(limit)

            items: List[Dict] = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                doc.setdefault("title", "Unknown Item")
                doc.setdefault("description", "No description")
                doc.setdefault("category", "General")
                doc.setdefault("price", 0)
                items.append(doc)

            logger.info(f"📦 Retrieved {len(items)} published artworks from MongoDB")

            if not items:
                logger.warning(
                    "⚠️ No published artworks found in MongoDB! "
                    "Please create artworks with status='published'."
                )

            return items

        except Exception as e:
            logger.error(f"❌ Error fetching MongoDB items: {e}")
            raise

    async def setup_collection(self, collection_name: str = None) -> bool:
        """
        Create Qdrant collection if it does not already exist.

        ✅ FIX: Never evaluate the Qdrant response object as a boolean.
               Always extract .collections into a plain Python list first.
        """
        if self.qdrant_client is None:
            raise Exception("Qdrant not connected - cannot setup collection")

        collection_name = collection_name or self.collection_name

        try:
            # ✅ CORRECT: extract names into a plain list before any comparison
            collections_response = self.qdrant_client.get_collections()
            existing_names = [col.name for col in collections_response.collections]

            if collection_name not in existing_names:
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE),
                )
                logger.info(f"✅ Created Qdrant collection: {collection_name}")
            else:
                logger.info(f"✅ Collection '{collection_name}' already exists")

            return True

        except Exception as e:
            logger.error(f"❌ Collection setup failed: {e}")
            raise

    async def upload_items(
        self, items: List[Dict], collection_name: str = None
    ) -> bool:
        """Upload items to Qdrant with real embeddings."""
        if self.qdrant_client is None:
            raise Exception("Qdrant not connected - cannot upload items")

        if not items:
            logger.warning("⚠️ No items to upload")
            return False

        collection_name = collection_name or self.collection_name

        try:
            points: List[PointStruct] = []

            for index, item in enumerate(items):
                text = f"{item.get('title', '')} {item.get('description', '')}"
                embedding = self.generate_embedding(text)

                if not embedding:
                    logger.warning(f"⚠️ Skipping item {index}: no embedding generated")
                    continue

                # Normalise to 768-dim
                if len(embedding) > 768:
                    embedding = embedding[:768]
                elif len(embedding) < 768:
                    embedding.extend([0.0] * (768 - len(embedding)))

                points.append(
                    PointStruct(
                        id=index + 1,
                        vector=embedding,
                        payload={
                            "title": item.get("title", ""),
                            "description": item.get("description", ""),
                            "category": item.get("category", ""),
                            "price": item.get("price", 0),
                            "mongo_id": str(item.get("_id", "")),
                        },
                    )
                )
                logger.debug(f"  ✓ Prepared: {item.get('title', 'Unknown')}")

            if points:
                self.qdrant_client.upsert(
                    collection_name=collection_name, points=points
                )
                logger.info(f"✅ Uploaded {len(points)} items to Qdrant")
                return True

            logger.warning("⚠️ No valid points to upload")
            return False

        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def search_related_items(
        self,
        text: str,
        collection_name: str = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Search Qdrant for items similar to *text*."""
        if self.qdrant_client is None:
            raise Exception("Qdrant not connected - cannot search")

        collection_name = collection_name or self.collection_name

        try:
            query_embedding = self.generate_embedding(text)
            if not query_embedding:
                logger.error("❌ Failed to generate query embedding")
                return []

            # Normalise to 768-dim
            if len(query_embedding) > 768:
                query_embedding = query_embedding[:768]
            elif len(query_embedding) < 768:
                query_embedding.extend([0.0] * (768 - len(query_embedding)))

            results = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
            )

            items = [
                {
                    "id": str(r.id),
                    "title": r.payload.get("title", ""),
                    "description": r.payload.get("description", ""),
                    "category": r.payload.get("category", ""),
                    "price": r.payload.get("price", 0),
                    "score": r.score,
                    "mongo_id": r.payload.get("mongo_id", ""),
                }
                for r in results
            ]

            logger.info(f"🔍 Found {len(items)} similar items for query: '{text}'")
            return items

        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            import traceback
            traceback.print_exc()
            raise