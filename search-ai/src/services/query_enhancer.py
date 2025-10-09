# services/query_enhancer.py - QUOTA PRESERVATION MODE
from typing import List
import google.generativeai as genai
from src.config.settings import settings
import logging
import os

logger = logging.getLogger(__name__)

# Fast, low-latency model for expansions
_MODEL = "gemini-1.5-flash"

# QUOTA PRESERVATION - Check environment variable
DISABLE_GEMINI_EXPANSION = os.getenv("DISABLE_GEMINI_EXPANSION", "true").lower() == "true"

def _fallback_expansions(query: str, topn: int = 3) -> List[str]:
    """
    Enhanced fallback expansions for cultural/artisan queries
    """
    q = query.lower()
    expansions = set()

    # Enhanced synonyms for Indian crafts
    synonyms = {
        "blue": ["indigo", "azure", "navy", "cobalt"],
        "kitchen": ["tableware", "dining", "serveware", "cookware"],
        "pottery": ["ceramic", "stoneware", "earthenware", "terracotta"],
        "bowl": ["dish", "plate", "serve bowl", "vessel"],
        "handmade": ["handcrafted", "artisan", "craft", "traditional"],
        "gift": ["present", "souvenir", "hamper", "offering"],
        "traditional": ["heritage", "classic", "handloom", "authentic"],
        "jewelry": ["ornament", "accessory", "adornment", "jewellery"],
        "kundan": ["gemstone", "precious stone", "royal jewelry", "traditional jewelry"],
        "rajasthani": ["rajasthan craft", "royal", "desert craft", "pink city"],
        "bridal": ["wedding", "marriage", "ceremonial", "festive"],
        "silk": ["fabric", "textile", "cloth", "material"],
        "brass": ["metal", "bronze", "copper alloy", "metalwork"],
        "wooden": ["wood", "timber", "carved", "handcarved"],
        "festival": ["celebration", "festive", "occasion", "ceremony"],
        "diwali": ["deepavali", "festival of lights", "celebration", "festive"],
        "holi": ["color festival", "spring festival", "celebration"],
        "wedding": ["marriage", "bridal", "ceremonial", "festive"]
    }

    for token in q.split():
        if token in synonyms:
            expansions.update(synonyms[token])

    # Cultural context combinations
    if "jewelry" in q and any(x in q for x in ["kundan", "rajasthani", "traditional"]):
        expansions.update(["traditional jewelry", "indian jewelry", "ethnic jewelry", "heritage jewelry"])
    
    if "pottery" in q and "blue" in q:
        expansions.update(["blue ceramic", "blue pottery", "indigo pottery", "ceramic art"])
        
    if "festival" in q or "diwali" in q or "celebration" in q:
        expansions.update(["festive items", "celebration decor", "traditional gifts", "ceremonial"])
        
    if "traditional" in q or "handmade" in q:
        expansions.update(["artisan craft", "heritage item", "cultural artifact", "authentic craft"])

    # Fallback to basic expansions
    if not expansions:
        expansions.update([f"artisan {q}", f"traditional {q}", f"handmade {q}"])

    # Clean and limit
    exps = [e.strip() for e in expansions if e.strip() and e.strip() != q.lower()]
    return list(set(exps))[:topn]  # Remove duplicates and limit


def enhance_query(query: str, topn: int = 3) -> List[str]:
    """
    Query enhancement with quota preservation mode.
    Uses enhanced fallback to preserve Gemini quota for cultural analysis.
    """
    
    # QUOTA PRESERVATION MODE - Skip Gemini entirely
    if DISABLE_GEMINI_EXPANSION:
        logger.debug(f"Using enhanced fallback query expansion (preserving Gemini quota): '{query}'")
        return _fallback_expansions(query, topn)
    
    # Original Gemini-based expansion (only if explicitly enabled)
    try:
        logger.info(f"Using Gemini for query expansion (will consume quota): '{query}'")
        
        model = genai.GenerativeModel(
            _MODEL,
            system_instruction=(
                "You expand e-commerce search queries for a handmade/crafts marketplace. "
                "Return 3-6 word phrases, specific to materials, techniques, and styles. "
                "Do NOT include explanations. Do NOT repeat the original query. "
                "Avoid stopwords. Focus on buyer intent (use-cases, materials, craft terms)."
            ),
            generation_config={
                # Force JSON so parsing is robust
                "response_mime_type": "application/json",
                "temperature": 0.4,
            },
        )

        prompt = {
            "query": query,
            "constraints": {
                "max_expansions": topn,
                "max_words_per_phrase": 6,
                "domain": "handmade crafts, textiles, pottery, jewelry, woodwork",
            },
            "output_format": {
                "expansions": ["<string>"]
            },
            "instruction": (
                "Generate up to {max_expansions} concise expansions that help find relevant handmade items. "
                "Focus on synonyms, related crafts, materials, techniques, and buyer intent. "
                "Return JSON as: {\"expansions\": [\"...\"]} with only short phrases."
            ),
        }

        resp = model.generate_content(prompt)
        data = resp.text  # already JSON because of response_mime_type
        # genai sometimes returns text already as JSON string; eval safely via json
        import json
        parsed = json.loads(data)
        raw_list = parsed.get("expansions", [])
        # Clean + dedupe + clip
        cleaned = []
        seen = set()
        for phrase in raw_list:
            p = " ".join(str(phrase).split())[:60]  # trim long phrases
            if p and p.lower() != query.lower() and p.lower() not in seen:
                cleaned.append(p)
                seen.add(p.lower())
        return cleaned[:topn] if cleaned else _fallback_expansions(query, topn)
        
    except Exception as e:
        logger.warning(f"Gemini query expansion failed: {e}, using enhanced fallback")
        return _fallback_expansions(query, topn)