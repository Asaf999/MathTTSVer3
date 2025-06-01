"""Rate limiting dependencies for FastAPI."""

from typing import Optional, Dict
from fastapi import Depends, Request, Response

from .rate_limiting import get_rate_limit_manager, RateLimitManager
from .auth.dependencies import get_current_token, get_api_key
from .auth.models import TokenData, APIKey


async def rate_limit_by_ip(
    request: Request,
    response: Response,
    rate_limiter: RateLimitManager = Depends(get_rate_limit_manager),
    limit: int = 60,
    window: int = 60
) -> Dict[str, int]:
    """
    Apply IP-based rate limiting.
    
    Args:
        limit: Requests per window
        window: Window size in seconds
    """
    metadata = await rate_limiter.check_ip_limit(request, limit, window)
    
    # Add headers to response
    response.headers["X-RateLimit-Limit"] = str(metadata["limit"])
    response.headers["X-RateLimit-Remaining"] = str(metadata["remaining"])
    response.headers["X-RateLimit-Reset"] = str(metadata["reset"])
    
    return metadata


async def rate_limit_by_user(
    response: Response,
    token_data: TokenData = Depends(get_current_token),
    rate_limiter: RateLimitManager = Depends(get_rate_limit_manager),
    limit: int = 1000,
    window: int = 3600
) -> Dict[str, int]:
    """
    Apply user-based rate limiting.
    
    Args:
        limit: Requests per window
        window: Window size in seconds
    """
    metadata = await rate_limiter.check_user_limit(token_data.sub, limit, window)
    
    # Add headers to response
    response.headers["X-RateLimit-Limit"] = str(metadata["limit"])
    response.headers["X-RateLimit-Remaining"] = str(metadata["remaining"])
    response.headers["X-RateLimit-Reset"] = str(metadata["reset"])
    
    return metadata


async def rate_limit_by_api_key(
    response: Response,
    api_key: APIKey = Depends(get_api_key),
    rate_limiter: RateLimitManager = Depends(get_rate_limit_manager),
    window: int = 3600
) -> Dict[str, int]:
    """
    Apply API key-based rate limiting.
    
    Uses the rate limit configured for the specific API key.
    """
    metadata = await rate_limiter.check_api_key_limit(
        api_key.id,
        api_key.rate_limit,
        window
    )
    
    # Add headers to response
    response.headers["X-RateLimit-Limit"] = str(metadata["limit"])
    response.headers["X-RateLimit-Remaining"] = str(metadata["remaining"])
    response.headers["X-RateLimit-Reset"] = str(metadata["reset"])
    
    return metadata


class RateLimitDepends:
    """
    Configurable rate limit dependency.
    
    Usage:
        @router.get("/endpoint", dependencies=[Depends(RateLimitDepends(limit=10, window=60))])
    """
    
    def __init__(self, limit: int = 60, window: int = 60, by: str = "ip"):
        """
        Initialize rate limit dependency.
        
        Args:
            limit: Number of requests allowed
            window: Time window in seconds
            by: Rate limit by "ip", "user", or "api_key"
        """
        self.limit = limit
        self.window = window
        self.by = by
    
    async def __call__(
        self,
        request: Request,
        response: Response,
        rate_limiter: RateLimitManager = Depends(get_rate_limit_manager),
        token_data: Optional[TokenData] = None,
        api_key: Optional[APIKey] = None
    ) -> Dict[str, int]:
        """Apply rate limiting based on configuration."""
        if self.by == "user" and token_data:
            token_data = token_data or Depends(get_current_token)
            metadata = await rate_limiter.check_user_limit(
                token_data.sub,
                self.limit,
                self.window
            )
        elif self.by == "api_key" and api_key:
            api_key = api_key or Depends(get_api_key)
            metadata = await rate_limiter.check_api_key_limit(
                api_key.id,
                self.limit or api_key.rate_limit,
                self.window
            )
        else:
            # Default to IP-based
            metadata = await rate_limiter.check_ip_limit(
                request,
                self.limit,
                self.window
            )
        
        # Add headers
        response.headers["X-RateLimit-Limit"] = str(metadata["limit"])
        response.headers["X-RateLimit-Remaining"] = str(metadata["remaining"])
        response.headers["X-RateLimit-Reset"] = str(metadata["reset"])
        
        return metadata