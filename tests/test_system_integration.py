"""
Comprehensive system integration test for MathTTS v3.

This test verifies that all components work together properly,
including domain entities, use cases, infrastructure, and adapters.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncio
import tempfile
from pathlib import Path
import pytest

from src.domain.entities import PatternEntity, MathematicalExpression
from src.domain.value_objects import (
    LaTeXExpression, 
    SpeechText, 
    PatternPriority,
    MathematicalDomain,
    AudienceLevel
)
from src.domain.services import PatternMatchingService
from src.infrastructure.persistence.memory_pattern_repository import MemoryPatternRepository
from src.infrastructure.cache import LRUCacheRepository
from src.infrastructure.logging import get_logger
from src.application.use_cases import ProcessExpressionUseCase
from src.application.dtos import ProcessExpressionRequest, BatchProcessRequest
from src.adapters.pattern_loaders import YAMLPatternLoader


logger = get_logger(__name__)


@pytest.fixture
async def pattern_repository():
    """Create and populate a pattern repository."""
    repo = MemoryPatternRepository()
    
    # Add test patterns
    patterns = [
        PatternEntity(
            id="frac_basic",
            pattern=r"\\frac{(\d+)}{(\d+)}",
            output_template="{1} over {2}",
            priority=PatternPriority.high(),
            domain=MathematicalDomain("general"),
            contexts=["inline", "display"],
            description="Basic fraction pattern"
        ),
        PatternEntity(
            id="sqrt_basic",
            pattern=r"\\sqrt{([^}]+)}",
            output_template="square root of {1}",
            priority=PatternPriority.high(),
            domain=MathematicalDomain("general"),
            contexts=["inline", "display"],
            description="Basic square root pattern"
        ),
        PatternEntity(
            id="sum_notation",
            pattern=r"\\sum_{([^}]+)}^{([^}]+)}",
            output_template="sum from {1} to {2} of",
            priority=PatternPriority.critical(),
            domain=MathematicalDomain("calculus"),
            contexts=["inline", "display"],
            description="Summation notation"
        ),
        PatternEntity(
            id="greek_alpha",
            pattern=r"\\alpha",
            output_template="alpha",
            priority=PatternPriority.medium(),
            domain=MathematicalDomain("general"),
            contexts=["inline", "display"],
            description="Greek letter alpha"
        )
    ]
    
    for pattern in patterns:
        await repo.add(pattern)
    
    return repo


@pytest.fixture
async def cache_repository():
    """Create a cache repository."""
    return LRUCacheRepository(max_size=100)


@pytest.fixture
async def pattern_matching_service(pattern_repository):
    """Create pattern matching service."""
    return PatternMatchingService(pattern_repository)


@pytest.fixture
async def process_expression_use_case(pattern_matching_service, pattern_repository, cache_repository):
    """Create process expression use case."""
    return ProcessExpressionUseCase(
        pattern_matching_service=pattern_matching_service,
        pattern_repository=pattern_repository,
        cache_repository=cache_repository
    )


class TestSystemIntegration:
    """System integration tests."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_processing(self, process_expression_use_case):
        """Test complete expression processing flow."""
        # Create request
        latex_expr = LaTeXExpression("\\frac{1}{2} + \\sqrt{x}")
        request = ProcessExpressionRequest(
            expression=latex_expr,
            audience_level=AudienceLevel("undergraduate"),
            domain=MathematicalDomain("general"),
            context="inline"
        )
        
        # Execute processing
        response = await process_expression_use_case.execute(request)
        
        # Verify response
        assert response.expression == latex_expr
        assert response.speech_text is not None
        assert response.speech_text.value == "1 over 2 + square root of x"
        assert response.processing_time_ms > 0
        assert response.cached is False
        assert response.patterns_applied == 2
        assert response.domain_detected == MathematicalDomain("general")
        assert response.complexity_score is not None
    
    @pytest.mark.asyncio
    async def test_caching_behavior(self, process_expression_use_case):
        """Test that caching works correctly."""
        # Create request
        latex_expr = LaTeXExpression("\\alpha + \\beta")
        request = ProcessExpressionRequest(
            expression=latex_expr,
            audience_level=AudienceLevel("undergraduate")
        )
        
        # First execution (cache miss)
        response1 = await process_expression_use_case.execute(request)
        assert response1.cached is False
        
        # Second execution (cache hit)
        response2 = await process_expression_use_case.execute(request)
        assert response2.cached is True
        assert response2.speech_text.value == response1.speech_text.value
        assert response2.processing_time_ms < response1.processing_time_ms
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, process_expression_use_case):
        """Test batch processing of multiple expressions."""
        # Create batch request
        requests = [
            ProcessExpressionRequest(
                expression=LaTeXExpression("\\frac{1}{2}"),
                audience_level=AudienceLevel("high_school")
            ),
            ProcessExpressionRequest(
                expression=LaTeXExpression("\\sqrt{9}"),
                audience_level=AudienceLevel("elementary")
            ),
            ProcessExpressionRequest(
                expression=LaTeXExpression("\\sum_{i=1}^{n} i"),
                audience_level=AudienceLevel("undergraduate"),
                domain=MathematicalDomain("calculus")
            )
        ]
        
        batch_request = BatchProcessRequest(requests=requests)
        
        # Execute batch
        batch_response = await process_expression_use_case.execute_batch(batch_request)
        
        # Verify batch response
        assert batch_response.successful_count == 3
        assert batch_response.failed_count == 0
        assert len(batch_response.results) == 3
        assert batch_response.total_processing_time_ms > 0
        
        # Verify individual results
        assert batch_response.results[0].speech_text.value == "1 over 2"
        assert batch_response.results[1].speech_text.value == "square root of 9"
        assert "sum from" in batch_response.results[2].speech_text.value
    
    @pytest.mark.asyncio
    async def test_pattern_repository_operations(self, pattern_repository):
        """Test pattern repository functionality."""
        # Test count
        count = await pattern_repository.count()
        assert count == 4
        
        # Test find by domain
        calculus_patterns = await pattern_repository.find_by_domain(
            MathematicalDomain("calculus")
        )
        assert len(calculus_patterns) == 1
        assert calculus_patterns[0].id == "sum_notation"
        
        # Test find by priority range
        high_priority_patterns = await pattern_repository.find_by_priority_range(
            PatternPriority(1000),
            PatternPriority(2000)
        )
        assert len(high_priority_patterns) == 3  # critical, high patterns
        
        # Test find by context
        inline_patterns = await pattern_repository.find_by_context("inline")
        assert len(inline_patterns) == 4  # all patterns support inline
        
        # Test statistics
        stats = await pattern_repository.get_statistics()
        assert stats["total_patterns"] == 4
        assert stats["domains"]["general"] == 3
        assert stats["domains"]["calculus"] == 1
        assert stats["priorities"]["critical"] == 1
        assert stats["priorities"]["high"] == 2
        assert stats["priorities"]["medium"] == 1
    
    @pytest.mark.asyncio
    async def test_yaml_pattern_loader(self, tmp_path):
        """Test YAML pattern loading functionality."""
        # Create test YAML file
        yaml_content = """
patterns:
  - pattern:
      id: test_pattern_1
      pattern: "\\\\pi"
      output_template: "pi"
      priority: 500
      domain: general
      contexts: ["inline"]
      description: "Pi constant"
  - pattern:
      id: test_pattern_2
      pattern: "\\\\theta"
      output_template: "theta"
      priority: 500
      domain: general
      contexts: ["inline", "display"]
      description: "Greek letter theta"
"""
        
        yaml_file = tmp_path / "test_patterns.yaml"
        yaml_file.write_text(yaml_content)
        
        # Load patterns
        loader = YAMLPatternLoader(patterns_dir=tmp_path)
        patterns = await loader.load_patterns()
        
        # Verify loaded patterns
        assert len(patterns) == 2
        assert patterns[0].id == "test_pattern_1"
        assert patterns[0].pattern == "\\pi"
        assert patterns[0].output_template == "pi"
        assert patterns[1].id == "test_pattern_2"
        assert patterns[1].pattern == "\\theta"
    
    @pytest.mark.asyncio
    async def test_security_validation(self):
        """Test security validation in LaTeX expressions."""
        # Test dangerous commands
        dangerous_expressions = [
            "\\input{/etc/passwd}",
            "\\write18{rm -rf /}",
            "\\def\\x{\\x}\\x",
            "\\csname @gobble\\endcsname",
            "\\catcode`\\@=11"
        ]
        
        for expr in dangerous_expressions:
            with pytest.raises(Exception) as exc_info:
                LaTeXExpression(expr)
            assert "Security" in str(exc_info.type) or "dangerous" in str(exc_info.value).lower()
        
        # Test valid expressions
        valid_expressions = [
            "\\frac{1}{2}",
            "\\sqrt{x^2 + y^2}",
            "\\int_{0}^{\\infty} e^{-x} dx",
            "\\sum_{n=1}^{\\infty} \\frac{1}{n^2}"
        ]
        
        for expr in valid_expressions:
            latex_expr = LaTeXExpression(expr)
            assert latex_expr.content == expr
    
    @pytest.mark.asyncio
    async def test_complex_expression_processing(self, process_expression_use_case):
        """Test processing of complex mathematical expressions."""
        # Complex calculus expression
        complex_expr = LaTeXExpression(
            "\\int_{0}^{\\infty} \\frac{x^2}{\\sqrt{1 + x^4}} dx"
        )
        
        request = ProcessExpressionRequest(
            expression=complex_expr,
            audience_level=AudienceLevel("graduate"),
            domain=MathematicalDomain("calculus"),
            context="display"
        )
        
        response = await process_expression_use_case.execute(request)
        
        # Should process without errors even if no patterns match
        assert response.speech_text is not None
        assert response.processing_time_ms > 0
        assert response.error is None
    
    @pytest.mark.asyncio
    async def test_error_handling(self, process_expression_use_case):
        """Test error handling in processing."""
        # Create request with invalid LaTeX (unbalanced braces)
        with pytest.raises(Exception):
            LaTeXExpression("\\frac{1}{2")
        
        # Test with empty expression
        with pytest.raises(Exception):
            LaTeXExpression("")
    
    @pytest.mark.asyncio
    async def test_cache_statistics(self, cache_repository):
        """Test cache repository statistics."""
        # Add some items
        await cache_repository.set("key1", {"value": "test1"})
        await cache_repository.set("key2", {"value": "test2"})
        
        # Get items (creates hits)
        await cache_repository.get("key1")
        await cache_repository.get("key1")
        await cache_repository.get("key2")
        await cache_repository.get("key3")  # miss
        
        # Check statistics
        stats = cache_repository.get_stats()
        assert stats["size"] == 2
        assert stats["hits"] == 3
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.75


