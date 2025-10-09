# services/search_service.py - FIXED VERSION
from typing import Dict, List, Optional, Any
from src.services.embedding_service import get_embedding
from src.services.query_enhancer import enhance_query
from src.services.reranker_service import rerank
from src.database.qdrant_client import qdrant
from src.config.settings import settings
from qdrant_client.models import (
    PointStruct, 
    Filter, 
    FieldCondition, 
    MatchValue, 
    MatchAny,
    ScrollRequest
)
import uuid
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


def index_item(item_id: str, text: str, payload: dict = None):
    """Index an item with proper payload structure for filtering"""
    try:
        vector = get_embedding(text)

        # If item_id is not a valid UUID, generate one
        try:
            point_id = str(uuid.UUID(item_id))
        except ValueError:
            point_id = str(uuid.uuid4())
            logger.warning(f"Invalid UUID {item_id}, generated new one: {point_id}")

        # FIXED: Ensure text is always stored in payload
        final_payload = payload or {}
        final_payload["text"] = text  # 👈 CRITICAL FIX
        final_payload["item_id"] = item_id
        
        # Ensure filterable fields exist (add defaults if missing)
        if "category" not in final_payload:
            final_payload["category"] = "unknown"
        if "material" not in final_payload:
            final_payload["material"] = "unknown"

        qdrant.upsert(
            collection_name=settings.COLLECTION_NAME,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=final_payload
                )
            ],
        )
        
        logger.info(f"Successfully indexed item {point_id} with text: '{text[:50]}...'")
        return {"status": "indexed", "id": point_id}
        
    except Exception as e:
        logger.error(f"Error indexing item {item_id}: {e}")
        raise


def _build_filter(filters: Optional[Dict]) -> Optional[Filter]:
    """
    Convert a dictionary of filters into a Qdrant Filter.
    Supports:
    - Single keyword (string)
    - Multi-value keywords (list)
    - Numeric range: dict with 'gte'/'lte'
    - Boolean values
    """
    if not filters:
        return None

    must_conditions = []

    for field, value in filters.items():
        if value is None:
            continue

        # Multi-value keyword list
        if isinstance(value, list) and value:
            must_conditions.append(FieldCondition(key=field, match=MatchAny(any=value)))

        # Numeric range: {"gte": 10, "lte": 50}
        elif isinstance(value, dict) and ("gte" in value or "lte" in value):
            range_params = {}
            if "gte" in value:
                range_params["gte"] = value["gte"]
            if "lte" in value:
                range_params["lte"] = value["lte"]
            must_conditions.append(FieldCondition(key=field, range=range_params))

        # Single keyword or boolean
        else:
            must_conditions.append(FieldCondition(key=field, match=MatchValue(value=value)))

    if not must_conditions:
        return None

    return Filter(must=must_conditions)



def _search_single_vector(query_vector, limit: int, qdrant_filter: Optional[Filter] = None):
    """Helper to search Qdrant with a single vector and improved error handling."""
    try:
        results = qdrant.search(
            collection_name=settings.COLLECTION_NAME,
            query_vector=query_vector,
            limit=limit,
            with_payload=True,
            query_filter=qdrant_filter,
        )
        return results
        
    except Exception as e:
        logger.error(f"Error in vector search: {e}")
        if "Index required but not found" in str(e):
            logger.error("Missing field index. Run init_qdrant() or create indexes manually.")
            return []
        raise


def _deduplicate_results(candidate_pool: Dict) -> Dict:
    """
    Remove duplicate results based on text content similarity.
    FIXED: Handle cases where text might be None or similar.
    """
    if not candidate_pool:
        return candidate_pool
    
    # Group by text content (handle None values)
    text_groups = defaultdict(list)
    
    for item_id, item_data in candidate_pool.items():
        text_key = (item_data.get("text") or "").strip().lower()
        if not text_key:  # Handle empty/None text
            text_key = f"no_text_{item_id}"
        
        text_groups[text_key].append((item_id, item_data))
    
    # Keep only the best scoring item from each text group
    deduplicated = {}
    for text_key, items in text_groups.items():
        # Sort by weighted_score, keep the best one
        best_item_id, best_item = max(items, key=lambda x: x[1]["weighted_score"])
        deduplicated[best_item_id] = best_item
    
    logger.info(f"Deduplicated: {len(candidate_pool)} -> {len(deduplicated)} results")
    return deduplicated


