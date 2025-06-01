"""Prometheus metrics for monitoring."""

from typing import Optional, Dict, Any, List
from enum import Enum
import time
from functools import wraps

from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    CollectorRegistry, generate_latest,
    CONTENT_TYPE_LATEST
)
from fastapi import Response


# Create custom registry to avoid conflicts
registry = CollectorRegistry()


# Application info
app_info = Info(
    'mathtts_app_info',
    'Application information',
    registry=registry
)


# Request metrics
http_requests_total = Counter(
    'mathtts_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'mathtts_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=registry
)

http_requests_in_progress = Gauge(
    'mathtts_http_requests_in_progress',
    'HTTP requests currently being processed',
    ['method', 'endpoint'],
    registry=registry
)


# Expression processing metrics
expressions_processed_total = Counter(
    'mathtts_expressions_processed_total',
    'Total expressions processed',
    ['cached', 'status'],
    registry=registry
)

expression_processing_duration_seconds = Histogram(
    'mathtts_expression_processing_duration_seconds',
    'Expression processing duration in seconds',
    ['cached'],
    registry=registry
)

pattern_matches_total = Counter(
    'mathtts_pattern_matches_total',
    'Total pattern matches',
    ['pattern_id', 'domain'],
    registry=registry
)


# TTS metrics
tts_synthesis_total = Counter(
    'mathtts_tts_synthesis_total',
    'Total TTS synthesis operations',
    ['provider', 'voice', 'status'],
    registry=registry
)

tts_synthesis_duration_seconds = Histogram(
    'mathtts_tts_synthesis_duration_seconds',
    'TTS synthesis duration in seconds',
    ['provider'],
    registry=registry
)

tts_audio_size_bytes = Histogram(
    'mathtts_tts_audio_size_bytes',
    'Generated audio size in bytes',
    ['provider', 'format'],
    registry=registry
)


# Cache metrics
cache_operations_total = Counter(
    'mathtts_cache_operations_total',
    'Total cache operations',
    ['operation', 'status'],
    registry=registry
)

cache_hit_ratio = Gauge(
    'mathtts_cache_hit_ratio',
    'Cache hit ratio',
    registry=registry
)

cache_size_bytes = Gauge(
    'mathtts_cache_size_bytes',
    'Current cache size in bytes',
    registry=registry
)

cache_items_total = Gauge(
    'mathtts_cache_items_total',
    'Total items in cache',
    registry=registry
)


# Authentication metrics
auth_attempts_total = Counter(
    'mathtts_auth_attempts_total',
    'Total authentication attempts',
    ['method', 'status'],
    registry=registry
)

active_sessions_total = Gauge(
    'mathtts_active_sessions_total',
    'Currently active user sessions',
    registry=registry
)


# Rate limiting metrics
rate_limit_exceeded_total = Counter(
    'mathtts_rate_limit_exceeded_total',
    'Total rate limit exceeded events',
    ['limit_type'],
    registry=registry
)


# Resource metrics
memory_usage_bytes = Gauge(
    'mathtts_memory_usage_bytes',
    'Memory usage in bytes',
    registry=registry
)

cpu_usage_percent = Gauge(
    'mathtts_cpu_usage_percent',
    'CPU usage percentage',
    registry=registry
)


# Pattern metrics
patterns_loaded_total = Gauge(
    'mathtts_patterns_loaded_total',
    'Total patterns loaded',
    ['domain'],
    registry=registry
)


# Error metrics
errors_total = Counter(
    'mathtts_errors_total',
    'Total errors',
    ['error_type', 'component'],
    registry=registry
)


class MetricsCollector:
    """Collect and expose metrics."""
    
    @staticmethod
    def set_app_info(version: str, environment: str):
        """Set application info."""
        app_info.info({
            'version': version,
            'environment': environment
        })
    
    @staticmethod
    def track_http_request(method: str, endpoint: str, status: int, duration: float):
        """Track HTTP request metrics."""
        http_requests_total.labels(method=method, endpoint=endpoint, status=str(status)).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    
    @staticmethod
    def track_expression_processing(cached: bool, success: bool, duration: float):
        """Track expression processing metrics."""
        status = "success" if success else "error"
        expressions_processed_total.labels(cached=str(cached), status=status).inc()
        expression_processing_duration_seconds.labels(cached=str(cached)).observe(duration)
    
    @staticmethod
    def track_pattern_match(pattern_id: str, domain: str):
        """Track pattern match."""
        pattern_matches_total.labels(pattern_id=pattern_id, domain=domain).inc()
    
    @staticmethod
    def track_tts_synthesis(provider: str, voice: str, success: bool, duration: float, audio_size: int, format: str):
        """Track TTS synthesis metrics."""
        status = "success" if success else "error"
        tts_synthesis_total.labels(provider=provider, voice=voice, status=status).inc()
        tts_synthesis_duration_seconds.labels(provider=provider).observe(duration)
        tts_audio_size_bytes.labels(provider=provider, format=format).observe(audio_size)
    
    @staticmethod
    def track_cache_operation(operation: str, hit: bool):
        """Track cache operation."""
        status = "hit" if hit else "miss"
        cache_operations_total.labels(operation=operation, status=status).inc()
    
    @staticmethod
    def update_cache_metrics(hit_ratio: float, size_bytes: int, item_count: int):
        """Update cache metrics."""
        cache_hit_ratio.set(hit_ratio)
        cache_size_bytes.set(size_bytes)
        cache_items_total.set(item_count)
    
    @staticmethod
    def track_auth_attempt(method: str, success: bool):
        """Track authentication attempt."""
        status = "success" if success else "failure"
        auth_attempts_total.labels(method=method, status=status).inc()
    
    @staticmethod
    def update_active_sessions(count: int):
        """Update active sessions count."""
        active_sessions_total.set(count)
    
    @staticmethod
    def track_rate_limit_exceeded(limit_type: str):
        """Track rate limit exceeded event."""
        rate_limit_exceeded_total.labels(limit_type=limit_type).inc()
    
    @staticmethod
    def update_resource_metrics(memory_bytes: int, cpu_percent: float):
        """Update resource usage metrics."""
        memory_usage_bytes.set(memory_bytes)
        cpu_usage_percent.set(cpu_percent)
    
    @staticmethod
    def update_patterns_loaded(domain_counts: Dict[str, int]):
        """Update patterns loaded count."""
        for domain, count in domain_counts.items():
            patterns_loaded_total.labels(domain=domain).set(count)
    
    @staticmethod
    def track_error(error_type: str, component: str):
        """Track error occurrence."""
        errors_total.labels(error_type=error_type, component=component).inc()


def track_request_metrics(endpoint: str):
    """Decorator to track request metrics."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            method = kwargs.get('request', args[0] if args else None).method
            
            # Track in-progress request
            http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
            
            start_time = time.time()
            try:
                response = await func(*args, **kwargs)
                status = getattr(response, 'status_code', 200)
                return response
            except Exception as e:
                status = 500
                raise
            finally:
                # Track completion
                duration = time.time() - start_time
                MetricsCollector.track_http_request(method, endpoint, status, duration)
                http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
        
        return wrapper
    return decorator


async def get_metrics() -> Response:
    """Get Prometheus metrics."""
    metrics_data = generate_latest(registry)
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST
    )


# Initialize metrics collector
metrics = MetricsCollector()