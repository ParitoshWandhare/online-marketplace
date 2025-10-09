# models/cultural_models.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime

class CraftType(str, Enum):
    """Indian craft categories"""
    POTTERY = "pottery"
    TEXTILES = "textiles" 
    JEWELRY = "jewelry"
    WOODWORK = "woodwork"
    METALCRAFT = "metalcraft"
    PAINTING = "painting"
    SCULPTURE = "sculpture"
    LEATHER_WORK = "leather_work"
    STONE_CARVING = "stone_carving"
    GLASS_WORK = "glass_work"
    PAPER_CRAFT = "paper_craft"
    BAMBOO_CRAFT = "bamboo_craft"
    UNKNOWN = "unknown"

class IndianRegion(str, Enum):
    """Major Indian regions for craft categorization"""
    RAJASTHAN = "rajasthan"
    GUJARAT = "gujarat"
    PUNJAB = "punjab"
    UTTAR_PRADESH = "uttar_pradesh"
    MADHYA_PRADESH = "madhya_pradesh"
    MAHARASHTRA = "maharashtra"
    WEST_BENGAL = "west_bengal"
    ODISHA = "odisha"
    TAMIL_NADU = "tamil_nadu"
    KERALA = "kerala"
    KARNATAKA = "karnataka"
    ANDHRA_PRADESH = "andhra_pradesh"
    ASSAM = "assam"
    JAMMU_KASHMIR = "jammu_kashmir"
    HIMACHAL_PRADESH = "himachal_pradesh"
    NORTHEAST = "northeast"
    UNKNOWN = "unknown"

class Festival(str, Enum):
    """Major Indian festivals for seasonal awareness"""
    DIWALI = "diwali"
    HOLI = "holi"
    DUSSEHRA = "dussehra"
    NAVRATRI = "navratri"
    GANESH_CHATURTHI = "ganesh_chaturthi"
    KARVA_CHAUTH = "karva_chauth"
    RAKSHA_BANDHAN = "raksha_bandhan"
    DHANTERAS = "dhanteras"
    CHRISTMAS = "christmas"
    EID = "eid"
    BAISAKHI = "baisakhi"
    PONGAL = "pongal"
    ONAM = "onam"
    DURGA_PUJA = "durga_puja"
    WEDDING_SEASON = "wedding_season"
    UNKNOWN = "unknown"

class CulturalSignificance(str, Enum):
    """Type of cultural significance"""
    CEREMONIAL = "ceremonial"
    FESTIVAL_ITEM = "festival_item"
    DAILY_USE = "daily_use"
    DECORATIVE = "decorative"
    RELIGIOUS = "religious"
    WEDDING_ITEM = "wedding_item"
    GIFT_ITEM = "gift_item"
    TOURIST_SOUVENIR = "tourist_souvenir"
    HERITAGE_PIECE = "heritage_piece"
    CONTEMPORARY = "contemporary"
    UNKNOWN = "unknown"

class CulturalContext(BaseModel):
    """Core cultural context for an artwork/product"""
    craft_type: Optional[CraftType] = None
    materials: List[str] = Field(default_factory=list)
    cultural_significance: Optional[CulturalSignificance] = None
    region: Optional[IndianRegion] = None
    traditional_techniques: List[str] = Field(default_factory=list)
    festival_relevance: List[Festival] = Field(default_factory=list)
    cultural_tags: List[str] = Field(default_factory=list)
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)
    analysis_timestamp: Optional[datetime] = None
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "craft_type": "pottery",
                "materials": ["clay", "natural_pigments", "glazes"],
                "cultural_significance": "festival_item",
                "region": "rajasthan",
                "traditional_techniques": ["wheel_throwing", "hand_painting", "firing"],
                "festival_relevance": ["diwali", "dhanteras"],
                "cultural_tags": ["traditional", "handmade", "decorative"],
                "confidence_score": 0.85,
                "analysis_timestamp": "2025-01-15T10:30:00Z"
            }
        }

