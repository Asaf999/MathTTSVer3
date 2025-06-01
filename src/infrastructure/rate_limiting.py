"""Enhanced rate limiting with Redis support."""

import time
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
import json
import hashlib
from abc import ABC, abstractmethod

from fastapi import Request, HTTPException, status


class RateLimiter(ABC):
    """Abstract base class for rate limiters."""
    
    @abstractmethod
    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request is allowed.
        
        Returns:
            Tuple of (is_allowed, metadata) where metadata contains:
            - limit: The rate limit
            - remaining: Requests remaining
            - reset: Unix timestamp when limit resets
        """
        pass


class InMemoryRateLimiter(RateLimiter):
    """Simple in-memory rate limiter using sliding window."""
    
    def __init__(self):
        """Initialize rate limiter."""
        self._requests: Dict[str, list[float]] = {}
    
    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> Tuple[bool, Dict[str, int]]:
        """Check if request is allowed."""
        now = time.time()
        window_start = now - window_seconds
        
        # Get requests for this key
        if key not in self._requests:
            self._requests[key] = []
        
        # Remove old requests outside window
        self._requests[key] = [
            timestamp for timestamp in self._requests[key]
            if timestamp > window_start
        ]
        
        # Check if under limit
        current_count = len(self._requests[key])
        is_allowed = current_count < limit
        
        if is_allowed:
            self._requests[key].append(now)
            current_count += 1
        
        # Calculate reset time (end of current window)
        reset_time = int(now + window_seconds)
        
        metadata = {
            "limit": limit,
            "remaining": max(0, limit - current_count),
            "reset": reset_time
        }
        
        return is_allowed, metadata


class RedisRateLimiter(RateLimiter):
    """Redis-based rate limiter for distributed systems."""
    
    def __init__(self, redis_client):
        """Initialize with Redis client."""
        self.redis = redis_client
    
    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> Tuple[bool, Dict[str, int]]:
        """Check if request is allowed using Redis."""
        now = time.time()
        window_start = now - window_seconds
        
        # Use Redis sorted sets for sliding window
        redis_key = f"rate_limit:{key}"
        
        # Remove old entries
        await self.redis.zremrangebyscore(redis_key, 0, window_start)
        
        # Count current requests
        current_count = await self.redis.zcard(redis_key)
        
        is_allowed = current_count < limit
        
        if is_allowed:
            # Add current request
            await self.redis.zadd(redis_key, {str(now): now})
            current_count += 1
        
        # Set expiry on key
        await self.redis.expire(redis_key, window_seconds + 60)
        
        # Calculate reset time
        reset_time = int(now + window_seconds)
        
        metadata = {
            "limit": limit,
            "remaining": max(0, limit - current_count),
            "reset": reset_time
        }
        
        return is_allowed, metadata


class RateLimitManager:
    """Manage rate limiting for different scenarios."""
    
    def __init__(self, rate_limiter: Optional[RateLimiter] = None):
        """Initialize rate limit manager."""
        self.rate_limiter = rate_limiter or InMemoryRateLimiter()
    
    def _get_client_key(self, request: Request) -> str:
        """Get client identifier from request."""
        # Try to get real IP from proxy headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get first IP in chain
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        return f"ip:{client_ip}"
    
    def _get_user_key(self, user_id: str) -> str:
        """Get rate limit key for authenticated user."""
        return f"user:{user_id}"
    
    def _get_api_key_key(self, api_key_id: str) -> str:
        """Get rate limit key for API key."""
        return f"api_key:{api_key_id}"
    
    async def check_ip_limit(
        self, 
        request: Request,
        limit: int = 60,
        window_seconds: int = 60
    ) -> Dict[str, int]:
        """Check IP-based rate limit."""
        key = self._get_client_key(request)
        is_allowed, metadata = await self.rate_limiter.is_allowed(key, limit, window_seconds)
        
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "Retry-After": str(metadata["reset"] - int(time.time())),
                    "X-RateLimit-Limit": str(metadata["limit"]),
                    "X-RateLimit-Remaining": str(metadata["remaining"]),
                    "X-RateLimit-Reset": str(metadata["reset"])
                }
            )
        
        return metadata
    
    async def check_user_limit(
        self,
        user_id: str,
        limit: int = 1000,
        window_seconds: int = 3600
    ) -> Dict[str, int]:
        """Check user-based rate limit."""
        key = self._get_user_key(user_id)
        is_allowed, metadata = await self.rate_limiter.is_allowed(key, limit, window_seconds)
        
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="User rate limit exceeded",
                headers={
                    "Retry-After": str(metadata["reset"] - int(time.time())),
                    "X-RateLimit-Limit": str(metadata["limit"]),
                    "X-RateLimit-Remaining": str(metadata["remaining"]),
                    "X-RateLimit-Reset": str(metadata["reset"])
                }
            )
        
        return metadata
    
    async def check_api_key_limit(
        self,
        api_key_id: str,
        limit: Optional[int] = None,
        window_seconds: int = 3600
    ) -> Dict[str, int]:
        """Check API key rate limit."""
        if limit is None:
            # Default high limit for API keys
            limit = 10000
        
        key = self._get_api_key_key(api_key_id)
        is_allowed, metadata = await self.rate_limiter.is_allowed(key, limit, window_seconds)
        
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="API key rate limit exceeded",
                headers={
                    "Retry-After": str(metadata["reset"] - int(time.time())),
                    "X-RateLimit-Limit": str(metadata["limit"]),
                    "X-RateLimit-Remaining": str(metadata["remaining"]),
                    "X-RateLimit-Reset": str(metadata["reset"])
                }
            )
        
        return metadata


# Global rate limit manager instance
_rate_limit_manager: Optional[RateLimitManager] = None


def get_rate_limit_manager() -> RateLimitManager:
    """Get rate limit manager instance."""
    global _rate_limit_manager
    if _rate_limit_manager is None:
        # In production, would initialize with Redis
        _rate_limit_manager = RateLimitManager()
    return _rate_limit_manager