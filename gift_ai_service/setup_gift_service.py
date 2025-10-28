# gift_ai_service/setup_gift_service.py
"""
Setup script to initialize the gift recommendation system.
FIXED: Now properly handles async operations
"""

import os
import logging
import sys
import asyncio
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.orchestrator import GiftOrchestrator

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def setup_gift_service():
    """Setup the gift service (async version)"""
    print("🚀 Setting up Gift Recommendation Service...")
    print("=" * 60)
    print(f"📦 Qdrant Collection: {os.getenv('COLLECTION_NAME', 'artworks')}")
    print(f"🗄️  MongoDB: {os.getenv('DATABASE_NAME', 'test')}.{os.getenv('COLLECTION_NAME', 'artworks')}")
    print("=" * 60)
    
    try:
        # Initialize orchestrator
        logger.info("Initializing GiftOrchestrator...")
        orchestrator = GiftOrchestrator()
        print("✅ GiftOrchestrator initialized")
        
        # Connect to databases
        logger.info("Connecting to databases...")
        await orchestrator.vector_store.connect()
        print("✅ Connected to MongoDB & Qdrant")
        
        # Refresh vector store
        print("\n📦 Refreshing vector store...")
        print("   1️⃣  Setting up Qdrant collection...")
        print("   2️⃣  Loading items from MongoDB...")
        print("   3️⃣  Generating embeddings...")
        print("   4️⃣  Uploading to Qdrant...")
        
        result = await orchestrator.refresh_vector_store()
        
        if result.get("success"):
            items_count = result.get("items_count", 0)
            print(f"\n🎉 Setup completed successfully!")
            print(f"   ✅ Uploaded {items_count} items to Qdrant")
            print(f"   ✅ Collection '{os.getenv('COLLECTION_NAME', 'artworks')}' is ready")
            print("\n💡 Next steps:")
            print("   1. Start main service: python main.py")
            print("   2. Start vision AI (optional): python vision_ai_service.py")
            print("   3. Test API: http://localhost:8001/docs")
            return True
        else:
            error = result.get("error", "Unknown error")
            step = result.get("step", "unknown")
            print(f"\n❌ Setup failed at step '{step}': {error}")
            print("\n🔍 Troubleshooting:")
            
            if step == "mongodb_check":
                print("   ⚠️  MongoDB not connected")
                print("   ➡️  Check MONGODB_URL in .env")
                print("   ➡️  Ensure MongoDB is running: mongod")
            elif step == "qdrant_check":
                print("   ⚠️  Qdrant not connected")
                print("   ➡️  Check QDRANT_URL in .env")
                print("   ➡️  Start Qdrant: docker run -p 6333:6333 qdrant/qdrant")
            elif step == "mongodb_empty":
                print("   ⚠️  No items in MongoDB")
                print("   ➡️  Add some test items to your MongoDB collection")
            
            return False
            
    except Exception as e:
        print(f"\n💥 Setup failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Entry point - runs async setup"""
    success = asyncio.run(setup_gift_service())
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()