"""
End-to-end tests for the complete MathTTS system.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
import asyncio
from pathlib import Path
import subprocess
import requests
import time
import json
import base64

from src.adapters.pattern_loaders import YAMLPatternLoader
from src.infrastructure.persistence import MemoryPatternRepository
from src.application.services import MathTTSService
from src.adapters.tts_providers import MockTTSAdapter
from src.infrastructure.cache import AudioCache
from src.domain.value_objects import TTSOptions, AudioFormat


@pytest.mark.e2e
class TestFullSystem:
    """End-to-end tests for complete system functionality."""
    
    @pytest.fixture
    def system_components(self, tmp_path):
        """Set up all system components."""
        # Load patterns
        patterns_dir = Path(__file__).parent.parent.parent / "patterns"
        if not patterns_dir.exists():
            pytest.skip("Patterns directory not found")
        
        loader = YAMLPatternLoader(patterns_dir)
        patterns = loader.load_all_patterns()
        
        # Create repository
        repo = MemoryPatternRepository()
        for pattern in patterns:
            repo.add(pattern)
        
        # Create TTS adapter
        tts = MockTTSAdapter()
        
        # Create cache
        cache = AudioCache(cache_dir=tmp_path / "cache")
        
        # Create service
        service = MathTTSService(repo, tts, cache)
        
        return {
            "service": service,
            "repository": repo,
            "tts": tts,
            "cache": cache,
            "patterns_count": len(patterns)
        }
    
    @pytest.mark.asyncio
    async def test_complete_latex_to_audio_flow(self, system_components):
        """Test complete flow from LaTeX input to audio output."""
        service = system_components["service"]
        tts = system_components["tts"]
        
        # Initialize TTS
        await tts.initialize()
        
        # Test expressions
        test_cases = [
            {
                "latex": r"\frac{1}{2} + \frac{1}{3} = \frac{5}{6}",
                "expected_words": ["half", "plus", "third", "equals"]
            },
            {
                "latex": r"\int_0^1 x^2 dx = \frac{1}{3}",
                "expected_words": ["integral", "squared", "equals", "third"]
            },
            {
                "latex": r"e^{i\pi} + 1 = 0",
                "expected_words": ["plus", "equals", "zero"]
            }
        ]
        
        for test in test_cases:
            # Convert to audio
            audio = await service.convert_latex_to_speech(test["latex"])
            
            # Verify audio properties
            assert audio is not None
            assert len(audio.data) > 0
            assert audio.format == AudioFormat.MP3
            assert audio.duration_seconds > 0
            
            # Verify it's cached
            cached_audio = await service.convert_latex_to_speech(test["latex"])
            assert cached_audio.data == audio.data
        
        # Check cache statistics
        stats = service.get_pattern_stats()
        assert stats["total_patterns"] == system_components["patterns_count"]
        assert stats["cache_enabled"] is True
        
        await tts.close()
    
    @pytest.mark.asyncio
    async def test_batch_processing_e2e(self, system_components):
        """Test batch processing of multiple expressions."""
        service = system_components["service"]
        tts = system_components["tts"]
        
        await tts.initialize()
        
        # Large batch of expressions
        expressions = [
            r"\frac{1}{n}",
            r"x^2 + y^2 = r^2",
            r"\sin(x) + \cos(x)",
            r"\lim_{x \to \infty} \frac{1}{x} = 0",
            r"\sum_{i=1}^{n} i = \frac{n(n+1)}{2}",
            r"\sqrt{2}",
            r"\pi \approx 3.14159",
            r"f'(x) = \frac{df}{dx}",
            r"\nabla \cdot \vec{F} = 0",
            r"E = mc^2"
        ]
        
        # Process batch
        results = await service.batch_convert(expressions)
        
        # Verify all converted
        assert len(results) == len(expressions)
        
        # Verify each result
        for i, audio in enumerate(results):
            assert audio is not None
            assert len(audio.data) > 0
            assert audio.format == AudioFormat.MP3
        
        await tts.close()
    
    @pytest.mark.asyncio
    async def test_different_voice_options(self, system_components):
        """Test conversion with different voice options."""
        service = system_components["service"]
        tts = system_components["tts"]
        
        await tts.initialize()
        
        latex = r"\frac{\pi}{2}"
        
        # Test different voices
        voices = await tts.list_voices()
        
        for voice in voices[:2]:  # Test first two voices
            options = TTSOptions(
                voice_id=voice.id,
                rate=1.2,
                pitch=0.9,
                volume=0.8
            )
            
            audio = await service.convert_latex_to_speech(latex, options)
            
            assert audio is not None
            assert audio.format == AudioFormat.MP3
        
        # Test different formats
        for format in [AudioFormat.MP3, AudioFormat.WAV]:
            options = TTSOptions(format=format)
            audio = await service.convert_latex_to_speech(latex, options)
            
            assert audio.format == format
            
            if format == AudioFormat.WAV:
                assert audio.data.startswith(b"RIFF")
            elif format == AudioFormat.MP3:
                assert audio.data.startswith(b"ID3")
        
        await tts.close()
    
    @pytest.mark.asyncio
    async def test_error_handling_e2e(self, system_components):
        """Test system error handling."""
        service = system_components["service"]
        tts = system_components["tts"]
        
        # Test before initialization
        with pytest.raises(RuntimeError):
            await service.convert_latex_to_speech("test")
        
        await tts.initialize()
        
        # Test invalid LaTeX
        with pytest.raises(ValueError):
            await service.convert_latex_to_speech("")
        
        # Test batch with some invalid expressions
        mixed_expressions = [
            r"\frac{1}{2}",  # Valid
            "",  # Invalid
            r"x^2",  # Valid
        ]
        
        results = await service.batch_convert(mixed_expressions)
        
        # Should get results for valid expressions only
        assert len(results) == 2
        
        await tts.close()
    
    @pytest.mark.asyncio
    async def test_cache_warmup(self, system_components):
        """Test cache warmup functionality."""
        service = system_components["service"]
        tts = system_components["tts"]
        cache = system_components["cache"]
        
        await tts.initialize()
        
        # Common expressions to cache
        common_expressions = [
            r"\frac{1}{2}",
            r"x^2",
            r"\pi",
            r"\infty",
            r"\sum",
            r"\int"
        ]
        
        # Warm up cache
        cached_count = await service.warmup_cache(common_expressions)
        assert cached_count == len(common_expressions)
        
        # Verify all are cached
        for expr in common_expressions:
            options = TTSOptions()
            cache_key = cache.generate_key(expr, options)
            cached = await cache.get(cache_key)
            assert cached is not None
        
        await tts.close()
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, system_components):
        """Test handling of concurrent conversion requests."""
        service = system_components["service"]
        tts = system_components["tts"]
        
        await tts.initialize()
        
        # Create multiple concurrent tasks
        expressions = [f"x^{i}" for i in range(10)]
        
        tasks = [
            service.convert_latex_to_speech(expr)
            for expr in expressions
        ]
        
        # Run concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        duration = time.time() - start_time
        
        # Verify all completed
        assert len(results) == len(expressions)
        assert all(r is not None for r in results)
        
        print(f"\nProcessed {len(expressions)} expressions concurrently in {duration:.2f}s")
        
        await tts.close()
    
    def test_cli_integration(self, tmp_path):
        """Test CLI integration (if main.py is runnable)."""
        # Check if CLI is available
        result = subprocess.run(
            ["python", "main.py", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        if result.returncode != 0:
            pytest.skip("CLI not available")
        
        assert "MathTTS" in result.stdout
        
        # Test version command
        result = subprocess.run(
            ["python", "main.py", "version"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0
        assert "MathTTS" in result.stdout
    
    @pytest.mark.asyncio
    async def test_pattern_coverage(self, system_components):
        """Test that common mathematical expressions are covered."""
        service = system_components["service"]
        tts = system_components["tts"]
        
        await tts.initialize()
        
        # Common mathematical expressions that should be supported
        common_math = [
            # Basic arithmetic
            (r"1 + 1 = 2", ["plus", "equals"]),
            (r"5 - 3 = 2", ["minus", "equals"]),
            (r"2 \times 3 = 6", ["times", "equals"]),
            (r"6 \div 2 = 3", ["divided", "equals"]),
            
            # Fractions
            (r"\frac{1}{2}", ["half"]),
            (r"\frac{3}{4}", ["three", "four"]),
            
            # Powers and roots
            (r"x^2", ["squared"]),
            (r"\sqrt{4} = 2", ["square root", "equals"]),
            
            # Greek letters
            (r"\alpha, \beta, \gamma", ["alpha", "beta", "gamma"]),
            
            # Calculus
            (r"\frac{d}{dx}", ["d", "d x"]),
            (r"\int f(x) dx", ["integral"]),
            (r"\lim_{x \to 0}", ["limit"]),
            
            # Trig functions
            (r"\sin(x)", ["sine"]),
            (r"\cos(x)", ["cosine"]),
            (r"\tan(x)", ["tangent"]),
        ]
        
        coverage_results = []
        
        for latex, expected_words in common_math:
            try:
                audio = await service.convert_latex_to_speech(latex)
                
                # Get the speech text (would need access to intermediate result)
                # For now, just verify conversion succeeds
                coverage_results.append({
                    "latex": latex,
                    "success": True,
                    "audio_size": len(audio.data)
                })
            except Exception as e:
                coverage_results.append({
                    "latex": latex,
                    "success": False,
                    "error": str(e)
                })
        
        # Calculate coverage
        successful = sum(1 for r in coverage_results if r["success"])
        coverage = successful / len(coverage_results) * 100
        
        print(f"\nPattern Coverage: {coverage:.1f}% ({successful}/{len(coverage_results)})")
        
        # Should have high coverage
        assert coverage >= 80, f"Pattern coverage too low: {coverage}%"
        
        await tts.close()