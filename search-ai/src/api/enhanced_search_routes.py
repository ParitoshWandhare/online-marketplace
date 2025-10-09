# api/enhanced_search_routes.py
"""
Enhanced search routes that add cultural intelligence to existing search API
These routes extend the functionality without breaking backward compatibility
"""

from fastapi import APIRouter, HTTPException, Query, Body, BackgroundTasks
from typing import Dict, List, Optional, Any
import asyncio
import logging
import time

from src.models.cultural_models import (
    EnhancedSearchRequest, EnhancedSearchResponse, CulturalSearchFilters,
    CulturalAnalysisRequest, CulturalAnalysisResponse,
    QueryEnhancementRequest, QueryEnhancementResponse,
    CraftType, IndianRegion, Festival, CulturalSignificance
)
from src.services.enhanced_search_service import enhanced_search_service
from src.services.cultural_service import cultural_service
from src.config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["Enhanced Search"])

# Cultural Search Endpoints

@router.post("/cultural", response_model=EnhancedSearchResponse)
async def cultural_search(request: EnhancedSearchRequest):
    """
    Enhanced search with cultural intelligence
    
    This endpoint performs intelligent search with:
    - Cultural context analysis
    - Regional craft awareness  
    - Festival/seasonal relevance
    - Traditional technique recognition
    - Cultural similarity scoring
    """
    try:
        logger.info(f"Cultural search for: '{request.query}' with cultural analysis: {request.enable_cultural_analysis}")
        
        response = await enhanced_search_service.search_with_cultural_intelligence(request)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in cultural search: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Cultural search failed: {str(e)}"
        )

@router.get("/cultural")
async def cultural_search_get(
    q: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=50, description="Maximum results"),
    expand: bool = Query(True, description="Use query expansion"),
    rerank: bool = Query(True, description="Apply LLM reranking"),
    threshold: float = Query(0.7, ge=0.0, le=1.0, description="Score threshold"),
    
    # Cultural parameters
    enable_cultural: bool = Query(True, description="Enable cultural analysis"),
    cultural_boost: float = Query(1.0, ge=0.0, le=2.0, description="Cultural context boost"),
    seasonal_boost: bool = Query(True, description="Apply seasonal/festival boost"),
    
    # Cultural filters
    craft_types: Optional[str] = Query(None, description="Comma-separated craft types"),
    regions: Optional[str] = Query(None, description="Comma-separated regions"),
    festivals: Optional[str] = Query(None, description="Comma-separated festivals"),
    materials: Optional[str] = Query(None, description="Comma-separated materials"),
    
    # Regional preference
    regional_preference: Optional[str] = Query(None, description="Preferred region")
):
    """
    GET endpoint for cultural search with query parameters
    """
    try:
        # Build cultural filters
        cultural_filters = None
        if any([craft_types, regions, festivals, materials]):
            cultural_filters = CulturalSearchFilters()
            
            if craft_types:
                cultural_filters.craft_types = [
                    CraftType(ct.strip()) for ct in craft_types.split(',')
                    if ct.strip() in CraftType.__members__.values()
                ]
            
            if regions:
                cultural_filters.regions = [
                    IndianRegion(r.strip()) for r in regions.split(',')
                    if r.strip() in IndianRegion.__members__.values()
                ]
            
            if festivals:
                cultural_filters.festivals = [
                    Festival(f.strip()) for f in festivals.split(',')
                    if f.strip() in Festival.__members__.values()
                ]
            
            if materials:
                cultural_filters.materials = [m.strip() for m in materials.split(',')]
        
        # Build request
        request = EnhancedSearchRequest(
            query=q,
            limit=limit,
            expand=expand,
            use_reranker=rerank,
            score_threshold=threshold,
            cultural_filters=cultural_filters,
            cultural_context_boost=cultural_boost,
            enable_cultural_analysis=enable_cultural,
            seasonal_boost=seasonal_boost,
            regional_preference=IndianRegion(regional_preference) if regional_preference else None
        )
        
        response = await enhanced_search_service.search_with_cultural_intelligence(request)
        
        return response
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(ve)}")
    except Exception as e:
        logger.error(f"Error in GET cultural search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# Cultural Analysis Endpoints

@router.post("/analyze", response_model=CulturalAnalysisResponse)
async def analyze_cultural_context(request: CulturalAnalysisRequest):
    """
    Analyze artwork/product for cultural context
    
    This endpoint analyzes text content to detect:
    - Craft type (pottery, textiles, etc.)
    - Regional origin and style
    - Cultural significance
    - Festival relevance
    - Traditional materials and techniques
    """
    try:
        logger.info(f"Cultural analysis for: '{request.title}'")
        
        response = await cultural_service.analyze_artwork_cultural_context(request)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in cultural analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Cultural analysis failed: {str(e)}"
        )

