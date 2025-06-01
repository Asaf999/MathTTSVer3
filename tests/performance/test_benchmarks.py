"""
Performance benchmarks for MathTTS Ver3.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
import time
import asyncio
from statistics import mean, stdev
from pathlib import Path

from src.adapters.pattern_loaders import YAMLPatternLoader
from src.infrastructure.persistence import MemoryPatternRepository
from src.domain.services import PatternMatcher
from src.domain.value_objects import LaTeXExpression, TTSOptions
from src.adapters.tts_providers import MockTTSAdapter
from src.infrastructure.cache import AudioCache


@pytest.mark.slow
class TestPerformanceBenchmarks:
    """Performance benchmark tests."""
    
    @pytest.fixture
    def real_patterns(self):
        """Load real patterns for benchmarking."""
        patterns_dir = Path(__file__).parent.parent.parent / "patterns"
        if not patterns_dir.exists():
            pytest.skip("Patterns directory not found")
        
        loader = YAMLPatternLoader(patterns_dir)
        return loader.load_all_patterns()
    
    @pytest.fixture
    def loaded_repository(self, real_patterns):
        """Create repository with real patterns."""
        repo = MemoryPatternRepository()
        for pattern in real_patterns:
            repo.add(pattern)
        return repo
    
    def benchmark_function(self, func, iterations=100):
        """
        Run a function multiple times and collect timing statistics.
        
        Args:
            func: Function to benchmark
            iterations: Number of iterations
            
        Returns:
            Dict with timing statistics
        """
        times = []
        
        for _ in range(iterations):
            start = time.perf_counter()
            func()
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to milliseconds
        
        return {
            "min": min(times),
            "max": max(times),
            "mean": mean(times),
            "stdev": stdev(times) if len(times) > 1 else 0,
            "iterations": iterations
        }
    
    async def async_benchmark_function(self, func, iterations=100):
        """Benchmark async function."""
        times = []
        
        for _ in range(iterations):
            start = time.perf_counter()
            await func()
            end = time.perf_counter()
            times.append((end - start) * 1000)
        
        return {
            "min": min(times),
            "max": max(times),
            "mean": mean(times),
            "stdev": stdev(times) if len(times) > 1 else 0,
            "iterations": iterations
        }
    
    def test_pattern_loading_performance(self):
        """Benchmark pattern loading from YAML."""
        patterns_dir = Path(__file__).parent.parent.parent / "patterns"
        if not patterns_dir.exists():
            pytest.skip("Patterns directory not found")
        
        loader = YAMLPatternLoader(patterns_dir)
        
        stats = self.benchmark_function(
            lambda: loader.load_all_patterns(),
            iterations=10
        )
        
        print(f"\nPattern Loading Performance:")
        print(f"  Mean: {stats['mean']:.2f}ms")
        print(f"  Min: {stats['min']:.2f}ms")
        print(f"  Max: {stats['max']:.2f}ms")
        print(f"  Stdev: {stats['stdev']:.2f}ms")
        
        # Loading should be reasonably fast
        assert stats['mean'] < 1000  # Less than 1 second on average
    
    def test_pattern_matching_performance(self, loaded_repository):
        """Benchmark pattern matching speed."""
        matcher = PatternMatcher(loaded_repository)
        
        # Test expressions of varying complexity
        test_expressions = [
            r"\frac{1}{2}",  # Simple
            r"x^2 + y^2 = z^2",  # Medium
            r"\int_0^1 \frac{x^2}{1+x^3} dx",  # Complex
            r"\sum_{n=1}^{\infty} \frac{1}{n^2} = \frac{\pi^2}{6}",  # Very complex
        ]
        
        for expr_str in test_expressions:
            expr = LaTeXExpression(expr_str)
            
            stats = self.benchmark_function(
                lambda: matcher.process_expression(expr),
                iterations=1000
            )
            
            print(f"\nPattern Matching for '{expr_str[:30]}...':")
            print(f"  Mean: {stats['mean']:.3f}ms")
            print(f"  Min: {stats['min']:.3f}ms")
            print(f"  Max: {stats['max']:.3f}ms")
            
            # Should be very fast
            assert stats['mean'] < 10  # Less than 10ms on average
    
    def test_repository_lookup_performance(self, loaded_repository):
        """Benchmark repository lookup operations."""
        # Test get_all performance
        stats = self.benchmark_function(
            lambda: loaded_repository.get_all(),
            iterations=1000
        )
        
        print(f"\nRepository get_all() Performance:")
        print(f"  Mean: {stats['mean']:.3f}ms")
        print(f"  Patterns: {len(loaded_repository.get_all())}")
        
        assert stats['mean'] < 1  # Should be sub-millisecond
        
        # Test get_by_domain performance
        stats = self.benchmark_function(
            lambda: loaded_repository.get_by_domain("calculus"),
            iterations=1000
        )
        
        print(f"\nRepository get_by_domain() Performance:")
        print(f"  Mean: {stats['mean']:.3f}ms")
        
        assert stats['mean'] < 1
    
    @pytest.mark.asyncio
    async def test_tts_synthesis_performance(self):
        """Benchmark TTS synthesis speed."""
        adapter = MockTTSAdapter()
        await adapter.initialize()
        
        test_texts = [
            "one half",  # Short
            "x squared plus y squared equals z squared",  # Medium
            "The integral from zero to one of x squared over one plus x cubed d x"  # Long
        ]
        
        options = TTSOptions()
        
        for text in test_texts:
            stats = await self.async_benchmark_function(
                lambda: adapter.synthesize(text, options),
                iterations=100
            )
            
            print(f"\nTTS Synthesis for '{text[:30]}...':")
            print(f"  Mean: {stats['mean']:.2f}ms")
            print(f"  Min: {stats['min']:.2f}ms")
            print(f"  Max: {stats['max']:.2f}ms")
            
            # Mock should be very fast
            assert stats['mean'] < 10
        
        await adapter.close()
    
    @pytest.mark.asyncio
    async def test_cache_performance(self, tmp_path):
        """Benchmark audio cache operations."""
        cache = AudioCache(cache_dir=tmp_path / "cache", max_size_mb=10)
        
        # Create test audio data
        from src.domain.value_objects import AudioData, AudioFormat
        audio = AudioData(
            data=b"x" * 10000,  # 10KB
            format=AudioFormat.MP3,
            sample_rate=44100,
            duration_seconds=1.0
        )
        
        # Test cache write performance
        keys = [f"key_{i}" for i in range(100)]
        
        write_stats = await self.async_benchmark_function(
            lambda: cache.put(keys[0], audio),
            iterations=100
        )
        
        print(f"\nCache Write Performance:")
        print(f"  Mean: {write_stats['mean']:.2f}ms")
        
        # Populate cache
        for key in keys:
            await cache.put(key, audio)
        
        # Test cache read performance (hits)
        read_stats = await self.async_benchmark_function(
            lambda: cache.get(keys[50]),
            iterations=1000
        )
        
        print(f"\nCache Read Performance (hits):")
        print(f"  Mean: {read_stats['mean']:.3f}ms")
        
        # Cache operations should be fast
        assert write_stats['mean'] < 50  # Writing includes file I/O
        assert read_stats['mean'] < 5   # Reading should be very fast
    
    def test_pattern_priority_impact(self, loaded_repository):
        """Test impact of pattern priority on matching performance."""
        matcher = PatternMatcher(loaded_repository)
        
        # Create expression that could match many patterns
        complex_expr = LaTeXExpression(
            r"\int_0^{\infty} \frac{\sin(x)}{x} dx = \frac{\pi}{2}"
        )
        
        # Benchmark with different repository sizes
        pattern_counts = [100, 200, 500, len(loaded_repository.get_all())]
        
        for count in pattern_counts:
            # Create subset repository
            subset_repo = MemoryPatternRepository()
            for i, pattern in enumerate(loaded_repository.get_all()):
                if i >= count:
                    break
                subset_repo.add(pattern)
            
            subset_matcher = PatternMatcher(subset_repo)
            
            stats = self.benchmark_function(
                lambda: subset_matcher.process_expression(complex_expr),
                iterations=100
            )
            
            print(f"\nMatching with {count} patterns:")
            print(f"  Mean: {stats['mean']:.3f}ms")
            
            # Performance should scale reasonably
            assert stats['mean'] < 20  # Even with many patterns
    
    def test_concurrent_pattern_matching(self, loaded_repository):
        """Test concurrent pattern matching performance."""
        matcher = PatternMatcher(loaded_repository)
        
        expressions = [
            LaTeXExpression(r"\frac{1}{2}"),
            LaTeXExpression(r"x^2 + y^2"),
            LaTeXExpression(r"\sin(x) + \cos(x)"),
            LaTeXExpression(r"\lim_{x \to 0} \frac{\sin(x)}{x}")
        ]
        
        def process_all_sequential():
            return [matcher.process_expression(expr) for expr in expressions]
        
        def process_all_concurrent():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = [
                    executor.submit(matcher.process_expression, expr)
                    for expr in expressions
                ]
                return [f.result() for f in futures]
        
        # Sequential processing
        seq_stats = self.benchmark_function(
            process_all_sequential,
            iterations=100
        )
        
        # Concurrent processing
        conc_stats = self.benchmark_function(
            process_all_concurrent,
            iterations=100
        )
        
        print(f"\nSequential Processing (4 expressions):")
        print(f"  Mean: {seq_stats['mean']:.2f}ms")
        
        print(f"\nConcurrent Processing (4 expressions):")
        print(f"  Mean: {conc_stats['mean']:.2f}ms")
        
        # Both should be reasonably fast
        assert seq_stats['mean'] < 50
        assert conc_stats['mean'] < 50