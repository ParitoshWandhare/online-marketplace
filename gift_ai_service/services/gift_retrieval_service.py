# gift_ai_service/services/gift_retrieval_service.py
"""
Gift Retrieval Service - Semantic Search
Retrieves relevant items based on intent using vector similarity
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

async def retrieve_similar(intent: Dict[str, Any], top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieve similar gifts based on extracted intent.
    
    Args:
        intent: Structured intent with occasion, recipient, budget, interests
        top_k: Number of items to retrieve
    
    Returns:
        List of items with similarity scores
    """
    from core.orchestrator import GiftOrchestrator
    
    try:
        # Build query from intent
        query_parts = []
        
        if intent.get('occasion'):
            query_parts.append(intent['occasion'])
        if intent.get('recipient'):
            query_parts.append(f"gift for {intent['recipient']}")
        if intent.get('interests'):
            query_parts.extend(intent['interests'])
        
        query = " ".join(query_parts)
        
        logger.info(f"🔍 Retrieving items for query: '{query}'")
        
        # Get orchestrator instance (assumes it's initialized)
        # In production, pass vector_store as parameter
        from core.vector_store import VectorStore
        vector_store = VectorStore()
        await vector_store.connect()
        
        # Search vector store
        items = await vector_store.search_related_items(
            text=query,
            limit=top_k
        )
        
        logger.info(f"✅ Retrieved {len(items)} items")
        return items
        
    except Exception as e:
        logger.error(f"❌ Retrieval failed: {e}")
        return []