@router.post("/enhance-query", response_model=QueryEnhancementResponse)
async def enhance_query_cultural_context(request: QueryEnhancementRequest):
    """
    Enhance search query with cultural context
    
    This endpoint analyzes a search query to:
    - Detect cultural intent and context
    - Expand with related cultural terms
    - Generate additional search variations
    - Identify regional and festival relevance
    """
    try:
        logger.info(f"Query enhancement for: '{request.original_query}'")
        
        response = cultural_service.analyze_query_cultural_context(request)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in query enhancement: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Query enhancement failed: {str(e)}"
        )

# Enhanced Indexing Endpoints

@router.post("/index/cultural")
async def index_with_cultural_analysis(
    item_id: str = Body(...),
    text: str = Body(...),
    payload: Optional[Dict[str, Any]] = Body(None)
):
    """
    Index an item with automatic cultural analysis
    
    This endpoint indexes content and automatically:
    - Analyzes cultural context
    - Extracts craft type and regional information
    - Identifies festival relevance
    - Stores cultural metadata for enhanced search
    """
    try:
        logger.info(f"Cultural indexing for item: {item_id}")
        
        result = await enhanced_search_service.index_with_cultural_analysis(
            item_id=item_id,
            text=text,
            payload=payload
        )
        
        return {
            "status": "indexed",
            "id": result["id"],
            "message": "Item indexed with cultural analysis",
            "cultural_analysis_applied": True
        }
        
    except Exception as e:
        logger.error(f"Error in cultural indexing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Cultural indexing failed: {str(e)}"
        )

# Cultural Information Endpoints

@router.get("/cultural/categories")
async def get_cultural_categories():
    """
    Get all available cultural categories
    
    Returns lists of:
    - Craft types
    - Indian regions
    - Festivals
    - Cultural significance types
    """
    try:
        from src.utils.cultural_analyzer import CulturalKnowledgeBase
        knowledge_base = CulturalKnowledgeBase()
        
        categories = knowledge_base.get_cultural_categories()
        
        return {
            "categories": categories,
            "stats": knowledge_base.get_stats()
        }
        
    except Exception as e:
        logger.error(f"Error getting cultural categories: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cultural categories: {str(e)}"
        )

@router.get("/cultural/seasonal")
async def get_seasonal_context():
    """
    Get current seasonal/festival context
    
    Returns information about:
    - Current active festivals
    - Seasonal relevance
    - Recommended cultural boosts
    """
    try:
        seasonal_context = cultural_service.get_seasonal_context()
        
        return {
            "seasonal_context": seasonal_context,
            "recommendations": {
                "boost_seasonal_items": len(seasonal_context.get("active_festivals", [])) > 0,
                "suggested_searches": [
                    f"{festival} gifts" for festival in seasonal_context.get("active_festivals", [])[:3]
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting seasonal context: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get seasonal context: {str(e)}"
        )

# Statistics and Monitoring Endpoints

@router.get("/cultural/stats")
async def get_cultural_search_stats():
    """Get cultural search service statistics"""
    try:
        stats = enhanced_search_service.get_cultural_stats()
        
        return {
            "status": "ok",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting cultural stats: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/cultural/health")
async def cultural_search_health_check():
    """Health check for cultural search functionality"""
    try:
        health = enhanced_search_service.health_check()
        
        return health
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# Cache Management Endpoints

@router.delete("/cultural/cache")
async def clear_cultural_cache():
    """Clear cultural analysis cache"""
    try:
        enhanced_search_service.clear_cultural_cache()
        
        return {
            "status": "cache_cleared",
            "message": "Cultural analysis cache cleared successfully"
        }
        
    except Exception as e:
        logger.error(f"Error clearing cultural cache: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )

# Batch Processing Endpoints

@router.post("/cultural/batch-analyze")
async def batch_cultural_analysis(
    items: List[Dict[str, str]] = Body(...),
    background_tasks: BackgroundTasks = None
):
    """
    Batch analyze multiple items for cultural context
    
    Useful for analyzing existing inventory or bulk uploads
    """
    try:
        if len(items) > 100:  # Limit batch size
            raise HTTPException(
                status_code=400,
                detail="Batch size limited to 100 items"
            )
        
        results = []
        
        for item in items:
            try:
                request = CulturalAnalysisRequest(
                    title=item.get("title", ""),
                    description=item.get("description", "")
                )
                
                response = await cultural_service.analyze_artwork_cultural_context(request)
                
                results.append({
                    "item_id": item.get("id", "unknown"),
                    "cultural_context": response.cultural_context.dict(),
                    "confidence": response.cultural_context.confidence_score
                })
                
            except Exception as e:
                logger.warning(f"Failed to analyze item {item.get('id', 'unknown')}: {e}")
                results.append({
                    "item_id": item.get("id", "unknown"),
                    "error": str(e),
                    "cultural_context": None
                })
        
        return {
            "status": "completed",
            "total_items": len(items),
            "successful_analyses": len([r for r in results if "error" not in r]),
            "failed_analyses": len([r for r in results if "error" in r]),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in batch cultural analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch analysis failed: {str(e)}"
        )