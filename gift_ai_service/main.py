"""
main.py — Gift AI Service
-------------------------
This FastAPI microservice powers the AI-driven gift bundle generation feature.

Responsibilities:
- Extract intent from user queries (occasion, recipient, budget, etc.)
- Retrieve relevant products from MongoDB + Qdrant hybrid vector store
- Use LLM to generate creative gift bundle suggestions
- Validate and return final ranked bundles to the Node backend

Environment variables are loaded from `.env`.
"""

import os
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional, List

# --- Load environment variables early ---
load_dotenv()

# --- Core imports ---
from core.orchestrator import GiftOrchestrator
from core.llm_client import LLMClient
from core.vector_store import QdrantMongoVectorStore

# --- Initialize FastAPI app ---
app = FastAPI(
    title="Gift AI Service",
    version="1.0.0",
    description="GenAI-powered service for intelligent gift recommendations and bundle generation."
)

# --- Enable CORS for integration with Node.js backend ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to backend domain in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------------
# 📘 Pydantic Models for Request Validation
# -------------------------------------------------------------------------

class BundleRequest(BaseModel):
    query: str = Field(..., example="Gift for parents for Diwali under 3000")
    user_id: Optional[str] = Field(None, example="653f12ab9f...")

class ArtworkIndexRequest(BaseModel):
    _id: str = Field(..., example="653f12ab9f...")
    title: str = Field(..., example="Handmade Clay Lamp")
    description: str = Field(..., example="Beautiful Diwali diya handcrafted from clay")
    tags: List[str] = Field(default_factory=list, example=["diwali", "decor", "lamp"])

# -------------------------------------------------------------------------
# 🚀 FastAPI Lifecycle Events (for safe dependency initialization)
# -------------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    """Initialize all dependencies at startup."""
    try:
        print("[Startup] Initializing LLM client and vector store...")

        app.state.llm_client = LLMClient(api_key=os.getenv("OPENAI_API_KEY"))

        app.state.vector_store = QdrantMongoVectorStore(
            MONGO_URI=os.getenv("MONGO_URI"),
            MONGO_DB=os.getenv("MONGO_DB", "test"),
            MONGO_COLLECTION=os.getenv("MONGO_COLLECTION", "artworks"),
            QDRANT_URL=os.getenv("QDRANT_URL", "http://localhost:6333"),
            QDRANT_API_KEY=os.getenv("QDRANT_API_KEY")
        )

        app.state.orchestrator = GiftOrchestrator(
            app.state.llm_client,
            app.state.vector_store
        )

        print("[Startup] Gift AI Service initialized successfully ✅")

    except Exception as e:
        print(f"[Startup Error] {traceback.format_exc()}")
        raise RuntimeError(f"Failed to initialize service: {str(e)}")

# -------------------------------------------------------------------------
# 🩺 Health Check
# -------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "Gift AI", "version": "1.0.0"}

# -------------------------------------------------------------------------
# 🎁 Generate Gift Bundle
# -------------------------------------------------------------------------

@app.post("/generate_gift_bundle")
async def generate_gift_bundle(request: BundleRequest):
    """
    Generate curated gift bundles based on user's natural language query.

    Example Input:
    {
        "query": "I want a Diwali gift for my parents under 3000"
    }

    Output:
    {
        "success": true,
        "result": [
            {
                "bundle_name": "Diwali Family Delight",
                "items": [...],
                "total_price": 2750,
                "explanation": "Perfect for parents celebrating Diwali together..."
            },
            ...
        ]
    }
    """
    orchestrator = app.state.orchestrator

    try:
        result = await orchestrator.generate_bundle_pipeline(request.query, request.user_id)
        return {"success": True, "result": result}
    except Exception as e:
        print(f"[ERROR] Gift bundle generation failed:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Gift bundle pipeline failed. See logs for details.")

# -------------------------------------------------------------------------
# 🧩 Index Artwork
# -------------------------------------------------------------------------

@app.post("/index_artwork")
async def index_artwork(request: ArtworkIndexRequest):
    """
    Index a single artwork into the hybrid MongoDB + Qdrant vector store.

    Usually called by Node backend after new artwork creation.
    """
    llm_client = app.state.llm_client
    vector_store = app.state.vector_store

    try:
        await vector_store.index_artwork(request.dict(), llm_client)
        return {"success": True, "message": f"Artwork '{request.title}' indexed successfully."}
    except Exception as e:
        print(f"[ERROR] Artwork indexing failed:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Artwork indexing failed. See logs for details.")

# -------------------------------------------------------------------------
# 🔄 Admin Utility: Reindex All Artworks (Optional)
# -------------------------------------------------------------------------

@app.post("/reindex_all_artworks")
async def reindex_all_artworks():
    """
    Reindex all artworks from MongoDB into Qdrant.
    Use only for testing or admin purposes.
    """
    llm_client = app.state.llm_client
    vector_store = app.state.vector_store

    try:
        all_docs = list(vector_store.mongo_collection.find({}))
        for doc in all_docs:
            await vector_store.index_artwork(doc, llm_client)
        return {"success": True, "message": f"Reindexed {len(all_docs)} artworks."}
    except Exception as e:
        print(f"[ERROR] Reindex failed:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Reindexing failed. See logs for details.")

# -------------------------------------------------------------------------
# ▶️ Run Locally with Uvicorn
# -------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8001)),
        reload=True
    )
