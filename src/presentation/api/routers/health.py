"""
Health check and monitoring API endpoints.

This module provides health checks, metrics, and status information
for monitoring and observability.
"""

import time
import psutil
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, Response

from src.infrastructure.config import get_settings, Settings
from src.infrastructure.logging import get_logger
from src.infrastructure.cache import LRUCacheRepository
from src.adapters.tts_providers import TTSProviderAdapter
from src.infrastructure.monitoring import get_metrics as get_prometheus_metrics, metrics
from ..dependencies import get_cache_repository, get_tts_provider
from ..schemas import HealthResponse, MetricsResponse


router = APIRouter()
logger = get_logger(__name__)

# Track application start time
_start_time = time.time()
_expressions_processed = 0
_expressions_cached = 0
_total_processing_time = 0.0


@router.get(
    "/",
    response_model=HealthResponse,
    summary="Health check",
    description="Get overall application health status"
)
async def health_check(
    settings: Settings = Depends(get_settings),
    cache_repo: LRUCacheRepository = Depends(get_cache_repository),
    tts_provider: TTSProviderAdapter = Depends(get_tts_provider)
) -> HealthResponse:
    """
    Perform health check on all system components.
    
    Returns the overall health status and component-specific status.
    """
    try:
        # Check component health
        database_status = "healthy"  # Would check actual database in production
        
        # Check cache
        try:
            cache_stats = cache_repo.get_stats()
            cache_status = "healthy"
        except Exception as e:
            logger.warning("Cache health check failed", error=str(e))
            cache_status = "degraded"
        
        # Check TTS provider
        try:
            if tts_provider.is_available():
                tts_status = "healthy"
            else:
                tts_status = "unavailable"
        except Exception as e:
            logger.warning("TTS provider health check failed", error=str(e))
            tts_status = "unhealthy"
        
        # Overall status
        if all(status == "healthy" for status in [database_status, cache_status, tts_status]):
            overall_status = "healthy"
        elif any(status == "unhealthy" for status in [database_status, cache_status, tts_status]):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"
        
        # Calculate uptime
        uptime = time.time() - _start_time
        
        # Memory usage
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
        except:
            memory_mb = None
        
        # Cache hit rate
        try:
            cache_hit_rate = (
                cache_stats.hits / (cache_stats.hits + cache_stats.misses) * 100
                if (cache_stats.hits + cache_stats.misses) > 0 else 0.0
            )
        except:
            cache_hit_rate = None
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat() + "Z",
            version=settings.app_version,
            environment=settings.environment.value,
            database=database_status,
            cache=cache_status,
            tts_provider=tts_status,
            uptime_seconds=uptime,
            memory_usage_mb=memory_mb,
            cache_hit_rate=cache_hit_rate
        )
        
    except Exception as e:
        logger.exception("Health check failed")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow().isoformat() + "Z",
            version=settings.app_version,
            environment=settings.environment.value,
            database="unknown",
            cache="unknown",
            tts_provider="unknown",
            uptime_seconds=time.time() - _start_time
        )


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="Application metrics",
    description="Get detailed application performance metrics"
)
async def get_metrics(
    cache_repo: LRUCacheRepository = Depends(get_cache_repository),
    tts_provider: TTSProviderAdapter = Depends(get_tts_provider)
) -> MetricsResponse:
    """
    Get detailed application metrics for monitoring.
    
    Includes processing statistics, performance metrics, and resource usage.
    """
    try:
        # Cache statistics
        cache_stats = cache_repo.get_stats()
        cache_hit_rate = (
            cache_stats.hits / (cache_stats.hits + cache_stats.misses) * 100
            if (cache_stats.hits + cache_stats.misses) > 0 else 0.0
        )
        
        # Processing statistics
        avg_processing_time = (
            _total_processing_time / _expressions_processed
            if _expressions_processed > 0 else 0.0
        )
        
        # Memory usage
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
        except:
            memory_mb = 0.0
        
        # Count available voices
        try:
            voices = await tts_provider.list_voices()
            voices_count = len(voices)
        except:
            voices_count = 0
        
        return MetricsResponse(
            expressions_processed_total=_expressions_processed,
            expressions_processed_cached=_expressions_cached,
            average_processing_time_ms=avg_processing_time,
            patterns_loaded=0,  # Would get from pattern repository
            voices_available=voices_count,
            cache_hit_rate=cache_hit_rate,
            memory_usage_mb=memory_mb,
            uptime_seconds=time.time() - _start_time
        )
        
    except Exception as e:
        logger.exception("Failed to get metrics")
        # Return minimal metrics on error
        return MetricsResponse(
            expressions_processed_total=_expressions_processed,
            expressions_processed_cached=_expressions_cached,
            average_processing_time_ms=0.0,
            patterns_loaded=0,
            voices_available=0,
            cache_hit_rate=0.0,
            memory_usage_mb=0.0,
            uptime_seconds=time.time() - _start_time
        )


@router.get(
    "/ready",
    summary="Readiness check",
    description="Check if application is ready to serve requests"
)
async def readiness_check(
    tts_provider: TTSProviderAdapter = Depends(get_tts_provider)
) -> Dict[str, Any]:
    """
    Readiness check for Kubernetes/container orchestration.
    
    Returns whether the application is ready to serve requests.
    """
    try:
        # Check if TTS provider is available
        if not tts_provider.is_available():
            return {"ready": False, "reason": "TTS provider not available"}
        
        return {"ready": True}
        
    except Exception as e:
        logger.warning("Readiness check failed", error=str(e))
        return {"ready": False, "reason": str(e)}


@router.get(
    "/live",
    summary="Liveness check",
    description="Check if application is alive"
)
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check for Kubernetes/container orchestration.
    
    Returns whether the application process is alive and responsive.
    """
    return {"alive": True, "timestamp": datetime.utcnow().isoformat() + "Z"}


@router.get(
    "/prometheus",
    summary="Prometheus metrics",
    description="Export metrics in Prometheus format",
    response_class=Response
)
async def prometheus_metrics(
    settings: Settings = Depends(get_settings)
) -> Response:
    """
    Export metrics in Prometheus format.
    
    These metrics can be scraped by Prometheus for monitoring.
    """
    # Update app info
    metrics.set_app_info(settings.app_version, settings.environment.value)
    
    # Get Prometheus formatted metrics
    return await get_prometheus_metrics()


# Helper functions to update metrics (called from other modules)

def increment_expressions_processed(processing_time_ms: float, cached: bool = False) -> None:
    """Increment expression processing metrics."""
    global _expressions_processed, _expressions_cached, _total_processing_time
    
    _expressions_processed += 1
    _total_processing_time += processing_time_ms
    
    if cached:
        _expressions_cached += 1


def reset_metrics() -> None:
    """Reset all metrics (for testing)."""
    global _expressions_processed, _expressions_cached, _total_processing_time
    
    _expressions_processed = 0
    _expressions_cached = 0
    _total_processing_time = 0.0
    
    # Update Prometheus metrics
    metrics.update_resource_metrics(int(memory_mb * 1024 * 1024), 0.0)
    metrics.update_cache_metrics(cache_hit_rate / 100, 0, cache_stats.count if cache_stats else 0)