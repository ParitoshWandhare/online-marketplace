# gift_ai_service/services/gift_retrieval_service.py
"""
Member C: Retrieve similar gifts from Qdrant
"""

from core.vector_store import VectorStore
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

async def retrieve_similar(
    intent: Dict[str, Any],
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Semantic search using intent as query.
    """
    vector_store = VectorStore()
    await vector_store.connect()

    query_text = f"{intent['occasion']} gift for {intent['recipient']} under {intent['budget_inr']} INR, {intent['sentiment']} style"
    
    try:
        results = await vector_store.search_related_items(
            text=query_text,
            limit=top_k
        )
        logger.info(f"Retrieved {len(results)} similar gifts")
        return results
    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        return []