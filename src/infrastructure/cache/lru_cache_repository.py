"""LRU cache repository implementation."""

from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    
    value: Any
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def access(self) -> None:
        """Record access to entry."""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()


class LRUCacheRepository:
    """LRU cache implementation."""
    
    def __init__(self, max_size: int = 1000, default_ttl: Optional[timedelta] = None) -> None:
        """Initialize LRU cache."""
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        async with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._cache[key]
            
            # Check expiration
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.access()
            self._hits += 1
            
            return entry.value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None
    ) -> None:
        """Set value in cache with optional TTL."""
        async with self._lock:
            # Calculate expiration
            expires_at = None
            if ttl or self.default_ttl:
                ttl = ttl or self.default_ttl
                expires_at = datetime.utcnow() + ttl
            
            # Create entry
            entry = CacheEntry(value=value, expires_at=expires_at)
            
            # If key exists, move to end
            if key in self._cache:
                self._cache.move_to_end(key)
            
            # Add entry
            self._cache[key] = entry
            
            # Evict if necessary
            while len(self._cache) > self.max_size:
                # Remove least recently used
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._evictions += 1
    
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        async with self._lock:
            if key not in self._cache:
                return False
            
            entry = self._cache[key]
            return not entry.is_expired()
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0
    
    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from cache."""
        results = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                results[key] = value
        return results
    
    async def set_many(
        self,
        items: dict[str, Any],
        ttl: Optional[timedelta] = None
    ) -> None:
        """Set multiple values in cache."""
        for key, value in items.items():
            await self.set(key, value, ttl)
    
    async def delete_many(self, keys: list[str]) -> None:
        """Delete multiple values from cache."""
        async with self._lock:
            for key in keys:
                if key in self._cache:
                    del self._cache[key]
    
    async def get_statistics(self) -> dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            # Calculate memory usage (approximate)
            import sys
            memory_bytes = sum(
                sys.getsizeof(k) + sys.getsizeof(v)
                for k, v in self._cache.items()
            )
            
            # Get age distribution
            now = datetime.utcnow()
            age_buckets = {"<1m": 0, "1m-1h": 0, "1h-1d": 0, ">1d": 0}
            
            for entry in self._cache.values():
                age = (now - entry.created_at).total_seconds()
                if age < 60:
                    age_buckets["<1m"] += 1
                elif age < 3600:
                    age_buckets["1m-1h"] += 1
                elif age < 86400:
                    age_buckets["1h-1d"] += 1
                else:
                    age_buckets[">1d"] += 1
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_rate": round(hit_rate, 2),
                "memory_bytes": memory_bytes,
                "memory_mb": round(memory_bytes / 1024 / 1024, 2),
                "age_distribution": age_buckets
            }
    
    async def cleanup_expired(self) -> int:
        """Remove expired entries."""
        async with self._lock:
            expired_keys = []
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)