from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from src.services.embedding_service import embed_text

qdrant = QdrantClient(host="localhost", port=6333)

def build_filter(filters: Dict) -> Optional[Filter]:
    """
    Convert user filter dict into Qdrant Filter object.
    Example: { "category": "pottery", "material": "clay" }
    """
    if not filters:
        return None

    must_conditions = []
    for field, value in filters.items():
        must_conditions.append(
            FieldCondition(
                key=field,
                match=MatchValue(value=value)
            )
        )

    return Filter(must=must_conditions)


def hybrid_search(
    query: str,
    collection: str,
    limit: int = 10,
    filters: Optional[Dict] = None,
    score_threshold: float = 0.7
) -> List[Dict]:
    """
    Perform hybrid search:
    1. Semantic vector search.
    2. If scores < threshold → fallback to keyword (payload filter).
    3. Merge results.
    """
    query_vector = embed_text(query)
    qdrant_filter = build_filter(filters)

    # 1️⃣ Semantic search
    semantic_results = qdrant.search(
        collection_name=collection,
        query_vector=query_vector,
        limit=limit,
        query_filter=qdrant_filter,
    )

    # Check if semantic results are relevant
    if semantic_results and semantic_results[0].score >= score_threshold:
        return [hit.dict() for hit in semantic_results]

    # 2️⃣ Fallback keyword search
    keyword_results = qdrant.scroll(
        collection_name=collection,
        scroll_filter=qdrant_filter,
        limit=limit
    )

    keyword_hits = []
    if keyword_results[0]:
        for point in keyword_results[0]:
            payload = point.payload
            if query.lower() in str(payload).lower():  # naive keyword match
                keyword_hits.append(point.dict())

    # 3️⃣ Merge (semantic first, then keyword)
    merged = [hit.dict() for hit in semantic_results] + keyword_hits
    seen_ids = set()
    deduped = []
    for item in merged:
        if item["id"] not in seen_ids:
            deduped.append(item)
            seen_ids.add(item["id"])

    return deduped[:limit]
