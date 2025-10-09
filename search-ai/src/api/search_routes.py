# api/search_routes.py
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from src.services.search_service import index_item, search_items, get_collection_stats
from src.services.embedding_service import embedding_service
from src.config.settings import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["Search"])


# Pydantic models for request validation
class IndexRequest(BaseModel):
    id: str = Field(..., description="Unique identifier for the item")
    text: str = Field(..., min_length=1, description="Text content to index")
    payload: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    @validator('text')
    def text_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Text cannot be empty or whitespace only')
        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "id": "pottery-001",
                "text": "blue pottery bowl handcrafted ceramic kitchen",
                "payload": {
                    "title": "Blue Ceramic Bowl",
                    "category": "pottery",
                    "material": "ceramic",
                    "price": 29.99,
                    "brand": "Artisan Crafts"
                }
            }
        }


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(5, ge=1, le=50, description="Maximum number of results to return")
    expand: bool = Field(True, description="Whether to use query expansion")
    use_reranker: bool = Field(True, description="Whether to apply LLM reranking")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filters to apply")
    score_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    
    @validator('query')
    def query_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty or whitespace only')
        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "query": "blue kitchen pottery",
                "limit": 10,
                "expand": True,
                "use_reranker": True,
                "filters": {
                    "category": "pottery",
                    "material": ["ceramic", "clay"]
                },
                "score_threshold": 0.7
            }
        }


class IndexResponse(BaseModel):
    status: str
    id: str
    message: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[Dict[str, Any]]
    filters_applied: Optional[Dict[str, Any]]
    processing_time_ms: Optional[float] = None


# Routes
@router.post("/index", response_model=IndexResponse)
def index_route(request: IndexRequest):
    """
    Index a new item for search.
    
    This endpoint adds or updates an item in the search index with the provided
    text content and metadata payload.
    """
    try:
        logger.info(f"Indexing item: {request.id}")
        
        result = index_item(
            item_id=request.id,
            text=request.text,
            payload=request.payload
        )
        
        return IndexResponse(
            status=result["status"],
            id=str(result["id"]),
            message="Item successfully indexed"
        )
        
    except Exception as e:
        logger.error(f"Error indexing item {request.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to index item: {str(e)}"
        )


@router.post("/", response_model=SearchResponse)
def search_route(request: SearchRequest):
    """
    Search for items using semantic similarity and optional filters.
    
    This endpoint performs intelligent search using:
    - Semantic similarity matching
    - Optional query expansion
    - Metadata filtering
    - LLM-based reranking
    - Fallback keyword matching
    """
    try:
        import time
        start_time = time.time()
        
        logger.info(f"Searching for: '{request.query}' with limit {request.limit}")
        
        results = search_items(
            query=request.query,
            limit=request.limit,
            use_expansion=request.expand,
            use_reranker=request.use_reranker,
            filters=request.filters,
            score_threshold=request.score_threshold
        )
        
        processing_time = round((time.time() - start_time) * 1000, 2)
        
        return SearchResponse(
            query=request.query,
            total_results=len(results),
            results=results,
            filters_applied=request.filters,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error searching for '{request.query}': {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/")
def search_get_route(
    q: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=50, description="Maximum results"),
    expand: bool = Query(True, description="Use query expansion"),
    rerank: bool = Query(True, description="Apply LLM reranking"),
    threshold: float = Query(0.7, ge=0.0, le=1.0, description="Score threshold"),
    category: Optional[str] = Query(None, description="Filter by category"),
    material: Optional[str] = Query(None, description="Filter by material")
):
    """
    Search endpoint with GET method for simple queries.
    
    Convenient for direct URL-based searches with basic filtering.
    """
    try:
        # Build filters from query parameters
        filters = {}
        if category:
            filters["category"] = category
        if material:
            filters["material"] = material
            
        filters = filters if filters else None
        
        results = search_items(
            query=q,
            limit=limit,
            use_expansion=expand,
            use_reranker=rerank,
            filters=filters,
            score_threshold=threshold
        )
        
        return {
            "query": q,
            "total_results": len(results),
            "results": results,
            "filters_applied": filters
        }
        
    except Exception as e:
        logger.error(f"Error in GET search for '{q}': {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.delete("/index/{item_id}")
def delete_item(item_id: str):
    """Delete an item from the search index."""
    try:
        from src.database.qdrant_client import qdrant
        from src.config.settings import settings
        
        # Convert to UUID format if needed
        import uuid
        try:
            point_id = str(uuid.UUID(item_id))
        except ValueError:
            point_id = item_id
            
        result = qdrant.delete(
            collection_name=settings.COLLECTION_NAME,
            points_selector=[point_id]
        )
        
        return {
            "status": "deleted",
            "id": item_id,
            "message": "Item removed from search index"
        }
        
    except Exception as e:
        logger.error(f"Error deleting item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete item: {str(e)}"
        )


@router.get("/stats")
def collection_stats():
    """Get collection statistics and health information."""
    try:
        stats = get_collection_stats()
        return {
            "collection_name": settings.COLLECTION_NAME,  # from settings
            "stats": stats,
            "status": "healthy" if "error" not in stats else "error"
        }
        
    except Exception as e:
        logger.error(f"Error getting collection stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.get("/health")
def health_check():
    """Simple health check endpoint."""
    try:
        # Quick test to ensure Qdrant connection works
        from src.database.qdrant_client import qdrant
        from src.config.settings import settings
        
        collections = qdrant.get_collections()
        
        return {
            "status": "healthy",
            "service": "search-ai",
            "qdrant_connected": True,
            "collections_available": len(collections.collections)
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "search-ai",
            "qdrant_connected": False,
            "error": str(e)
        }
    
@router.get("/embedding/status")
def get_embedding_status():
    """Check embedding provider status and statistics"""
    try:
        provider_info = embedding_service.get_provider_info()
        stats = embedding_service.get_stats()
        
        return {
            "status": "ok",
            "current_provider": provider_info["current_provider"],
            "gemini_available": provider_info["gemini_available"],
            "ollama_available": provider_info.get("ollama_available", False),
            "fallback_active": provider_info["fallback_active"],
            "stats": stats,
            "cooldown_remaining_seconds": provider_info.get("cooldown_remaining", 0)
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/embedding/test")
def test_embedding_providers(
    text: str = Query("test embedding"),
    provider: str = Query("auto")
):
    try:
        embedding = None
        actual_provider = provider
        
        if provider == "gemini":
            embedding = embedding_service.force_gemini(text)
            actual_provider = "gemini"
        elif provider == "ollama":
            embedding = embedding_service.force_ollama(text)
            actual_provider = "ollama"
        else:  # auto
            embedding = embedding_service.get_embedding(text)
            # Get the actual provider used
            provider_info = embedding_service.get_provider_info()
            actual_provider = provider_info["current_provider"]
        
        return {
            "status": "success" if embedding else "failed",
            "provider_used": actual_provider,
            "embedding_dimensions": len(embedding) if embedding else 0,
            "text_tested": text,
            "embedding_preview": embedding[:5] if embedding else None
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}