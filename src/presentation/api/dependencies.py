"""
Dependency injection for the FastAPI application.

This module contains dependency functions and application lifecycle events.
"""

from typing import AsyncGenerator, Optional
from functools import lru_cache

from fastapi import Depends, HTTPException, Header

from src.infrastructure.config import get_settings, Settings
from src.infrastructure.logging import get_logger
from src.infrastructure.persistence import MemoryPatternRepository
from src.infrastructure.cache import LRUCacheRepository
from src.adapters.pattern_loaders import YAMLPatternLoader
from src.adapters.tts_providers import EdgeTTSAdapter, TTSProviderAdapter
from src.application.use_cases import ProcessExpressionUseCase
from src.domain.services import PatternMatchingService


logger = get_logger(__name__)

# Global instances
_pattern_repository: Optional[MemoryPatternRepository] = None
_cache_repository: Optional[LRUCacheRepository] = None
_tts_provider: Optional[TTSProviderAdapter] = None
_pattern_matching_service: Optional[PatternMatchingService] = None
_process_expression_use_case: Optional[ProcessExpressionUseCase] = None


async def startup_event() -> None:
    """Initialize application resources on startup."""
    global _pattern_repository, _cache_repository, _tts_provider
    global _pattern_matching_service, _process_expression_use_case
    
    settings = get_settings()
    logger.info("Initializing application resources")
    
    try:
        # Initialize repositories
        _pattern_repository = MemoryPatternRepository()
        _cache_repository = LRUCacheRepository(max_size=settings.cache.max_size)
        
        # Load patterns
        pattern_loader = YAMLPatternLoader(settings.patterns.patterns_dir)
        patterns = await pattern_loader.load_patterns()
        
        for pattern in patterns:
            await _pattern_repository.add(pattern)
        
        logger.info(f"Loaded {len(patterns)} patterns")
        
        # Initialize TTS provider
        if settings.tts.default_provider == "edge-tts":
            _tts_provider = EdgeTTSAdapter()
        else:
            # Add other providers as they're implemented
            _tts_provider = EdgeTTSAdapter()
        
        await _tts_provider.initialize()
        
        # Initialize services
        _pattern_matching_service = PatternMatchingService(_pattern_repository)
        
        # Initialize use cases
        _process_expression_use_case = ProcessExpressionUseCase(
            pattern_matching_service=_pattern_matching_service,
            pattern_repository=_pattern_repository,
            cache_repository=_cache_repository
        )
        
        logger.info("Application resources initialized successfully")
        
    except Exception as e:
        logger.exception("Failed to initialize application resources")
        raise


async def shutdown_event() -> None:
    """Clean up application resources on shutdown."""
    logger.info("Cleaning up application resources")
    
    if _tts_provider:
        await _tts_provider.close()
    
    logger.info("Application resources cleaned up")


# Dependency functions

@lru_cache()
def get_cached_settings() -> Settings:
    """Get cached settings instance."""
    return get_settings()


async def get_pattern_repository() -> MemoryPatternRepository:
    """Get pattern repository instance."""
    if not _pattern_repository:
        raise HTTPException(
            status_code=503,
            detail="Pattern repository not initialized"
        )
    return _pattern_repository


async def get_cache_repository() -> LRUCacheRepository:
    """Get cache repository instance."""
    if not _cache_repository:
        raise HTTPException(
            status_code=503,
            detail="Cache repository not initialized"
        )
    return _cache_repository


async def get_tts_provider() -> TTSProviderAdapter:
    """Get TTS provider instance."""
    if not _tts_provider:
        raise HTTPException(
            status_code=503,
            detail="TTS provider not initialized"
        )
    return _tts_provider


async def get_pattern_matching_service() -> PatternMatchingService:
    """Get pattern matching service instance."""
    if not _pattern_matching_service:
        raise HTTPException(
            status_code=503,
            detail="Pattern matching service not initialized"
        )
    return _pattern_matching_service


async def get_process_expression_use_case() -> ProcessExpressionUseCase:
    """Get process expression use case instance."""
    if not _process_expression_use_case:
        raise HTTPException(
            status_code=503,
            detail="Process expression use case not initialized"
        )
    return _process_expression_use_case


async def verify_api_key(
    x_api_key: Optional[str] = Header(None),
    settings: Settings = Depends(get_cached_settings)
) -> Optional[str]:
    """
    Verify API key if authentication is enabled.
    
    This is an alternative to the middleware approach,
    useful for specific endpoints.
    """
    if not settings.api.api_key_enabled:
        return None
    
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    if x_api_key not in settings.api.api_keys:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    return x_api_key


class PaginationParams:
    """Common pagination parameters."""
    
    def __init__(
        self,
        offset: int = 0,
        limit: int = 20,
        max_limit: int = 100
    ):
        """
        Initialize pagination parameters.
        
        Args:
            offset: Number of items to skip
            limit: Number of items to return
            max_limit: Maximum allowed limit
        """
        if offset < 0:
            raise HTTPException(
                status_code=400,
                detail="Offset must be non-negative"
            )
        
        if limit < 1:
            raise HTTPException(
                status_code=400,
                detail="Limit must be positive"
            )
        
        if limit > max_limit:
            raise HTTPException(
                status_code=400,
                detail=f"Limit exceeds maximum of {max_limit}"
            )
        
        self.offset = offset
        self.limit = limit