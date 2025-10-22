"""
Setup script to initialize the gift recommendation system.
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

def setup_gift_service():
    """Setup the gift service by initializing the vector store."""
    print("🚀 Setting up Gift Recommendation Service...")
    print("=" * 50)
    print(f"📦 Qdrant Collection: artworks")
    print(f"🗄️  MongoDB Collection: {os.getenv('MONGO_COLLECTION', 'artworks')}")
    print("=" * 50)
    
    try:
        # Initialize orchestrator
        orchestrator = GiftOrchestrator()
        print("✓ GiftOrchestrator initialized")
        
        # Refresh vector store
        print("\n📦 Setting up vector store...")
        print("   - Using existing Qdrant collection: artworks")
        print("   - Loading items from MongoDB") 
        print("   - Generating embeddings")
        print("   - Uploading to Qdrant collection: artworks")
        
        success = orchestrator.refresh_vector_store()
        
        if success:
            print("\n🎉 Setup completed successfully!")
            print("   The gift recommendation service is now ready to use.")
            print("\n💡 You can now run: python -m tests.test_gift_services")
        else:
            print("\n❌ Setup failed!")
            print("   Please check your configuration and try again.")
            
        return success
        
    except Exception as e:
        print(f"\n💥 Setup failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    setup_gift_service()