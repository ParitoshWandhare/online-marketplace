# Test this in a Python script or add as a temporary endpoint
from src.database.qdrant_client import qdrant
from src.config.settings import settings

def test_qdrant_connection():
    try:
        # Test connection
        collections = qdrant.get_collections()
        print(f"✓ Connected to Qdrant. Collections: {[c.name for c in collections.collections]}")
        
        # Check your collection
        if settings.COLLECTION_NAME in [c.name for c in collections.collections]:
            info = qdrant.get_collection(settings.COLLECTION_NAME)
            print(f"✓ Collection '{settings.COLLECTION_NAME}' exists")
            print(f"  Points: {info.points_count}")
            print(f"  Status: {info.status}")
        else:
            print(f"✗ Collection '{settings.COLLECTION_NAME}' missing!")
            
    except Exception as e:
        print(f"✗ Qdrant connection failed: {e}")

test_qdrant_connection()