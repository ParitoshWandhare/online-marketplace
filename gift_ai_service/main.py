"""
Main entry point for the Gift AI Service.
----------------------------------------
This FastAPI app coordinates:
- LLM interactions (via OpenAI)
- Hybrid vector retrieval (MongoDB + Qdrant)
- Gift bundle generation pipeline

Environment variables are loaded from `.env`.
"""

import os
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

# Load environment variables early
load_dotenv()

# --- Core imports ---
from core.orchestrator import GiftOrchestrator
from core.llm_client import LLMClient
from core.vector_store import QdrantMongoVectorStore

# --- Initialize FastAPI app ---
app = FastAPI(title="Gift AI Service", version="1.0.0")

# --- Initialize dependencies ---

try:
    #  Initialize LLM client
    llm_client = LLMClient(api_key=os.getenv("OPENAI_API_KEY"))

    #  Initialize Vector Store (MongoDB + Qdrant)
    vector_store = QdrantMongoVectorStore(
        mongo_uri=os.getenv("MONGO_URI"),
        mongo_db=os.getenv("MONGO_DB", "marketplaceDB"),
        mongo_collection=os.getenv("MONGO_COLLECTION", "artworks"),
        qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        qdrant_api_key=os.getenv("QDRANT_API_KEY")
    )

    #  Initialize Orchestrator
    orchestrator = GiftOrchestrator(llm_client, vector_store)

except Exception as e:
    raise RuntimeError(f"Initialization failed: {e}")

# --- API Routes ---

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "Gift AI", "version": "1.0.0"}


@app.post("/generate_gift_bundle")
async def generate_bundle(request: dict):
    """
    Generate a curated gift bundle based on user's query.

    Request JSON:
    {
        "query": "Gift for parents for Diwali under 3000",
        "user_id": "optional"
    }
    """
    query = request.get("query")
    user_id = request.get("user_id")

    if not query:
        raise HTTPException(status_code=400, detail="Missing required field: 'query'")

    try:
        result = await orchestrator.generate_bundle_pipeline(query, user_id)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@app.post("/index_artwork")
async def index_artwork(request: dict):
    """
    Index a single artwork into Qdrant + MongoDB vector store.
    Called by Node backend after a new artwork is created.

    Request JSON:
    {
        "_id": "...",
        "title": "Handmade Lamp",
        "description": "Clay Diya for Diwali",
        "tags": ["diwali", "decor"]
    }
    """
    try:
        await vector_store.index_artwork(request, llm_client)
        return {"success": True, "message": "Artwork indexed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing error: {str(e)}")


# --- Run with Uvicorn (only when directly executed) ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
