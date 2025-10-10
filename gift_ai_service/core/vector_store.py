"""
Mongo + Qdrant Vector Store
---------------------------
Stores embeddings in Qdrant, artwork data in MongoDB.
Used by GiftRetrievalService to perform hybrid retrieval.
"""

from qdrant_client import QdrantClient, models
from pymongo import MongoClient
from bson import ObjectId
import asyncio

class QdrantMongoVectorStore:
    def __init__(self, MONGO_URI, MONGO_DB, MONGO_COLLECTION, QDRANT_URL, QDRANT_API_KEY=None):
        # MongoDB setup
        self.mongo_client = MongoClient(MONGO_URI)
        self.mongo_collection = self.mongo_client[MONGO_DB][MONGO_COLLECTION]

        # Qdrant setup
        self.qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        self.collection_name = "artworks"

        # Ensure Qdrant collection exists
        self._ensure_qdrant_collection()

    def _ensure_qdrant_collection(self):
        try:
            self.qdrant.get_collection(self.collection_name)
        except Exception:
            self.qdrant.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=1536,  # OpenAI embedding size
                    distance=models.Distance.COSINE
                )
            )

    async def index_artwork(self, doc, llm_client):
        """
        Generate embedding for artwork and store in Qdrant.
        """
        text = f"{doc.get('title', '')}. {doc.get('description', '')}. Tags: {', '.join(doc.get('tags', []))}"
        embedding = await llm_client.get_embedding(text)

        # Insert embedding into Qdrant
        self.qdrant.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=str(doc["_id"]),
                    vector=embedding,
                    payload={
                        "mongo_id": str(doc["_id"]),
                        "title": doc.get("title"),
                        "tags": doc.get("tags", [])
                    }
                )
            ]
        )

        # Optionally store the embedding in Mongo too
        self.mongo_collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"embedding_indexed": True}}
        )

    async def search(self, query_text, llm_client, top_k=5):
        """
        Search artworks similar to query text.
        Returns full MongoDB documents.
        """
        query_embedding = await llm_client.get_embedding(query_text)

        hits = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k
        )

        mongo_ids = [ObjectId(hit.payload["mongo_id"]) for hit in hits]
        results = list(self.mongo_collection.find({"_id": {"$in": mongo_ids}}))

        # Sort by Qdrant relevance order
        id_to_doc = {str(r["_id"]): r for r in results}
        ranked_results = [id_to_doc[hit.payload["mongo_id"]] for hit in hits if hit.payload["mongo_id"] in id_to_doc]
        return ranked_results
