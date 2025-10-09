# algorithms/content_based.py
import time
from typing import Dict, List, Tuple, Optional, Set, Any
from collections import defaultdict, Counter
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.models.cultural_models import (
    CulturalContext, CraftType, IndianRegion, Festival, CulturalSignificance
)
from src.models.recommendation_models import (
    RecommendationScore, SimilarityMetric, CulturalSimilarityConfig,
    RegionalDiscoveryConfig, SeasonalBoostConfig
)
from src.utils.cultural_analyzer import CulturalKnowledgeBase
from src.utils.logger import recommendation_logger as logger

@dataclass
class SimilarityResult:
    """Result of similarity calculation between two items"""
    similarity_score: float
    cultural_similarity: float
    vector_similarity: float
    seasonal_relevance: float
    regional_match: float
    festival_relevance: float
    match_reasons: List[str]
    diversity_penalty: float = 0.0

class CulturalContentBasedRecommender:
    """
    Content-based recommender leveraging cultural intelligence
    Enhanced with comprehensive logging for debugging and monitoring
    """
    
    def __init__(self):
        logger.info("Initializing Cultural Content-Based Recommender")
        
        try:
            self.knowledge_base = CulturalKnowledgeBase()
            logger.debug("Cultural knowledge base loaded for content-based recommendations")
        except Exception as e:
            logger.error("Failed to initialize cultural knowledge base in content-based recommender", error=str(e))
            raise
        
        # Default configurations matching your cultural service patterns
        self.cultural_config = CulturalSimilarityConfig()
        self.regional_config = RegionalDiscoveryConfig()
        self.seasonal_config = SeasonalBoostConfig()
        
        # Performance tracking similar to your cultural service
        self.stats = {
            "recommendations_generated": 0,
            "cultural_similarities_calculated": 0,
            "cache_hits": 0,
            "avg_calculation_time_ms": 0.0,
            "fallback_calculations": 0,
            "failed_calculations": 0
        }
        
        # Simple cache similar to your cultural analysis cache
        self.similarity_cache = {}
        self.cache_ttl = 1800  # 30 minutes
        
        logger.info("Cultural Content-Based Recommender initialized successfully")

    def calculate_cultural_similarity(
        self, 
        source_context: CulturalContext, 
        candidate_context: CulturalContext,
        config: Optional[CulturalSimilarityConfig] = None,
        request_id: str = ""
    ) -> SimilarityResult:
        """
        Calculate cultural similarity between two items using your cultural taxonomy
        Enhanced with comprehensive logging
        """
        calc_start = time.time()
        
        if not config:
            config = self.cultural_config
        
        # Safe enum value extraction for logging
        source_craft_val = source_context.craft_type.value if hasattr(source_context.craft_type, 'value') else str(source_context.craft_type) if source_context.craft_type else "none"
        source_region_val = source_context.region.value if hasattr(source_context.region, 'value') else str(source_context.region) if source_context.region else "none"
        candidate_craft_val = candidate_context.craft_type.value if hasattr(candidate_context.craft_type, 'value') else str(candidate_context.craft_type) if candidate_context.craft_type else "none"
        candidate_region_val = candidate_context.region.value if hasattr(candidate_context.region, 'value') else str(candidate_context.region) if candidate_context.region else "none"
        
        logger.debug(
            f"[{request_id}] Calculating cultural similarity",
            source_craft=source_craft_val,
            source_region=source_region_val,
            candidate_craft=candidate_craft_val,
            candidate_region=candidate_region_val
        )
        
        match_reasons = []
        
        try:
            # Craft type similarity (highest weight)
            craft_similarity = 0.0
            if source_context.craft_type and candidate_context.craft_type:
                # Compare as strings for safety
                source_craft_str = str(source_context.craft_type)
                candidate_craft_str = str(candidate_context.craft_type)
                
                if source_craft_str == candidate_craft_str:
                    craft_similarity = 1.0
                    craft_value = source_context.craft_type.value if hasattr(source_context.craft_type, 'value') else str(source_context.craft_type)
                    match_reasons.append(f"Same craft type: {craft_value}")
                    logger.debug(f"[{request_id}] Exact craft type match: {craft_value}")
                else:
                    # Check for related craft types using your knowledge base
                    craft_similarity = self._calculate_craft_type_relatedness(
                        source_context.craft_type, candidate_context.craft_type, request_id
                    )
                    if craft_similarity > 0.3:
                        s_craft = source_context.craft_type.value if hasattr(source_context.craft_type, 'value') else str(source_context.craft_type)
                        c_craft = candidate_context.craft_type.value if hasattr(candidate_context.craft_type, 'value') else str(candidate_context.craft_type)
                        match_reasons.append(f"Related craft types: {s_craft} → {c_craft}")
                        logger.debug(f"[{request_id}] Related craft types: {craft_similarity:.2f}")
            
            # Regional similarity
            regional_similarity = 0.0
            if source_context.region and candidate_context.region:
                # Compare as strings for safety
                source_region_str = str(source_context.region)
                candidate_region_str = str(candidate_context.region)
                
                if source_region_str == candidate_region_str:
                    regional_similarity = 1.0
                    region_value = source_context.region.value if hasattr(source_context.region, 'value') else str(source_context.region)
                    match_reasons.append(f"Same region: {region_value}")
                    logger.debug(f"[{request_id}] Exact region match: {region_value}")
                else:
                    # Check for neighboring regions or cultural connections
                    regional_similarity = self._calculate_regional_relatedness(
                        source_context.region, candidate_context.region, request_id
                    )
                    if regional_similarity > 0.2:
                        s_region = source_context.region.value if hasattr(source_context.region, 'value') else str(source_context.region)
                        c_region = candidate_context.region.value if hasattr(candidate_context.region, 'value') else str(candidate_context.region)
                        match_reasons.append(f"Related regions: {s_region} → {c_region}")
                        logger.debug(f"[{request_id}] Related regions: {regional_similarity:.2f}")
            
            # Material similarity
            material_similarity = self._calculate_material_similarity(
                source_context.materials, candidate_context.materials, request_id
            )
            if material_similarity > 0.3:
                common_materials = set(source_context.materials) & set(candidate_context.materials)
                if common_materials:
                    match_reasons.append(f"Shared materials: {', '.join(list(common_materials)[:3])}")
                    logger.debug(f"[{request_id}] Material similarity: {material_similarity:.2f}")
            
            # Technique similarity
            technique_similarity = self._calculate_technique_similarity(
                source_context.traditional_techniques, candidate_context.traditional_techniques, request_id
            )
            if technique_similarity > 0.3:
                common_techniques = set(source_context.traditional_techniques) & set(candidate_context.traditional_techniques)
                if common_techniques:
                    match_reasons.append(f"Similar techniques: {', '.join(list(common_techniques)[:2])}")
                    logger.debug(f"[{request_id}] Technique similarity: {technique_similarity:.2f}")
            
            # Festival relevance similarity
            festival_similarity = self._calculate_festival_similarity(
                source_context.festival_relevance, candidate_context.festival_relevance, request_id
            )
            if festival_similarity > 0.3:
                common_festivals = set(source_context.festival_relevance) & set(candidate_context.festival_relevance)
                if common_festivals:
                    festival_values = [f.value if hasattr(f, 'value') else str(f) for f in common_festivals]
                    match_reasons.append(f"Festival relevance: {', '.join(festival_values)}")
                    logger.debug(f"[{request_id}] Festival similarity: {festival_similarity:.2f}")
            
            # Calculate weighted cultural similarity
            cultural_similarity = (
                craft_similarity * config.craft_type_weight +
                regional_similarity * config.region_weight +
                material_similarity * config.material_weight +
                technique_similarity * config.technique_weight +
                festival_similarity * config.festival_weight
            )
            
            # Apply seasonal relevance boost (similar to your seasonal context)
            seasonal_relevance = self._calculate_seasonal_relevance(candidate_context, request_id)
            
            calc_time = (time.time() - calc_start) * 1000
            self.stats["cultural_similarities_calculated"] += 1
            
            result = SimilarityResult(
                similarity_score=cultural_similarity,
                cultural_similarity=cultural_similarity,
                vector_similarity=0.0,  # Will be set by calling function if available
                seasonal_relevance=seasonal_relevance,
                regional_match=regional_similarity,
                festival_relevance=festival_similarity,
                match_reasons=match_reasons
            )
            
            logger.debug(
                f"[{request_id}] Cultural similarity calculated",
                processing_time_ms=calc_time,
                cultural_score=cultural_similarity,
                craft_score=craft_similarity,
                region_score=regional_similarity,
                material_score=material_similarity,
                technique_score=technique_similarity,
                festival_score=festival_similarity,
                seasonal_score=seasonal_relevance,
                match_reasons_count=len(match_reasons)
            )
            
            return result
            
        except Exception as e:
            calc_time = (time.time() - calc_start) * 1000
            self.stats["failed_calculations"] += 1
            logger.error(
                f"[{request_id}] Cultural similarity calculation failed",
                error=str(e),
                error_type=type(e).__name__,
                processing_time_ms=calc_time
            )
            
            # Return minimal similarity result
            return SimilarityResult(
                similarity_score=0.0,
                cultural_similarity=0.0,
                vector_similarity=0.0,
                seasonal_relevance=0.0,
                regional_match=0.0,
                festival_relevance=0.0,
                match_reasons=["Error in similarity calculation"]
            )

    def find_similar_items(
        self,
        source_item: Dict[str, Any],
        candidate_items: List[Dict[str, Any]],
        limit: int = 5,
        similarity_threshold: float = 0.3,
        enable_diversity: bool = True,
        request_id: str = ""
    ) -> List[Tuple[Dict[str, Any], SimilarityResult]]:
        """
        Find similar items using cultural intelligence
        Enhanced with comprehensive logging
        """
        start_time = time.time()
        
        logger.info(
            f"[{request_id}] Finding similar items",
            candidate_count=len(candidate_items),
            similarity_threshold=similarity_threshold,
            enable_diversity=enable_diversity,
            target_limit=limit
        )
        
        if not candidate_items:
            logger.warning(f"[{request_id}] No candidate items provided for similarity calculation")
            return []
        
        source_cultural_context = source_item.get('cultural_context')
        if not source_cultural_context:
            logger.warning(f"[{request_id}] Source item missing cultural context, recommendations may be limited")
            return []
        
        similarities = []
        region_counts = defaultdict(int)
        craft_counts = defaultdict(int)
        processed_count = 0
        skipped_count = 0
        
        # Safe enum value extraction for logging
        source_craft_val = source_cultural_context.craft_type.value if hasattr(source_cultural_context.craft_type, 'value') else str(source_cultural_context.craft_type) if source_cultural_context.craft_type else "none"
        source_region_val = source_cultural_context.region.value if hasattr(source_cultural_context.region, 'value') else str(source_cultural_context.region) if source_cultural_context.region else "none"
        
        logger.debug(
            f"[{request_id}] Starting similarity calculations",
            source_craft=source_craft_val,
            source_region=source_region_val
        )
        
        for candidate in candidate_items:
            candidate_cultural_context = candidate.get('cultural_context')
            if not candidate_cultural_context:
                skipped_count += 1
                continue
            
            # Skip if same item
            if source_item.get('id') == candidate.get('id'):
                skipped_count += 1
                continue
            
            # Calculate similarity
            try:
                similarity_result = self.calculate_cultural_similarity(
                    source_cultural_context, candidate_cultural_context, request_id=request_id
                )
                
                # Apply vector similarity if available
                if 'vector_similarity' in candidate:
                    similarity_result.vector_similarity = candidate['vector_similarity']
                    # Combine cultural and vector similarity
                    similarity_result.similarity_score = (
                        similarity_result.cultural_similarity * 0.7 +
                        similarity_result.vector_similarity * 0.3
                    )
                    logger.debug(
                        f"[{request_id}] Combined similarity for {candidate['id']}",
                        cultural=similarity_result.cultural_similarity,
                        vector=similarity_result.vector_similarity,
                        combined=similarity_result.similarity_score
                    )
                
                # Apply diversity penalty if needed
                if enable_diversity:
                    diversity_penalty = self._calculate_diversity_penalty(
                        candidate_cultural_context, region_counts, craft_counts, request_id
                    )
                    similarity_result.diversity_penalty = diversity_penalty
                    similarity_result.similarity_score += diversity_penalty
                
                # Check threshold
                if similarity_result.similarity_score >= similarity_threshold:
                    similarities.append((candidate, similarity_result))
                    
                    # Track for diversity - safe enum value extraction
                    if enable_diversity:
                        if candidate_cultural_context.region:
                            region_val = candidate_cultural_context.region.value if hasattr(candidate_cultural_context.region, 'value') else str(candidate_cultural_context.region)
                            region_counts[region_val] += 1
                        if candidate_cultural_context.craft_type:
                            craft_val = candidate_cultural_context.craft_type.value if hasattr(candidate_cultural_context.craft_type, 'value') else str(candidate_cultural_context.craft_type)
                            craft_counts[craft_val] += 1
                    
                    logger.debug(
                        f"[{request_id}] Added candidate {candidate['id']}",
                        score=similarity_result.similarity_score,
                        reasons_count=len(similarity_result.match_reasons)
                    )
                else:
                    logger.debug(
                        f"[{request_id}] Rejected candidate {candidate['id']}",
                        score=similarity_result.similarity_score,
                        threshold=similarity_threshold
                    )
                
                processed_count += 1
                
            except Exception as e:
                logger.error(
                    f"[{request_id}] Error calculating similarity for candidate {candidate.get('id', 'unknown')}",
                    error=str(e),
                    error_type=type(e).__name__
                )
                skipped_count += 1
                continue
        
        # Sort by similarity score (descending)
        similarities.sort(key=lambda x: x[1].similarity_score, reverse=True)
        
        # Limit results
        top_similarities = similarities[:limit]
        
        # Update stats
        processing_time = (time.time() - start_time) * 1000
        self.stats["recommendations_generated"] += 1
        self.stats["avg_calculation_time_ms"] = (
            (self.stats["avg_calculation_time_ms"] * (self.stats["recommendations_generated"] - 1) + processing_time)
            / self.stats["recommendations_generated"]
        )
        
        logger.info(
            f"[{request_id}] Similar items calculation completed",
            processing_time_ms=processing_time,
            candidates_processed=processed_count,
            candidates_skipped=skipped_count,
            similarities_found=len(similarities),
            returned_count=len(top_similarities),
            unique_regions=len(region_counts),
            unique_crafts=len(craft_counts),
            top_score=top_similarities[0][1].similarity_score if top_similarities else 0.0
        )
        
        return top_similarities

    def find_regional_discoveries(
        self,
        source_item: Dict[str, Any],
        candidate_items: List[Dict[str, Any]],
        limit: int = 5,
        diversity_factor: float = 0.3,
        request_id: str = ""
    ) -> List[Tuple[Dict[str, Any], SimilarityResult]]:
        """
        Find items from different regions to promote cross-cultural discovery
        Enhanced with comprehensive logging
        """
        start_time = time.time()
        
        logger.info(
            f"[{request_id}] Finding regional discoveries",
            candidate_count=len(candidate_items),
            diversity_factor=diversity_factor,
            target_limit=limit
        )
        
        source_cultural_context = source_item.get('cultural_context')
        if not source_cultural_context or not source_cultural_context.region:
            logger.warning(f"[{request_id}] Source item missing region information for regional discovery")
            return []
        
        source_region = source_cultural_context.region
        regional_discoveries = []
        regions_found = set()
        
        # Safe enum value extraction for logging
        source_region_val = source_region.value if hasattr(source_region, 'value') else str(source_region)
        logger.debug(f"[{request_id}] Source region: {source_region_val}, looking for different regions")
        
        for candidate in candidate_items:
            candidate_cultural_context = candidate.get('cultural_context')
            if not candidate_cultural_context or not candidate_cultural_context.region:
                continue
            
            # Compare as strings for safety
            source_region_str = str(source_region)
            candidate_region_str = str(candidate_cultural_context.region)
            unknown_str = str(IndianRegion.UNKNOWN)
            
            # Skip same region unless it's unknown
            if candidate_region_str == source_region_str and source_region_str != unknown_str:
                continue
            
            try:
                # Calculate base cultural similarity
                similarity_result = self.calculate_cultural_similarity(
                    source_cultural_context, candidate_cultural_context, request_id=request_id
                )
                
                # Apply regional discovery bonus
                regional_bonus = self._calculate_regional_discovery_bonus(
                    source_region, candidate_cultural_context.region, request_id
                )
                
                similarity_result.similarity_score += regional_bonus
                
                # Safe enum value extraction for match reasons
                region_val = candidate_cultural_context.region.value if hasattr(candidate_cultural_context.region, 'value') else str(candidate_cultural_context.region)
                similarity_result.match_reasons.append(f"Regional discovery: {region_val}")
                
                regional_discoveries.append((candidate, similarity_result))
                regions_found.add(region_val)
                
                logger.debug(
                    f"[{request_id}] Added regional discovery {candidate['id']}",
                    region=region_val,
                    base_score=similarity_result.cultural_similarity,
                    bonus=regional_bonus,
                    final_score=similarity_result.similarity_score
                )
                
            except Exception as e:
                logger.error(
                    f"[{request_id}] Error in regional discovery for candidate {candidate.get('id', 'unknown')}",
                    error=str(e)
                )
                continue
        
        # Sort by cultural similarity (even across regions)
        regional_discoveries.sort(key=lambda x: x[1].similarity_score, reverse=True)
        
        processing_time = (time.time() - start_time) * 1000
        final_discoveries = regional_discoveries[:limit]
        
        logger.info(
            f"[{request_id}] Regional discoveries completed",
            processing_time_ms=processing_time,
            discoveries_found=len(regional_discoveries),
            unique_regions_found=len(regions_found),
            returned_count=len(final_discoveries),
            source_region=source_region_val
        )
        
        return final_discoveries

    def find_seasonal_recommendations(
        self,
        candidate_items: List[Dict[str, Any]],
        current_festivals: List[Festival],
        limit: int = 10,
        request_id: str = ""
    ) -> List[Tuple[Dict[str, Any], SimilarityResult]]:
        """
        Find items relevant to current festivals/seasons
        Enhanced with comprehensive logging
        """
        start_time = time.time()
        
        # Safe festival value extraction
        festival_values = [f.value if hasattr(f, 'value') else str(f) for f in current_festivals]
        
        logger.info(
            f"[{request_id}] Finding seasonal recommendations",
            candidate_count=len(candidate_items),
            active_festivals=festival_values,
            target_limit=limit
        )
        
        seasonal_items = []
        festival_matches = defaultdict(int)
        significance_matches = defaultdict(int)
        
        for candidate in candidate_items:
            candidate_cultural_context = candidate.get('cultural_context')
            if not candidate_cultural_context:
                continue
            
            try:
                # Check festival relevance
                festival_match_score = 0.0
                matching_festivals = []
                
                for festival in current_festivals:
                    # Compare as strings for safety
                    festival_str = str(festival)
                    for candidate_festival in candidate_cultural_context.festival_relevance:
                        if str(candidate_festival) == festival_str:
                            festival_match_score += 0.3  # Each matching festival adds score
                            matching_festivals.append(festival)
                            festival_val = festival.value if hasattr(festival, 'value') else str(festival)
                            festival_matches[festival_val] += 1
                            break
                
                # Check cultural significance for seasonal items
                seasonal_significance_bonus = 0.0
                # Compare as strings for safety
                sig_str = str(candidate_cultural_context.cultural_significance)
                if (sig_str == str(CulturalSignificance.FESTIVAL_ITEM) or 
                    sig_str == str(CulturalSignificance.GIFT_ITEM) or
                    sig_str == str(CulturalSignificance.DECORATIVE)):
                    seasonal_significance_bonus = 0.2
                    sig_val = candidate_cultural_context.cultural_significance.value if hasattr(candidate_cultural_context.cultural_significance, 'value') else str(candidate_cultural_context.cultural_significance)
                    significance_matches[sig_val] += 1
                
                total_seasonal_score = festival_match_score + seasonal_significance_bonus
                
                if total_seasonal_score > 0.1:  # Minimum seasonal relevance
                    # Safe festival value extraction for match reasons
                    festival_values = [f.value if hasattr(f, 'value') else str(f) for f in matching_festivals]
                    
                    similarity_result = SimilarityResult(
                        similarity_score=total_seasonal_score,
                        cultural_similarity=0.0,
                        vector_similarity=0.0,
                        seasonal_relevance=total_seasonal_score,
                        regional_match=0.0,
                        festival_relevance=festival_match_score,
                        match_reasons=[f"Festival relevance: {', '.join(festival_values)}"] if matching_festivals else ["Seasonal significance"]
                    )
                    
                    seasonal_items.append((candidate, similarity_result))
                    
                    logger.debug(
                        f"[{request_id}] Added seasonal item {candidate['id']}",
                        festivals_matched=len(matching_festivals),
                        festival_score=festival_match_score,
                        significance_bonus=seasonal_significance_bonus,
                        total_score=total_seasonal_score
                    )
            
            except Exception as e:
                logger.error(
                    f"[{request_id}] Error in seasonal relevance calculation for {candidate.get('id', 'unknown')}",
                    error=str(e)
                )
                continue
        
        # Sort by seasonal relevance
        seasonal_items.sort(key=lambda x: x[1].seasonal_relevance, reverse=True)
        
        processing_time = (time.time() - start_time) * 1000
        final_items = seasonal_items[:limit]
        
        logger.info(
            f"[{request_id}] Seasonal recommendations completed",
            processing_time_ms=processing_time,
            seasonal_items_found=len(seasonal_items),
            returned_count=len(final_items),
            festival_distribution=dict(festival_matches),
            significance_distribution=dict(significance_matches),
            top_seasonal_score=final_items[0][1].seasonal_relevance if final_items else 0.0
        )
        
        return final_items

    # Helper methods for similarity calculations with logging

    def _calculate_craft_type_relatedness(self, craft1: CraftType, craft2: CraftType, request_id: str = "") -> float:
        """Calculate relatedness between different craft types"""
        # Define craft type relationships based on your cultural knowledge
        craft_relationships = {
            CraftType.POTTERY: [CraftType.SCULPTURE, CraftType.METALCRAFT],
            CraftType.TEXTILES: [CraftType.LEATHER_WORK, CraftType.PAPER_CRAFT],
            CraftType.JEWELRY: [CraftType.METALCRAFT, CraftType.GLASS_WORK],
            CraftType.WOODWORK: [CraftType.BAMBOO_CRAFT, CraftType.SCULPTURE],
            CraftType.PAINTING: [CraftType.TEXTILES, CraftType.PAPER_CRAFT],
            CraftType.METALCRAFT: [CraftType.JEWELRY, CraftType.POTTERY]
        }
        
        relatedness = 0.0
        
        # Compare as strings for safety
        craft1_str = str(craft1)
        craft2_str = str(craft2)
        
        # Check relationships using string comparison
        for key_craft, related_crafts in craft_relationships.items():
            if str(key_craft) == craft1_str:
                if any(str(rc) == craft2_str for rc in related_crafts):
                    relatedness = 0.6
                    break
            elif str(key_craft) == craft2_str:
                if any(str(rc) == craft1_str for rc in related_crafts):
                    relatedness = 0.6
                    break
        
        if relatedness > 0:
            craft1_val = craft1.value if hasattr(craft1, 'value') else str(craft1)
            craft2_val = craft2.value if hasattr(craft2, 'value') else str(craft2)
            logger.debug(f"[{request_id}] Craft type relatedness: {craft1_val} → {craft2_val} = {relatedness}")
        
        return relatedness

    def _calculate_regional_relatedness(self, region1: IndianRegion, region2: IndianRegion, request_id: str = "") -> float:
        """Calculate relatedness between regions"""
        # Define neighboring regions or cultural connections
        regional_connections = {
            IndianRegion.RAJASTHAN: [IndianRegion.GUJARAT, IndianRegion.MADHYA_PRADESH],
            IndianRegion.GUJARAT: [IndianRegion.RAJASTHAN, IndianRegion.MAHARASHTRA],
            IndianRegion.TAMIL_NADU: [IndianRegion.KERALA, IndianRegion.KARNATAKA],
            IndianRegion.WEST_BENGAL: [IndianRegion.ODISHA, IndianRegion.ASSAM],
        }
        
        relatedness = 0.0
        
        # Compare as strings for safety
        region1_str = str(region1)
        region2_str = str(region2)
        
        # Check relationships using string comparison
        for key_region, connected_regions in regional_connections.items():
            if str(key_region) == region1_str:
                if any(str(cr) == region2_str for cr in connected_regions):
                    relatedness = 0.4
                    break
            elif str(key_region) == region2_str:
                if any(str(cr) == region1_str for cr in connected_regions):
                    relatedness = 0.4
                    break
        
        if relatedness > 0:
            region1_val = region1.value if hasattr(region1, 'value') else str(region1)
            region2_val = region2.value if hasattr(region2, 'value') else str(region2)
            logger.debug(f"[{request_id}] Regional relatedness: {region1_val} → {region2_val} = {relatedness}")
        
        return relatedness

    def _calculate_material_similarity(self, materials1: List[str], materials2: List[str], request_id: str = "") -> float:
        """Calculate similarity based on shared materials"""
        if not materials1 or not materials2:
            return 0.0
        
        set1 = set(materials1)
        set2 = set(materials2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        if union == 0:
            return 0.0
        
        jaccard_similarity = intersection / union
        
        if jaccard_similarity > 0:
            logger.debug(
                f"[{request_id}] Material similarity calculated",
                common_materials=list(set1 & set2),
                similarity=jaccard_similarity
            )
        
        return jaccard_similarity

    def _calculate_technique_similarity(self, techniques1: List[str], techniques2: List[str], request_id: str = "") -> float:
        """Calculate similarity based on shared techniques"""
        return self._calculate_material_similarity(techniques1, techniques2, request_id)

    def _calculate_festival_similarity(self, festivals1: List[Festival], festivals2: List[Festival], request_id: str = "") -> float:
        """Calculate similarity based on shared festival relevance"""
        if not festivals1 or not festivals2:
            return 0.0
        
        # Convert to strings for comparison
        set1 = set(str(f) for f in festivals1)
        set2 = set(str(f) for f in festivals2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        if union == 0:
            return 0.0
        
        similarity = intersection / union
        
        if similarity > 0:
            # Find common festivals for logging
            common_festivals = []
            for f1 in festivals1:
                for f2 in festivals2:
                    if str(f1) == str(f2):
                        festival_val = f1.value if hasattr(f1, 'value') else str(f1)
                        common_festivals.append(festival_val)
                        break
            
            logger.debug(
                f"[{request_id}] Festival similarity calculated",
                common_festivals=common_festivals,
                similarity=similarity
            )
        
        return similarity

    def _calculate_seasonal_relevance(self, cultural_context: CulturalContext, request_id: str = "") -> float:
        """Calculate seasonal relevance based on current time and festivals"""
        current_month = datetime.now().month
        
        # Check if item has relevance to current season festivals
        seasonal_score = 0.0
        
        # Simple seasonal mapping (can be enhanced with your seasonal context service)
        current_season_festivals = {
            1: [],
            2: [],
            3: [Festival.HOLI],
            10: [Festival.DUSSEHRA, Festival.NAVRATRI],
            11: [Festival.DIWALI, Festival.DHANTERAS],
            12: [Festival.CHRISTMAS]
        }.get(current_month, [])
        
        matching_festivals = []
        for festival in current_season_festivals:
            # Compare as strings for safety
            festival_str = str(festival)
            for candidate_festival in cultural_context.festival_relevance:
                if str(candidate_festival) == festival_str:
                    seasonal_score += 0.2
                    festival_val = festival.value if hasattr(festival, 'value') else str(festival)
                    matching_festivals.append(festival_val)
                    break
        
        capped_score = min(seasonal_score, 1.0)
        
        if capped_score > 0:
            logger.debug(
                f"[{request_id}] Seasonal relevance calculated",
                current_month=current_month,
                matching_festivals=matching_festivals,
                score=capped_score
            )
        
        return capped_score

    def _calculate_diversity_penalty(
        self, 
        cultural_context: CulturalContext, 
        region_counts: Dict[str, int],
        craft_counts: Dict[str, int],
        request_id: str = ""
    ) -> float:
        """Calculate diversity penalty to prevent over-clustering"""
        penalty = 0.0
        
        # Penalize if too many items from same region - safe enum value extraction
        if cultural_context.region:
            region_val = cultural_context.region.value if hasattr(cultural_context.region, 'value') else str(cultural_context.region)
            region_count = region_counts.get(region_val, 0)
            if region_count >= self.regional_config.max_same_region_items:
                penalty += self.regional_config.same_region_penalty
        
        # Penalize if too many items of same craft type - safe enum value extraction
        if cultural_context.craft_type:
            craft_val = cultural_context.craft_type.value if hasattr(cultural_context.craft_type, 'value') else str(cultural_context.craft_type)
            craft_count = craft_counts.get(craft_val, 0)
            if craft_count >= 2:  # Limit same craft type
                penalty -= 0.05
        
        if penalty != 0:
            # Safe enum value extraction for logging
            region_log = cultural_context.region.value if hasattr(cultural_context.region, 'value') else str(cultural_context.region) if cultural_context.region else None
            craft_log = cultural_context.craft_type.value if hasattr(cultural_context.craft_type, 'value') else str(cultural_context.craft_type) if cultural_context.craft_type else None
            
            logger.debug(
                f"[{request_id}] Diversity penalty applied",
                region=region_log,
                craft=craft_log,
                penalty=penalty
            )
        
        return penalty

    def _calculate_regional_discovery_bonus(self, source_region: IndianRegion, target_region: IndianRegion, request_id: str = "") -> float:
        """Calculate bonus for regional discovery"""
        # Compare as strings for safety
        if str(source_region) == str(target_region):
            return 0.0
        
        # Bonus for discovering different regions
        base_bonus = self.regional_config.diversity_boost_factor
        
        # Extra bonus for neighboring regions (maintains cultural connection)
        if self._calculate_regional_relatedness(source_region, target_region, request_id) > 0:
            base_bonus += self.regional_config.neighboring_region_bonus
        
        # Safe enum value extraction for logging
        source_val = source_region.value if hasattr(source_region, 'value') else str(source_region)
        target_val = target_region.value if hasattr(target_region, 'value') else str(target_region)
        
        logger.debug(
            f"[{request_id}] Regional discovery bonus calculated",
            source_region=source_val,
            target_region=target_val,
            bonus=base_bonus
        )
        
        return base_bonus

    def get_stats(self) -> Dict[str, Any]:
        """Get recommender statistics (enhanced with logging)"""
        stats_data = {
            **self.stats,
            "cache_size": len(self.similarity_cache),
            "knowledge_base_stats": self.knowledge_base.get_stats()
        }
        
        logger.debug("Content-based recommender statistics requested", **stats_data)
        return stats_data

    def clear_cache(self):
        """Clear similarity cache"""
        cache_size = len(self.similarity_cache)
        self.similarity_cache.clear()
        logger.info(f"Content-based recommendation cache cleared (was {cache_size} entries)")

# Global instance (matching your service patterns)
content_based_recommender = CulturalContentBasedRecommender()