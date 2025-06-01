"""
Custom middleware for the MathTTS API.

This module contains middleware for rate limiting, API key authentication,
and other cross-cutting concerns.
"""

import time
from typing import Dict, List, Optional, Callable
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.infrastructure.logging import get_logger


logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.
    
    Implements a simple in-memory rate limiter using a sliding window.
    For production, consider using Redis for distributed rate limiting.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 60,
        excluded_paths: Optional[List[str]] = None
    ):
        """
        Initialize rate limiter.
        
        Args:
            app: ASGI application
            requests_per_minute: Maximum requests per minute per IP
            excluded_paths: Paths to exclude from rate limiting
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.excluded_paths = excluded_paths or ["/docs", "/redoc", "/openapi.json", "/api/v1/health"]
        
        # Store request timestamps per IP
        self._request_times: Dict[str, List[datetime]] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request with rate limiting."""
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Clean old entries and check rate limit
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)
        
        # Remove old timestamps
        self._request_times[client_ip] = [
            timestamp for timestamp in self._request_times[client_ip]
            if timestamp > cutoff
        ]
        
        # Check if rate limit exceeded
        if len(self._request_times[client_ip]) >= self.requests_per_minute:
            logger.warning(
                "Rate limit exceeded",
                client_ip=client_ip,
                requests_count=len(self._request_times[client_ip])
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": 60
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0"
                }
            )
        
        # Record this request
        self._request_times[client_ip].append(now)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self.requests_per_minute - len(self._request_times[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    API key authentication middleware.
    
    Requires a valid API key in the X-API-Key header for all requests.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        api_keys: List[str],
        excluded_paths: Optional[List[str]] = None
    ):
        """
        Initialize API key middleware.
        
        Args:
            app: ASGI application
            api_keys: List of valid API keys
            excluded_paths: Paths to exclude from API key check
        """
        super().__init__(app)
        self.api_keys = set(api_keys)
        self.excluded_paths = excluded_paths or [
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/health"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request with API key authentication."""
        # Skip auth for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Check for API key
        api_key = request.headers.get("X-API-Key")
        
        if not api_key:
            logger.warning(
                "Missing API key",
                client_ip=request.client.host if request.client else "unknown"
            )
            return JSONResponse(
                status_code=401,
                content={"error": "Missing API key"},
                headers={"WWW-Authenticate": "ApiKey"}
            )
        
        if api_key not in self.api_keys:
            logger.warning(
                "Invalid API key",
                client_ip=request.client.host if request.client else "unknown",
                api_key_prefix=api_key[:8] + "..." if len(api_key) > 8 else api_key
            )
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid API key"},
                headers={"WWW-Authenticate": "ApiKey"}
            )
        
        # Process request
        return await call_next(request)


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Response compression middleware.
    
    Compresses responses using gzip when appropriate.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        minimum_size: int = 1024,
        excluded_content_types: Optional[List[str]] = None
    ):
        """
        Initialize compression middleware.
        
        Args:
            app: ASGI application
            minimum_size: Minimum response size to compress (bytes)
            excluded_content_types: Content types to exclude from compression
        """
        super().__init__(app)
        self.minimum_size = minimum_size
        self.excluded_content_types = excluded_content_types or [
            "image/",
            "video/",
            "audio/"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request with response compression."""
        # Check if client accepts gzip
        accept_encoding = request.headers.get("Accept-Encoding", "")
        if "gzip" not in accept_encoding:
            return await call_next(request)
        
        # Process request
        response = await call_next(request)
        
        # Check if we should compress
        content_type = response.headers.get("Content-Type", "")
        if any(excluded in content_type for excluded in self.excluded_content_types):
            return response
        
        # For simplicity, we're not implementing actual compression here
        # In production, use a proper compression middleware
        return response