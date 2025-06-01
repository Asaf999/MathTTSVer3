"""
Integration tests for MathTTS v3.

This module tests the complete system working together,
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from LaTeX input to speech output.
"""

import pytest
from pathlib import Path
import tempfile
import yaml
from unittest.mock import patch

from src.domain.value_objects import LaTeXExpression, AudienceLevel, MathematicalDomain
from src.domain.services import PatternMatchingService
from src.application.use_cases import ProcessExpressionUseCase
from src.application.dtos import ProcessExpressionRequest
from src.infrastructure.persistence import MemoryPatternRepository
from src.infrastructure.cache import LRUCacheRepository
from src.adapters.pattern_loaders import YAMLPatternLoader
from src.adapters.tts_providers import MockTTSProviderAdapter, TTSOptions


class TestEndToEndProcessing:
    """Test complete expression processing pipeline."""
    
    @pytest.fixture
    async def setup_system(self):
        """Set up a complete system for testing."""
        # Create pattern repository
        pattern_repo = MemoryPatternRepository()
        
        # Create test patterns
        patterns_data = [
            {
                "id": "fraction_basic",
                "pattern": "\\\\frac\\{([^}]+)\\}\\{([^}]+)\\}",
                "output_template": "\\1 over \\2",
                "priority": 1000,
                "domain": "algebra",
                "contexts": ["inline", "display"],
                "description": "Basic fractions"
            },
            {
                "id": "sin_function",
                "pattern": "\\\\sin\\(([^)]+)\\)",
                "output_template": "sine of \\1",
                "priority": 800,
                "domain": "calculus", 
                "contexts": ["inline"],
                "description": "Sine function"
            },
            {
                "id": "derivative_basic",
                "pattern": "\\\\frac\\{d\\}\\{dx\\}",
                "output_template": "the derivative with respect to x of",
                "priority": 1200,
                "domain": "calculus",
                "contexts": ["inline", "display"],
                "description": "Basic derivative notation"
            }
        ]
        
        # Load patterns into repository
        for pattern_data in patterns_data:
            from src.domain.entities import PatternEntity
            from src.domain.value_objects import PatternPriority
            
            pattern = PatternEntity(
                id=pattern_data["id"],
                pattern=pattern_data["pattern"],
                output_template=pattern_data["output_template"],
                priority=PatternPriority(pattern_data["priority"]),
                domain=MathematicalDomain(pattern_data["domain"].upper()),
                contexts=pattern_data["contexts"],
                description=pattern_data["description"]
            )
            await pattern_repo.add(pattern)
        
        # Create cache
        cache_repo = LRUCacheRepository(max_size=100)
        
        # Create services
        pattern_service = PatternMatchingService(pattern_repo)
        
        # Create use case
        use_case = ProcessExpressionUseCase(
            pattern_matching_service=pattern_service,
            pattern_repository=pattern_repo,
            cache_repository=cache_repo
        )
        
        return {
            "use_case": use_case,
            "pattern_repo": pattern_repo,
            "cache_repo": cache_repo,
            "pattern_service": pattern_service
        }
    
    @pytest.mark.asyncio
    async def test_simple_expression_processing(self, setup_system):
        """Test processing a simple LaTeX expression."""
        components = await setup_system
        use_case = components["use_case"]
        
        # Create request
        expression = LaTeXExpression("\\frac{1}{2}")
        request = ProcessExpressionRequest(
            expression=expression,
            audience_level=AudienceLevel.HIGH_SCHOOL,
            context="inline"
        )
        
        # Process expression
        result = await use_case.execute(request)
        
        # Verify result
        assert result.speech_text.plain_text == "1 over 2"
        assert result.processing_time_ms > 0
        assert not result.cached  # First time processing
        assert result.patterns_applied >= 1
    
    @pytest.mark.asyncio
    async def test_caching_behavior(self, setup_system):
        """Test that expressions are cached properly."""
        components = await setup_system
        use_case = components["use_case"]
        
        expression = LaTeXExpression("\\sin(x)")
        request = ProcessExpressionRequest(
            expression=expression,
            audience_level=AudienceLevel.HIGH_SCHOOL,
            context="inline"
        )
        
        # First request
        result1 = await use_case.execute(request)
        assert not result1.cached
        
        # Second request (should be cached)
        result2 = await use_case.execute(request)
        assert result2.cached
        assert result2.speech_text.plain_text == result1.speech_text.plain_text
        assert result2.processing_time_ms < result1.processing_time_ms  # Should be faster
    
    @pytest.mark.asyncio
    async def test_pattern_priority_ordering(self, setup_system):
        """Test that higher priority patterns are applied first."""
        components = await setup_system
        pattern_service = components["pattern_service"]
        
        expression = LaTeXExpression("\\frac{d}{dx}")
        
        # This should match the derivative pattern (priority 1200) 
        # rather than the basic fraction pattern (priority 1000)
        result = await pattern_service.apply_patterns(expression)
        
        assert "derivative" in result.plain_text.lower()
    
    @pytest.mark.asyncio
    async def test_domain_detection(self, setup_system):
        """Test automatic domain detection."""
        components = await setup_system
        use_case = components["use_case"]
        
        # Calculus expression
        calculus_expr = LaTeXExpression("\\sin(x)")
        request = ProcessExpressionRequest(
            expression=calculus_expr,
            audience_level=AudienceLevel.HIGH_SCHOOL
        )
        
        result = await use_case.execute(request)
        
        # Should detect calculus domain
        assert result.domain_detected == MathematicalDomain.CALCULUS
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, setup_system):
        """Test batch processing of multiple expressions."""
        components = await setup_system
        use_case = components["use_case"]
        
        expressions = [
            "\\frac{1}{2}",
            "\\sin(x)",
            "\\frac{d}{dx}"
        ]
        
        requests = []
        for expr in expressions:
            latex_expr = LaTeXExpression(expr)
            request = ProcessExpressionRequest(
                expression=latex_expr,
                audience_level=AudienceLevel.HIGH_SCHOOL
            )
            requests.append(request)
        
        from src.application.dtos import BatchProcessRequest
        batch_request = BatchProcessRequest(requests=requests)
        
        # Process batch
        batch_result = await use_case.execute_batch(batch_request)
        
        # Verify results
        assert len(batch_result.results) == 3
        assert batch_result.successful_count == 3
        assert batch_result.failed_count == 0
        assert batch_result.total_processing_time_ms > 0
        
        # Verify individual results
        expected_outputs = [
            "1 over 2",
            "sine of x", 
            "the derivative with respect to x of"
        ]
        
        for i, result in enumerate(batch_result.results):
            assert expected_outputs[i] in result.speech_text.plain_text


