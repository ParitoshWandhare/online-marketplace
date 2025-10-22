"""
Orchestrator for the gift recommendation system.
Coordinates vector store, validation, and bundle generation.
"""

import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GiftOrchestrator:
    """Main orchestrator for gift recommendation flow."""
    
    def __init__(self):
        """Initialize GiftOrchestrator with all required services."""
        from core.vector_store import VectorStore
        from services.gift_bundle_service import GiftBundleService
        
        self.vector_store = VectorStore()
        self.bundle_service = GiftBundleService()
        logger.info("GiftOrchestrator initialized successfully")

    def refresh_vector_store(self) -> bool:
        """
        Refresh vector store with latest items from MongoDB.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Starting vector store refresh")
            
            # Setup collection - will use the default "artworks" collection
            logger.info("Step 1: Setting up Qdrant collection...")
            if not self.vector_store.setup_collection():  # No parameter = use default
                logger.error("Failed to setup collection")
                return False
            logger.info("✓ Collection setup completed")
            
            # Get items from MongoDB
            logger.info("Step 2: Retrieving items from MongoDB...")
            items = self.vector_store.get_mongo_items(limit=100)
            
            if not items:
                logger.warning("No items found in MongoDB")
                return False
            
            logger.info(f"✓ Retrieved {len(items)} items")
            
            # Upload to vector store - will use the default "artworks" collection
            logger.info("Step 3: Uploading items to Qdrant...")
            success = self.vector_store.upload_items(items)  # No parameter = use default
            
            if success:
                logger.info("✓ Vector store refresh completed successfully")
                logger.info(f"✓ Uploaded {len(items)} items to Qdrant collection 'artworks'")
            else:
                logger.error("✗ Vector store refresh failed")
                
            return success
            
        except Exception as e:
            logger.error(f"Error refreshing vector store: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def process_gift_query(self, user_intent: str, limit: int = 10) -> Dict[str, Any]:
        """
        Process a gift query through the full pipeline.
        
        Args:
            user_intent: User's gift search intent
            limit: Maximum number of items to retrieve
            
        Returns:
            Dict containing final gift suggestions
        """
        logger.info(f"Processing gift query: {user_intent}")
        
        try:
            # Step 1: Retrieve items from vector store - will use the default "artworks" collection
            logger.info("Step 1: Retrieving similar items from vector store")
            items = self.vector_store.search_related_items(
                text=user_intent,
                collection_name=None,  # None = use default "artworks" collection
                limit=limit
            )
            
            if not items:
                logger.warning("No items found for query")
                return {
                    'query': user_intent,
                    'bundles': [],
                    'error': 'No matching items found in vector store. Please refresh the vector store first.'
                }
            
            logger.info(f"✓ Retrieved {len(items)} similar items")
            
            # Step 2: Validate items
            logger.info("Step 2: Validating items")
            from services.gift_validation_service import validate_items
            valid_items, invalid_items = validate_items(items)
            
            if not valid_items:
                logger.warning("No valid items after validation")
                return {
                    'query': user_intent,
                    'bundles': [],
                    'error': 'No valid items available',
                    'invalid_items': invalid_items
                }
            
            logger.info(f"✓ Validation passed: {len(valid_items)} valid items")
            
            # Step 3: Generate bundles
            logger.info("Step 3: Generating gift bundles")
            result = self.bundle_service.generate_bundles(user_intent, valid_items)
            
            # Add metadata
            result['metadata'] = {
                'total_items_retrieved': len(items),
                'valid_items_count': len(valid_items),
                'invalid_items_count': len(invalid_items)
            }
            
            logger.info(f"✓ Successfully processed query. Generated {len(result['bundles'])} bundles")
            return result
            
        except Exception as e:
            logger.error(f"Error processing gift query: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'query': user_intent,
                'bundles': [],
                'error': f'Processing failed: {str(e)}'
            }