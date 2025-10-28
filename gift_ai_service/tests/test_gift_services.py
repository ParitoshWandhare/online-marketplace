"""
Test script for the gift recommendation system.
"""

import os
import logging
import sys
from dotenv import load_dotenv

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.orchestrator import GiftOrchestrator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_gift_service():
    """Test the complete gift recommendation service."""
    logger.info("Starting gift service test")
    
    try:
        # Initialize orchestrator
        orchestrator = GiftOrchestrator()
        logger.info("Orchestrator initialized successfully")
        
        # First, refresh vector store with items (THIS IS CRITICAL)
        logger.info("Step 1: Refreshing vector store with items...")
        success = orchestrator.refresh_vector_store()
        if success:
            logger.info("✓ Vector store refreshed successfully - collection created and items uploaded")
        else:
            logger.error("✗ Vector store refresh failed")
            logger.info("Continuing with test, but search may fail...")
        
        # Test queries
        test_queries = [
            "decorative items for home office",
            "diwali gift ideas for family",
            "birthday gift for art lover",
            "anniversary present for book enthusiasts"
        ]
        
        # Test each query
        for query in test_queries:
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing query: {query}")
            logger.info(f"{'='*60}")
            
            result = orchestrator.process_gift_query(query, limit=5)
            
            # Print results
            print(f"\n📋 Query: {result['query']}")
            print(f"🎁 Number of bundles: {len(result['bundles'])}")
            
            if 'error' in result:
                print(f"❌ Error: {result['error']}")
                continue
            
            if not result['bundles']:
                print("⚠️  No bundles generated")
                continue
            
            for i, bundle in enumerate(result['bundles'], 1):
                print(f"\n📦 Bundle {i}: {bundle['bundle_name']}")
                print(f"📝 Description: {bundle['description']}")
                print("🛍️ Items:")
                for item in bundle['items']:
                    print(f"   • {item['title']}: {item['reason']}")
            
            if 'metadata' in result:
                print(f"\n📊 Metadata: {result['metadata']}")
        
        logger.info("🎉 Gift service test completed successfully")
        
    except Exception as e:
        logger.error(f"💥 Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

def test_vector_store_setup():
    """Test just the vector store setup separately."""
    logger.info("Testing vector store setup only...")
    
    try:
        from core.vector_store import VectorStore
        vector_store = VectorStore()
        
        # Test collection setup
        logger.info("Setting up collection...")
        if vector_store.setup_collection("gift_items"):
            logger.info("✓ Collection setup successful")
        else:
            logger.error("✗ Collection setup failed")
            return False
        
        # Test getting items from MongoDB
        logger.info("Getting items from MongoDB...")
        items = vector_store.get_mongo_items(limit=10)
        logger.info(f"Retrieved {len(items)} items from MongoDB")
        
        # Test uploading items
        if items:
            logger.info("Uploading items to Qdrant...")
            if vector_store.upload_items(items):
                logger.info(f"✓ Successfully uploaded {len(items)} items to Qdrant")
            else:
                logger.error("✗ Failed to upload items to Qdrant")
                return False
        else:
            logger.warning("No items to upload")
        
        # Test search
        logger.info("Testing search functionality...")
        search_results = vector_store.search_related_items("decorative items", "gift_items", limit=3)
        logger.info(f"Search returned {len(search_results)} items")
        
        return True
        
    except Exception as e:
        logger.error(f"Vector store test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎁 Gift Recommendation System Test")
    print("=" * 50)
    
    # First test vector store setup
    print("\n1. Testing Vector Store Setup...")
    vector_store_success = test_vector_store_setup()
    
    if vector_store_success:
        print("\n2. Testing Complete Gift Service...")
        test_gift_service()
    else:
        print("\n❌ Vector store setup failed. Cannot proceed with full test.")
        print("💡 Please check your Qdrant and MongoDB connections.")