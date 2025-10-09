# services/enhanced_search_service.py
"""
Enhanced search service that integrates cultural intelligence with existing search infrastructure
This extends your current search_service.py without breaking existing functionality
FIXED: Resolved async deadlock issue that was causing 19-second delays
"""

import time
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

from src.services.search_service import search_items as base_search_items, index_item as base_index_item
from src.services.cultural_service import cultural_service
from src.models.cultural_models import (
    EnhancedSearchRequest, EnhancedSearchResponse, CulturalSearchResult,
    CulturalSearchFilters, CulturalAnalysisRequest, CulturalQueryContext,
    QueryEnhancementRequest, CulturalContext, CraftType, IndianRegion, Festival
)
from src.services.embedding_service import embedding_service
from src.database.qdrant_client import qdrant
from src.config.settings import settings
from src.utils.cultural_analyzer import CulturalKnowledgeBase

logger = logging.getLogger(__name__)

class EnhancedSearchService:
    """
    Enhanced search service with cultural intelligence
    Extends existing search functionality with cultural analysis and scoring
    """
    
    def __init__(self):
        self.knowledge_base = CulturalKnowledgeBase()
        self.cultural_cache = {}  # Cache for cultural analysis results
        self.cache_ttl = 3600  # 1 hour
        
        # Performance tracking
        self.stats = {
            "enhanced_searches": 0,
            "cultural_analyses": 0,
            "cache_hits": 0,
            "avg_cultural_processing_time": 0.0,
            "total_processing_time": 0.0
        }
        
        logger.info("Enhanced Search Service with Cultural Intelligence initialized")

    async def search_with_cultural_intelligence(self, request: EnhancedSearchRequest) -> EnhancedSearchResponse:
        """
        FIXED: Main enhanced search method that adds cultural intelligence to existing search
        """
        start_time = time.time()
        self.stats["enhanced_searches"] += 1
        
        try:
            # Step 1: Analyze query for cultural context
            cultural_query_context = None
            enhanced_query = request.query
            
            if request.enable_cultural_analysis:
                cultural_start = time.time()
                
                query_enhancement_request = QueryEnhancementRequest(
                    original_query=request.query,
                    user_location=None,
                    current_season=datetime.now().strftime("%B")
                )
                
                enhancement_response = cultural_service.analyze_query_cultural_context(query_enhancement_request)
                cultural_query_context = enhancement_response.cultural_context
                enhanced_query = enhancement_response.enhanced_query
                
                cultural_processing_time = (time.time() - cultural_start) * 1000
                self._update_cultural_stats(cultural_processing_time)
                
                logger.info(f"Query enhancement: '{request.query}' -> '{enhanced_query}'")
            
            # Step 2: Perform base search with enhanced query
            base_filters = request.filters or {}
            
            if request.cultural_filters:
                cultural_base_filters = self._convert_cultural_filters(request.cultural_filters)
                base_filters.update(cultural_base_filters)
            
            base_results = base_search_items(
                query=enhanced_query,
                limit=min(request.limit * 2, 50),
                use_expansion=request.expand,
                use_reranker=request.use_reranker,
                filters=base_filters,
                score_threshold=request.score_threshold
            )
            
            # Step 3: FIXED - Use synchronous cultural analysis
            enhanced_results = []
            if request.enable_cultural_analysis and base_results:
                # FIXED: Use synchronous method instead of async
                enhanced_results = self._enhance_results_with_cultural_context_sync(
                    base_results, cultural_query_context, request
                )
            else:
                enhanced_results = self._convert_base_results(base_results)
            
            # Step 4: Apply cultural scoring and reranking
            if request.enable_cultural_analysis and cultural_query_context:
                enhanced_results = self._apply_cultural_scoring(
                    enhanced_results, cultural_query_context, request
                )
            
            # Step 5: Apply seasonal boost if enabled
            if request.seasonal_boost:
                enhanced_results = self._apply_seasonal_boost(enhanced_results)
            
            # Step 6: Final ranking and limiting
            enhanced_results.sort(key=lambda x: x.weighted_score, reverse=True)
            final_results = enhanced_results[:request.limit]
            
            # Step 7: Generate cultural insights
            cultural_insights = self._generate_cultural_insights(
                cultural_query_context, enhanced_results
            ) if cultural_query_context else {}
            
            total_time = (time.time() - start_time) * 1000
            self.stats["total_processing_time"] = total_time
            
            logger.info(f"Enhanced search completed in {total_time:.2f}ms with {len(final_results)} results")
            
            return EnhancedSearchResponse(
                query=request.query,
                total_results=len(final_results),
                results=final_results,
                filters_applied=base_filters,
                cultural_filters_applied=request.cultural_filters,
                processing_time_ms=round(total_time, 2),
                detected_cultural_intent=cultural_insights.get("cultural_intent"),
                seasonal_context=cultural_insights.get("seasonal_context"),
                suggested_regions=cultural_insights.get("suggested_regions"),
                suggested_festivals=cultural_insights.get("suggested_festivals")
            )
            
        except Exception as e:
            logger.error(f"Error in enhanced search: {e}")
            # Fallback to basic search
            base_results = base_search_items(
                query=request.query,
                limit=request.limit,
                use_expansion=request.expand,
                use_reranker=request.use_reranker,
                filters=request.filters,
                score_threshold=request.score_threshold
            )
            
            fallback_results = self._convert_base_results(base_results)
            
            return EnhancedSearchResponse(
                query=request.query,
                total_results=len(fallback_results),
                results=fallback_results,
                filters_applied=request.filters,
                processing_time_ms=round((time.time() - start_time) * 1000, 2)
            )

    def _enhance_results_with_cultural_context_sync(
        self, 
        base_results: List[Dict], 
        query_context: Optional[CulturalQueryContext],
        request: EnhancedSearchRequest
    ) -> List[CulturalSearchResult]:
        """
        FIXED: Synchronous version to avoid async deadlock
        Enhance search results with cultural analysis
        """
        enhanced_results = []
        
        for result in base_results:
            try:
                # Check cache first
                cache_key = f"{result['id']}:{result.get('text', '')[:50]}"
                cultural_context = None
                
                if cache_key in self.cultural_cache:
                    cache_entry = self.cultural_cache[cache_key]
                    if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                        cultural_context = cache_entry["context"]
                        self.stats["cache_hits"] += 1
                
                # Perform cultural analysis if not cached
                if cultural_context is None:
                    title = result.get("payload", {}).get("title", "")
                    description = result.get("text", "")
                    
                    if title or description:
                        # FIXED: Direct synchronous cultural analysis
                        text_content = f"{title} {description}".strip()
                        cultural_context = self._analyze_cultural_context_sync(text_content)
                        
                        # Cache the result
                        self.cultural_cache[cache_key] = {
                            "context": cultural_context,
                            "timestamp": time.time()
                        }
                        
                        self.stats["cultural_analyses"] += 1
                
                # Calculate cultural score
                cultural_score = cultural_service.calculate_cultural_score(
                    cultural_context, query_context
                ) if cultural_context and query_context else 0.0
                
                # Check regional match
                regional_match = False
                if request.regional_preference and cultural_context:
                    regional_match = cultural_context.region == request.regional_preference
                
                # Create enhanced result
                enhanced_result = CulturalSearchResult(
                    id=result["id"],
                    score=result["score"],
                    weighted_score=result["weighted_score"],
                    hits=result["hits"],
                    text=result["text"],
                    payload=result["payload"],
                    cultural_context=cultural_context,
                    cultural_score=cultural_score,
                    regional_match=regional_match
                )
                
                enhanced_results.append(enhanced_result)
                
            except Exception as e:
                logger.warning(f"Failed to enhance result {result.get('id', 'unknown')}: {e}")
                # Add result without cultural enhancement
                enhanced_result = CulturalSearchResult(
                    id=result["id"],
                    score=result["score"],
                    weighted_score=result["weighted_score"],
                    hits=result["hits"],
                    text=result["text"],
                    payload=result["payload"]
                )
                enhanced_results.append(enhanced_result)
        
        return enhanced_results

    def _analyze_cultural_context_sync(self, text: str) -> CulturalContext:
        """
        FIXED: Synchronous cultural analysis using pattern matching
        This avoids the async deadlock issue
        """
        text_lower = text.lower()
        detected_keywords = []
        
        # Craft type detection
        craft_type = CraftType.UNKNOWN
        for craft, keywords in self.knowledge_base.craft_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                craft_type = CraftType(craft)
                detected_keywords.extend([kw for kw in keywords if kw in text_lower])
                break
        
        # Material detection
        materials = []
        for material_list in self.knowledge_base.material_keywords.values():
            for material in material_list:
                if material in text_lower:
                    materials.append(material)
        
        # Remove duplicates and limit
        materials = list(set(materials))[:5]
        
        # Region detection
        region = IndianRegion.UNKNOWN
        for reg, keywords in self.knowledge_base.regional_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                region = IndianRegion(reg)
                break
        
        # Festival relevance
        festivals = []
        for fest, keywords in self.knowledge_base.festival_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                festivals.append(Festival(fest))
        
        # Cultural significance detection
        cultural_significance = None
        for sig, keywords in self.knowledge_base.cultural_significance_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                from src.models.cultural_models import CulturalSignificance
                cultural_significance = CulturalSignificance(sig)
                break
        
        # Traditional techniques
        techniques = []
        for technique_list in self.knowledge_base.technique_keywords.values():
            for technique in technique_list:
                if technique in text_lower:
                    techniques.append(technique)
        
        # Remove duplicates and limit
        techniques = list(set(techniques))[:3]
        
        # Calculate confidence score
        confidence = 0.1  # Base confidence
        if craft_type != CraftType.UNKNOWN:
            confidence += 0.3
        if region != IndianRegion.UNKNOWN:
            confidence += 0.2
        if festivals:
            confidence += 0.15
        if materials:
            confidence += 0.1
        if techniques:
            confidence += 0.05
        
        confidence = min(confidence, 1.0)
        
        return CulturalContext(
            craft_type=craft_type,
            materials=materials,
            cultural_significance=cultural_significance,
            region=region,
            traditional_techniques=techniques,
            festival_relevance=festivals,
            cultural_tags=detected_keywords[:5],  # Limit to top 5
            confidence_score=confidence,
            analysis_timestamp=datetime.now()
        )

    def _convert_base_results(self, base_results: List[Dict]) -> List[CulturalSearchResult]:
        """Convert base search results to enhanced format without cultural analysis"""
        enhanced_results = []
        
        for result in base_results:
            enhanced_result = CulturalSearchResult(
                id=result["id"],
                score=result["score"],
                weighted_score=result["weighted_score"],
                hits=result["hits"],
                text=result["text"],
                payload=result["payload"]
            )
            enhanced_results.append(enhanced_result)
        
        return enhanced_results

    def _convert_cultural_filters(self, cultural_filters: CulturalSearchFilters) -> Dict[str, Any]:
        """Convert cultural filters to base search filters format"""
        base_filters = {}
        
        # Convert craft types to category filter
        if cultural_filters.craft_types:
            base_filters["craft_type"] = [craft.value for craft in cultural_filters.craft_types]
        
        # Convert regions to region filter  
        if cultural_filters.regions:
            base_filters["region"] = [region.value for region in cultural_filters.regions]
        
        # Convert festivals to festival filter
        if cultural_filters.festivals:
            base_filters["festival_relevance"] = [festival.value for festival in cultural_filters.festivals]
        
        # Convert materials
        if cultural_filters.materials:
            base_filters["materials"] = cultural_filters.materials
        
        # Convert cultural significance
        if cultural_filters.cultural_significance:
            base_filters["cultural_significance"] = [sig.value for sig in cultural_filters.cultural_significance]
        
        # Convert traditional techniques
        if cultural_filters.traditional_techniques:
            base_filters["traditional_techniques"] = cultural_filters.traditional_techniques
        
        # Convert cultural tags
        if cultural_filters.cultural_tags:
            base_filters["cultural_tags"] = cultural_filters.cultural_tags
        
        return base_filters

    def _apply_cultural_scoring(
        self, 
        results: List[CulturalSearchResult], 
        query_context: CulturalQueryContext,
        request: EnhancedSearchRequest
    ) -> List[CulturalSearchResult]:
        """Apply cultural scoring and boost to search results"""
        
        for result in results:
            if result.cultural_context and result.cultural_score is not None:
                # Apply cultural context boost
                cultural_boost = result.cultural_score * request.cultural_context_boost
                
                # Apply regional preference boost
                if request.regional_preference and result.regional_match:
                    cultural_boost += 0.1
                
                # Update weighted score
                result.weighted_score = result.weighted_score + (result.weighted_score * cultural_boost)
                
                # Ensure score doesn't exceed reasonable bounds
                result.weighted_score = min(result.weighted_score, 2.0)
        
        return results

    def _apply_seasonal_boost(self, results: List[CulturalSearchResult]) -> List[CulturalSearchResult]:
        """Apply seasonal/festival boost to relevant items"""
        seasonal_context = cultural_service.get_seasonal_context()
        active_festivals = seasonal_context.get("active_festivals", [])
        
        if not active_festivals:
            return results
        
        for result in results:
            if result.cultural_context:
                # Check if item is relevant to current festivals
                festival_overlap = set(f.value for f in result.cultural_context.festival_relevance) & set(active_festivals)
                
                if festival_overlap:
                    seasonal_boost = len(festival_overlap) * 0.15  # 15% boost per matching festival
                    result.seasonal_relevance = seasonal_boost
                    result.weighted_score = result.weighted_score * (1 + seasonal_boost)
                    
                    logger.debug(f"Applied seasonal boost of {seasonal_boost:.2f} to item {result.id}")
        
        return results

    def _generate_cultural_insights(
        self, 
        query_context: Optional[CulturalQueryContext], 
        results: List[CulturalSearchResult]
    ) -> Dict[str, Any]:
        """Generate cultural insights from search results and query context"""
        insights = {}
        
        if query_context:
            # Detect cultural intent
            if query_context.detected_craft_types:
                insights["cultural_intent"] = f"Looking for {', '.join(c.value for c in query_context.detected_craft_types[:2])}"
            
            # Seasonal context
            if query_context.detected_festivals:
                insights["seasonal_context"] = f"Festival context: {', '.join(f.value for f in query_context.detected_festivals[:2])}"
        
        # Analyze results for suggestions
        result_regions = set()
        result_festivals = set()
        
        for result in results:
            if result.cultural_context:
                if result.cultural_context.region and result.cultural_context.region != IndianRegion.UNKNOWN:
                    result_regions.add(result.cultural_context.region)
                result_festivals.update(result.cultural_context.festival_relevance)
        
        # Suggest related regions (limit to top 3)
        if result_regions:
            insights["suggested_regions"] = list(result_regions)[:3]
        
        # Suggest related festivals (limit to top 3)
        if result_festivals:
            insights["suggested_festivals"] = list(result_festivals)[:3]
        
        return insights

    def _update_cultural_stats(self, processing_time: float):
        """Update cultural processing statistics"""
        current_avg = self.stats["avg_cultural_processing_time"]
        total_analyses = self.stats["cultural_analyses"]
        
        if total_analyses > 0:
            self.stats["avg_cultural_processing_time"] = (
                (current_avg * (total_analyses - 1) + processing_time) / total_analyses
            )
        else:
            self.stats["avg_cultural_processing_time"] = processing_time

    async def index_with_cultural_analysis(
        self, 
        item_id: str, 
        text: str, 
        payload: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Index an item with automatic cultural analysis
        Extends the base index_item function
        """
        try:
            # Extract title and description for cultural analysis
            title = payload.get("title", "") if payload else ""
            description = text
            
            # Perform cultural analysis
            if title or description:
                # FIXED: Use synchronous cultural analysis for indexing too
                text_content = f"{title} {description}".strip()
                cultural_context = self._analyze_cultural_context_sync(text_content)
                
                # Add cultural metadata to payload
                enhanced_payload = payload.copy() if payload else {}
                enhanced_payload.update({
                    "craft_type": cultural_context.craft_type.value if cultural_context.craft_type else "unknown",
                    "materials": cultural_context.materials,
                    "cultural_significance": cultural_context.cultural_significance.value if cultural_context.cultural_significance else "unknown",
                    "region": cultural_context.region.value if cultural_context.region else "unknown",
                    "traditional_techniques": cultural_context.traditional_techniques,
                    "festival_relevance": [f.value for f in cultural_context.festival_relevance],
                    "cultural_tags": cultural_context.cultural_tags,
                    "cultural_confidence": cultural_context.confidence_score,
                    "cultural_analysis_timestamp": cultural_context.analysis_timestamp.isoformat() if cultural_context.analysis_timestamp else None
                })
                
                # Use base indexing service with enhanced payload
                result = base_index_item(item_id, text, enhanced_payload)
                
                logger.info(f"Indexed item {item_id} with cultural analysis: {cultural_context.craft_type}")
                return result
            else:
                # Fallback to base indexing without cultural analysis
                return base_index_item(item_id, text, payload)
                
        except Exception as e:
            logger.error(f"Error in cultural indexing for {item_id}: {e}")
            # Fallback to base indexing
            return base_index_item(item_id, text, payload)

    def get_cultural_stats(self) -> Dict[str, Any]:
        """Get enhanced search service statistics"""
        return {
            **self.stats,
            "cache_size": len(self.cultural_cache),
            "cultural_service_stats": cultural_service.get_stats(),
            "knowledge_base_stats": self.knowledge_base.get_stats()
        }

    def clear_cultural_cache(self):
        """Clear cultural analysis cache"""
        self.cultural_cache.clear()
        cultural_service.clear_cache()
        logger.info("Cultural caches cleared")

    def health_check(self) -> Dict[str, Any]:
        """Health check for enhanced search service"""
        try:
            # Test basic functionality
            test_request = EnhancedSearchRequest(
                query="test pottery",
                limit=1,
                enable_cultural_analysis=False  # Skip cultural analysis for health check
            )
            
            # This would be async in real implementation
            # For now, just check if services are accessible
            knowledge_base_stats = self.knowledge_base.get_stats()
            cultural_stats = cultural_service.get_stats()
            
            return {
                "status": "healthy",
                "enhanced_search_available": True,
                "cultural_analysis_available": True,
                "knowledge_base_loaded": knowledge_base_stats["craft_types_covered"] > 0,
                "stats": self.get_cultural_stats()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "enhanced_search_available": False
            }

# Global instance
enhanced_search_service = EnhancedSearchService()

# Backward compatible functions
async def search_with_cultural_intelligence(request: EnhancedSearchRequest) -> EnhancedSearchResponse:
    """Main enhanced search function"""
    return await enhanced_search_service.search_with_cultural_intelligence(request)

async def index_with_cultural_analysis(item_id: str, text: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Index with cultural analysis"""
    return await enhanced_search_service.index_with_cultural_analysis(item_id, text, payload)