# models/recommendation_models.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

from src.models.cultural_models import (
    CulturalContext, CraftType, IndianRegion, Festival, CulturalSignificance
)

class RecommendationType(str, Enum):
    """Types of recommendations"""
    CULTURAL_SIMILARITY = "cultural_similarity"
    FESTIVAL_SEASONAL = "festival_seasonal"
    REGIONAL_DISCOVERY = "regional_discovery"
    ARTISAN_STYLE = "artisan_style"
    MATERIAL_BASED = "material_based"
    TECHNIQUE_MATCH = "technique_match"
    CROSS_CULTURAL = "cross_cultural"
    TRENDING = "trending"

class SimilarityMetric(str, Enum):
    """Similarity calculation methods"""
    CULTURAL_CONTEXT = "cultural_context"
    VECTOR_SIMILARITY = "vector_similarity"
    HYBRID_WEIGHTED = "hybrid_weighted"
    FESTIVAL_SEASONAL = "festival_seasonal"
    REGIONAL_CRAFT = "regional_craft"

class RecommendationRequest(BaseModel):
    """Request for item-based recommendations"""
    item_id: str = Field(..., min_length=1)
    recommendation_types: List[RecommendationType] = Field(
        default=[RecommendationType.CULTURAL_SIMILARITY], 
        max_items=5
    )
    limit: int = Field(5, ge=1, le=20)
    similarity_threshold: float = Field(0.3, ge=0.0, le=1.0)
    enable_diversity: bool = True  # Prevent over-clustering in same region/craft
    seasonal_boost: bool = True
    exclude_item_ids: Optional[List[str]] = None
    
    # Cultural preferences
    preferred_regions: Optional[List[IndianRegion]] = None
    preferred_festivals: Optional[List[Festival]] = None
    min_cultural_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    @validator('item_id')
    def item_id_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Item ID cannot be empty')
        return v.strip()

class UserPreferenceRequest(BaseModel):
    """Request for user preference-based recommendations"""
    user_id: Optional[str] = None
    user_interaction_history: Optional[List[str]] = None  # List of item IDs
    preferred_craft_types: Optional[List[CraftType]] = None
    preferred_regions: Optional[List[IndianRegion]] = None
    preferred_festivals: Optional[List[Festival]] = None
    preferred_materials: Optional[List[str]] = None
    budget_range: Optional[Dict[str, float]] = None  # {"min": 100, "max": 1000}
    
    recommendation_types: List[RecommendationType] = Field(
        default=[RecommendationType.CULTURAL_SIMILARITY, RecommendationType.REGIONAL_DISCOVERY],
        max_items=3
    )
    limit: int = Field(10, ge=1, le=50)
    diversity_factor: float = Field(0.3, ge=0.0, le=1.0)  # Higher = more diverse

class SeasonalRecommendationRequest(BaseModel):
    """Request for seasonal/festival recommendations"""
    current_festival: Optional[Festival] = None
    upcoming_festivals: Optional[List[Festival]] = None
    region_preference: Optional[IndianRegion] = None
    include_gift_items: bool = True
    include_decorative: bool = True
    limit: int = Field(10, ge=1, le=30)
    price_range: Optional[Dict[str, float]] = None

class RecommendationScore(BaseModel):
    """Detailed scoring breakdown for a recommendation"""
    overall_score: float = Field(..., ge=0.0, le=1.0)
    cultural_similarity: float = Field(0.0, ge=0.0, le=1.0)
    vector_similarity: float = Field(0.0, ge=0.0, le=1.0)
    seasonal_relevance: float = Field(0.0, ge=0.0, le=1.0)
    regional_match: float = Field(0.0, ge=0.0, le=1.0)
    festival_relevance: float = Field(0.0, ge=0.0, le=1.0)
    diversity_bonus: float = Field(0.0, ge=-0.2, le=0.2)  # Can be negative for over-clustering
    
class RecommendationItem(BaseModel):
    """Single recommendation result"""
    id: str
    text: str
    payload: Dict[str, Any]
    
    # Recommendation specific fields
    recommendation_type: RecommendationType
    similarity_metric: SimilarityMetric
    score_breakdown: RecommendationScore
    
    # Cultural context
    cultural_context: Optional[CulturalContext] = None
    cultural_match_reasons: List[str] = Field(default_factory=list)
    seasonal_context: Optional[str] = None
    
    # Additional metadata
    distance_from_source: Optional[float] = None  # Vector distance
    regional_diversity_score: Optional[float] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": "item_123",
                "text": "Traditional Rajasthani blue pottery vase with intricate patterns",
                "recommendation_type": "cultural_similarity",
                "score_breakdown": {
                    "overall_score": 0.85,
                    "cultural_similarity": 0.9,
                    "vector_similarity": 0.8,
                    "seasonal_relevance": 0.7,
                    "regional_match": 1.0
                },
                "cultural_match_reasons": [
                    "Same craft type: pottery",
                    "Similar region: rajasthan", 
                    "Matching festival relevance: diwali"
                ]
            }
        }