@pytest.mark.asyncio
async def test_full_system_workflow():
    """Test complete system workflow from YAML loading to speech output."""
    # Create temporary directory for patterns
    with tempfile.TemporaryDirectory() as tmpdir:
        patterns_dir = Path(tmpdir)
        
        # Create pattern file
        pattern_file = patterns_dir / "math_patterns.yaml"
        pattern_file.write_text("""
patterns:
  - pattern:
      id: fraction_to_speech
      pattern: "\\\\frac{([^}]+)}{([^}]+)}"
      output_template: "{1} divided by {2}"
      priority: 1000
      domain: general
      contexts: ["inline", "display"]
  - pattern:
      id: power_to_speech
      pattern: "([a-zA-Z0-9]+)\\^{([^}]+)}"
      output_template: "{1} to the power of {2}"
      priority: 900
      domain: general
      contexts: ["inline"]
""")
        
        # Load patterns
        loader = YAMLPatternLoader(patterns_dir)
        patterns = await loader.load_patterns()
        
        # Create repository and add patterns
        repo = MemoryPatternRepository()
        for pattern in patterns:
            await repo.add(pattern)
        
        # Create services
        pattern_service = PatternMatchingService(repo)
        cache = LRUCacheRepository(max_size=10)
        use_case = ProcessExpressionUseCase(pattern_service, repo, cache)
        
        # Process expression
        expr = LaTeXExpression("\\frac{x^{2} + 1}{2}")
        request = ProcessExpressionRequest(
            expression=expr,
            audience_level=AudienceLevel("undergraduate")
        )
        
        response = await use_case.execute(request)
        
        # Verify result
        assert response.speech_text is not None
        assert "divided by" in response.speech_text.value
        assert response.patterns_applied > 0
        
        logger.info(f"Expression: {expr.content}")
        logger.info(f"Speech output: {response.speech_text.value}")
        logger.info(f"Patterns applied: {response.patterns_applied}")


if __name__ == "__main__":
    # Run the full workflow test
    asyncio.run(test_full_system_workflow())