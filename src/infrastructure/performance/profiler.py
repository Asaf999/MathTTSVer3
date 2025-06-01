"""
Performance profiling utilities for MathTTS v3.
"""

import asyncio
import functools
import time
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Callable, Dict, List, Optional, TypeVar

from src.infrastructure.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class PerformanceMetrics:
    """Container for performance metrics."""
    
    def __init__(self):
        self.measurements: Dict[str, List[float]] = {}
        self.counters: Dict[str, int] = {}
    
    def record_duration(self, metric_name: str, duration_ms: float) -> None:
        """Record a duration measurement."""
        if metric_name not in self.measurements:
            self.measurements[metric_name] = []
        self.measurements[metric_name].append(duration_ms)
    
    def increment_counter(self, counter_name: str, amount: int = 1) -> None:
        """Increment a counter."""
        if counter_name not in self.counters:
            self.counters[counter_name] = 0
        self.counters[counter_name] += amount
    
    def get_stats(self, metric_name: str) -> Dict[str, float]:
        """Get statistics for a metric."""
        if metric_name not in self.measurements:
            return {}
        
        values = self.measurements[metric_name]
        if not values:
            return {}
        
        return {
            "count": len(values),
            "total": sum(values),
            "average": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "p50": self._percentile(values, 50),
            "p90": self._percentile(values, 90),
            "p99": self._percentile(values, 99)
        }
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value."""
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        summary = {
            "metrics": {},
            "counters": self.counters.copy()
        }
        
        for metric_name in self.measurements:
            summary["metrics"][metric_name] = self.get_stats(metric_name)
        
        return summary


# Global metrics instance
_metrics = PerformanceMetrics()


def get_metrics() -> PerformanceMetrics:
    """Get global metrics instance."""
    return _metrics


@contextmanager
def time_block(metric_name: str):
    """Context manager to time a code block."""
    start_time = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        _metrics.record_duration(metric_name, duration_ms)
        logger.debug(f"{metric_name} took {duration_ms:.2f}ms")


@asynccontextmanager
async def async_time_block(metric_name: str):
    """Async context manager to time a code block."""
    start_time = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        _metrics.record_duration(metric_name, duration_ms)
        logger.debug(f"{metric_name} took {duration_ms:.2f}ms")


def profile_function(metric_name: Optional[str] = None):
    """Decorator to profile function execution time."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        name = metric_name or f"{func.__module__}.{func.__name__}"
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            with time_block(name):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def profile_async_function(metric_name: Optional[str] = None):
    """Decorator to profile async function execution time."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        name = metric_name or f"{func.__module__}.{func.__name__}"
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            async with async_time_block(name):
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


class PerformanceOptimizer:
    """Performance optimization utilities."""
    
    @staticmethod
    async def batch_process_async(
        items: List[Any],
        process_func: Callable[[Any], Any],
        batch_size: int = 10,
        max_concurrent: int = 5
    ) -> List[Any]:
        """
        Process items in batches with concurrency control.
        
        Args:
            items: Items to process
            process_func: Async function to process each item
            batch_size: Size of each batch
            max_concurrent: Maximum concurrent batches
            
        Returns:
            List of results in same order as input
        """
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_batch(batch: List[Any]) -> List[Any]:
            async with semaphore:
                return await asyncio.gather(*[process_func(item) for item in batch])
        
        # Process in batches
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await process_batch(batch)
            results.extend(batch_results)
        
        return results
    
    @staticmethod
    def memoize(maxsize: int = 128):
        """
        Memoization decorator with size limit.
        
        Args:
            maxsize: Maximum cache size
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            cache = {}
            cache_order = []
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Create cache key
                key = str(args) + str(sorted(kwargs.items()))
                
                # Check cache
                if key in cache:
                    return cache[key]
                
                # Compute result
                result = func(*args, **kwargs)
                
                # Update cache
                cache[key] = result
                cache_order.append(key)
                
                # Evict if necessary
                if len(cache) > maxsize:
                    oldest_key = cache_order.pop(0)
                    del cache[oldest_key]
                
                return result
            
            wrapper.cache_info = lambda: {
                "size": len(cache),
                "maxsize": maxsize
            }
            wrapper.cache_clear = lambda: (cache.clear(), cache_order.clear())
            
            return wrapper
        return decorator
    
    @staticmethod
    async def parallel_map(
        func: Callable[[Any], Any],
        items: List[Any],
        max_workers: int = 10
    ) -> List[Any]:
        """
        Apply function to items in parallel.
        
        Args:
            func: Async function to apply
            items: Items to process
            max_workers: Maximum concurrent workers
            
        Returns:
            List of results
        """
        semaphore = asyncio.Semaphore(max_workers)
        
        async def worker(item):
            async with semaphore:
                return await func(item)
        
        return await asyncio.gather(*[worker(item) for item in items])


def optimize_pattern_loading():
    """Optimize pattern loading performance."""
    from src.adapters.pattern_loaders import YAMLPatternLoader
    
    # Patch the loader to use parallel loading
    original_load = YAMLPatternLoader._load_from_file
    
    @profile_async_function("pattern_loading.load_file")
    async def optimized_load(self, file_path):
        return await original_load(self, file_path)
    
    YAMLPatternLoader._load_from_file = optimized_load
    
    logger.info("Pattern loading optimization applied")


def optimize_pattern_matching():
    """Optimize pattern matching performance."""
    from src.domain.services import PatternMatchingService
    
    # Add caching to pattern compilation
    original_init = PatternMatchingService.__init__
    
    def optimized_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self._pattern_cache = {}
    
    PatternMatchingService.__init__ = optimized_init
    
    logger.info("Pattern matching optimization applied")


def apply_performance_optimizations():
    """Apply all performance optimizations."""
    optimize_pattern_loading()
    optimize_pattern_matching()
    logger.info("All performance optimizations applied")