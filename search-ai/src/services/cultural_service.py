# services/cultural_service.py
import asyncio
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import re
import google.generativeai as genai

from src.services.embedding_service import embedding_service
from src.models.cultural_models import (
    CulturalContext, CulturalAnalysisRequest, CulturalAnalysisResponse,
    CraftType, IndianRegion, Festival, CulturalSignificance,
    CulturalQueryContext, QueryEnhancementRequest, QueryEnhancementResponse
)
from src.utils.cultural_analyzer import CulturalKnowledgeBase
from src.config.settings import settings
from src.utils.logger import cultural_logger as logger

class CulturalAnalysisService:
    """
    AI-powered cultural analysis service for Indian artisan marketplace
    Enhanced with comprehensive logging and Gemini integration
    """
    
    def __init__(self):
        logger.info("Initializing Cultural Analysis Service")
        
        try:
            self.knowledge_base = CulturalKnowledgeBase()
            logger.debug("Cultural knowledge base loaded successfully")
        except Exception as e:
            logger.error("Failed to initialize cultural knowledge base", error=str(e))
            raise
        
        self.cache = {}  # Simple in-memory cache for frequent analyses
        self.cache_ttl = 3600  # 1 hour
        
        # Performance tracking
        self.stats = {
            "analyses_performed": 0,
            "cache_hits": 0,
            "ai_calls": 0,
            "avg_processing_time": 0.0,
            "fallback_analyses": 0,
            "failed_analyses": 0,
            "query_enhancements": 0,
            "gemini_successes": 0,
            "gemini_failures": 0
        }
        
        logger.info("Cultural Analysis Service initialized successfully")

    def _create_cultural_analysis_prompt(self, title: str, description: str) -> str:
        """Create enhanced structured prompt for Gemini cultural analysis"""
        logger.debug("Creating enhanced cultural analysis prompt for Gemini")
        
        prompt = f"""You are an expert in Indian traditional arts and crafts. Analyze this artwork/craft item and return ONLY a valid JSON object with the specified structure.

ARTWORK TO ANALYZE:
Title: {title}
Description: {description}

RETURN ONLY THIS JSON FORMAT (no additional text):
{{
    "craft_type": "one of: pottery, textiles, jewelry, woodwork, metalcraft, painting, sculpture, leather_work, stone_carving, glass_work, paper_craft, bamboo_craft, unknown",
    "materials": ["list", "of", "detected", "materials"],
    "cultural_significance": "one of: ceremonial, festival_item, daily_use, decorative, religious, wedding_item, gift_item, tourist_souvenir, heritage_piece, contemporary, unknown",
    "region": "one of: rajasthan, gujarat, punjab, uttar_pradesh, madhya_pradesh, maharashtra, west_bengal, odisha, tamil_nadu, kerala, karnataka, andhra_pradesh, assam, jammu_kashmir, himachal_pradesh, northeast, unknown",
    "traditional_techniques": ["list", "of", "traditional", "techniques"],
    "festival_relevance": ["festivals from: diwali, holi, dussehra, navratri, ganesh_chaturthi, karva_chauth, raksha_bandhan, dhanteras, christmas, eid, baisakhi, pongal, onam, durga_puja, wedding_season"],
    "cultural_tags": ["descriptive", "cultural", "tags"],
    "confidence_score": 0.85,
    "reasoning": "Brief explanation of analysis decisions"
}}

ANALYSIS GUIDELINES:
- Focus on traditional Indian craft identification
- Consider regional artistic styles and materials
- Identify festival/seasonal relevance
- Assess cultural significance and usage context
- Provide confidence score based on clarity of cultural indicators

RETURN ONLY THE JSON OBJECT."""
        
        logger.debug("Enhanced Gemini prompt created", prompt_length=len(prompt))
        return prompt

    async def _call_gemini_for_cultural_analysis(self, prompt: str, request_id: str = "") -> str:
        """Call Gemini API for cultural analysis - FIXED VERSION"""
        try:
            logger.debug(f"[{request_id}] Calling Gemini API for cultural analysis")
            
            # Configure Gemini
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            
            # Make the API call
            api_start = time.time()
            response = await asyncio.to_thread(
                model.generate_content, 
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=1000,
                )
            )
            api_time = (time.time() - api_start) * 1000
            
            logger.debug(f"[{request_id}] Gemini API call completed", processing_time_ms=api_time)
            
            if response.text:
                self.stats["gemini_successes"] += 1
                return response.text.strip()
            else:
                logger.warning(f"[{request_id}] Gemini returned empty response")
                self.stats["gemini_failures"] += 1
                return "{}"
                
        except Exception as e:
            logger.error(f"[{request_id}] Gemini API call failed", error=str(e), error_type=type(e).__name__)
            self.stats["gemini_failures"] += 1
            return "{}"

    def _parse_ai_cultural_response(self, ai_response: str) -> Tuple[CulturalContext, str]:
        """Parse AI response into structured cultural context - FIXED"""
        logger.debug("Parsing AI cultural response", response_length=len(ai_response))
        
        try:
            # Extract JSON
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                logger.debug("Found JSON in AI response", json_length=len(json_str))
                parsed = json.loads(json_str)
            else:
                logger.debug("Attempting to parse entire response as JSON")
                parsed = json.loads(ai_response)
            
            logger.debug("AI response parsed successfully", parsed_fields=list(parsed.keys()))
            
            # Safe enum conversion function
            def safe_enum_convert(enum_class, value, default):
                if value is None:
                    return default
                if isinstance(value, enum_class):
                    return value
                try:
                    return enum_class(value)
                except (ValueError, TypeError):
                    return default
            
            # CREATE CONTEXT FIRST
            context = CulturalContext(
                craft_type=safe_enum_convert(CraftType, parsed.get("craft_type"), CraftType.UNKNOWN),
                materials=parsed.get("materials", []),
                cultural_significance=safe_enum_convert(CulturalSignificance, parsed.get("cultural_significance"), CulturalSignificance.UNKNOWN),
                region=safe_enum_convert(IndianRegion, parsed.get("region"), IndianRegion.UNKNOWN),
                traditional_techniques=parsed.get("traditional_techniques", []),
                festival_relevance=[
                    safe_enum_convert(Festival, f, Festival.UNKNOWN) 
                    for f in parsed.get("festival_relevance", [])
                    if safe_enum_convert(Festival, f, Festival.UNKNOWN) != Festival.UNKNOWN
                ],
                cultural_tags=parsed.get("cultural_tags", []),
                confidence_score=float(parsed.get("confidence_score", 0.5)),
                analysis_timestamp=datetime.now()
            )
            
            reasoning = parsed.get("reasoning", "AI analysis completed")
            
            # Safe logging after context creation
            logger.info(
                "Cultural context parsed successfully",
                craft_type=context.craft_type.value if hasattr(context.craft_type, 'value') else str(context.craft_type),
                region=context.region.value if hasattr(context.region, 'value') else str(context.region),
                confidence=context.confidence_score,
                festivals_count=len(context.festival_relevance),
                materials_count=len(context.materials)
            )
            
            return context, reasoning
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(
                "Failed to parse AI response, using fallback analysis",
                error=str(e),
                error_type=type(e).__name__
            )
            return self._enhanced_fallback_analysis(ai_response), "Fallback analysis due to parsing error"

    def _enhanced_fallback_analysis(self, text: str, title: str = "") -> CulturalContext:
        """Enhanced fallback analysis with higher confidence scores"""
        logger.info("Using enhanced keyword-based cultural analysis")
        
        combined_text = f"{title} {text}".lower()
        detected_keywords = []
        confidence_boost = 0.0
        
        # Enhanced craft type detection
        craft_type = CraftType.UNKNOWN
        craft_confidence = 0.0
        
        for craft, keywords in self.knowledge_base.craft_keywords.items():
            matching_keywords = [kw for kw in keywords if kw in combined_text]
            if matching_keywords:
                match_strength = len(matching_keywords) / len(keywords)
                if match_strength > craft_confidence:
                    craft_type = CraftType(craft)
                    craft_confidence = match_strength
                    detected_keywords.extend(matching_keywords)
                    logger.debug(f"Enhanced craft detection: {craft} (confidence: {craft_confidence:.2f})")
        
        # Enhanced material detection
        materials = []
        for material_list in self.knowledge_base.material_keywords.values():
            for material in material_list:
                if material in combined_text:
                    materials.append(material)
                    confidence_boost += 0.05
        
        # Enhanced region detection
        region = IndianRegion.UNKNOWN
        region_confidence = 0.0
        
        for reg, keywords in self.knowledge_base.regional_keywords.items():
            matching_keywords = [kw for kw in keywords if kw in combined_text]
            if matching_keywords:
                match_strength = len(matching_keywords) / len(keywords)
                if match_strength > region_confidence:
                    region = IndianRegion(reg)
                    region_confidence = match_strength
                    confidence_boost += 0.1
        
        # Enhanced festival relevance
        festivals = []
        for fest, keywords in self.knowledge_base.festival_keywords.items():
            matching_keywords = [kw for kw in keywords if kw in combined_text]
            if matching_keywords:
                festivals.append(Festival(fest))
                confidence_boost += 0.05
        
        # Enhanced cultural significance detection
        cultural_significance = CulturalSignificance.UNKNOWN
        for significance, keywords in self.knowledge_base.cultural_significance_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                cultural_significance = CulturalSignificance(significance)
                confidence_boost += 0.05
                break
        
        # Calculate enhanced confidence score
        base_confidence = 0.4
        final_confidence = min(
            base_confidence + craft_confidence * 0.3 + region_confidence * 0.2 + confidence_boost,
            0.8
        )
        
        fallback_context = CulturalContext(
            craft_type=craft_type,
            materials=materials,
            region=region,
            festival_relevance=festivals,
            cultural_significance=cultural_significance,
            cultural_tags=detected_keywords[:10],
            confidence_score=final_confidence,
            analysis_timestamp=datetime.now()
        )
        
        self.stats["fallback_analyses"] += 1
        
        # Safe logging using the enum variables directly
        logger.info(
            "Enhanced fallback analysis completed",
            craft_type=craft_type.value if craft_type and hasattr(craft_type, 'value') else "unknown",
            region=region.value if region and hasattr(region, 'value') else "unknown",
            materials_found=len(materials),
            festivals_found=len(festivals),
            final_confidence=final_confidence
        )
        
        return fallback_context

    def _fallback_analysis(self, text: str) -> CulturalContext:
        """Legacy fallback analysis for backwards compatibility"""
        return self._enhanced_fallback_analysis(text)

    async def analyze_artwork_cultural_context(self, request: CulturalAnalysisRequest) -> CulturalAnalysisResponse:
        """Main method to analyze artwork for cultural context using Gemini AI"""
        start_time = time.time()
        request_id = f"cultural_req_{int(start_time * 1000)}"
        
        logger.info(
            f"[{request_id}] Starting cultural analysis",
            title=request.title[:50] + "..." if len(request.title) > 50 else request.title,
            description_length=len(request.description),
            has_image_urls=bool(request.image_urls),
            existing_tags_count=len(request.existing_tags) if request.existing_tags else 0
        )
        
        # Check cache first
        cache_key = f"{request.title}:{request.description}"[:100]
        logger.log_cache_operation("read", "cultural_analysis", cache_key[:30])
        
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                self.stats["cache_hits"] += 1
                processing_time = (time.time() - start_time) * 1000
                
                logger.info(
                    f"[{request_id}] Using cached cultural analysis",
                    processing_time_ms=processing_time,
                    cache_age_seconds=int(time.time() - cache_entry["timestamp"])
                )
                logger.log_cache_operation("read", "cultural_analysis", cache_key[:30], hit=True)
                
                return CulturalAnalysisResponse(
                    cultural_context=cache_entry["context"],
                    reasoning=cache_entry["reasoning"],
                    detected_keywords=cache_entry.get("keywords", []),
                    processing_time_ms=round(processing_time, 2)
                )
        
        logger.log_cache_operation("read", "cultural_analysis", cache_key[:30], hit=False)
        
        try:
            # Create AI prompt
            logger.debug(f"[{request_id}] Creating AI prompt for cultural analysis")
            prompt = self._create_cultural_analysis_prompt(request.title, request.description)
            
            # Use Gemini AI analysis with fallback
            logger.debug(f"[{request_id}] Attempting Gemini-powered cultural analysis")
            self.stats["ai_calls"] += 1
            
            try:
                ai_response = await self._call_gemini_for_cultural_analysis(prompt, request_id)
                
                if ai_response and ai_response != "{}":
                    cultural_context, reasoning = self._parse_ai_cultural_response(ai_response)
                    logger.info(f"[{request_id}] Gemini analysis successful", confidence=cultural_context.confidence_score)
                else:
                    logger.warning(f"[{request_id}] Gemini analysis failed, using enhanced fallback")
                    cultural_context = self._enhanced_fallback_analysis(f"{request.title} {request.description}", request.title)
                    reasoning = "Enhanced keyword-based analysis (Gemini API failed)"
                    
            except Exception as e:
                logger.error(f"[{request_id}] Gemini analysis completely failed", error=str(e))
                cultural_context = self._enhanced_fallback_analysis(f"{request.title} {request.description}", request.title)
                reasoning = f"Enhanced fallback analysis due to error: {str(e)}"
            
            # Cache the result
            logger.debug(f"[{request_id}] Caching cultural analysis result")
            self.cache[cache_key] = {
                "context": cultural_context,
                "reasoning": reasoning,
                "keywords": cultural_context.cultural_tags,
                "timestamp": time.time()
            }
            logger.log_cache_operation("write", "cultural_analysis", cache_key[:30])
            
            # Update stats
            processing_time = (time.time() - start_time) * 1000
            self.stats["analyses_performed"] += 1
            self.stats["avg_processing_time"] = (
                (self.stats["avg_processing_time"] * (self.stats["analyses_performed"] - 1) + processing_time)
                / self.stats["analyses_performed"]
            )
            
            # Safe logging with defensive checks
            logger.info(
                f"[{request_id}] Cultural analysis completed successfully",
                processing_time_ms=processing_time,
                craft_type=cultural_context.craft_type.value if hasattr(cultural_context.craft_type, 'value') else str(cultural_context.craft_type),
                region=cultural_context.region.value if hasattr(cultural_context.region, 'value') else str(cultural_context.region),
                confidence=cultural_context.confidence_score,
                materials_detected=len(cultural_context.materials),
                festivals_detected=len(cultural_context.festival_relevance),
                techniques_detected=len(cultural_context.traditional_techniques)
            )
            
            logger.log_cultural_analysis(
                f"{request.title}_{request_id}",
                {
                    "craft_type": cultural_context.craft_type.value if hasattr(cultural_context.craft_type, 'value') else str(cultural_context.craft_type),
                    "region": cultural_context.region.value if hasattr(cultural_context.region, 'value') else str(cultural_context.region),
                    "confidence": cultural_context.confidence_score
                },
                processing_time / 1000
            )
            
            return CulturalAnalysisResponse(
                cultural_context=cultural_context,
                reasoning=reasoning,
                detected_keywords=cultural_context.cultural_tags,
                processing_time_ms=round(processing_time, 2)
            )
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self.stats["failed_analyses"] += 1
            
            logger.error(
                f"[{request_id}] Cultural analysis failed",
                error=str(e),
                error_type=type(e).__name__,
                processing_time_ms=processing_time
            )
            logger.log_error_with_traceback(e, f"[{request_id}] cultural analysis")
            
            # Return minimal fallback analysis
            fallback_context = CulturalContext(
                craft_type=CraftType.UNKNOWN,
                confidence_score=0.1,
                analysis_timestamp=datetime.now()
            )
            
            return CulturalAnalysisResponse(
                cultural_context=fallback_context,
                reasoning=f"Analysis failed: {str(e)}",
                detected_keywords=[],
                processing_time_ms=round(processing_time, 2)
            )

    def analyze_query_cultural_context(self, request: QueryEnhancementRequest) -> QueryEnhancementResponse:
        """Analyze search query for cultural context and enhance it"""
        start_time = time.time()
        request_id = f"query_enhance_{int(start_time * 1000)}"
        
        logger.info(
            f"[{request_id}] Starting query cultural enhancement",
            original_query=request.original_query,
            user_location=request.user_location,
            has_user_preferences=bool(request.user_preferences),
            current_season=request.current_season
        )
        
        try:
            original_query = request.original_query.lower()
            cultural_context = CulturalQueryContext()
            enhanced_terms = []
            additional_queries = []
            
            # Detect craft types
            craft_matches = 0
            for craft, keywords in self.knowledge_base.craft_keywords.items():
                matching_keywords = [kw for kw in keywords if kw in original_query]
                if matching_keywords:
                    cultural_context.detected_craft_types.append(CraftType(craft))
                    enhanced_terms.extend(keywords[:2])
                    craft_matches += 1
            
            # Detect regions
            region_matches = 0
            for region, keywords in self.knowledge_base.regional_keywords.items():
                matching_keywords = [kw for kw in keywords if kw in original_query]
                if matching_keywords:
                    cultural_context.detected_regions.append(IndianRegion(region))
                    enhanced_terms.extend(keywords[:2])
                    region_matches += 1
            
            # Detect festivals
            festival_matches = 0
            for festival, keywords in self.knowledge_base.festival_keywords.items():
                matching_keywords = [kw for kw in keywords if kw in original_query]
                if matching_keywords:
                    cultural_context.detected_festivals.append(Festival(festival))
                    enhanced_terms.extend(keywords[:2])
                    festival_matches += 1
            
            # Create enhanced query
            enhanced_query = request.original_query
            if enhanced_terms:
                unique_terms = list(set(enhanced_terms))[:3]
                enhanced_query += " " + " ".join(unique_terms)
            
            # Generate additional queries
            if cultural_context.detected_craft_types:
                for craft_type in cultural_context.detected_craft_types[:2]:
                    additional_query = f"{request.original_query} {craft_type.value} traditional"
                    additional_queries.append(additional_query)
            
            if cultural_context.detected_festivals:
                for festival in cultural_context.detected_festivals[:2]:
                    additional_query = f"{request.original_query} {festival.value} special"
                    additional_queries.append(additional_query)
            
            # Calculate confidence
            total_detections = craft_matches + region_matches + festival_matches
            cultural_context.confidence_score = min(total_detections * 0.3, 1.0)
            cultural_context.expansion_terms = enhanced_terms
            
            processing_time = (time.time() - start_time) * 1000
            self.stats["query_enhancements"] += 1
            
            return QueryEnhancementResponse(
                original_query=request.original_query,
                enhanced_query=enhanced_query,
                cultural_context=cultural_context,
                additional_queries=additional_queries,
                processing_time_ms=round(processing_time, 2)
            )
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"[{request_id}] Query enhancement failed", error=str(e))
            
            return QueryEnhancementResponse(
                original_query=request.original_query,
                enhanced_query=request.original_query,
                cultural_context=CulturalQueryContext(confidence_score=0.0),
                additional_queries=[],
                processing_time_ms=round(processing_time, 2)
            )

    def get_seasonal_context(self) -> Dict[str, Any]:
        """Get current seasonal/festival context"""
        current_month = datetime.now().month
        
        seasonal_festivals = {
            1: [],
            2: [],  
            3: [Festival.HOLI],
            4: [],
            8: [],
            9: [Festival.GANESH_CHATURTHI],
            10: [Festival.DUSSEHRA, Festival.NAVRATRI],
            11: [Festival.DIWALI, Festival.DHANTERAS, Festival.KARVA_CHAUTH],
            12: [Festival.CHRISTMAS]
        }
        
        current_festivals = seasonal_festivals.get(current_month, [])
        
        return {
            "current_month": current_month,
            "active_festivals": [f.value for f in current_festivals],
            "seasonal_boost_keywords": self.knowledge_base.get_seasonal_keywords(current_festivals)
        }

    def calculate_cultural_score(self, cultural_context: CulturalContext, query_context: Optional[CulturalQueryContext] = None) -> float:
        """Calculate cultural relevance score"""
        base_score = cultural_context.confidence_score
        
        if not query_context:
            return base_score
        
        bonus = 0.0
        
        if cultural_context.craft_type in query_context.detected_craft_types:
            bonus += 0.2
        
        if cultural_context.region in query_context.detected_regions:
            bonus += 0.15
        
        festival_overlap = set(cultural_context.festival_relevance) & set(query_context.detected_festivals)
        if festival_overlap:
            bonus += 0.1 * len(festival_overlap)
        
        return min(base_score + bonus, 1.0)

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            **self.stats,
            "cache_size": len(self.cache),
            "knowledge_base_stats": self.knowledge_base.get_stats(),
            "gemini_success_rate": (
                self.stats["gemini_successes"] / max(self.stats["gemini_successes"] + self.stats["gemini_failures"], 1)
            ) * 100
        }

    def clear_cache(self):
        """Clear analysis cache"""
        cache_size = len(self.cache)
        self.cache.clear()
        logger.info(f"Cultural analysis cache cleared (was {cache_size} entries)")

# Global instance
cultural_service = CulturalAnalysisService()