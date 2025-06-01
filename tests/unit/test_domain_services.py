"""
Unit tests for domain services.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import unittest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from src.domain.services import PatternMatchingService
from src.domain.entities import PatternEntity, MathematicalExpression
from src.domain.entities.pattern import PatternContext
from src.domain.value_objects import (
    LaTeXExpression,
    SpeechText,
    PatternPriority,
    MathematicalDomain,
    AudienceLevel
)
from src.domain.exceptions import ProcessingError
from src.domain.interfaces import PatternRepository


class TestPatternMatchingService(unittest.TestCase):
    """Test cases for PatternMatchingService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_repository = Mock(spec=PatternRepository)
        self.service = PatternMatchingService(
            pattern_repository=self.mock_repository,
            timeout_seconds=5.0,
            max_iterations=10
        )
        
        # Create test patterns
        self.frac_pattern = PatternEntity(
            id="frac_pattern",
            name="Fraction",
            pattern=r"\\frac\{(\d+)\}\{(\d+)\}",
            output_template=r"\1 over \2",
            priority=PatternPriority.high(),
            domain=MathematicalDomain("general"),
            contexts=[PatternContext.ANY]
        )
        
        self.sqrt_pattern = PatternEntity(
            id="sqrt_pattern",
            name="Square Root",
            pattern=r"\\sqrt\{([^}]+)\}",
            output_template=r"square root of \1",
            priority=PatternPriority.high(),
            domain=MathematicalDomain("general"),
            contexts=[PatternContext.ANY]
        )
        
        self.alpha_pattern = PatternEntity(
            id="alpha_pattern",
            name="Alpha",
            pattern=r"\\alpha",
            output_template="alpha",
            priority=PatternPriority.medium(),
            domain=MathematicalDomain("general"),
            contexts=[PatternContext.ANY]
        )
    
    def async_test(coro):
        """Decorator to run async tests."""
        def wrapper(self):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(coro(self))
        return wrapper
    
    @async_test
    async def test_process_expression_success(self):
        """Test successful expression processing."""
        # Setup
        expr = MathematicalExpression(
            latex_expression=LaTeXExpression(r"\frac{1}{2}"),
            audience_level=AudienceLevel("undergraduate")
        )
        
        # Mock repository to return patterns
        self.mock_repository.find_by_domain = AsyncMock(
            side_effect=[
                [self.frac_pattern],  # Domain patterns
                []  # General patterns
            ]
        )
        
        # Execute
        result = await self.service.process_expression(expr)
        
        # Verify
        self.assertIsInstance(result, SpeechText)
        self.assertEqual(result.value, "1 over 2")
        self.assertIn("frac_pattern", expr.metadata.patterns_applied)
        self.mock_repository.find_by_domain.assert_called()
    
    @async_test
    async def test_process_expression_no_patterns(self):
        """Test processing when no patterns are found."""
        # Setup
        expr = MathematicalExpression(
            latex_expression=LaTeXExpression(r"\unknown{command}"),
            audience_level=AudienceLevel("undergraduate")
        )
        
        # Mock repository to return no patterns
        self.mock_repository.find_by_domain = AsyncMock(return_value=[])
        
        # Execute and verify exception
        with self.assertRaises(ProcessingError) as ctx:
            await self.service.process_expression(expr)
        
        self.assertIn("No patterns found", str(ctx.exception))
    
    @async_test
    async def test_multiple_pattern_application(self):
        """Test applying multiple patterns in sequence."""
        # Setup
        expr = MathematicalExpression(
            latex_expression=LaTeXExpression(r"\frac{1}{2} + \sqrt{\alpha}"),
            audience_level=AudienceLevel("undergraduate")
        )
        
        # Mock repository
        self.mock_repository.find_by_domain = AsyncMock(
            side_effect=[
                [self.frac_pattern, self.sqrt_pattern, self.alpha_pattern],
                []
            ]
        )
        
        # Execute
        result = await self.service.process_expression(expr)
        
        # Verify - patterns should be applied iteratively
        self.assertIsInstance(result, SpeechText)
        # First iteration: \frac{1}{2} -> "1 over 2"
        # Second iteration: \sqrt{\alpha} -> "square root of \alpha"
        # Third iteration: \alpha -> "alpha"
        self.assertEqual(result.value, "1 over 2 + square root of alpha")
    
    @async_test
    async def test_pattern_priority_ordering(self):
        """Test that patterns are applied in priority order."""
        # Create patterns with different priorities
        high_priority = PatternEntity(
            id="high",
            name="High Priority",
            pattern=r"test",
            output_template="HIGH",
            priority=PatternPriority.critical(),
            domain=MathematicalDomain("general"),
            contexts=[PatternContext.ANY]
        )
        
        low_priority = PatternEntity(
            id="low",
            name="Low Priority", 
            pattern=r"test",
            output_template="LOW",
            priority=PatternPriority.low(),
            domain=MathematicalDomain("general"),
            contexts=[PatternContext.ANY]
        )
        
        expr = MathematicalExpression(
            latex_expression=LaTeXExpression("test"),
            audience_level=AudienceLevel("undergraduate")
        )
        
        # Mock repository returns patterns in wrong order
        self.mock_repository.find_by_domain = AsyncMock(
            side_effect=[
                [low_priority, high_priority],
                []
            ]
        )
        
        # Execute
        result = await self.service.process_expression(expr)
        
        # High priority pattern should be applied first
        self.assertEqual(result.value, "HIGH")
    
    @async_test
    async def test_post_processing_basic_audience(self):
        """Test post-processing for basic audience."""
        # Setup expression for elementary audience
        expr = MathematicalExpression(
            latex_expression=LaTeXExpression("test"),
            audience_level=AudienceLevel("elementary")
        )
        
        # Create pattern that outputs formal language
        formal_pattern = PatternEntity(
            id="formal",
            name="Formal",
            pattern=r"test",
            output_template="with respect to x such that y implies z",
            priority=PatternPriority.medium(),
            domain=MathematicalDomain("general"),
            contexts=[PatternContext.ANY]
        )
        
        self.mock_repository.find_by_domain = AsyncMock(
            side_effect=[
                [formal_pattern],
                []
            ]
        )
        
        # Execute
        result = await self.service.process_expression(expr)
        
        # Verify simplification for basic audience
        self.assertEqual(result.value, "By x where y means z")
    
    @async_test
    async def test_post_processing_advanced_audience(self):
        """Test post-processing for advanced audience."""
        # Setup expression for graduate audience
        expr = MathematicalExpression(
            latex_expression=LaTeXExpression("test"),
            audience_level=AudienceLevel("graduate")
        )
        
        # Create pattern with informal output
        informal_pattern = PatternEntity(
            id="informal",
            name="Informal",
            pattern=r"test",
            output_template="x dot y cross z",
            priority=PatternPriority.medium(),
            domain=MathematicalDomain("general"),
            contexts=[PatternContext.ANY]
        )
        
        self.mock_repository.find_by_domain = AsyncMock(
            side_effect=[
                [informal_pattern],
                []
            ]
        )
        
        # Execute
        result = await self.service.process_expression(expr)
        
        # Verify formalization for advanced audience
        self.assertEqual(result.value, "X inner product y cross product z")
    
    @async_test
    async def test_max_iterations_limit(self):
        """Test that pattern matching stops after max iterations."""
        # Create a pattern that keeps matching
        recursive_pattern = PatternEntity(
            id="recursive",
            name="Recursive",
            pattern=r"a",
            output_template="aa",
            priority=PatternPriority.high(),
            domain=MathematicalDomain("general"),
            contexts=[PatternContext.ANY]
        )
        
        expr = MathematicalExpression(
            latex_expression=LaTeXExpression("a"),
            audience_level=AudienceLevel("undergraduate")
        )
        
        self.mock_repository.find_by_domain = AsyncMock(
            side_effect=[
                [recursive_pattern],
                []
            ]
        )
        
        # Set low max iterations
        self.service.max_iterations = 3
        
        # Execute
        result = await self.service.process_expression(expr)
        
        # Should stop after 3 iterations: a -> aa -> aaaa -> aaaaaaaa
        self.assertEqual(result.value, "aaaaaaaa")
    
    @async_test
    async def test_timeout_handling(self):
        """Test timeout handling during pattern matching."""
        # Create slow pattern
        class SlowPattern(PatternEntity):
            def apply(self, text, context=None):
                import time
                time.sleep(10)  # Longer than timeout
                return super().apply(text, context)
        
        slow_pattern = SlowPattern(
            id="slow",
            name="Slow",
            pattern=r"test",
            output_template="result",
            priority=PatternPriority.high(),
            domain=MathematicalDomain("general"),
            contexts=[PatternContext.ANY]
        )
        
        expr = MathematicalExpression(
            latex_expression=LaTeXExpression("test"),
            audience_level=AudienceLevel("undergraduate")
        )
        
        self.mock_repository.find_by_domain = AsyncMock(
            side_effect=[
                [slow_pattern],
                []
            ]
        )
        
        # Set short timeout
        self.service.timeout_seconds = 0.1
        
        # Execute and verify timeout error
        with self.assertRaises(ProcessingError) as ctx:
            await self.service.process_expression(expr)
        
        self.assertIn("timed out", str(ctx.exception))
    
    @async_test
    async def test_pattern_error_handling(self):
        """Test handling of pattern application errors."""
        # Create pattern that raises error
        error_pattern = PatternEntity(
            id="error",
            name="Error",
            pattern=r"\\invalid{regex",  # Invalid regex
            output_template="result",
            priority=PatternPriority.high(),
            domain=MathematicalDomain("general"),
            contexts=[PatternContext.ANY]
        )
        
        expr = MathematicalExpression(
            latex_expression=LaTeXExpression("test"),
            audience_level=AudienceLevel("undergraduate")
        )
        
        self.mock_repository.find_by_domain = AsyncMock(
            side_effect=[
                [error_pattern],
                []
            ]
        )
        
        # Execute and verify error is raised
        with self.assertRaises(ProcessingError) as ctx:
            await self.service.process_expression(expr)
        
        self.assertIn("Pattern matching failed", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()