class CulturalAnalysisRequest(BaseModel):
    """Request for cultural analysis"""
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    image_urls: Optional[List[str]] = None
    existing_tags: Optional[List[str]] = None
    user_location: Optional[str] = None
    
    @validator('title', 'description')
    def text_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Text cannot be empty')
        return v.strip()

class CulturalAnalysisResponse(BaseModel):
    """Response from cultural analysis"""
    cultural_context: CulturalContext
    reasoning: Optional[str] = None
    detected_keywords: List[str] = Field(default_factory=list)
    processing_time_ms: Optional[float] = None

# Enhanced Search Models with Cultural Fields
class CulturalSearchFilters(BaseModel):
    """Cultural-specific search filters"""
    craft_types: Optional[List[CraftType]] = None
    regions: Optional[List[IndianRegion]] = None
    festivals: Optional[List[Festival]] = None
    cultural_significance: Optional[List[CulturalSignificance]] = None
    materials: Optional[List[str]] = None
    traditional_techniques: Optional[List[str]] = None
    cultural_tags: Optional[List[str]] = None
    min_cultural_score: Optional[float] = Field(None, ge=0.0, le=1.0)

class EnhancedSearchRequest(BaseModel):
    """Extended search request with cultural parameters"""
    query: str = Field(..., min_length=1)
    limit: int = Field(5, ge=1, le=50)
    expand: bool = True
    use_reranker: bool = True
    score_threshold: float = Field(0.7, ge=0.0, le=1.0)
    
    # Cultural enhancements
    cultural_filters: Optional[CulturalSearchFilters] = None
    cultural_context_boost: float = Field(1.0, ge=0.0, le=2.0)
    enable_cultural_analysis: bool = True
    seasonal_boost: bool = True  # Boost festival-relevant items
    regional_preference: Optional[IndianRegion] = None
    
    # Legacy filters (maintain backward compatibility)
    filters: Optional[Dict[str, Any]] = None
    
    @validator('query')
    def query_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()

class CulturalSearchResult(BaseModel):
    """Search result with cultural enrichment"""
    id: str
    score: float
    weighted_score: float
    hits: int
    text: str
    payload: Dict[str, Any]
    
    # Cultural enhancements
    cultural_context: Optional[CulturalContext] = None
    cultural_score: Optional[float] = None
    seasonal_relevance: Optional[float] = None
    regional_match: Optional[bool] = None

class EnhancedSearchResponse(BaseModel):
    """Enhanced search response with cultural intelligence"""
    query: str
    total_results: int
    results: List[CulturalSearchResult]
    filters_applied: Optional[Dict[str, Any]] = None
    cultural_filters_applied: Optional[CulturalSearchFilters] = None
    processing_time_ms: Optional[float] = None
    
    # Cultural insights
    detected_cultural_intent: Optional[str] = None
    seasonal_context: Optional[str] = None
    suggested_regions: Optional[List[IndianRegion]] = None
    suggested_festivals: Optional[List[Festival]] = None

# Cultural Query Enhancement Models
class CulturalQueryContext(BaseModel):
    """Detected cultural context in user queries"""
    detected_craft_types: List[CraftType] = Field(default_factory=list)
    detected_regions: List[IndianRegion] = Field(default_factory=list)
    detected_festivals: List[Festival] = Field(default_factory=list)
    seasonal_intent: Optional[str] = None
    cultural_intent: Optional[str] = None
    traditional_terms: List[str] = Field(default_factory=list)
    expansion_terms: List[str] = Field(default_factory=list)
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)

class QueryEnhancementRequest(BaseModel):
    """Request for cultural query enhancement"""
    original_query: str
    user_location: Optional[str] = None
    user_preferences: Optional[Dict[str, Any]] = None
    current_season: Optional[str] = None

class QueryEnhancementResponse(BaseModel):
    """Response from cultural query enhancement"""
    original_query: str
    enhanced_query: str
    cultural_context: CulturalQueryContext
    additional_queries: List[str] = Field(default_factory=list)
    processing_time_ms: Optional[float] = None