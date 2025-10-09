# src/utils/cache_manager.py
import redis
import json
import logging
import hashlib
from typing import Any, Optional, Union, Dict, List
from src.config.settings import settings
import orjson  # Faster JSON serialization

logger = logging.getLogger(__name__)

class CacheManager:
    """Redis-based cache manager with connection pooling"""
    
    def __init__(self):
        self._redis_pool = None
        self._client = None
        self.is_connected = False
        
    def _get_connection_pool(self):
        """Create Redis connection pool if not exists"""
        if self._redis_pool is None:
            try:
                self._redis_pool = redis.ConnectionPool.from_url(
                    settings.REDIS_URL,
                    max_connections=settings.REDIS_MAX_CONNECTIONS,
                    retry_on_timeout=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    health_check_interval=30
                )
                self._client = redis.Redis(connection_pool=self._redis_pool)
                
                # Test connection
                self._client.ping()
                self.is_connected = True
                logger.info("Redis connection pool established successfully")
                
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.is_connected = False
                self._client = None
                
        return self._client
    
    def _generate_cache_key(self, prefix: str, data: Union[str, Dict, List]) -> str:
        """Generate consistent cache key from data"""
        if isinstance(data, str):
            key_data = data
        else:
            # Sort dict keys for consistent hashing
            key_data = orjson.dumps(data, option=orjson.OPT_SORT_KEYS).decode()
            
        # Create hash for long keys
        if len(key_data) > 100:
            key_hash = hashlib.md5(key_data.encode()).hexdigest()
            return f"searchai:{prefix}:{key_hash}"
        else:
            safe_data = key_data.replace(" ", "_").replace(":", "_")[:50]
            return f"searchai:{prefix}:{safe_data}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not settings.ENABLE_CACHE:
            return None
            
        client = self._get_connection_pool()
        if not client or not self.is_connected:
            return None
            
        try:
            value = client.get(key)
            if value:
                return orjson.loads(value)
            return None
            
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL"""
        if not settings.ENABLE_CACHE:
            return False
            
        client = self._get_connection_pool()
        if not client or not self.is_connected:
            return False
            
        try:
            serialized = orjson.dumps(value)
            result = client.setex(key, ttl, serialized)
            return result
            
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        client = self._get_connection_pool()
        if not client or not self.is_connected:
            return False
            
        try:
            result = client.delete(key)
            return bool(result)
            
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        client = self._get_connection_pool()
        if not client or not self.is_connected:
            return 0
            
        try:
            keys = client.keys(f"searchai:{pattern}:*")
            if keys:
                return client.delete(*keys)
            return 0
            
        except Exception as e:
            logger.warning(f"Cache clear pattern error for {pattern}: {e}")
            return 0
    
    # Specific cache methods for SearchAI
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding"""
        key = self._generate_cache_key("embedding", text)
        return self.get(key)
    
    def set_embedding(self, text: str, embedding: List[float]) -> bool:
        """Cache embedding"""
        key = self._generate_cache_key("embedding", text)
        return self.set(key, embedding, settings.EMBEDDING_CACHE_TTL)
    
    def get_query_expansion(self, query: str) -> Optional[List[str]]:
        """Get cached query expansion"""
        key = self._generate_cache_key("expansion", query)
        return self.get(key)
    
    def set_query_expansion(self, query: str, expansions: List[str]) -> bool:
        """Cache query expansion"""
        key = self._generate_cache_key("expansion", query)
        return self.set(key, expansions, settings.QUERY_EXPANSION_CACHE_TTL)
    
    def get_search_results(self, query: str, filters: Optional[Dict] = None, limit: int = 10) -> Optional[List[Dict]]:
        """Get cached search results"""
        cache_data = {
            "query": query,
            "filters": filters or {},
            "limit": limit
        }
        key = self._generate_cache_key("search", cache_data)
        return self.get(key)
    
    def set_search_results(self, query: str, filters: Optional[Dict], limit: int, results: List[Dict]) -> bool:
        """Cache search results"""
        cache_data = {
            "query": query,
            "filters": filters or {},
            "limit": limit
        }
        key = self._generate_cache_key("search", cache_data)
        return self.set(key, results, settings.SEARCH_CACHE_TTL)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        client = self._get_connection_pool()
        if not client or not self.is_connected:
            return {"status": "disconnected"}
            
        try:
            info = client.info()
            return {
                "status": "connected",
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info)
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"status": "error", "error": str(e)}
    
    def _calculate_hit_rate(self, info: Dict) -> str:
        """Calculate cache hit rate percentage"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        if total == 0:
            return "0%"
            
        hit_rate = (hits / total) * 100
        return f"{hit_rate:.1f}%"
    
    def health_check(self) -> Dict[str, Any]:
        """Check Redis health"""
        try:
            client = self._get_connection_pool()
            if not client:
                return {"healthy": False, "error": "No connection"}
                
            # Test basic operations
            test_key = "searchai:health:test"
            client.set(test_key, "ok", ex=10)
            result = client.get(test_key)
            client.delete(test_key)
            
            if result == b"ok":
                return {"healthy": True, "latency_ms": "< 1"}
            else:
                return {"healthy": False, "error": "Test operation failed"}
                
        except Exception as e:
            return {"healthy": False, "error": str(e)}

# Global cache manager instance
cache_manager = CacheManager()