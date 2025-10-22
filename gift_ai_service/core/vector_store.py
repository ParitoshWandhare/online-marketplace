"""
Vector store implementation for gift recommendation system using Qdrant.
Handles embeddings generation and vector similarity search.
"""

import os
import logging
import numpy as np
import uuid
from typing import List, Dict, Any, Optional
import requests
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VectorStore:
    """Handles vector operations for gift recommendations using Qdrant."""
    
    def __init__(self):
        """Initialize VectorStore with environment variables."""
        self.qdrant_url = os.getenv('QDRANT_URL')
        self.qdrant_api_key = os.getenv('QDRANT_API_KEY')
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.mongo_uri = os.getenv('MONGO_URI')
        self.mongo_db = os.getenv('MONGO_DB', 'test')
        self.mongo_collection = os.getenv('MONGO_COLLECTION', 'artworks')
        
        # Use the same collection name as in Qdrant
        self.qdrant_collection_name = "artworks"
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key)
        
        # Initialize MongoDB client only if URI is provided
        self.mongo_client = None
        self.collection = None
        self.mongo_initialized = False
        
        if self.mongo_uri and self.mongo_uri != "your_mongodb_uri_here":
            try:
                from pymongo import MongoClient
                self.mongo_client = MongoClient(self.mongo_uri)
                self.db = self.mongo_client[self.mongo_db]
                self.collection = self.db[self.mongo_collection]
                self.mongo_initialized = True
                logger.info("MongoDB client initialized successfully")
            except ImportError:
                logger.warning("pymongo not installed, MongoDB functionality disabled")
            except Exception as e:
                logger.warning(f"MongoDB connection failed: {str(e)}")
        else:
            logger.warning("MongoDB URI not configured, using mock data")
        
        # Configure Gemini
        if self.google_api_key and self.google_api_key != "your_google_api_key_here":
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.google_api_key)
                self.genai = genai
            except ImportError:
                logger.warning("google-generativeai not installed, Gemini functionality disabled")
                self.genai = None
        else:
            logger.warning("Google API key not configured, using fallback embeddings")
            self.genai = None
        
        # Test Ollama connection
        self.ollama_available = self._test_ollama_connection()
        
        logger.info(f"VectorStore initialized successfully with Qdrant collection: {self.qdrant_collection_name}")

    def _test_ollama_connection(self) -> bool:
        """Test if Ollama is available."""
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            return response.status_code == 200
        except:
            logger.warning("Ollama is not available on localhost:11434")
            return False

    def _generate_simple_embedding(self, text: str) -> List[float]:
        """
        Generate a simple embedding using TF-IDF like approach.
        This is a fallback when no external embedding service is available.
        """
        # Simple character-based embedding for demo purposes
        text = text.lower()
        embedding = [0.0] * 128
        
        for i, char in enumerate(text[:128]):
            embedding[i] = (ord(char) % 100) / 100.0
            
        # Add some semantic-like features based on keywords
        keywords = {
            'art': 0.1, 'painting': 0.2, 'decorative': 0.3, 'home': 0.4,
            'office': 0.5, 'gift': 0.6, 'diwali': 0.7, 'family': 0.8,
            'birthday': 0.9, 'anniversary': 1.0, 'wall': 0.15, 'canvas': 0.25,
            'print': 0.35, 'poster': 0.45, 'photography': 0.55, 'sculpture': 0.65
        }
        
        for keyword, value in keywords.items():
            if keyword in text:
                embedding.append(value)
        
        # Pad or truncate to 128 dimensions
        if len(embedding) < 128:
            embedding.extend([0.0] * (128 - len(embedding)))
        else:
            embedding = embedding[:128]
            
        return embedding

    def _generate_point_id(self, item: Dict, index: int) -> Any:
        """
        Generate a valid Qdrant point ID.
        Qdrant accepts:
        - Unsigned integers (0 to 2^63-1)
        - UUID strings
        """
        try:
            # Option 1: Use simple sequential integers (safest)
            # This ensures we stay within unsigned integer range
            return index + 1
            
            # Option 2: If you want to use MongoDB _id mapping, uncomment below:
            # if '_id' in item:
            #     mongo_id_str = str(item['_id'])
            #     # Create a smaller hash that fits in unsigned int range
            #     point_id = hash(mongo_id_str) & 0x7FFFFFFFFFFFFFFF  # Mask to positive 63-bit
            #     return point_id
            # else:
            #     return index + 1
            
        except:
            # Final fallback: use UUID as string
            return str(uuid.uuid4())

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embeddings using Gemini API first, fallback to Ollama if fails.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List[float] or None: Embedding vector or None if failed
        """
        # Try Gemini first
        if self.google_api_key and self.google_api_key != "your_google_api_key_here" and self.genai:
            try:
                result = self.genai.embed_content(
                    model='models/embedding-001',
                    content=text,
                    task_type="retrieval_document"
                )
                embedding = result['embedding']
                logger.info("Successfully generated embedding using Gemini")
                return embedding
            except Exception as e:
                logger.warning(f"Gemini embedding failed: {str(e)}. Falling back to Ollama.")
        
        # Fallback to Ollama
        if self.ollama_available:
            try:
                response = requests.post(
                    'http://localhost:11434/api/embeddings',
                    json={
                        'model': 'nomic-embed-text',
                        'prompt': text
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    embedding = response.json()['embedding']
                    logger.info("Successfully generated embedding using Ollama")
                    return embedding
                else:
                    logger.warning(f"Ollama embedding failed with status: {response.status_code}")
            except Exception as e:
                logger.warning(f"Ollama embedding failed: {str(e)}")
        
        # Final fallback: simple local embedding
        logger.info("Using simple local embedding as fallback")
        return self._generate_simple_embedding(text)

    def get_mongo_items(self, limit: int = 100) -> List[Dict]:
        """
        Get items from MongoDB.
        
        Args:
            limit: Maximum number of items to retrieve
            
        Returns:
            List of items from MongoDB
        """
        if not self.mongo_initialized or self.collection is None:
            logger.error("MongoDB collection not available")
            return self._get_mock_items()
        
        try:
            # Get sample items for testing
            items = list(self.collection.find(
                {"title": {"$exists": True}},
                {"title": 1, "description": 1, "category": 1, "price": 1, "_id": 1}
            ).limit(limit))
            
            # Convert ObjectId to string for JSON serialization
            for item in items:
                if '_id' in item:
                    item['_id'] = str(item['_id'])
                    
                # Ensure required fields exist
                item.setdefault('title', 'Unknown Item')
                item.setdefault('description', 'No description available')
                item.setdefault('category', 'General')
                item.setdefault('price', 0)
                    
            logger.info(f"Retrieved {len(items)} items from MongoDB")
            return items
        except Exception as e:
            logger.error(f"Error retrieving items from MongoDB: {str(e)}")
            return self._get_mock_items()

    def _get_mock_items(self) -> List[Dict]:
        """Return mock items for testing when MongoDB is not available."""
        mock_items = [
            {
                '_id': '1',
                'title': 'Modern Art Painting',
                'description': 'Beautiful abstract painting for home decoration',
                'category': 'Art',
                'price': 150.00
            },
            {
                '_id': '2', 
                'title': 'Handcrafted Diya Set',
                'description': 'Traditional oil lamps for Diwali celebrations',
                'category': 'Home Decor',
                'price': 25.00
            },
            {
                '_id': '3',
                'title': 'Office Desk Organizer',
                'description': 'Wooden organizer for home office supplies',
                'category': 'Office',
                'price': 35.00
            },
            {
                '_id': '4',
                'title': 'Family Photo Frame',
                'description': 'Elegant frame for family photographs',
                'category': 'Home Decor',
                'price': 45.00
            },
            {
                '_id': '5',
                'title': 'Scented Candles Set',
                'description': 'Aromatherapy candles for relaxing atmosphere',
                'category': 'Home Decor', 
                'price': 30.00
            },
            {
                '_id': '6',
                'title': 'Wall Art Canvas Print',
                'description': 'Modern canvas print for office walls',
                'category': 'Art',
                'price': 75.00
            },
            {
                '_id': '7',
                'title': 'Desk Plant Decor',
                'description': 'Small decorative plant for office desk',
                'category': 'Home Decor',
                'price': 20.00
            }
        ]
        logger.info(f"Using {len(mock_items)} mock items for testing")
        return mock_items

    def setup_collection(self, collection_name: str = None) -> bool:
        """
        Create or recreate a Qdrant collection.
        
        Args:
            collection_name: Name of the collection to create (defaults to artworks)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if collection_name is None:
            collection_name = self.qdrant_collection_name
            
        try:
            # Check if collection already exists
            try:
                existing_collections = self.qdrant_client.get_collections()
                collection_exists = any(
                    col.name == collection_name 
                    for col in existing_collections.collections
                )
                
                if collection_exists:
                    logger.info(f"Collection {collection_name} already exists")
                    return True
                else:
                    logger.info(f"Collection {collection_name} doesn't exist, creating new...")
            except Exception as e:
                logger.warning(f"Could not check existing collections: {str(e)}")
            
            # Create new collection
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=768,
                    distance=models.Distance.COSINE
                )
            )
            logger.info(f"✓ Successfully created collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up collection {collection_name}: {str(e)}")
            return False

    def upload_items(self, items: List[Dict], collection_name: str = None) -> bool:
        """
        Upload a list of items with embeddings to Qdrant.
        
        Args:
            items: List of items to upload
            collection_name: Qdrant collection name (defaults to artworks)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if collection_name is None:
            collection_name = self.qdrant_collection_name
            
        try:
            points = []
            successful_embeddings = 0
            
            for index, item in enumerate(items):
                # Generate embedding from title and description
                text_to_embed = f"{item.get('title', '')} {item.get('description', '')}"
                embedding = self.generate_embedding(text_to_embed)
                
                if embedding:
                    successful_embeddings += 1
                    # Ensure embedding is the right size
                    if len(embedding) > 768:
                        embedding = embedding[:768]
                    elif len(embedding) < 768:
                        embedding.extend([0.0] * (768 - len(embedding)))
                    
                    # Generate valid Qdrant point ID (simple sequential integers)
                    point_id = self._generate_point_id(item, index)
                    
                    point = models.PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            'title': item.get('title', ''),
                            'description': item.get('description', ''),
                            'category': item.get('category', ''),
                            'price': item.get('price', 0),
                            'source': 'mongodb' if self.mongo_initialized else 'mock',
                            'mongo_id': str(item.get('_id', ''))
                        }
                    )
                    points.append(point)
            
            # Upload to Qdrant
            if points:
                self.qdrant_client.upsert(
                    collection_name=collection_name,
                    points=points
                )
                logger.info(f"Successfully uploaded {len(points)} items to Qdrant collection '{collection_name}'")
                logger.info(f"Embedding success rate: {successful_embeddings}/{len(items)} items")
                return True
            else:
                logger.warning("No points to upload")
                return False
                
        except Exception as e:
            logger.error(f"Error uploading items to Qdrant: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def search_related_items(self, text: str, collection_name: str = None, limit: int = 3) -> List[Dict]:
        """
        Search Qdrant for similar items based on text query.
        
        Args:
            text: Query text to search for
            collection_name: Qdrant collection to search in (defaults to artworks)
            limit: Maximum number of results to return
            
        Returns:
            List[Dict]: List of similar items
        """
        if collection_name is None:
            collection_name = self.qdrant_collection_name
            
        try:
            # Generate embedding for query
            query_embedding = self.generate_embedding(text)
            if not query_embedding:
                logger.error("Failed to generate embedding for query")
                return self._get_mock_items()[:limit]
            
            # Ensure embedding is the right size
            if len(query_embedding) > 768:
                query_embedding = query_embedding[:768]
            elif len(query_embedding) < 768:
                query_embedding.extend([0.0] * (768 - len(query_embedding)))
            
            # Search in Qdrant
            search_results = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit
            )
            
            # Format results
            items = []
            for result in search_results:
                items.append({
                    'id': result.id,
                    'title': result.payload.get('title', ''),
                    'description': result.payload.get('description', ''),
                    'category': result.payload.get('category', ''),
                    'price': result.payload.get('price', 0),
                    'score': result.score,
                    'mongo_id': result.payload.get('mongo_id', '')
                })
            
            logger.info(f"Found {len(items)} similar items for query: {text}")
            return items
            
        except Exception as e:
            logger.error(f"Error searching related items: {str(e)}")
            return self._get_mock_items()[:limit]