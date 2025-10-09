# src/services/reranker_service.py - QUOTA PRESERVATION MODE + MODEL FALLBACK
from typing import List, Dict, Any
import google.generativeai as genai
from src.config.settings import settings
import json
import re
import logging
import os

logger = logging.getLogger(__name__)

# Configure Gemini (kept for manual testing)
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    logger.info("Configured Gemini client")
except Exception as e:
    logger.error(f"Failed to configure Gemini client: {e}")

# Maximum number of candidates to send to Gemini for reranking
MAX_RERANK_CANDIDATES = 10

# QUOTA PRESERVATION - Check environment variable
DISABLE_GEMINI_RERANKING = os.getenv("DISABLE_GEMINI_RERANKING", "true").lower() == "true"


# ---------------------------
# Internal helpers
# ---------------------------

def _get_gemini_model(preferred="gemini-1.5-flash"):
    """
    Get a Gemini model with fallback:
    - Try preferred (gemini-1.5-flash)
    - Fall back to gemini-1.5-pro
    - Fall back to gemini-pro-vision
    """
    try:
        return genai.GenerativeModel(preferred)
    except Exception as e:
        logger.warning(f"Model {preferred} unavailable, trying fallback. Error: {e}")
        if preferred == "gemini-1.5-flash":
            return _get_gemini_model("gemini-1.5-pro")
        elif preferred == "gemini-1.5-pro":
            return _get_gemini_model("gemini-pro-vision")
        else:
            raise


def _format_candidate(idx: int, c: Dict[str, Any]) -> str:
    text = c.get("text") or ""
    payload = c.get("payload") or {}
    title = payload.get("title") or ""
    category = payload.get("category") or ""
    snippet = text or title or json.dumps(payload, ensure_ascii=False)
    snippet = snippet.replace("\n", " ").strip()
    if len(snippet) > 200:
        snippet = snippet[:197] + "..."
    cat_part = f" category: {category}" if category else ""
    return f"[{idx}] {snippet}{cat_part}"


def _extract_json_from_text(s: str):
    s = (s or "").strip()
    if not s:
        raise ValueError("empty response text")

    try:
        return json.loads(s)
    except Exception:
        pass

    m = re.search(r"```(?:json)?\s*(\{[\s\S]*\}|\[[\s\S]*\])\s*```", s, flags=re.IGNORECASE)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass

    m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", s)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass

    raise ValueError("No JSON found in response")


# ---------------------------
# Cultural fallback reranker
# ---------------------------

def _cultural_score_rerank(query: str, candidates: List[Dict]) -> List[Dict]:
    if not candidates:
        return []

    logger.debug(f"Using cultural relevance reranking: '{query}'")

    query_lower = query.lower()
    query_tokens = set(query_lower.split())

    cultural_keywords = {
        "high_priority": [
            "traditional", "handmade", "artisan", "heritage", "authentic", "cultural",
            "kundan", "rajasthani", "banarasi", "madhubani", "warli", "phulkari",
            "diwali", "festival", "ceremonial", "bridal", "wedding", "festive"
        ],
        "medium_priority": [
            "pottery", "ceramic", "jewelry", "textile", "silk", "brass", "wooden",
            "blue", "gold", "silver", "handcrafted", "decorative", "ornamental"
        ],
        "craft_types": [
            "pottery", "textiles", "jewelry", "woodwork", "metalcraft", "painting",
            "sculpture", "leather", "stone", "glass", "paper", "bamboo"
        ],
        "materials": [
            "clay", "ceramic", "silk", "cotton", "wool", "gold", "silver", "brass",
            "copper", "wood", "bamboo", "stone", "glass", "leather", "paper"
        ],
        "regions": [
            "rajasthan", "rajasthani", "gujarat", "punjab", "bengal", "tamil",
            "kerala", "mumbai", "delhi", "varanasi", "jaipur", "udaipur"
        ]
    }

    scored_candidates = []
    for candidate in candidates:
        text = (candidate.get("text", "") or "").lower()
        payload = candidate.get("payload", {}) or {}
        title = (payload.get("title", "") or "").lower()
        category = (payload.get("category", "") or "").lower()

        combined_text = f"{text} {title} {category}"
        candidate_tokens = set(combined_text.split())

        score = candidate.get("weighted_score", 0.0)
        cultural_bonus = 0.0

        if len(query_tokens & candidate_tokens) > 0:
            cultural_bonus += len(query_tokens & candidate_tokens) * 0.1

        cultural_bonus += sum(1 for kw in cultural_keywords["high_priority"] if kw in combined_text) * 0.08
        cultural_bonus += sum(1 for kw in cultural_keywords["medium_priority"] if kw in combined_text) * 0.05
        cultural_bonus += sum(1 for kw in cultural_keywords["craft_types"] if kw in combined_text) * 0.06
        cultural_bonus += sum(1 for kw in cultural_keywords["materials"] if kw in combined_text) * 0.04
        cultural_bonus += sum(1 for kw in cultural_keywords["regions"] if kw in combined_text) * 0.07

        if any(token in title for token in query_tokens):
            cultural_bonus += 0.1
        if query_lower in category or category in query_lower:
            cultural_bonus += 0.15

        final_score = score + cultural_bonus
        scored_candidates.append({
            **candidate,
            "cultural_rerank_score": final_score,
            "cultural_bonus": cultural_bonus,
            "original_score": score
        })

    return sorted(scored_candidates, key=lambda x: x["cultural_rerank_score"], reverse=True)


# ---------------------------
# Main reranker
# ---------------------------

def rerank(query: str, candidates: List[Dict]) -> List[Dict]:
    if not candidates:
        return []

    if DISABLE_GEMINI_RERANKING:
        logger.info("Gemini reranking disabled, using cultural reranker")
        return _cultural_score_rerank(query, candidates)

    logger.info(f"Using Gemini for reranking: '{query}'")
    candidates_for_rerank = candidates[:MAX_RERANK_CANDIDATES]
    docs = [_format_candidate(i, c) for i, c in enumerate(candidates_for_rerank)]

    prompt = f"""
You are a ranking system. Given a search query and candidate results,
sort them by relevance to the query.

Query: "{query}"

Candidates:
{chr(10).join(docs)}

Return ONLY valid JSON in this exact format:
{{ "order": [indexes in most relevant order] }}
"""

    try:
        model = _get_gemini_model()
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.0,
            },
        )

        parsed = _extract_json_from_text(response.text or "")
        order = parsed.get("order") if isinstance(parsed, dict) else parsed
        order = [int(i) for i in order if isinstance(i, int) or str(i).isdigit()]

        reranked_slice = [candidates_for_rerank[i] for i in order if 0 <= i < len(candidates_for_rerank)]
        reranked_ids = {c.get("id") for c in reranked_slice}
        remaining = [c for c in candidates if c.get("id") not in reranked_ids]
        return reranked_slice + remaining

    except Exception as e:
        logger.warning(f"Gemini reranking failed: {e}, using cultural fallback")
        return _cultural_score_rerank(query, candidates)
