# gift_ai_service/services/gift_retrieval_service.py
"""
Retrieval service for finding similar gifts
FIXED: Don't use global vector_store, get it from orchestrator
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

async def retrieve_similar(
    intent: Dict[str, Any], 
    top_k: int = 5,
    vector_store = None  # Accept vector_store as parameter
) -> List[Dict[str, Any]]:
    """
    Retrieve similar gifts based on extracted intent
    
    Args:
        intent: Extracted intent dictionary containing occasion, recipient, etc.
        top_k: Number of items to retrieve
        vector_store: VectorStore instance (passed from orchestrator)
        
    Returns:
        List of gift items with fields at root level
    """
    # If no vector_store provided, try to get from orchestrator
    if vector_store is None:
        logger.error("❌ No vector_store provided to retrieve_similar")
        raise Exception("Vector store not provided")
    
    try:
        # Build search query from intent
        query_parts = []
        
        if intent.get('occasion'):
            query_parts.append(intent['occasion'])
        
        if intent.get('recipient'):
            query_parts.append(f"gift for {intent['recipient']}")
        
        if intent.get('interests'):
            interests = intent['interests']
            if isinstance(interests, list):
                query_parts.extend(interests)
            else:
                query_parts.append(str(interests))
        
        if intent.get('sentiment'):
            query_parts.append(intent['sentiment'])
        
        # Create search query
        search_query = ' '.join(query_parts) if query_parts else 'handmade gift'
        
        logger.info(f"🔍 Retrieval query: '{search_query}'")
        
        # Search in vector store (passed from orchestrator)
        items = await vector_store.search_related_items(
            text=search_query,
            limit=top_k
        )
        
        logger.info(f"Found {len(items)} similar items for query: '{search_query}'")
        
        # Ensure all items have required fields at root level
        formatted_items = []
        for item in items:
            # If fields are in payload, move them to root
            if 'payload' in item and not item.get('title'):
                payload = item.get('payload', {})
                formatted_item = {
                    'title': payload.get('title', ''),
                    'description': payload.get('description', ''),
                    'price': payload.get('price', 0),
                    'category': payload.get('category', 'General'),
                    'mongo_id': payload.get('mongo_id', ''),
                    'score': item.get('score', 1.0),
                    'payload': payload  # Keep for reference
                }
            else:
                # Already formatted correctly
                formatted_item = item
            
            formatted_items.append(formatted_item)
        
        return formatted_items
        
    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        import traceback
        traceback.print_exc()
        raise  # Re-raise to be handled by orchestrator