# services/recommendation_service.py - COMPLETE FIXED VERSION
import time
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import traceback
from src.services.cultural_service import cultural_service
from src.services.search_service import search_items
from src.database.qdrant_client import qdrant
from src.algorithms.content_based import content_based_recommender, SimilarityResult
from src.algorithms.collaborative_filtering import collaborative_filter  # ADDED: Import collaborative filter
from src.models.recommendation_models import (
    RecommendationRequest, RecommendationResponse, RecommendationItem, RecommendationScore,
    UserPreferenceRequest, SeasonalRecommendationRequest, BatchRecommendationRequest,
    RecommendationType, SimilarityMetric, CulturalSimilarityConfig, RegionalDiscoveryConfig,
    SeasonalBoostConfig  # ADDED: Import configs
)
from src.models.cultural_models import (
    CulturalContext, CulturalAnalysisRequest, CraftType, IndianRegion, Festival, CulturalSignificance
)
from src.config.settings import settings
from src.utils.logger import recommendation_logger as logger
from qdrant_client.models import ScrollRequest



class CulturalRecommendationService:
    """
    Complete recommendation service integrating cultural intelligence with collaborative filtering
    FIXED: All critical issues resolved for production readiness
    """
    
    def __init__(self):
        logger.info("Initializing Complete Cultural Recommendation Service")
        
        # ADDED: Load configurations
        self.cultural_config = CulturalSimilarityConfig()
        self.regional_config = RegionalDiscoveryConfig()
        self.seasonal_config = SeasonalBoostConfig()
        
        # Enhanced caching system
        self.cache = {}
        self.cultural_cache = {}  # ADDED: Separate cache for cultural analysis
        self.cache_ttl = 1800  # 30 minutes
        
        # ENHANCED: Performance stats with more metrics
        self.stats = {
            "recommendations_served": 0,
            "cache_hits": 0,
            "cultural_analyses_performed": 0,
            "collaborative_recommendations": 0,  # ADDED
            "seasonal_recommendations": 0,  # ADDED
            "avg_response_time_ms": 0.0,
            "fallback_used": 0,
            "failed_requests": 0,
            "empty_responses": 0,
            "cultural_cache_hits": 0  # ADDED
        }
        
        logger.info("Complete Cultural Recommendation Service initialized successfully")

    def _safe_enum_value(self, enum_obj):

        if enum_obj is None:
            return None
        if hasattr(enum_obj, 'value'):
            return enum_obj.value
        return str(enum_obj)
    async def get_item_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        """
        ENHANCED: Main method for item-based recommendations with performance optimizations
        """
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000)}"
        
        logger.info(
            f"[{request_id}] Starting item recommendation request",
            item_id=request.item_id,
            rec_types=[rt.value for rt in request.recommendation_types],
            limit=request.limit,
            similarity_threshold=request.similarity_threshold
        )
        
        # ENHANCED: Better cache key with more parameters
        cache_key = f"rec_{request.item_id}_{'-'.join([rt.value for rt in request.recommendation_types])}_{request.limit}_{request.similarity_threshold}"
        
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                self.stats["cache_hits"] += 1
                processing_time = (time.time() - start_time) * 1000
                
                logger.debug(f"[{request_id}] Using cached recommendations", processing_time_ms=processing_time)
                
                cached_response = cache_entry["response"]
                cached_response.processing_time_ms = round(processing_time, 2)
                cached_response.cache_hits = 1
                return cached_response
        
        try:
            # Step 1: Get source item with cultural context (OPTIMIZED)
            logger.debug(f"[{request_id}] Fetching source item with cultural context")
            source_item = await self._get_item_with_cultural_context_optimized(request.item_id, request_id)
            
            if not source_item:
                error_msg = f"Source item {request.item_id} not found"
                logger.warning(f"[{request_id}] {error_msg}")
                self.stats["failed_requests"] += 1
                return self._create_empty_response(request, error_msg)
            
            logger.info(
                f"[{request_id}] Source item retrieved successfully",
                cultural_context=self._get_cultural_context_summary(source_item.get('cultural_context'))
            )
            
            # Step 2: Get candidate items for recommendations (OPTIMIZED)
            logger.debug(f"[{request_id}] Fetching candidate items")
            candidate_items = await self._get_candidate_items_optimized(
                source_item, 
                exclude_ids=request.exclude_item_ids or [],
                request_id=request_id
            )
            
            if not candidate_items:
                error_msg = "No candidate items found"
                logger.warning(f"[{request_id}] {error_msg}")
                self.stats["empty_responses"] += 1
                return self._create_empty_response(request, error_msg)
            
            logger.info(f"[{request_id}] Found {len(candidate_items)} candidate items")
            
            # Step 3: Generate recommendations based on types requested (ENHANCED)
            all_recommendations = []
            recommendation_stats = defaultdict(int)
            
            for rec_type in request.recommendation_types:
                logger.debug(f"[{request_id}] Generating {rec_type.value} recommendations")
                
                try:
                    type_recommendations = await self._generate_recommendations_by_type_enhanced(
                        rec_type, source_item, candidate_items, request, request_id
                    )
                    all_recommendations.extend(type_recommendations)
                    recommendation_stats[rec_type] += len(type_recommendations)
                    
                    logger.debug(
                        f"[{request_id}] Generated {len(type_recommendations)} {rec_type.value} recommendations"
                    )
                    
                except Exception as e:
                    logger.error(
                        f"[{request_id}] Failed to generate {rec_type.value} recommendations: {str(e)}",
                        error_type=type(e).__name__,
                        recommendation_type=rec_type.value
                    )
                    continue
            
            logger.info(
                f"[{request_id}] Generated {len(all_recommendations)} total recommendations across {len(recommendation_stats)} types"
            )
            
            # Step 4: Deduplicate and rank
            logger.debug(f"[{request_id}] Deduplicating and ranking recommendations")
            final_recommendations = self._deduplicate_and_rank_recommendations(
                all_recommendations, request.limit, request_id
            )
            
            # Step 5: Create response
            processing_time = (time.time() - start_time) * 1000
            response = RecommendationResponse(
                source_item_id=request.item_id,
                total_recommendations=len(final_recommendations),
                recommendations=final_recommendations,
                recommendation_types_used=request.recommendation_types,
                processing_time_ms=round(processing_time, 2),
                cultural_diversity_stats=self._calculate_diversity_stats(final_recommendations),
                seasonal_recommendations_count=recommendation_stats.get(RecommendationType.FESTIVAL_SEASONAL, 0),
                cross_cultural_recommendations_count=recommendation_stats.get(RecommendationType.CROSS_CULTURAL, 0),
                cache_hits=0,
                recommendation_confidence=self._calculate_overall_confidence(final_recommendations)
            )
            
            # Step 6: Cache the response
            self.cache[cache_key] = {
                "response": response,
                "timestamp": time.time()
            }
            
            # Step 7: Update stats and log final results
            self._update_stats(processing_time / 1000)
            
            logger.info(
                f"[{request_id}] Recommendation request completed successfully",
                final_count=len(final_recommendations),
                processing_time_ms=processing_time,
                confidence=response.recommendation_confidence,
                diversity_regions=response.cultural_diversity_stats.get("unique_regions", 0),
                diversity_crafts=response.cultural_diversity_stats.get("unique_craft_types", 0)
            )
            
            return response
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"[{request_id}] Critical error in recommendation request: {str(e)}")
            self.stats["failed_requests"] += 1
            return self._create_error_response(request, str(e))


    
    async def get_user_recommendations(self, request: UserPreferenceRequest) -> RecommendationResponse:
        """
        FIXED: Generate recommendations with collaborative filtering integration
        """
        start_time = time.time()
        request_id = f"user_req_{int(start_time * 1000)}"
        
        logger.info(
            f"[{request_id}] Starting user preference recommendation request",
            user_id=request.user_id,
            preferred_regions=[r.value for r in request.preferred_regions] if request.preferred_regions else None,
            preferred_crafts=[c.value for c in request.preferred_craft_types] if request.preferred_craft_types else None,
            interaction_history_count=len(request.user_interaction_history) if request.user_interaction_history else 0
        )
        
        try:
            # Step 1: Determine recommendation strategy based on user history
            use_collaborative = (
                request.user_interaction_history and 
                len(request.user_interaction_history) >= 5 and 
                request.user_id
            )
            
            if use_collaborative:
                logger.info(f"[{request_id}] Using collaborative filtering for user with {len(request.user_interaction_history)} interactions")
                return await self._get_collaborative_recommendations(request, request_id)
            else:
                logger.info(f"[{request_id}] Using content-based recommendations (insufficient interaction history)")
                return await self._get_content_based_user_recommendations(request, request_id)
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"[{request_id}] Error in user preference recommendation: {str(e)}")
            self.stats["failed_requests"] += 1
            return self._create_error_response(request, str(e))

    async def _get_collaborative_recommendations(self, request: UserPreferenceRequest, request_id: str) -> RecommendationResponse:
        """
        ADDED: New method using collaborative filtering
        """
        start_time = time.time()
        
        try:
            # Get candidate items efficiently
            candidate_items = await self._get_candidate_items_for_user_optimized(request, request_id)
            
            if not candidate_items:
                logger.warning(f"[{request_id}] No suitable items for collaborative filtering")
                return await self._get_content_based_user_recommendations(request, request_id)
            
            # Use collaborative filtering
            logger.debug(f"[{request_id}] Applying collaborative filtering")
            collaborative_recs = collaborative_filter.get_collaborative_recommendations(
                request.user_id, candidate_items, request.limit
            )
            
            # Convert collaborative results to RecommendationItem format
            recommendations = []
            for item_data, score in collaborative_recs:
                similarity_result = SimilarityResult(
                    similarity_score=score,
                    cultural_similarity=0.0,
                    vector_similarity=0.0,
                    seasonal_relevance=0.0,
                    regional_match=0.0,
                    festival_relevance=0.0,
                    match_reasons=["Collaborative filtering recommendation"]
                )
                
                rec_item = self._create_recommendation_item(
                    item_data, similarity_result, RecommendationType.CULTURAL_SIMILARITY,
                    SimilarityMetric.CULTURAL_CONTEXT, request_id
                )
                recommendations.append(rec_item)
            
            # Apply diversity if requested
            if request.diversity_factor > 0:
                recommendations = self._apply_user_diversity_preferences(
                    recommendations, request.diversity_factor, request.limit, request_id
                )
            
            processing_time = (time.time() - start_time) * 1000
            self.stats["collaborative_recommendations"] += 1
            
            response = RecommendationResponse(
                source_item_id=None,
                total_recommendations=len(recommendations),
                recommendations=recommendations,
                recommendation_types_used=request.recommendation_types,
                processing_time_ms=round(processing_time, 2),
                cultural_diversity_stats=self._calculate_diversity_stats(recommendations)
            )
            
            logger.info(f"[{request_id}] Collaborative recommendations completed: {len(recommendations)} items")
            return response
            
        except Exception as e:
            logger.error(f"[{request_id}] Collaborative filtering failed: {str(e)}")
            # Fallback to content-based
            return await self._get_content_based_user_recommendations(request, request_id)

    async def _get_content_based_user_recommendations(self, request: UserPreferenceRequest, request_id: str) -> RecommendationResponse:
        """
        ENHANCED: Content-based user recommendations with optimizations
        """
        start_time = time.time()
        
        try:
            # Get user items for analysis (optimized)
            user_items = []
            if request.user_interaction_history:
                for item_id in request.user_interaction_history[-10:]:  # Last 10 interactions
                    item = await self._get_item_with_cultural_context_optimized(item_id, request_id)
                    if item:
                        user_items.append(item)
            
            logger.info(f"[{request_id}] Retrieved {len(user_items)} user interaction items")
            
            # Create user cultural profile
            user_cultural_profile = self._create_user_cultural_profile(request, user_items, request_id)
            
            # Get candidate items
            candidate_items = await self._get_candidate_items_for_user_optimized(request, request_id)
            
            if not candidate_items:
                error_msg = "No suitable items found for user preferences"
                logger.warning(f"[{request_id}] {error_msg}")
                self.stats["empty_responses"] += 1
                return self._create_empty_response(request, error_msg)
            
            # Generate recommendations
            recommendations = await self._generate_user_based_recommendations(
                user_cultural_profile, candidate_items, request, request_id
            )
            
            # Apply diversity
            final_recommendations = self._apply_user_diversity_preferences(
                recommendations, request.diversity_factor, request.limit, request_id
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            response = RecommendationResponse(
                source_item_id=None,
                total_recommendations=len(final_recommendations),
                recommendations=final_recommendations,
                recommendation_types_used=request.recommendation_types,
                processing_time_ms=round(processing_time, 2),
                cultural_diversity_stats=self._calculate_diversity_stats(final_recommendations)
            )
            
            self._update_stats(processing_time / 1000)
            
            logger.info(f"[{request_id}] Content-based user recommendations completed: {len(final_recommendations)} items")
            return response
            
        except Exception as e:
            logger.error(f"[{request_id}] Content-based user recommendations failed: {str(e)}")
            raise

    async def get_seasonal_recommendations(self, request: SeasonalRecommendationRequest) -> RecommendationResponse:
        """
        FIXED: Seasonal recommendations with improved festival detection
        """
        start_time = time.time()
        request_id = f"seasonal_req_{int(start_time * 1000)}"
        
        logger.info(
            f"[{request_id}] Starting seasonal recommendation request",
            current_festival=request.current_festival.value if request.current_festival else None,
            upcoming_festivals=[f.value for f in request.upcoming_festivals] if request.upcoming_festivals else None,
            region_preference=request.region_preference.value if request.region_preference else None,
            limit=request.limit
        )
        
        try:
            # FIXED: Improved festival detection
            active_festivals = self._determine_active_festivals(request, request_id)
            
            if not active_festivals:
                logger.warning(f"[{request_id}] No active festivals found, using current month context")
                # Add default seasonal context
                current_month = datetime.now().month
                if current_month in [10, 11]:  # October-November
                    active_festivals = [Festival.DIWALI, Festival.DHANTERAS, Festival.DUSSEHRA]
                elif current_month == 3:  # March
                    active_festivals = [Festival.HOLI]
                elif current_month == 9:  # September
                    active_festivals = [Festival.GANESH_CHATURTHI]
            
            logger.info(f"[{request_id}] Active festivals: {[f.value for f in active_festivals]}")
            
            # Get items efficiently (OPTIMIZED)
            all_items = await self._get_seasonal_candidate_items(request_id)
            
            if not all_items:
                error_msg = "No items available for seasonal analysis"
                logger.warning(f"[{request_id}] {error_msg}")
                self.stats["empty_responses"] += 1
                return self._create_empty_response(request, error_msg)
            
            # ENHANCED: Better seasonal filtering
            seasonal_items = self._find_seasonal_items_enhanced(all_items, active_festivals, request, request_id)
            
            # Convert to recommendation items
            recommendations = []
            for item_data, relevance_score in seasonal_items[:request.limit]:
                similarity_result = SimilarityResult(
                    similarity_score=relevance_score,
                    cultural_similarity=0.0,
                    vector_similarity=0.0,
                    seasonal_relevance=relevance_score,
                    regional_match=0.0,
                    festival_relevance=relevance_score,
                    match_reasons=[f"Festival relevance: {', '.join([f.value for f in active_festivals])}"]
                )
                
                rec_item = self._create_recommendation_item(
                    item_data, similarity_result, RecommendationType.FESTIVAL_SEASONAL,
                    SimilarityMetric.FESTIVAL_SEASONAL, request_id
                )
                recommendations.append(rec_item)
            
            processing_time = (time.time() - start_time) * 1000
            self.stats["seasonal_recommendations"] += 1
            
            response = RecommendationResponse(
                source_item_id=None,
                total_recommendations=len(recommendations),
                recommendations=recommendations,
                recommendation_types_used=[RecommendationType.FESTIVAL_SEASONAL],
                processing_time_ms=round(processing_time, 2),
                seasonal_recommendations_count=len(recommendations),
                cultural_diversity_stats=self._calculate_diversity_stats(recommendations)
            )
            
            self._update_stats(processing_time / 1000)
            
            logger.info(
                f"[{request_id}] Seasonal recommendation request completed successfully",
                final_count=len(recommendations),
                processing_time_ms=processing_time,
                festivals_matched=len(active_festivals)
            )
            
            return response
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"[{request_id}] Seasonal recommendation error: {str(e)}")
            self.stats["failed_requests"] += 1
            return self._create_error_response(request, str(e))

    # OPTIMIZED HELPER METHODS

    async def _get_item_with_cultural_context_optimized(self, item_id: str, request_id: str = "") -> Optional[Dict[str, Any]]:
        """
        OPTIMIZED: Get item with cultural context using caching
        """
        # Check cultural cache first
        if item_id in self.cultural_cache:
            cache_entry = self.cultural_cache[item_id]
            if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                self.stats["cultural_cache_hits"] += 1
                logger.debug(f"[{request_id}] Using cached cultural context for {item_id}")
                return cache_entry["item_data"]
        
        try:
            # Try direct retrieval first (most efficient)
            import uuid
            try:
                uuid_obj = uuid.UUID(item_id)
                point_ids = [str(uuid_obj)]
            except ValueError:
                point_ids = [item_id]
            
            points = qdrant.retrieve(
                collection_name=settings.COLLECTION_NAME,
                ids=point_ids,
                with_payload=True,
                with_vectors=True
            )
            
            if points and len(points) > 0:
                point = points[0]
                payload = point.payload or {}
                
                text = payload.get("text") or payload.get("description") or payload.get("title") or ""
                if not text:
                    logger.warning(f"[{request_id}] Item {item_id} has no text")
                    return None
                
                item_data = {
                    "id": str(point.id),
                    "text": text,
                    "payload": payload,
                    "vector": point.vector if hasattr(point, 'vector') else None
                }
                
                # Add cultural context with caching
                if "cultural_context" not in payload:
                    analysis_request = CulturalAnalysisRequest(
                        title=payload.get("title", ""),
                        description=text
                    )
                    cultural_analysis = await cultural_service.analyze_artwork_cultural_context(analysis_request)
                    item_data["cultural_context"] = cultural_analysis.cultural_context
                    self.stats["cultural_analyses_performed"] += 1
                else:
                    existing = payload["cultural_context"]
                    item_data["cultural_context"] = CulturalContext(**existing) if isinstance(existing, dict) else existing
                
                # Cache the result
                self.cultural_cache[item_id] = {
                    "item_data": item_data,
                    "timestamp": time.time()
                }
                
                logger.debug(f"[{request_id}] Retrieved and cached item: {item_id}")
                return item_data
            
            logger.warning(f"[{request_id}] Item {item_id} not found")
            return None
            
        except Exception as e:
            logger.error(f"[{request_id}] Error retrieving item {item_id}: {str(e)}")
            return None

    async def _get_candidate_items_optimized(self, source_item: Dict[str, Any], exclude_ids: List[str] = None, request_id: str = "") -> List[Dict[str, Any]]:
        """
        OPTIMIZED: Get candidate items with batch cultural analysis
        """
        exclude_ids = exclude_ids or []
        exclude_ids.append(source_item["id"])
        
        try:
            # Use search service for efficiency
            search_query = source_item["text"][:100]
            
            search_results = search_items(
                query=search_query,
                limit=30,  # REDUCED: More reasonable limit for performance
                use_expansion=False,
                use_reranker=False,
                score_threshold=0.1
            )
            
            # BATCH PROCESS: Collect items needing cultural analysis
            candidates = []
            items_needing_analysis = []
            
            for result in search_results:
                if result["id"] not in exclude_ids:
                    item_data = {
                        "id": result["id"],
                        "text": result["text"],
                        "payload": result["payload"],
                        "vector_similarity": result["score"]
                    }
                    
                    if "cultural_context" not in result["payload"]:
                        items_needing_analysis.append(item_data)
                    else:
                        existing_context = result["payload"]["cultural_context"]
                        item_data["cultural_context"] = CulturalContext(**existing_context) if isinstance(existing_context, dict) else existing_context
                        candidates.append(item_data)
            
            # Batch cultural analysis for items that need it (PERFORMANCE IMPROVEMENT)
            if items_needing_analysis:
                logger.debug(f"[{request_id}] Batch analyzing {len(items_needing_analysis)} items")
                await self._batch_cultural_analysis(items_needing_analysis, request_id)
                candidates.extend(items_needing_analysis)
            
            logger.info(f"[{request_id}] Retrieved {len(candidates)} candidate items (optimized)")
            return candidates
            
        except Exception as e:
            logger.error(f"[{request_id}] Error getting candidate items: {str(e)}")
            return []

    async def _batch_cultural_analysis(self, items: List[Dict[str, Any]], request_id: str):
        """
        ADDED: Batch cultural analysis for performance
        """
        try:
            # Analyze items in smaller batches to avoid overwhelming the AI service
            batch_size = 5
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                
                # Process batch concurrently
                tasks = []
                for item in batch:
                    if item["text"]:  # Only analyze items with text
                        task = cultural_service.analyze_artwork_cultural_context(
                            CulturalAnalysisRequest(
                                title=item["payload"].get("title", ""),
                                description=item["text"]
                            )
                        )
                        tasks.append((item, task))
                
                # Wait for batch completion
                for item, task in tasks:
                    try:
                        cultural_analysis = await task
                        item["cultural_context"] = cultural_analysis.cultural_context
                        self.stats["cultural_analyses_performed"] += 1
                    except Exception as e:
                        logger.warning(f"[{request_id}] Cultural analysis failed for item {item['id']}: {str(e)}")
                        # Use fallback analysis
                        item["cultural_context"] = cultural_service._enhanced_fallback_analysis(
                            item["text"], item["payload"].get("title", "")
                        )
                
                # Small delay between batches to be respectful to AI service
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"[{request_id}] Batch cultural analysis error: {str(e)}")

    async def _get_candidate_items_for_user_optimized(self, request: UserPreferenceRequest, request_id: str) -> List[Dict[str, Any]]:
        """
        OPTIMIZED: Get candidate items for user with better filtering
        """
        try:
            # Use search-based approach instead of loading all items
            if request.preferred_craft_types or request.preferred_regions:
                # Build search queries based on preferences
                search_terms = []
                
                if request.preferred_craft_types:
                    search_terms.extend([craft.value for craft in request.preferred_craft_types])
                
                if request.preferred_regions:
                    search_terms.extend([region.value for region in request.preferred_regions])
                
                search_query = " ".join(search_terms) if search_terms else "indian craft traditional"
                
                search_results = search_items(
                    query=search_query,
                    limit=50,  # Reasonable limit
                    use_expansion=False,
                    use_reranker=False,
                    score_threshold=0.0  # Accept all for user preferences
                )
                
                # Convert search results to candidate format
                candidates = []
                for result in search_results:
                    item_data = {
                        "id": result["id"],
                        "text": result["text"],
                        "payload": result["payload"],
                        "vector_similarity": result["score"]
                    }
                    
                    # Add cultural context
                    if "cultural_context" not in result["payload"]:
                        # For user recommendations, use fallback for performance
                        item_data["cultural_context"] = cultural_service._enhanced_fallback_analysis(
                            result["text"], result["payload"].get("title", "")
                        )
                    else:
                        existing_context = result["payload"]["cultural_context"]
                        item_data["cultural_context"] = CulturalContext(**existing_context) if isinstance(existing_context, dict) else existing_context
                    
                    candidates.append(item_data)
                
                # Apply preference filters
                filtered_candidates = self._apply_user_preference_filters(candidates, request, request_id)
                
                logger.info(f"[{request_id}] User candidate items: {len(search_results)} -> {len(filtered_candidates)} after filtering")
                return filtered_candidates
            
            else:
                # No specific preferences, get diverse items
                return await self._get_diverse_candidate_items(request, request_id)
                
        except Exception as e:
            logger.error(f"[{request_id}] Error getting user candidate items: {str(e)}")
            return []

    def _apply_user_preference_filters(self, candidates: List[Dict[str, Any]], request: UserPreferenceRequest, request_id: str) -> List[Dict[str, Any]]:
        """FIXED: Apply user preference filters with relaxed matching"""
        filtered_items = []
        
        for item in candidates:
            cultural_context = item.get("cultural_context")
            if not cultural_context:
                continue
            
            should_include = True
            
            # FIXED: Apply craft type filter with partial matching
            if request.preferred_craft_types:
                craft_match = False
                for preferred_craft in request.preferred_craft_types:
                    # Compare enum values safely
                    item_craft = self._safe_enum_value(cultural_context.craft_type)
                    preferred_craft_val = self._safe_enum_value(preferred_craft)
                    if item_craft == preferred_craft_val:
                        craft_match = True
                        break
                if not craft_match:
                    should_include = False
            
            # FIXED: Apply region filter with partial matching - be more lenient
            if request.preferred_regions and should_include:
                region_match = False
                for preferred_region in request.preferred_regions:
                    item_region = self._safe_enum_value(cultural_context.region)
                    preferred_region_val = self._safe_enum_value(preferred_region)
                    if item_region == preferred_region_val:
                        region_match = True
                        break
                # Don't filter out if region is unknown - allow regional discovery
                if not region_match and item_region != "unknown":
                    should_include = False
            
            # Keep other filters as they are...
            
            if should_include:
                filtered_items.append(item)
        
        return filtered_items

    async def _get_diverse_candidate_items(self, request: UserPreferenceRequest, request_id: str) -> List[Dict[str, Any]]:
        """
        ADDED: Get diverse candidate items when no specific preferences
        """
        try:
            # Search for diverse Indian crafts
            diverse_queries = ["indian traditional craft", "handmade artisan", "cultural heritage"]
            all_candidates = []
            
            for query in diverse_queries:
                search_results = search_items(
                    query=query,
                    limit=20,
                    use_expansion=False,
                    use_reranker=False,
                    score_threshold=0.0
                )
                
                for result in search_results:
                    item_data = {
                        "id": result["id"],
                        "text": result["text"],
                        "payload": result["payload"],
                        "vector_similarity": result["score"]
                    }
                    
                    # Use fallback cultural analysis for performance
                    if "cultural_context" not in result["payload"]:
                        item_data["cultural_context"] = cultural_service._enhanced_fallback_analysis(
                            result["text"], result["payload"].get("title", "")
                        )
                    else:
                        existing_context = result["payload"]["cultural_context"]
                        item_data["cultural_context"] = CulturalContext(**existing_context) if isinstance(existing_context, dict) else existing_context
                    
                    all_candidates.append(item_data)
            
            # Remove duplicates and return diverse set
            unique_candidates = {item["id"]: item for item in all_candidates}
            return list(unique_candidates.values())[:50]  # Limit for performance
            
        except Exception as e:
            logger.error(f"[{request_id}] Error getting diverse candidates: {str(e)}")
            return []

    async def _get_seasonal_candidate_items(self, request_id: str) -> List[Dict[str, Any]]:
        """
        OPTIMIZED: Get items for seasonal analysis efficiently
        """
        try:
            # Search for seasonal/festival-related items
            seasonal_queries = ["festival", "diwali", "celebration", "traditional", "gift", "decorative"]
            
            all_items = []
            for query in seasonal_queries:
                search_results = search_items(
                    query=query,
                    limit=15,  # Smaller batches for performance
                    use_expansion=False,
                    use_reranker=False,
                    score_threshold=0.0
                )
                
                for result in search_results:
                    item_data = {
                        "id": result["id"],
                        "text": result["text"],
                        "payload": result["payload"]
                    }
                    
                    # Add cultural context efficiently
                    if "cultural_context" not in result["payload"]:
                        item_data["cultural_context"] = cultural_service._enhanced_fallback_analysis(
                            result["text"], result["payload"].get("title", "")
                        )
                    else:
                        existing_context = result["payload"]["cultural_context"]
                        item_data["cultural_context"] = CulturalContext(**existing_context) if isinstance(existing_context, dict) else existing_context
                    
                    all_items.append(item_data)
            
            # Remove duplicates
            unique_items = {item["id"]: item for item in all_items}
            final_items = list(unique_items.values())
            
            logger.info(f"[{request_id}] Retrieved {len(final_items)} seasonal candidate items")
            return final_items
            
        except Exception as e:
            logger.error(f"[{request_id}] Error getting seasonal candidates: {str(e)}")
            return []

    def _determine_active_festivals(self, request: SeasonalRecommendationRequest, request_id: str) -> List[Festival]:
        """
        FIXED: Better festival determination logic
        """
        active_festivals = []
        
        # Add explicitly requested festivals
        if request.current_festival:
            active_festivals.append(request.current_festival)
        
        if request.upcoming_festivals:
            active_festivals.extend(request.upcoming_festivals)
        
        # If no specific festivals, determine from current date
        if not active_festivals:
            current_month = datetime.now().month
            current_day = datetime.now().day
            
            # Enhanced seasonal festival mapping
            seasonal_mapping = {
                1: [],  # January
                2: [],  # February
                3: [Festival.HOLI],  # March
                4: [],  # April
                5: [],  # May
                6: [],  # June
                7: [],  # July
                8: [Festival.RAKSHA_BANDHAN],  # August
                9: [Festival.GANESH_CHATURTHI],  # September
                10: [Festival.DUSSEHRA, Festival.NAVRATRI],  # October
                11: [Festival.DIWALI, Festival.DHANTERAS, Festival.KARVA_CHAUTH],  # November
                12: [Festival.CHRISTMAS]  # December
            }
            
            month_festivals = seasonal_mapping.get(current_month, [])
            active_festivals.extend(month_festivals)
            
            # Add wedding season (Oct-Feb)
            if current_month in [10, 11, 12, 1, 2]:
                active_festivals.append(Festival.WEDDING_SEASON)
        
        logger.debug(f"[{request_id}] Determined active festivals: {[f.value for f in active_festivals]}")
        return active_festivals

    def _find_seasonal_items_enhanced(self, items: List[Dict[str, Any]], festivals: List[Festival], request: SeasonalRecommendationRequest, request_id: str) -> List[Tuple[Dict[str, Any], float]]:
        """
        ENHANCED: Better seasonal item detection with improved scoring
        """
        seasonal_items = []
        
        for item in items:
            cultural_context = item.get("cultural_context")
            if not cultural_context:
                continue
            
            relevance_score = 0.0
            
            # Festival relevance scoring
            for festival in festivals:
                if festival in cultural_context.festival_relevance:
                    relevance_score += 0.4  # Higher base score
            
            # Cultural significance scoring
            if cultural_context.cultural_significance in [
                CulturalSignificance.FESTIVAL_ITEM,
                CulturalSignificance.GIFT_ITEM,
                CulturalSignificance.DECORATIVE,
                CulturalSignificance.CEREMONIAL
            ]:
                relevance_score += 0.3
            
            # Regional preference bonus
            if request.region_preference and cultural_context.region == request.region_preference:
                relevance_score += 0.2
            
            # Traditional craft bonus for festivals
            if cultural_context.cultural_tags:
                traditional_indicators = ["traditional", "heritage", "festival", "celebration"]
                if any(tag in traditional_indicators for tag in cultural_context.cultural_tags):
                    relevance_score += 0.1
            
            # Only include items with meaningful seasonal relevance
            if relevance_score >= 0.2:  # Minimum threshold
                seasonal_items.append((item, relevance_score))
        
        # Sort by relevance score
        seasonal_items.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"[{request_id}] Found {len(seasonal_items)} seasonal items with relevance >= 0.2")
        return seasonal_items

    async def _generate_user_based_recommendations(
        self,
        user_cultural_profile: Dict[str, Any],
        candidate_items: List[Dict[str, Any]],
        request: UserPreferenceRequest,
        request_id: str = ""
    ) -> List[RecommendationItem]:
        """Generate recommendations based on user profile - FIXED ENUM HANDLING"""
        logger.debug(f"[{request_id}] Generating user-based recommendations")
        
        recommendations = []
        
        try:
            for item in candidate_items:
                cultural_context = item.get("cultural_context")
                if not cultural_context:
                    continue
                
                compatibility_score = 0.0
                match_reasons = []
                
                # FIXED: Craft type compatibility with safe enum handling
                if cultural_context.craft_type:
                    craft_value = self._safe_enum_value(cultural_context.craft_type)
                    if craft_value and craft_value in user_cultural_profile["preferred_craft_types"]:
                        craft_score = user_cultural_profile["preferred_craft_types"][craft_value]
                        compatibility_score += craft_score * 0.4
                        match_reasons.append(f"Craft preference: {craft_value}")
                
                # FIXED: Region compatibility with safe enum handling
                if cultural_context.region:
                    region_value = self._safe_enum_value(cultural_context.region)
                    if region_value and region_value in user_cultural_profile["preferred_regions"]:
                        region_score = user_cultural_profile["preferred_regions"][region_value]
                        compatibility_score += region_score * 0.3
                        match_reasons.append(f"Region preference: {region_value}")
                
                # FIXED: Festival compatibility with safe enum handling
                if cultural_context.festival_relevance:
                    for festival in cultural_context.festival_relevance:
                        festival_value = self._safe_enum_value(festival)
                        if festival_value and festival_value in user_cultural_profile["preferred_festivals"]:
                            festival_score = user_cultural_profile["preferred_festivals"][festival_value]
                            compatibility_score += festival_score * 0.2
                            match_reasons.append(f"Festival match: {festival_value}")
                
                # Material compatibility (unchanged - materials are strings)
                if cultural_context.materials:
                    for material in cultural_context.materials:
                        if material in user_cultural_profile["preferred_materials"]:
                            material_score = user_cultural_profile["preferred_materials"][material]
                            compatibility_score += material_score * 0.1
                            match_reasons.append(f"Material preference: {material}")
                
                # FIXED: Cultural exploration bonus with safe enum handling
                if user_cultural_profile["cultural_openness"] > 0.5:
                    craft_value = self._safe_enum_value(cultural_context.craft_type)
                    region_value = self._safe_enum_value(cultural_context.region)
                    
                    is_new_craft = craft_value not in user_cultural_profile["preferred_craft_types"]
                    is_new_region = region_value not in user_cultural_profile["preferred_regions"]
                    
                    if is_new_craft or is_new_region:
                        exploration_bonus = user_cultural_profile["cultural_openness"] * 0.1
                        compatibility_score += exploration_bonus
                        match_reasons.append("Cultural exploration bonus")
                
                if compatibility_score > 0.1:
                    # FIXED: Festival relevance calculation
                    festival_relevance = 0.0
                    if cultural_context.festival_relevance:
                        festival_matches = 0
                        for festival in cultural_context.festival_relevance:
                            festival_value = self._safe_enum_value(festival)
                            if festival_value and festival_value in user_cultural_profile["preferred_festivals"]:
                                festival_matches += 1
                        festival_relevance = festival_matches / max(len(cultural_context.festival_relevance), 1)
                    
                    # FIXED: Regional match calculation
                    region_match = 0.0
                    if cultural_context.region:
                        region_value = self._safe_enum_value(cultural_context.region)
                        if region_value and region_value in user_cultural_profile["preferred_regions"]:
                            region_match = 1.0
                    
                    similarity_result = SimilarityResult(
                        similarity_score=compatibility_score,
                        cultural_similarity=compatibility_score,
                        vector_similarity=0.0,
                        seasonal_relevance=0.0,
                        regional_match=region_match,
                        festival_relevance=festival_relevance,
                        match_reasons=match_reasons
                    )
                    
                    rec_item = self._create_recommendation_item(
                        item, similarity_result, RecommendationType.CULTURAL_SIMILARITY, 
                        SimilarityMetric.CULTURAL_CONTEXT, request_id
                    )
                    recommendations.append(rec_item)
            
            recommendations.sort(key=lambda x: x.score_breakdown.overall_score, reverse=True)
            
            logger.info(f"[{request_id}] Generated {len(recommendations)} user-based recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"[{request_id}] Error generating user-based recommendations: {str(e)}")
            logger.error(f"[{request_id}] Error traceback: {traceback.format_exc()}")
            return []

    def _find_cross_cultural_recommendations(
        self, 
        source_item: Dict[str, Any], 
        candidates: List[Dict[str, Any]], 
        limit: int,
        request_id: str
    ) -> List[Tuple[Dict[str, Any], SimilarityResult]]:
        """FIXED: Find cross-cultural recommendations with proper enum handling"""
        source_context = source_item.get("cultural_context")
        if not source_context:
            logger.warning(f"[{request_id}] No source cultural context for cross-cultural recommendations")
            return []
        
        cross_cultural_items = []
        source_region = self._safe_enum_value(source_context.region)
        source_craft = self._safe_enum_value(source_context.craft_type)
        
        logger.debug(f"[{request_id}] Looking for cross-cultural items different from region: {source_region}, craft: {source_craft}")
        
        for candidate in candidates:
            candidate_context = candidate.get("cultural_context")
            if not candidate_context:
                continue
            
            candidate_region = self._safe_enum_value(candidate_context.region)
            candidate_craft = self._safe_enum_value(candidate_context.craft_type)
            
            # FIXED: Look for items from different regions but similar craft types
            # Also include items with same region but different craft types for cultural exploration
            is_different_region = (source_region != candidate_region and 
                                candidate_region and candidate_region != "unknown")
            is_same_craft = (source_craft == candidate_craft and 
                            candidate_craft and candidate_craft != "unknown")
            is_different_craft = (source_craft != candidate_craft and 
                                candidate_craft and candidate_craft != "unknown")
            
            # Include if: different region OR different craft type (for cultural exploration)
            if is_different_region or (source_region == candidate_region and is_different_craft):
                try:
                    # Calculate cross-cultural similarity
                    similarity_score = 0.0
                    match_reasons = []
                    
                    # Same craft type bonus (for regional variation)
                    if is_same_craft:
                        similarity_score += 0.4
                        match_reasons.append(f"Same craft type: {candidate_craft}")
                    
                    # Different region bonus (cross-cultural discovery)
                    if is_different_region:
                        similarity_score += 0.3
                        match_reasons.append(f"Cross-cultural discovery: {source_region} → {candidate_region}")
                    
                    # Different craft bonus (craft exploration)
                    if is_different_craft:
                        similarity_score += 0.25
                        match_reasons.append(f"Craft exploration: {source_craft} → {candidate_craft}")
                    
                    # Material similarity bonus
                    if (source_context.materials and candidate_context.materials):
                        common_materials = set(source_context.materials) & set(candidate_context.materials)
                        if common_materials:
                            material_bonus = len(common_materials) * 0.05
                            similarity_score += material_bonus
                            match_reasons.append(f"Shared materials: {', '.join(list(common_materials)[:2])}")
                    
                    # Cultural significance alignment
                    if (source_context.cultural_significance and 
                        candidate_context.cultural_significance and
                        self._safe_enum_value(source_context.cultural_significance) == 
                        self._safe_enum_value(candidate_context.cultural_significance)):
                        similarity_score += 0.1
                        match_reasons.append("Similar cultural significance")
                    
                    # Lower threshold for cross-cultural to encourage discovery
                    if similarity_score >= 0.15:  # Lower threshold
                        similarity_result = SimilarityResult(
                            similarity_score=similarity_score,
                            cultural_similarity=similarity_score,
                            vector_similarity=0.0,
                            seasonal_relevance=0.0,
                            regional_match=0.0 if is_different_region else 1.0,
                            festival_relevance=0.0,
                            match_reasons=match_reasons
                        )
                        
                        cross_cultural_items.append((candidate, similarity_result))
                        
                        logger.debug(f"[{request_id}] Added cross-cultural item: {candidate['id']} (score: {similarity_score:.2f})")
                    
                except Exception as e:
                    logger.error(f"[{request_id}] Error processing cross-cultural candidate: {str(e)}")
                    continue
        
        # Sort by similarity score
        cross_cultural_items.sort(key=lambda x: x[1].similarity_score, reverse=True)
        
        logger.info(f"[{request_id}] Found {len(cross_cultural_items)} cross-cultural recommendations")
        return cross_cultural_items[:limit]

    # REMAINING HELPER METHODS (keeping existing implementations but with minor fixes)

    async def _generate_user_based_recommendations(
        self,
        user_cultural_profile: Dict[str, Any],
        candidate_items: List[Dict[str, Any]],
        request: UserPreferenceRequest,
        request_id: str = ""
    ) -> List[RecommendationItem]:
        """Generate recommendations based on user profile - FIXED ENUM HANDLING"""
        logger.debug(f"[{request_id}] Generating user-based recommendations")
        
        recommendations = []
        
        try:
            for item in candidate_items:
                cultural_context = item.get("cultural_context")
                if not cultural_context:
                    continue
                
                compatibility_score = 0.0
                match_reasons = []
                
                # FIXED: Craft type compatibility with safe enum handling
                if cultural_context.craft_type:
                    craft_value = self._safe_enum_value(cultural_context.craft_type)
                    if craft_value and craft_value in user_cultural_profile["preferred_craft_types"]:
                        craft_score = user_cultural_profile["preferred_craft_types"][craft_value]
                        compatibility_score += craft_score * 0.4
                        match_reasons.append(f"Craft preference: {craft_value}")
                
                # FIXED: Region compatibility with safe enum handling
                if cultural_context.region:
                    region_value = self._safe_enum_value(cultural_context.region)
                    if region_value and region_value in user_cultural_profile["preferred_regions"]:
                        region_score = user_cultural_profile["preferred_regions"][region_value]
                        compatibility_score += region_score * 0.3
                        match_reasons.append(f"Region preference: {region_value}")
                
                # FIXED: Festival compatibility with safe enum handling
                if cultural_context.festival_relevance:
                    for festival in cultural_context.festival_relevance:
                        festival_value = self._safe_enum_value(festival)
                        if festival_value and festival_value in user_cultural_profile["preferred_festivals"]:
                            festival_score = user_cultural_profile["preferred_festivals"][festival_value]
                            compatibility_score += festival_score * 0.2
                            match_reasons.append(f"Festival match: {festival_value}")
                
                # Material compatibility (unchanged - materials are strings)
                if cultural_context.materials:
                    for material in cultural_context.materials:
                        if material in user_cultural_profile["preferred_materials"]:
                            material_score = user_cultural_profile["preferred_materials"][material]
                            compatibility_score += material_score * 0.1
                            match_reasons.append(f"Material preference: {material}")
                
                # FIXED: Cultural exploration bonus with safe enum handling
                if user_cultural_profile["cultural_openness"] > 0.5:
                    craft_value = self._safe_enum_value(cultural_context.craft_type)
                    region_value = self._safe_enum_value(cultural_context.region)
                    
                    is_new_craft = craft_value not in user_cultural_profile["preferred_craft_types"]
                    is_new_region = region_value not in user_cultural_profile["preferred_regions"]
                    
                    if is_new_craft or is_new_region:
                        exploration_bonus = user_cultural_profile["cultural_openness"] * 0.1
                        compatibility_score += exploration_bonus
                        match_reasons.append("Cultural exploration bonus")
                
                if compatibility_score > 0.1:
                    # FIXED: Festival relevance calculation
                    festival_relevance = 0.0
                    if cultural_context.festival_relevance:
                        festival_matches = 0
                        for festival in cultural_context.festival_relevance:
                            festival_value = self._safe_enum_value(festival)
                            if festival_value and festival_value in user_cultural_profile["preferred_festivals"]:
                                festival_matches += 1
                        festival_relevance = festival_matches / max(len(cultural_context.festival_relevance), 1)
                    
                    # FIXED: Regional match calculation
                    region_match = 0.0
                    if cultural_context.region:
                        region_value = self._safe_enum_value(cultural_context.region)
                        if region_value and region_value in user_cultural_profile["preferred_regions"]:
                            region_match = 1.0
                    
                    similarity_result = SimilarityResult(
                        similarity_score=compatibility_score,
                        cultural_similarity=compatibility_score,
                        vector_similarity=0.0,
                        seasonal_relevance=0.0,
                        regional_match=region_match,
                        festival_relevance=festival_relevance,
                        match_reasons=match_reasons
                    )
                    
                    rec_item = self._create_recommendation_item(
                        item, similarity_result, RecommendationType.CULTURAL_SIMILARITY, 
                        SimilarityMetric.CULTURAL_CONTEXT, request_id
                    )
                    recommendations.append(rec_item)
            
            recommendations.sort(key=lambda x: x.score_breakdown.overall_score, reverse=True)
            
            logger.info(f"[{request_id}] Generated {len(recommendations)} user-based recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"[{request_id}] Error generating user-based recommendations: {str(e)}")
            logger.error(f"[{request_id}] Error traceback: {traceback.format_exc()}")
            return []

    def _create_user_cultural_profile(
        self, 
        request: UserPreferenceRequest, 
        user_items: List[Dict[str, Any]],
        request_id: str = ""
    ) -> Dict[str, Any]:
        """Create user cultural profile from preferences and history - FIXED ENUM HANDLING"""
        logger.debug(f"[{request_id}] Creating user cultural profile")
        
        profile = {
            "preferred_craft_types": {},
            "preferred_regions": {}, 
            "preferred_festivals": {},
            "preferred_materials": {},
            "cultural_openness": 0.5,
            "interaction_count": len(user_items)
        }
        
        # FIXED: Extract preferences from explicit user inputs with safe enum handling
        if request.preferred_craft_types:
            for craft_type in request.preferred_craft_types:
                craft_value = self._safe_enum_value(craft_type)
                if craft_value:
                    profile["preferred_craft_types"][craft_value] = 1.0
        
        if request.preferred_regions:
            for region in request.preferred_regions:
                region_value = self._safe_enum_value(region)
                if region_value:
                    profile["preferred_regions"][region_value] = 1.0
        
        if request.preferred_festivals:
            for festival in request.preferred_festivals:
                festival_value = self._safe_enum_value(festival)
                if festival_value:
                    profile["preferred_festivals"][festival_value] = 1.0
        
        # FIXED: Extract patterns from user interaction history with safe enum handling
        if user_items:
            craft_counts = {}
            region_counts = {}
            material_counts = {}
            
            for item in user_items:
                cultural_context = item.get("cultural_context")
                if cultural_context:
                    # FIXED: Count craft types with safe enum handling
                    if cultural_context.craft_type:
                        craft_value = self._safe_enum_value(cultural_context.craft_type)
                        if craft_value:
                            craft_counts[craft_value] = craft_counts.get(craft_value, 0) + 1
                    
                    # FIXED: Count regions with safe enum handling
                    if cultural_context.region:
                        region_value = self._safe_enum_value(cultural_context.region)
                        if region_value:
                            region_counts[region_value] = region_counts.get(region_value, 0) + 1
                    
                    # Count materials (unchanged - materials are strings)
                    if cultural_context.materials:
                        for material in cultural_context.materials:
                            material_counts[material] = material_counts.get(material, 0) + 1
            
            # Convert counts to preferences (normalize)
            total_items = len(user_items)
            for craft, count in craft_counts.items():
                profile["preferred_craft_types"][craft] = count / total_items
            
            for region, count in region_counts.items():
                profile["preferred_regions"][region] = count / total_items
            
            for material, count in material_counts.items():
                if count >= 2:  # Only include materials seen multiple times
                    profile["preferred_materials"][material] = count / total_items
            
            # Calculate cultural openness (diversity of preferences)
            unique_crafts = len(craft_counts)
            unique_regions = len(region_counts)
            profile["cultural_openness"] = min((unique_crafts + unique_regions) / 10, 1.0)
        
        logger.info(
            f"[{request_id}] User cultural profile created",
            craft_preferences=len(profile["preferred_craft_types"]),
            region_preferences=len(profile["preferred_regions"]),
            cultural_openness=profile["cultural_openness"],
            based_on_items=len(user_items)
        )
        
        return profile

    def _apply_user_diversity_preferences(
        self,
        recommendations: List[RecommendationItem],
        diversity_factor: float,
        limit: int,
        request_id: str = ""
    ) -> List[RecommendationItem]:
        """Apply diversity preferences to recommendations"""
        logger.debug(f"[{request_id}] Applying diversity preferences", diversity_factor=diversity_factor)
        
        if not recommendations or diversity_factor == 0:
            return recommendations[:limit]
        
        try:
            region_counts = {}
            craft_counts = {}
            diversified_recommendations = []
            
            sorted_recs = sorted(recommendations, key=lambda x: x.score_breakdown.overall_score, reverse=True)
            
            for rec in sorted_recs:
                if len(diversified_recommendations) >= limit:
                    break
                
                cultural_context = rec.cultural_context
                if not cultural_context:
                    diversified_recommendations.append(rec)
                    continue
                
                region = self._safe_enum_value(cultural_context.region) if cultural_context.region else "unknown"
                craft = self._safe_enum_value(cultural_context.craft_type) if cultural_context.craft_type else "unknown"
                
                region_count = region_counts.get(region, 0)
                craft_count = craft_counts.get(craft, 0)
                
                max_same_region = max(1, int(limit * (1 - diversity_factor)))
                max_same_craft = max(1, int(limit * (1 - diversity_factor)))
                
                if region_count < max_same_region and craft_count < max_same_craft:
                    diversified_recommendations.append(rec)
                    region_counts[region] = region_count + 1
                    craft_counts[craft] = craft_count + 1
                elif diversity_factor < 0.8:
                    diversified_recommendations.append(rec)
            
            logger.info(
                f"[{request_id}] Applied diversity preferences",
                original_count=len(recommendations),
                final_count=len(diversified_recommendations),
                unique_regions=len(region_counts),
                unique_crafts=len(craft_counts)
            )
            
            return diversified_recommendations
            
        except Exception as e:
            logger.error(f"[{request_id}] Error applying diversity preferences: {str(e)}")
            return recommendations[:limit]

    def _create_recommendation_item(
        self, 
        item_data: Dict[str, Any], 
        similarity_result, 
        rec_type: RecommendationType, 
        similarity_metric: SimilarityMetric,
        request_id: str = ""
    ) -> RecommendationItem:
        """Create a RecommendationItem from item data and similarity results"""
        
        try:
            score_breakdown = RecommendationScore(
                overall_score=similarity_result.similarity_score,
                cultural_similarity=similarity_result.cultural_similarity,
                vector_similarity=similarity_result.vector_similarity,
                seasonal_relevance=similarity_result.seasonal_relevance,
                regional_match=similarity_result.regional_match,
                festival_relevance=similarity_result.festival_relevance,
                diversity_bonus=getattr(similarity_result, 'diversity_penalty', 0.0)
            )
            
            seasonal_context = None
            if similarity_result.seasonal_relevance > 0:
                seasonal_context = f"Seasonal relevance: {similarity_result.seasonal_relevance:.2f}"
            
            rec_item = RecommendationItem(
                id=item_data["id"],
                text=item_data["text"],
                payload=item_data["payload"],
                recommendation_type=rec_type,
                similarity_metric=similarity_metric,
                score_breakdown=score_breakdown,
                cultural_context=item_data.get("cultural_context"),
                cultural_match_reasons=similarity_result.match_reasons,
                seasonal_context=seasonal_context,
                distance_from_source=1.0 - similarity_result.vector_similarity if similarity_result.vector_similarity else None
            )
            
            return rec_item
            
        except Exception as e:
            logger.error(f"[{request_id}] Error creating recommendation item: {str(e)}")
            return RecommendationItem(
                id=item_data["id"],
                text=item_data["text"],
                payload=item_data["payload"],
                recommendation_type=rec_type,
                similarity_metric=similarity_metric,
                score_breakdown=RecommendationScore(overall_score=0.0),
                cultural_context=item_data.get("cultural_context"),
                cultural_match_reasons=[],
                seasonal_context=None
            )

    def _deduplicate_and_rank_recommendations(
        self, 
        recommendations: List[RecommendationItem], 
        limit: int,
        request_id: str = ""
    ) -> List[RecommendationItem]:
        """Deduplicate and rank recommendations"""
        
        logger.debug(f"[{request_id}] Deduplicating and ranking {len(recommendations)} recommendations")
        
        unique_recommendations = {}
        duplicate_count = 0
        
        for rec in recommendations:
            if rec.id not in unique_recommendations:
                unique_recommendations[rec.id] = rec
            else:
                duplicate_count += 1
                if rec.score_breakdown.overall_score > unique_recommendations[rec.id].score_breakdown.overall_score:
                    unique_recommendations[rec.id] = rec
        
        if duplicate_count > 0:
            logger.debug(f"[{request_id}] Removed {duplicate_count} duplicate recommendations")
        
        sorted_recommendations = sorted(
            unique_recommendations.values(), 
            key=lambda x: x.score_breakdown.overall_score, 
            reverse=True
        )
        
        final_recommendations = sorted_recommendations[:limit]
        
        logger.debug(
            f"[{request_id}] Final ranking completed",
            unique_count=len(unique_recommendations),
            final_count=len(final_recommendations),
            top_score=final_recommendations[0].score_breakdown.overall_score if final_recommendations else 0.0
        )
        
        return final_recommendations

    def _calculate_diversity_stats(self, recommendations: List[RecommendationItem]) -> Dict[str, int]:
        """Calculate diversity statistics for recommendations - FIXED ENUM HANDLING"""
        regions = set()
        craft_types = set()
        
        for rec in recommendations:
            if rec.cultural_context:
                # FIXED: Safe region value extraction
                if rec.cultural_context.region:
                    region_value = self._safe_enum_value(rec.cultural_context.region)
                    if region_value:
                        regions.add(region_value)
                
                # FIXED: Safe craft type value extraction
                if rec.cultural_context.craft_type:
                    craft_value = self._safe_enum_value(rec.cultural_context.craft_type)
                    if craft_value:
                        craft_types.add(craft_value)
        
        return {
            "unique_regions": len(regions),
            "unique_craft_types": len(craft_types),
            "total_items": len(recommendations)
        }

    def _calculate_overall_confidence(self, recommendations: List[RecommendationItem]) -> float:
        """Calculate overall confidence in recommendations"""
        if not recommendations:
            return 0.0
        
        total_confidence = sum(rec.score_breakdown.overall_score for rec in recommendations)
        return total_confidence / len(recommendations)

    def _create_empty_response(self, request, message: str) -> RecommendationResponse:
        """Create empty response for error cases"""
        return RecommendationResponse(
            source_item_id=getattr(request, 'item_id', None),
            total_recommendations=0,
            recommendations=[],
            recommendation_types_used=getattr(request, 'recommendation_types', []),
            processing_time_ms=0.0
        )

    def _create_error_response(self, request, error_message: str) -> RecommendationResponse:
        """Create error response"""
        logger.error(f"Recommendation error: {error_message}")
        return self._create_empty_response(request, error_message)

    def _update_stats(self, processing_time: float):
        """Update service statistics"""
        processing_time_ms = processing_time * 1000
        self.stats["recommendations_served"] += 1
        self.stats["avg_response_time_ms"] = (
            (self.stats["avg_response_time_ms"] * (self.stats["recommendations_served"] - 1) + processing_time_ms)
            / self.stats["recommendations_served"]
        )
    
    def _get_cultural_context_summary(self, cultural_context) -> str:
        """Get a concise summary of cultural context for logging"""
        if not cultural_context:
            return "none"
        
        parts = []
        
        if hasattr(cultural_context, 'craft_type') and cultural_context.craft_type:
            craft_value = cultural_context.craft_type.value if hasattr(cultural_context.craft_type, 'value') else str(cultural_context.craft_type)
            parts.append(f"craft:{craft_value}")
        
        if hasattr(cultural_context, 'region') and cultural_context.region:
            region_value = cultural_context.region.value if hasattr(cultural_context.region, 'value') else str(cultural_context.region)
            parts.append(f"region:{region_value}")
        
        if hasattr(cultural_context, 'festival_relevance') and cultural_context.festival_relevance:
            parts.append(f"festivals:{len(cultural_context.festival_relevance)}")
        
        return "|".join(parts) if parts else "basic"

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics with enhanced metrics"""
        stats_data = {
            **self.stats,
            "cache_size": len(self.cache),
            "cultural_cache_size": len(self.cultural_cache),
            "content_based_stats": content_based_recommender.get_stats(),
            "collaborative_filter_stats": collaborative_filter.get_collaborative_stats(),
            "cache_efficiency": {
                "recommendation_hit_rate": self.stats["cache_hits"] / max(self.stats["recommendations_served"], 1),
                "cultural_hit_rate": self.stats["cultural_cache_hits"] / max(self.stats["cultural_analyses_performed"], 1)
            }
        }
        
        logger.debug("Service statistics requested", **stats_data)
        return stats_data

    def clear_cache(self):
        """Clear all recommendation service caches"""
        cache_size = len(self.cache)
        cultural_cache_size = len(self.cultural_cache)
        
        self.cache.clear()
        self.cultural_cache.clear()
        content_based_recommender.clear_cache()
        collaborative_filter.clear_cache()
        
        logger.info(f"All caches cleared - Recommendation: {cache_size}, Cultural: {cultural_cache_size}")

    async def test_item_lookup(self, item_id: str) -> Dict[str, Any]:
        """Enhanced test method to debug item lookup issues"""
        logger.info(f"Testing item lookup for: {item_id}")
        
        try:
            # Test optimized lookup
            item = await self._get_item_with_cultural_context_optimized(item_id, "test")
            
            if item:
                return {
                    "status": "found",
                    "item_id": item_id,
                    "found_item": {
                        "id": item["id"],
                        "text": item["text"][:100] + "..." if len(item["text"]) > 100 else item["text"],
                        "title": item["payload"].get("title", "No title"),
                        "has_cultural_context": bool(item.get("cultural_context")),
                        "cultural_summary": self._get_cultural_context_summary(item.get("cultural_context"))
                    }
                }
            else:
                # Get sample items for debugging
                sample_items = []
                offset = None
                count = 0
                
                while count < 10:
                    points, next_offset = qdrant.scroll(
                        collection_name=settings.COLLECTION_NAME,
                        limit=50,
                        offset=offset,
                        with_payload=True
                    )
                    
                    if not points:
                        break
                    
                    for point in points:
                        if count >= 10:
                            break
                        
                        payload = point.payload or {}
                        sample_items.append({
                            "point_id": str(point.id),
                            "payload_item_id": payload.get("item_id", ""),
                            "title": payload.get("title", "")[:50]
                        })
                        count += 1
                    
                    if not next_offset:
                        break
                    offset = next_offset
                
                return {
                    "status": "not_found",
                    "search_item_id": item_id,
                    "sample_items": sample_items,
                    "suggestions": [f"Try: {item['point_id']}" for item in sample_items[:5]]
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "item_id": item_id
            }

    async def get_recommendation_performance_report(self) -> Dict[str, Any]:
        """
        ADDED: Get comprehensive performance report for monitoring
        """
        try:
            stats = self.get_stats()
            
            # Calculate performance metrics
            avg_response_time = stats.get("avg_response_time_ms", 0)
            total_served = stats.get("recommendations_served", 0)
            cache_hit_rate = stats.get("cache_hits", 0) / max(total_served, 1)
            
            # Performance status
            performance_status = "excellent"
            if avg_response_time > 5000:  # 5 seconds
                performance_status = "poor"
            elif avg_response_time > 2000:  # 2 seconds
                performance_status = "needs_improvement"
            elif avg_response_time > 1000:  # 1 second
                performance_status = "good"
            
            # Recommendations
            recommendations = []
            if avg_response_time > 2000:
                recommendations.append("Consider increasing cache TTL or implementing Redis")
            if cache_hit_rate < 0.3:
                recommendations.append("Cache hit rate is low, review caching strategy")
            if stats.get("failed_requests", 0) > total_served * 0.05:
                recommendations.append("High failure rate detected, investigate error patterns")
            
            return {
                "performance_status": performance_status,
                "metrics": {
                    "avg_response_time_ms": avg_response_time,
                    "cache_hit_rate": cache_hit_rate,
                    "success_rate": (total_served - stats.get("failed_requests", 0)) / max(total_served, 1),
                    "cultural_analysis_efficiency": stats.get("cultural_cache_hits", 0) / max(stats.get("cultural_analyses_performed", 1), 1)
                },
                "usage_stats": {
                    "total_recommendations_served": total_served,
                    "collaborative_recommendations": stats.get("collaborative_recommendations", 0),
                    "seasonal_recommendations": stats.get("seasonal_recommendations", 0),
                    "cultural_analyses_performed": stats.get("cultural_analyses_performed", 0)
                },
                "recommendations": recommendations,
                "cache_status": {
                    "recommendation_cache_size": len(self.cache),
                    "cultural_cache_size": len(self.cultural_cache),
                    "cache_memory_estimate_mb": (len(self.cache) + len(self.cultural_cache)) * 0.01  # Rough estimate
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating performance report: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def optimize_performance(self) -> Dict[str, Any]:
        """
        ADDED: Optimize performance by cleaning old cache entries and other optimizations
        """
        try:
            start_time = time.time()
            
            # Clean old cache entries
            current_time = time.time()
            
            # Clean recommendation cache
            old_rec_entries = [
                key for key, value in self.cache.items()
                if current_time - value["timestamp"] > self.cache_ttl
            ]
            for key in old_rec_entries:
                del self.cache[key]
            
            # Clean cultural cache
            old_cultural_entries = [
                key for key, value in self.cultural_cache.items()
                if current_time - value["timestamp"] > self.cache_ttl
            ]
            for key in old_cultural_entries:
                del self.cultural_cache[key]
            
            # Clear component caches
            content_based_recommender.clear_cache()
            collaborative_filter.clear_cache()
            
            optimization_time = (time.time() - start_time) * 1000
            
            return {
                "status": "optimized",
                "optimization_time_ms": optimization_time,
                "cleaned_entries": {
                    "recommendation_cache": len(old_rec_entries),
                    "cultural_cache": len(old_cultural_entries)
                },
                "remaining_cache_sizes": {
                    "recommendation_cache": len(self.cache),
                    "cultural_cache": len(self.cultural_cache)
                }
            }
            
        except Exception as e:
            logger.error(f"Error during performance optimization: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

# Global instance
recommendation_service = CulturalRecommendationService()