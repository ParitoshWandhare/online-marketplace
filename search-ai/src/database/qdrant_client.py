# Fix for qdrant_client.py - Add proper scroll and retrieve methods

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, 
    VectorParams, 
    FieldCondition, 
    PayloadSchemaType,
    CreateFieldIndex,
    ScrollRequest,
    Filter
)
from typing import List, Tuple, Optional, Any
from src.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class EnhancedQdrantClient:
    """Enhanced Qdrant client with proper scroll and retrieve methods"""
    
    def __init__(self):
        self.client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
    
    def scroll(
        self, 
        collection_name: str, 
        scroll_filter: Optional[Filter] = None,
        limit: int = 100,
        offset: Optional[str] = None,
        with_payload: bool = True,
        with_vectors: bool = False
    ) -> Tuple[List[Any], Optional[str]]:
        """
        Proper scroll method for Qdrant - FIXED
        Returns: (points, next_page_offset)
        """
        try:
            # Don't use ScrollRequest - call scroll directly
            result = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=scroll_filter,
                limit=limit,
                offset=offset,
                with_payload=with_payload,
                with_vectors=with_vectors
            )
            
            # Result is a tuple: (points, next_offset)
            if isinstance(result, tuple):
                points = result[0] if result[0] else []
                next_offset = result[1] if len(result) > 1 else None
            else:
                # Fallback for different response format
                points = getattr(result, 'points', [])
                next_offset = getattr(result, 'next_page_offset', None)
            
            logger.info(f"Scroll returned {len(points)} points")
            return points, next_offset
            
        except Exception as e:
            logger.error(f"Error in scroll operation: {e}")
            return [], None
    
    def retrieve(self, collection_name: str, ids: List[str], with_payload: bool = True, with_vectors: bool = False):
        """Retrieve specific points by ID"""
        try:
            result = self.client.retrieve(
                collection_name=collection_name,
                ids=ids,
                with_payload=with_payload,
                with_vectors=with_vectors
            )
            logger.info(f"Retrieved {len(result) if result else 0} points for IDs: {ids}")
            return result if result else []
        except Exception as e:
            logger.error(f"Error retrieving points {ids}: {e}")
            return []
    
    def get_collection(self, collection_name: str):
        """Get collection info"""
        return self.client.get_collection(collection_name)
    
    def get_collections(self):
        """Get all collections"""
        return self.client.get_collections()
    
    def recreate_collection(self, collection_name: str, vectors_config):
        """Recreate collection"""
        return self.client.recreate_collection(collection_name, vectors_config=vectors_config)
    
    def create_payload_index(self, collection_name: str, field_name: str, field_schema):
        """Create payload index"""
        return self.client.create_payload_index(collection_name, field_name, field_schema)
    
    def search(self, *args, **kwargs):
        """Proxy search to client"""
        return self.client.search(*args, **kwargs)
    
    def upsert(self, *args, **kwargs):
        """Proxy upsert to client"""
        return self.client.upsert(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Proxy delete to client"""
        return self.client.delete(*args, **kwargs)

# Create enhanced client instance
qdrant = EnhancedQdrantClient()

# Rest of the existing functions remain the same but use the enhanced client
def init_qdrant():
    try:
        collections = [c.name for c in qdrant.get_collections().collections]
        
        if settings.COLLECTION_NAME not in collections:
            logger.info(f"Creating new collection: {settings.COLLECTION_NAME}")
            
            # Create collection with vectors only
            qdrant.recreate_collection(
                collection_name=settings.COLLECTION_NAME,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            )
            
            # Create field indexes after collection creation
            create_field_indexes()
        else:
            logger.info(f"Collection {settings.COLLECTION_NAME} already exists")
            # Check if indexes exist, create if missing
            ensure_field_indexes()
            
    except Exception as e:
        logger.error(f"Error initializing Qdrant: {e}")
        raise

def create_field_indexes():
    """Create field indexes for filtering"""
    try:
        # Create index for category field
        qdrant.create_payload_index(
            collection_name=settings.COLLECTION_NAME,
            field_name="category",
            field_schema=PayloadSchemaType.KEYWORD
        )
        logger.info("Created index for 'category' field")
        
        # Create index for material field if you use it
        qdrant.create_payload_index(
            collection_name=settings.COLLECTION_NAME,
            field_name="material", 
            field_schema=PayloadSchemaType.KEYWORD
        )
        logger.info("Created index for 'material' field")
        
        # Create index for cultural context fields
        qdrant.create_payload_index(
            collection_name=settings.COLLECTION_NAME,
            field_name="craft_type",
            field_schema=PayloadSchemaType.KEYWORD
        )
        logger.info("Created index for 'craft_type' field")
        
    except Exception as e:
        logger.error(f"Error creating field indexes: {e}")
        # Don't raise here as indexes might already exist

def ensure_field_indexes():
    """Ensure required field indexes exist"""
    try:
        # Get collection info to check existing indexes
        collection_info = qdrant.get_collection(settings.COLLECTION_NAME)
        
        # Check if category index exists
        existing_indexes = collection_info.payload_schema or {}
        
        if "category" not in existing_indexes:
            logger.info("Category index missing, creating...")
            qdrant.create_payload_index(
                collection_name=settings.COLLECTION_NAME,
                field_name="category",
                field_schema=PayloadSchemaType.KEYWORD
            )
            
        if "material" not in existing_indexes:
            logger.info("Material index missing, creating...")
            qdrant.create_payload_index(
                collection_name=settings.COLLECTION_NAME,
                field_name="material",
                field_schema=PayloadSchemaType.KEYWORD
            )
            
    except Exception as e:
        logger.warning(f"Could not check/create indexes: {e}")