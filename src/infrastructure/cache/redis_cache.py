"""
Redis cache implementation for MathTTS v3.
"""

import asyncio
import json
import pickle
from typing import Any, Dict, Optional
from datetime import timedelta

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from src.domain.interfaces import CacheRepository
from src.infrastructure.config.settings import Settings
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class RedisCacheRepository(CacheRepository):
    """
    Redis-based cache implementation.
    
    Features:
    - Async Redis client
    - JSON and pickle serialization
    - TTL support
    - Connection pooling
    - Graceful fallback on connection errors
    """
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db: Optional[int] = None,
        password: Optional[str] = None,
        ttl: Optional[int] = None,
        key_prefix: str = "mathtts:",
        connection_pool_size: int = 10
    ):
        """
        Initialize Redis cache repository.
        
        Args:
            host: Redis host (defaults to settings)
            port: Redis port (defaults to settings)
            db: Redis database number (defaults to settings)
            password: Redis password
            ttl: Default TTL in seconds
            key_prefix: Prefix for all keys
            connection_pool_size: Connection pool size
        """
        if not REDIS_AVAILABLE:
            raise ImportError("redis package is not installed. Install with: pip install redis[hiredis]")
        
        settings = Settings()
        
        self.host = host or settings.redis_host
        self.port = port or settings.redis_port
        self.db = db or settings.redis_db
        self.password = password or settings.redis_password
        self.ttl = ttl or settings.cache_ttl
        self.key_prefix = key_prefix
        
        # Create connection pool
        self.pool = redis.ConnectionPool(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            max_connections=connection_pool_size,
            decode_responses=False  # We'll handle encoding ourselves
        )
        
        self.client: Optional[redis.Redis] = None
        self._connected = False
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._errors = 0
    
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.client = redis.Redis(connection_pool=self.pool)
            await self.client.ping()
            self._connected = True
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._connected = False
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.client:
            await self.client.close()
            await self.pool.disconnect()
            self._connected = False
            logger.info("Disconnected from Redis")
    
    def _make_key(self, key: str) -> str:
        """Create full key with prefix."""
        return f"{self.key_prefix}{key}"
    
    async def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage."""
        try:
            # Try JSON first for better interoperability
            json_str = json.dumps(value, default=str)
            return json_str.encode('utf-8')
        except (TypeError, ValueError):
            # Fall back to pickle for complex objects
            return pickle.dumps(value)
    
    async def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage."""
        try:
            # Try JSON first
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            try:
                return pickle.loads(data)
            except Exception as e:
                logger.error(f"Failed to deserialize data: {e}")
                return None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._connected:
            return None
        
        full_key = self._make_key(key)
        
        try:
            data = await self.client.get(full_key)
            
            if data is None:
                self._misses += 1
                return None
            
            self._hits += 1
            return await self._deserialize(data)
            
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            self._errors += 1
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional TTL."""
        if not self._connected:
            return False
        
        full_key = self._make_key(key)
        ttl = ttl or self.ttl
        
        try:
            serialized = await self._serialize(value)
            
            if ttl:
                await self.client.setex(
                    full_key,
                    timedelta(seconds=ttl),
                    serialized
                )
            else:
                await self.client.set(full_key, serialized)
            
            return True
            
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            self._errors += 1
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self._connected:
            return False
        
        full_key = self._make_key(key)
        
        try:
            result = await self.client.delete(full_key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            self._errors += 1
            return False
    
    async def has(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._connected:
            return False
        
        full_key = self._make_key(key)
        
        try:
            return await self.client.exists(full_key) > 0
            
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            self._errors += 1
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries with our prefix."""
        if not self._connected:
            return
        
        try:
            # Find all keys with our prefix
            pattern = f"{self.key_prefix}*"
            cursor = 0
            
            while True:
                cursor, keys = await self.client.scan(
                    cursor,
                    match=pattern,
                    count=100
                )
                
                if keys:
                    await self.client.delete(*keys)
                
                if cursor == 0:
                    break
            
            logger.info(f"Cleared all keys with prefix {self.key_prefix}")
            
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            self._errors += 1
    
    async def get_many(self, keys: list[str]) -> Dict[str, Any]:
        """Get multiple values at once."""
        if not self._connected:
            return {}
        
        full_keys = [self._make_key(k) for k in keys]
        
        try:
            values = await self.client.mget(full_keys)
            
            result = {}
            for key, data in zip(keys, values):
                if data is not None:
                    self._hits += 1
                    result[key] = await self._deserialize(data)
                else:
                    self._misses += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Redis mget error: {e}")
            self._errors += 1
            return {}
    
    async def set_many(
        self, 
        items: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Set multiple values at once."""
        if not self._connected:
            return False
        
        ttl = ttl or self.ttl
        
        try:
            # Prepare pipeline
            pipe = self.client.pipeline()
            
            for key, value in items.items():
                full_key = self._make_key(key)
                serialized = await self._serialize(value)
                
                if ttl:
                    pipe.setex(full_key, timedelta(seconds=ttl), serialized)
                else:
                    pipe.set(full_key, serialized)
            
            # Execute pipeline
            await pipe.execute()
            return True
            
        except Exception as e:
            logger.error(f"Redis mset error: {e}")
            self._errors += 1
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0
        
        stats = {
            "connected": self._connected,
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "hits": self._hits,
            "misses": self._misses,
            "errors": self._errors,
            "hit_rate": hit_rate,
            "total_requests": total_requests
        }
        
        # Try to get Redis info
        if self._connected and self.client:
            try:
                # Get memory info asynchronously in a sync context
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're already in an async context
                    info_task = asyncio.create_task(self.client.info("memory"))
                else:
                    # Create new event loop for sync context
                    info = asyncio.run(self.client.info("memory"))
                    stats["redis_memory_used"] = info.get("used_memory_human", "unknown")
                    stats["redis_memory_peak"] = info.get("used_memory_peak_human", "unknown")
            except Exception:
                pass
        
        return stats
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on existing key."""
        if not self._connected:
            return False
        
        full_key = self._make_key(key)
        
        try:
            return await self.client.expire(full_key, ttl)
            
        except Exception as e:
            logger.error(f"Redis expire error for key {key}: {e}")
            self._errors += 1
            return False
    
    async def ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for key."""
        if not self._connected:
            return None
        
        full_key = self._make_key(key)
        
        try:
            ttl = await self.client.ttl(full_key)
            return ttl if ttl >= 0 else None
            
        except Exception as e:
            logger.error(f"Redis ttl error for key {key}: {e}")
            self._errors += 1
            return None


class RedisConnectionManager:
    """Manager for Redis connections with retry logic."""
    
    def __init__(self, cache: RedisCacheRepository, max_retries: int = 3):
        self.cache = cache
        self.max_retries = max_retries
    
    async def ensure_connected(self) -> bool:
        """Ensure Redis is connected with retry logic."""
        if self.cache._connected:
            return True
        
        for attempt in range(self.max_retries):
            try:
                await self.cache.connect()
                return True
            except Exception as e:
                logger.warning(f"Redis connection attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return False
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.ensure_connected()
        return self.cache
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Keep connection alive for reuse
        pass