class TestTTSIntegration:
    """Test TTS provider integration."""
    
    @pytest.mark.asyncio
    async def test_complete_latex_to_audio_pipeline(self):
        """Test complete pipeline from LaTeX to audio."""
        # Set up minimal system
        pattern_repo = MemoryPatternRepository()
        cache_repo = LRUCacheRepository(max_size=10)
        pattern_service = PatternMatchingService(pattern_repo)
        
        use_case = ProcessExpressionUseCase(
            pattern_matching_service=pattern_service,
            pattern_repository=pattern_repo,
            cache_repository=cache_repo
        )
        
        # Set up TTS provider
        tts_provider = MockTTSProviderAdapter()
        await tts_provider.initialize()
        
        try:
            # Process expression to get speech text
            expression = LaTeXExpression("x^2")
            request = ProcessExpressionRequest(
                expression=expression,
                audience_level=AudienceLevel.HIGH_SCHOOL
            )
            
            result = await use_case.execute(request)
            
            # Convert to audio
            options = TTSOptions(voice_id="mock-voice-1")
            audio_data = await tts_provider.synthesize(result.speech_text, options)
            
            # Verify audio generation
            assert audio_data.size_bytes > 0
            assert audio_data.duration_seconds is not None
            assert audio_data.format.value == "mp3"
            
        finally:
            await tts_provider.close()


