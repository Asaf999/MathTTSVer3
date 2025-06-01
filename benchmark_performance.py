#!/usr/bin/env python3
"""
Performance benchmark for MathTTS v3.

This script compares performance between standard and optimized implementations.
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.domain.entities import PatternEntity, MathematicalExpression
from src.domain.entities.pattern import PatternContext
from src.domain.value_objects import (
    LaTeXExpression,
    PatternPriority,
    MathematicalDomain,
    AudienceLevel
)
from src.domain.services import PatternMatchingService
from src.infrastructure.persistence.memory_pattern_repository import MemoryPatternRepository
from src.infrastructure.performance.optimized_pattern_service import OptimizedPatternMatchingService
from src.infrastructure.performance.profiler import get_metrics, apply_performance_optimizations
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


async def create_test_patterns(count: int = 100) -> List[PatternEntity]:
    """Create test patterns for benchmarking."""
    patterns = []
    
    # Common patterns
    common_patterns = [
        (r"\\frac\{([^}]+)\}\{([^}]+)\}", r"\1 over \2", "fraction"),
        (r"\\sqrt\{([^}]+)\}", r"square root of \1", "sqrt"),
        (r"\\sin", "sine", "trig"),
        (r"\\cos", "cosine", "trig"),
        (r"\\tan", "tangent", "trig"),
        (r"\\log", "log", "log"),
        (r"\\ln", "natural log", "log"),
        (r"\\alpha", "alpha", "greek"),
        (r"\\beta", "beta", "greek"),
        (r"\\gamma", "gamma", "greek"),
        (r"\\sum_\{([^}]+)\}\^\{([^}]+)\}", r"sum from \1 to \2", "sum"),
        (r"\\int_\{([^}]+)\}\^\{([^}]+)\}", r"integral from \1 to \2", "integral"),
        (r"\\lim_\{([^}]+)\}", r"limit as \1", "limit"),
        (r"\^2", " squared", "power"),
        (r"\^3", " cubed", "power"),
        (r"\^n", " to the n", "power"),
        (r"\\pm", " plus or minus ", "operator"),
        (r"\\times", " times ", "operator"),
        (r"\\div", " divided by ", "operator"),
        (r"\\infty", "infinity", "constant")
    ]
    
    # Generate patterns
    for i in range(count):
        pattern_template = common_patterns[i % len(common_patterns)]
        pattern = PatternEntity(
            id=f"pattern_{i}",
            name=f"Pattern {i}",
            pattern=pattern_template[0],
            output_template=pattern_template[1],
            priority=PatternPriority(500 + (i % 1000)),
            domain=MathematicalDomain("general"),
            contexts=[PatternContext.ANY],
            description=f"Test pattern for {pattern_template[2]}"
        )
        patterns.append(pattern)
    
    return patterns


async def create_test_expressions(count: int = 50) -> List[MathematicalExpression]:
    """Create test expressions for benchmarking."""
    expressions = []
    
    # Sample LaTeX expressions
    latex_samples = [
        r"\frac{1}{2} + \frac{3}{4}",
        r"\sqrt{x^2 + y^2}",
        r"\sin(\theta) + \cos(\theta)",
        r"\int_{0}^{\infty} e^{-x} dx",
        r"\sum_{n=1}^{\infty} \frac{1}{n^2}",
        r"\lim_{x \to 0} \frac{\sin x}{x}",
        r"\alpha + \beta + \gamma",
        r"f(x) = ax^2 + bx + c",
        r"\log_a(x) = \frac{\ln x}{\ln a}",
        r"e^{i\theta} = \cos\theta + i\sin\theta"
    ]
    
    for i in range(count):
        latex = latex_samples[i % len(latex_samples)]
        expr = MathematicalExpression(
            latex_expression=LaTeXExpression(latex),
            audience_level=AudienceLevel("undergraduate"),
            context="inline"
        )
        expressions.append(expr)
    
    return expressions


async def benchmark_standard_service(
    patterns: List[PatternEntity],
    expressions: List[MathematicalExpression]
) -> dict:
    """Benchmark standard pattern matching service."""
    print("\n--- Benchmarking Standard Service ---")
    
    # Create repository and service
    repo = MemoryPatternRepository()
    for pattern in patterns:
        await repo.add(pattern)
    
    service = PatternMatchingService(repo)
    
    # Warm up
    for expr in expressions[:5]:
        await service.process_expression(expr)
    
    # Benchmark
    start_time = time.perf_counter()
    results = []
    
    for expr in expressions:
        expr_start = time.perf_counter()
        result = await service.process_expression(expr)
        expr_time = (time.perf_counter() - expr_start) * 1000
        results.append(expr_time)
    
    total_time = time.perf_counter() - start_time
    
    return {
        "total_time": total_time,
        "average_time_ms": sum(results) / len(results),
        "min_time_ms": min(results),
        "max_time_ms": max(results),
        "expressions_per_second": len(expressions) / total_time
    }


async def benchmark_optimized_service(
    patterns: List[PatternEntity],
    expressions: List[MathematicalExpression]
) -> dict:
    """Benchmark optimized pattern matching service."""
    print("\n--- Benchmarking Optimized Service ---")
    
    # Create repository and service
    repo = MemoryPatternRepository()
    for pattern in patterns:
        await repo.add(pattern)
    
    service = OptimizedPatternMatchingService(repo)
    
    # Warm up
    for expr in expressions[:5]:
        await service.process_expression(expr)
    
    # Benchmark
    start_time = time.perf_counter()
    results = []
    
    for expr in expressions:
        expr_start = time.perf_counter()
        result = await service.process_expression(expr)
        expr_time = (time.perf_counter() - expr_start) * 1000
        results.append(expr_time)
    
    total_time = time.perf_counter() - start_time
    
    # Get optimization stats
    opt_stats = service.get_optimization_stats()
    
    return {
        "total_time": total_time,
        "average_time_ms": sum(results) / len(results),
        "min_time_ms": min(results),
        "max_time_ms": max(results),
        "expressions_per_second": len(expressions) / total_time,
        "optimization_stats": opt_stats
    }


async def run_benchmark():
    """Run performance benchmark."""
    print("=" * 70)
    print("MathTTS v3 Performance Benchmark")
    print("=" * 70)
    
    # Create test data
    print("\nCreating test data...")
    patterns = await create_test_patterns(100)
    expressions = await create_test_expressions(50)
    print(f"Created {len(patterns)} patterns and {len(expressions)} expressions")
    
    # Run benchmarks
    standard_results = await benchmark_standard_service(patterns, expressions)
    optimized_results = await benchmark_optimized_service(patterns, expressions)
    
    # Print results
    print("\n" + "=" * 70)
    print("BENCHMARK RESULTS")
    print("=" * 70)
    
    print("\nStandard Service:")
    print(f"  Total time: {standard_results['total_time']:.2f}s")
    print(f"  Average time per expression: {standard_results['average_time_ms']:.2f}ms")
    print(f"  Min/Max time: {standard_results['min_time_ms']:.2f}ms / {standard_results['max_time_ms']:.2f}ms")
    print(f"  Throughput: {standard_results['expressions_per_second']:.1f} expressions/second")
    
    print("\nOptimized Service:")
    print(f"  Total time: {optimized_results['total_time']:.2f}s")
    print(f"  Average time per expression: {optimized_results['average_time_ms']:.2f}ms")
    print(f"  Min/Max time: {optimized_results['min_time_ms']:.2f}ms / {optimized_results['max_time_ms']:.2f}ms")
    print(f"  Throughput: {optimized_results['expressions_per_second']:.1f} expressions/second")
    
    # Calculate improvement
    speedup = standard_results['total_time'] / optimized_results['total_time']
    print(f"\nSpeedup: {speedup:.2f}x")
    print(f"Performance improvement: {(speedup - 1) * 100:.1f}%")
    
    # Print optimization stats
    if "optimization_stats" in optimized_results:
        stats = optimized_results["optimization_stats"]
        print("\nOptimization Statistics:")
        print(f"  Cache size: {stats['cache_size']}")
        print(f"  Compiled patterns: {stats['compiled_patterns']}")
        print(f"  Overall pattern hit rate: {stats['overall_hit_rate']:.2%}")
    
    # Get profiler metrics
    metrics = get_metrics()
    summary = metrics.get_summary()
    
    print("\nProfiling Metrics:")
    for metric_name, metric_data in summary["metrics"].items():
        if metric_data:
            print(f"\n  {metric_name}:")
            print(f"    Count: {metric_data['count']}")
            print(f"    Average: {metric_data['average']:.2f}ms")
            print(f"    P90: {metric_data['p90']:.2f}ms")
            print(f"    P99: {metric_data['p99']:.2f}ms")


async def benchmark_cache_effectiveness():
    """Benchmark cache effectiveness."""
    print("\n" + "=" * 70)
    print("Cache Effectiveness Benchmark")
    print("=" * 70)
    
    # Create limited set of expressions
    expressions = await create_test_expressions(10)
    patterns = await create_test_patterns(50)
    
    # Setup service
    repo = MemoryPatternRepository()
    for pattern in patterns:
        await repo.add(pattern)
    
    service = OptimizedPatternMatchingService(repo)
    
    # Process each expression multiple times
    print("\nProcessing expressions multiple times...")
    
    for round_num in range(3):
        print(f"\nRound {round_num + 1}:")
        round_times = []
        
        for expr in expressions:
            start = time.perf_counter()
            await service.process_expression(expr)
            elapsed = (time.perf_counter() - start) * 1000
            round_times.append(elapsed)
        
        avg_time = sum(round_times) / len(round_times)
        print(f"  Average time: {avg_time:.2f}ms")
    
    # Print cache stats
    stats = service.get_optimization_stats()
    print(f"\nFinal cache size: {stats['cache_size']}")
    print(f"Cache hit rate: {stats['overall_hit_rate']:.2%}")


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    
    # Run benchmarks
    asyncio.run(run_benchmark())
    asyncio.run(benchmark_cache_effectiveness())