def search_items(
    query: str,
    limit: int = 5,
    use_expansion: bool = True,
    use_reranker: bool = True,
    filters: Optional[Dict] = None,
    score_threshold: float = 0.7
):
    """
    FIXED: Improved multi-pass hybrid search with deduplication and performance optimization.
    """
    try:
        import time
        start_time = time.time()
        
        # 1) Prepare subqueries - LIMIT expansion for performance
        subqueries: List[str] = [query]
        if use_expansion:
            try:
                # FIXED: Reduce expansion queries for better performance
                expansions = enhance_query(query, topn=2)  # Reduced from 3 to 2
                subqueries.extend(expansions)
            except Exception as e:
                logger.warning(f"Query expansion failed: {e}")

        # FIXED: Simplified weights for better performance
        weights = [1.0, 0.8, 0.6][:len(subqueries)]

        # Build filter
        qdrant_filter = _build_filter(filters)
        if qdrant_filter and filters:
            logger.info(f"Applied filters: {filters}")

        # 2) Run semantic searches
        candidate_pool = {}
        per_query_fetch = min(limit * 2, 20)  # FIXED: Reduced fetch size for performance

        for sq, w in zip(subqueries, weights):
            try:
                vec = get_embedding(sq)
                results = _search_single_vector(vec, limit=per_query_fetch, qdrant_filter=qdrant_filter)

                for r in results:
                    _id = str(r.id)  # Ensure string ID
                    raw_score = r.score or 0.0
                    weighted = raw_score * w
                    
                    # FIXED: Better text extraction
                    payload = r.payload or {}
                    text_content = payload.get("text") or payload.get("title") or "No text available"

                    if _id not in candidate_pool:
                        candidate_pool[_id] = {
                            "id": _id,
                            "score": raw_score,
                            "weighted_score": weighted,
                            "text": text_content,  # FIXED: Ensure text is not None
                            "payload": payload,
                            "hits": 1,
                            "best_weight": w,
                        }
                    else:
                        # Update if this is a better score
                        if weighted > candidate_pool[_id]["weighted_score"]:
                            candidate_pool[_id]["weighted_score"] = weighted
                            candidate_pool[_id]["score"] = raw_score
                            candidate_pool[_id]["best_weight"] = w
                        candidate_pool[_id]["hits"] += 1
                        
            except Exception as e:
                logger.error(f"Error in semantic search for query '{sq}': {e}")
                continue

        # FIXED: Add deduplication step
        candidate_pool = _deduplicate_results(candidate_pool)

        # 3) Apply multi-hit boost
        for item in candidate_pool.values():
            boost = 0.02 * (item["hits"] - 1)  # FIXED: Reduced boost for less bias
            item["weighted_score"] += boost

        # 4) Rank by weighted score
        ranked = sorted(candidate_pool.values(), key=lambda x: x["weighted_score"], reverse=True)
        topk = ranked[:limit]

        # 5) OPTIONAL: Apply reranker only if we have good results
        if use_reranker and topk and len(topk) >= 2:
            try:
                rerank_start = time.time()
                topk = rerank(query, topk)
                rerank_time = (time.time() - rerank_start) * 1000
                logger.info(f"Reranking took {rerank_time:.2f}ms")
            except Exception as e:
                logger.warning(f"Reranking failed: {e}")

        # 6) Return clean response
        final_results = []
        for item in topk:
            # FIXED: Ensure all required fields are present
            result = {
                "id": str(item["id"]),
                "score": round(item["score"], 4),
                "weighted_score": round(item["weighted_score"], 5),
                "hits": item["hits"],
                "text": item["text"] or "No text available",  # FIXED: Never return None
                "payload": item["payload"] or {},
            }
            final_results.append(result)
        
        total_time = (time.time() - start_time) * 1000
        logger.info(f"Search for '{query}' completed in {total_time:.2f}ms, returned {len(final_results)} results")
        
        return final_results
        
    except Exception as e:
        logger.error(f"Critical error in search_items: {e}")
        return []


def get_collection_stats():
    """Utility function to check collection health"""
    try:
        info = qdrant.get_collection(settings.COLLECTION_NAME)
        return {
            "points_count": info.points_count,
            "vectors_count": info.vectors_count,
            "indexed_vectors_count": info.indexed_vectors_count,
            "payload_schema": dict(info.payload_schema) if info.payload_schema else {},
            "status": info.status
        }
    except Exception as e:
        logger.error(f"Error getting collection stats: {e}")
        return {"error": str(e)}


# UTILITY FUNCTION: Clean up duplicate items
def cleanup_duplicates():
    """Remove duplicate items from the collection"""
    try:
        # Get all points
        all_points, _ = qdrant.scroll(
            collection_name=settings.COLLECTION_NAME,
            limit=1000,
            with_payload=True,
        )
        
        # Group by text content
        text_to_points = defaultdict(list)
        for point in all_points:
            text = (point.payload or {}).get("text", "")
            text_to_points[text].append(point)
        
        # Identify duplicates to delete
        to_delete = []
        for text, points in text_to_points.items():
            if len(points) > 1:
                # Keep the first one, delete the rest
                for point in points[1:]:
                    to_delete.append(point.id)
        
        # Delete duplicates
        if to_delete:
            qdrant.delete(
                collection_name=settings.COLLECTION_NAME,
                points_selector=to_delete
            )
            logger.info(f"Deleted {len(to_delete)} duplicate points")
            
        return {"deleted_duplicates": len(to_delete)}
        
    except Exception as e:
        logger.error(f"Error cleaning duplicates: {e}")
        return {"error": str(e)}