"""Cache repository interface."""

from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any, Optional


class CacheRepository(ABC):
    """Abstract cache repository interface."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(
        self, 
        key: str, 
        value: Any,
        ttl: Optional[timedelta] = None
    ) -> None:
        """Set value in cache with optional TTL."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from cache."""
        pass
    
    @abstractmethod
    async def set_many(
        self,
        items: dict[str, Any],
        ttl: Optional[timedelta] = None
    ) -> None:
        """Set multiple values in cache."""
        pass
    
    @abstractmethod
    async def delete_many(self, keys: list[str]) -> None:
        """Delete multiple values from cache."""
        pass
    
    @abstractmethod
    async def get_statistics(self) -> dict[str, Any]:
        """Get cache statistics."""
        pass