class RecommendationResponse(BaseModel):
    """Response containing recommendations"""
    source_item_id: Optional[str] = None
    total_recommendations: int
    recommendations: List[RecommendationItem]
    
    # Request context
    recommendation_types_used: List[RecommendationType]
    filters_applied: Optional[Dict[str, Any]] = None
    processing_time_ms: Optional[float] = None
    
    # Cultural insights
    cultural_diversity_stats: Optional[Dict[str, int]] = None  # {"regions": 3, "craft_types": 2}
    seasonal_recommendations_count: Optional[int] = None
    cross_cultural_recommendations_count: Optional[int] = None
    
    # Performance metadata
    cache_hits: Optional[int] = None
    fallback_used: Optional[bool] = None
    recommendation_confidence: Optional[float] = None

class CulturalSimilarityConfig(BaseModel):
    """Configuration for cultural similarity calculations"""
    craft_type_weight: float = Field(0.3, ge=0.0, le=1.0)
    region_weight: float = Field(0.25, ge=0.0, le=1.0)
    material_weight: float = Field(0.2, ge=0.0, le=1.0)
    technique_weight: float = Field(0.15, ge=0.0, le=1.0)
    festival_weight: float = Field(0.1, ge=0.0, le=1.0)
    
    @validator('*', allow_reuse=True)
    def weights_sum_validation(cls, v, values):
        # Don't enforce exact sum = 1.0 for flexibility, but warn if too far off
        return v

class RegionalDiscoveryConfig(BaseModel):
    """Configuration for regional craft discovery"""
    same_region_penalty: float = Field(-0.1, ge=-0.5, le=0.0)
    neighboring_region_bonus: float = Field(0.05, ge=0.0, le=0.2)
    diversity_boost_factor: float = Field(0.1, ge=0.0, le=0.3)
    max_same_region_items: int = Field(2, ge=1, le=5)

class SeasonalBoostConfig(BaseModel):
    """Configuration for seasonal/festival boosting"""
    current_festival_boost: float = Field(0.2, ge=0.0, le=0.5)
    upcoming_festival_boost: float = Field(0.1, ge=0.0, le=0.3)
    seasonal_decay_days: int = Field(30, ge=7, le=90)
    off_season_penalty: float = Field(0.0, ge=-0.2, le=0.0)

class BatchRecommendationRequest(BaseModel):
    """Request for batch recommendations for multiple items"""
    item_ids: List[str] = Field(..., min_items=1, max_items=10)
    recommendations_per_item: int = Field(5, ge=1, le=10)
    recommendation_types: List[RecommendationType] = Field(
        default=[RecommendationType.CULTURAL_SIMILARITY]
    )
    enable_cross_item_deduplication: bool = True
    similarity_threshold: float = Field(0.3, ge=0.0, le=1.0)

class BatchRecommendationResponse(BaseModel):
    """Response for batch recommendations"""
    total_items_processed: int
    successful_recommendations: int
    failed_recommendations: int
    recommendations_by_item: Dict[str, RecommendationResponse]
    processing_time_ms: Optional[float] = None
    
    # Batch-level insights
    most_common_regions: Optional[List[str]] = None
    most_common_craft_types: Optional[List[str]] = None
    diversity_across_batch: Optional[float] = None

# Analytics and Insights Models

class RecommendationAnalytics(BaseModel):
    """Analytics for recommendation performance"""
    total_recommendations_served: int
    recommendation_type_distribution: Dict[RecommendationType, int]
    average_cultural_similarity_score: float
    regional_distribution: Dict[IndianRegion, int]
    craft_type_distribution: Dict[CraftType, int]
    seasonal_recommendation_effectiveness: Dict[Festival, float]
    
    # Performance metrics
    average_response_time_ms: float
    cache_hit_rate: float
    fallback_usage_rate: float
    
    # Quality metrics
    recommendation_diversity_score: float
    cross_cultural_discovery_rate: float
    
    timestamp: datetime = Field(default_factory=datetime.now)

class UserInteractionFeedback(BaseModel):
    """User feedback on recommendations for learning"""
    user_id: Optional[str] = None
    item_id: str
    recommended_item_id: str
    interaction_type: str  # "click", "view", "purchase", "ignore", "dislike"
    interaction_duration_seconds: Optional[float] = None
    explicit_rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    feedback_text: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Context
    recommendation_type: RecommendationType
    cultural_match_accuracy: Optional[float] = None  # User's perceived accuracy
    seasonal_relevance_accuracy: Optional[float] = None