# gift_ai_service/core/vector_store.py
"""
Vector Store using MongoDB + Qdrant
All async methods, fully compatible with orchestrator
"""

from motor.motor_asyncio import AsyncIOMotorClient
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from core.config import settings
import logging
import uuid

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.mongo_client = None
        self.mongo_db = None
        self.mongo_collection = None
        self.qdrant_client = None
        self.collection_name = settings.COLLECTION_NAME

    async def connect(self):
        """Connect to MongoDB and Qdrant"""
        try:
            self.mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
            self.mongo_db = self.mongo_client[settings.DATABASE_NAME]
            self.mongo_collection = self.mongo_db[settings.COLLECTION_NAME]
            logger.info(f"Connected to MongoDB: {settings.DATABASE_NAME}.{settings.COLLECTION_NAME}")
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")

        try:
            if settings.QDRANT_URL and settings.QDRANT_API_KEY:
                self.qdrant_client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY
                )
                logger.info("Connected to Qdrant")
            else:
                logger.warning("Qdrant not configured")
        except Exception as e:
            logger.error(f"Qdrant connection failed: {e}")

    async def close(self):
        if self.mongo_client:
            self.mongo_client.close()
            logger.info("MongoDB connection closed")

    async def get_mongo_items(self, limit: int = 100):
        """Fetch items from MongoDB asynchronously"""
        if not self.mongo_collection:
            return []
        try:
            cursor = self.mongo_collection.find().limit(limit)
            items = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                items.append(doc)
            return items
        except Exception as e:
            logger.error(f"Error fetching items: {e}")
            return []

    async def setup_collection(self) -> bool:
        """Create Qdrant collection"""
        if not self.qdrant_client:
            return False
        try:
            self.qdrant_client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
            logger.info(f"Qdrant collection '{self.collection_name}' created")
            return True
        except Exception as e:
            logger.error(f"Collection setup failed: {e}")
            return False

    async def upload_items(self, items):
        """Upload items to Qdrant"""
        if not self.qdrant_client or not items:
            return False
        try:
            points = []
            for item in items:
                point_id = str(uuid.uuid4())
                vector = item.get("embedding", [0.0] * 768)
                payload = {k: v for k, v in item.items() if k != "embedding"}
                points.append(PointStruct(id=point_id, vector=vector, payload=payload))
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            return True
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return False

    async def search_related_items(self, text: str, collection_name: str = None, limit: int = 10):
        """Search Qdrant"""
        if not self.qdrant_client:
            return []
        try:
            # Dummy embedding - replace with real one
            query_vector = [0.1] * 768
            results = self.qdrant_client.search(
                collection_name=collection_name or self.collection_name,
                query_vector=query_vector,
                limit=limit
            )
            return [hit.payload for hit in results]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []