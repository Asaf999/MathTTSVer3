"""Performance optimization infrastructure."""

from .profiler import (
    PerformanceMetrics,
    PerformanceOptimizer,
    get_metrics,
    time_block,
    async_time_block,
    profile_function,
    profile_async_function,
    apply_performance_optimizations
)
from .optimized_pattern_service import OptimizedPatternMatchingService
from .optimized_pattern_loader import OptimizedYAMLPatternLoader

__all__ = [
    "PerformanceMetrics",
    "PerformanceOptimizer",
    "get_metrics",
    "time_block",
    "async_time_block",
    "profile_function",
    "profile_async_function",
    "apply_performance_optimizations",
    "OptimizedPatternMatchingService",
    "OptimizedYAMLPatternLoader"
]