class TestSystemConfiguration:
    """Test system configuration and setup."""
    
    def test_configuration_loading(self):
        """Test that configuration loads correctly."""
        from src.infrastructure.config import get_settings
        
        settings = get_settings()
        
        # Basic configuration should be available
        assert settings.app_name is not None
        assert settings.app_version is not None
        assert settings.environment is not None
        
        # Subsystem configurations should be available
        assert settings.cache is not None
        assert settings.tts is not None
        assert settings.patterns is not None
    
    @pytest.mark.asyncio
    async def test_pattern_loading_from_file(self):
        """Test loading patterns from actual YAML files."""
        # Create temporary pattern file
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            pattern_file = temp_dir / "test_patterns.yaml"
            
            pattern_data = {
                "pattern": {
                    "id": "test_pattern",
                    "pattern": "x\\^2",
                    "output_template": "x squared",
                    "priority": 500,
                    "domain": "algebra",
                    "contexts": ["inline"],
                    "description": "Square notation"
                }
            }
            
            with open(pattern_file, "w") as f:
                yaml.dump(pattern_data, f)
            
            # Load patterns
            loader = YAMLPatternLoader(temp_dir)
            patterns = await loader.load_patterns()
            
            assert len(patterns) == 1
            assert patterns[0].id == "test_pattern"
            assert patterns[0].output_template == "x squared"
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_logging_setup(self):
        """Test that logging is properly configured."""
        from src.infrastructure.logging import get_logger
        
        logger = get_logger("integration_test")
        
        # Should not raise exceptions
        logger.info("Test log message")
        logger.debug("Debug message")
        logger.warning("Warning message")


class TestErrorHandling:
    """Test error handling throughout the system."""
    
    @pytest.mark.asyncio
    async def test_invalid_latex_expression(self):
        """Test handling of invalid LaTeX expressions."""
        with pytest.raises(ValueError):
            LaTeXExpression("")  # Empty expression
        
        with pytest.raises(ValueError):
            LaTeXExpression("a" * 20000)  # Too long expression
    
    @pytest.mark.asyncio
    async def test_processing_with_no_patterns(self):
        """Test processing when no patterns are available."""
        # Empty pattern repository
        pattern_repo = MemoryPatternRepository()
        cache_repo = LRUCacheRepository(max_size=10)
        pattern_service = PatternMatchingService(pattern_repo)
        
        use_case = ProcessExpressionUseCase(
            pattern_matching_service=pattern_service,
            pattern_repository=pattern_repo,
            cache_repository=cache_repo
        )
        
        expression = LaTeXExpression("\\frac{1}{2}")
        request = ProcessExpressionRequest(
            expression=expression,
            audience_level=AudienceLevel.HIGH_SCHOOL
        )
        
        # Should handle gracefully and return the original expression
        result = await use_case.execute(request)
        
        assert result.speech_text.plain_text == "\\frac{1}{2}"  # Original unchanged
        assert result.patterns_applied == 0
    
    @pytest.mark.asyncio
    async def test_tts_provider_error_handling(self):
        """Test TTS provider error handling."""
        from src.adapters.tts_providers import TTSProviderError
        
        # Mock a failing TTS provider
        class FailingTTSProvider(MockTTSProviderAdapter):
            async def synthesize(self, text, options):
                raise TTSProviderError("Mock TTS failure")
        
        provider = FailingTTSProvider()
        await provider.initialize()
        
        options = TTSOptions(voice_id="test")
        
        with pytest.raises(TTSProviderError):
            await provider.synthesize("test", options)


class TestPerformance:
    """Test system performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_processing_time_reasonable(self, setup_system):
        """Test that processing times are reasonable."""
        components = await setup_system
        use_case = components["use_case"]
        
        expression = LaTeXExpression("\\frac{1}{2}")
        request = ProcessExpressionRequest(
            expression=expression,
            audience_level=AudienceLevel.HIGH_SCHOOL
        )
        
        result = await use_case.execute(request)
        
        # Processing should be fast (under 100ms for simple expressions)
        assert result.processing_time_ms < 100
    
    @pytest.mark.asyncio
    async def test_cache_performance_improvement(self, setup_system):
        """Test that caching provides performance improvement."""
        components = await setup_system
        use_case = components["use_case"]
        
        expression = LaTeXExpression("\\sin(x)")
        request = ProcessExpressionRequest(
            expression=expression,
            audience_level=AudienceLevel.HIGH_SCHOOL
        )
        
        # First request (not cached)
        result1 = await use_case.execute(request)
        uncached_time = result1.processing_time_ms
        
        # Second request (cached)
        result2 = await use_case.execute(request)
        cached_time = result2.processing_time_ms
        
        # Cached request should be significantly faster
        assert cached_time < uncached_time * 0.5  # At least 50% faster