"""
Unit tests for application layer components.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import unittest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.application.use_cases import ProcessExpressionUseCase
from src.application.dtos_v3 import (
    ProcessExpressionRequest,
    ProcessExpressionResponse,
    BatchProcessRequest,
    BatchProcessResponse
)
from src.domain.value_objects import (
    LaTeXExpression,
    SpeechText,
    AudienceLevel,
    MathematicalDomain
)
from src.domain.services import PatternMatchingService
from src.domain.interfaces import PatternRepository
from src.infrastructure.cache import LRUCacheRepository


class TestProcessExpressionUseCase(unittest.TestCase):
    """Test cases for ProcessExpressionUseCase."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_pattern_service = Mock(spec=PatternMatchingService)
        self.mock_pattern_repo = Mock(spec=PatternRepository)
        self.mock_cache_repo = Mock(spec=LRUCacheRepository)
        
        self.use_case = ProcessExpressionUseCase(
            pattern_matching_service=self.mock_pattern_service,
            pattern_repository=self.mock_pattern_repo,
            cache_repository=self.mock_cache_repo
        )
        
        # Test data
        self.test_expression = LaTeXExpression(r"\frac{1}{2}")
        self.test_request = ProcessExpressionRequest(
            expression=self.test_expression,
            audience_level=AudienceLevel("undergraduate"),
            domain=MathematicalDomain("general"),
            context="inline"
        )
    
    def async_test(coro):
        """Decorator to run async tests."""
        def wrapper(self):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(coro(self))
        return wrapper
    
    @async_test
    async def test_execute_success_no_cache(self):
        """Test successful execution without cache hit."""
        # Setup
        expected_speech = SpeechText(value="one half")
        self.mock_cache_repo.get = AsyncMock(return_value=None)
        self.mock_pattern_service.process_expression = AsyncMock(
            return_value=expected_speech
        )
        self.mock_cache_repo.set = AsyncMock()
        
        # Execute
        response = await self.use_case.execute(self.test_request)
        
        # Verify
        self.assertIsInstance(response, ProcessExpressionResponse)
        self.assertEqual(response.expression, self.test_expression)
        self.assertEqual(response.speech_text, expected_speech)
        self.assertFalse(response.cached)
        self.assertGreater(response.processing_time_ms, 0)
        
        # Verify cache was checked and set
        self.mock_cache_repo.get.assert_called_once()
        self.mock_cache_repo.set.assert_called_once()
        
        # Verify pattern service was called
        self.mock_pattern_service.process_expression.assert_called_once()
    
    @async_test
    async def test_execute_success_with_cache(self):
        """Test successful execution with cache hit."""
        # Setup
        cached_data = {
            "speech_text": SpeechText(value="one half"),
            "patterns_applied": 2,
            "domain_detected": MathematicalDomain("general"),
            "complexity_score": 1.5
        }
        self.mock_cache_repo.get = AsyncMock(return_value=cached_data)
        
        # Execute
        response = await self.use_case.execute(self.test_request)
        
        # Verify
        self.assertEqual(response.speech_text.value, "one half")
        self.assertTrue(response.cached)
        self.assertEqual(response.patterns_applied, 2)
        
        # Pattern service should not be called on cache hit
        self.mock_pattern_service.process_expression.assert_not_called()
    
    @async_test
    async def test_execute_pattern_service_error(self):
        """Test handling of pattern service errors."""
        # Setup
        self.mock_cache_repo.get = AsyncMock(return_value=None)
        self.mock_pattern_service.process_expression = AsyncMock(
            side_effect=Exception("Pattern matching failed")
        )
        
        # Execute
        response = await self.use_case.execute(self.test_request)
        
        # Verify fallback response
        self.assertIsInstance(response, ProcessExpressionResponse)
        self.assertEqual(response.speech_text.value, self.test_expression.content)
        self.assertFalse(response.cached)
        self.assertEqual(response.patterns_applied, 0)
        self.assertIsNotNone(response.error)
        self.assertIn("Pattern matching failed", response.error)
    
    @async_test
    async def test_execute_without_cache_repository(self):
        """Test execution without cache repository."""
        # Create use case without cache
        use_case_no_cache = ProcessExpressionUseCase(
            pattern_matching_service=self.mock_pattern_service,
            pattern_repository=self.mock_pattern_repo,
            cache_repository=None
        )
        
        expected_speech = SpeechText(value="one half")
        self.mock_pattern_service.process_expression = AsyncMock(
            return_value=expected_speech
        )
        
        # Execute
        response = await use_case_no_cache.execute(self.test_request)
        
        # Verify
        self.assertEqual(response.speech_text, expected_speech)
        self.assertFalse(response.cached)
    
    @async_test
    async def test_batch_execute_all_success(self):
        """Test batch execution with all successful."""
        # Setup
        requests = [
            ProcessExpressionRequest(
                expression=LaTeXExpression(r"\frac{1}{2}"),
                audience_level=AudienceLevel("undergraduate")
            ),
            ProcessExpressionRequest(
                expression=LaTeXExpression(r"\sqrt{4}"),
                audience_level=AudienceLevel("high_school")
            ),
            ProcessExpressionRequest(
                expression=LaTeXExpression(r"\alpha + \beta"),
                audience_level=AudienceLevel("graduate")
            )
        ]
        
        batch_request = BatchProcessRequest(requests=requests)
        
        # Mock responses
        self.mock_cache_repo.get = AsyncMock(return_value=None)
        self.mock_pattern_service.process_expression = AsyncMock(
            side_effect=[
                SpeechText(value="one half"),
                SpeechText(value="square root of four"),
                SpeechText(value="alpha plus beta")
            ]
        )
        self.mock_cache_repo.set = AsyncMock()
        
        # Execute
        response = await self.use_case.execute_batch(batch_request)
        
        # Verify
        self.assertIsInstance(response, BatchProcessResponse)
        self.assertEqual(len(response.results), 3)
        self.assertEqual(response.successful_count, 3)
        self.assertEqual(response.failed_count, 0)
        self.assertGreater(response.total_processing_time_ms, 0)
        
        # Verify results
        self.assertEqual(response.results[0].speech_text.value, "one half")
        self.assertEqual(response.results[1].speech_text.value, "square root of four")
        self.assertEqual(response.results[2].speech_text.value, "alpha plus beta")
    
    @async_test
    async def test_batch_execute_partial_failure(self):
        """Test batch execution with some failures."""
        # Setup
        requests = [
            ProcessExpressionRequest(
                expression=LaTeXExpression(r"\frac{1}{2}"),
                audience_level=AudienceLevel("undergraduate")
            ),
            ProcessExpressionRequest(
                expression=LaTeXExpression(r"\invalid"),
                audience_level=AudienceLevel("undergraduate")
            )
        ]
        
        batch_request = BatchProcessRequest(requests=requests)
        
        # Mock first success, second failure
        self.mock_cache_repo.get = AsyncMock(return_value=None)
        self.mock_pattern_service.process_expression = AsyncMock(
            side_effect=[
                SpeechText(value="one half"),
                Exception("Invalid pattern")
            ]
        )
        
        # Execute
        response = await self.use_case.execute_batch(batch_request)
        
        # Verify
        self.assertEqual(len(response.results), 2)
        self.assertEqual(response.successful_count, 2)  # Fallback counts as success
        self.assertEqual(response.failed_count, 0)
        
        # First should succeed
        self.assertEqual(response.results[0].speech_text.value, "one half")
        self.assertIsNone(response.results[0].error)
        
        # Second should have error but fallback value
        self.assertEqual(response.results[1].speech_text.value, r"\invalid")
        self.assertIsNotNone(response.results[1].error)
    
    @async_test
    async def test_cache_key_generation(self):
        """Test cache key generation for different requests."""
        # Same content, different audience
        request1 = ProcessExpressionRequest(
            expression=LaTeXExpression(r"\frac{1}{2}"),
            audience_level=AudienceLevel("undergraduate")
        )
        request2 = ProcessExpressionRequest(
            expression=LaTeXExpression(r"\frac{1}{2}"),
            audience_level=AudienceLevel("elementary")
        )
        
        key1 = self.use_case._generate_cache_key(request1)
        key2 = self.use_case._generate_cache_key(request2)
        
        # Keys should be different
        self.assertNotEqual(key1, key2)
        
        # Same request should generate same key
        key1_repeat = self.use_case._generate_cache_key(request1)
        self.assertEqual(key1, key1_repeat)
    
    @async_test
    async def test_request_validation(self):
        """Test request validation."""
        # Valid request
        valid_request = ProcessExpressionRequest(
            expression=LaTeXExpression(r"\frac{1}{2}"),
            audience_level=AudienceLevel("undergraduate")
        )
        
        # Should not raise
        valid_request.__post_init__()
        
        # Invalid request - wrong type for expression
        with self.assertRaises(TypeError):
            ProcessExpressionRequest(
                expression="not a LaTeXExpression",
                audience_level=AudienceLevel("undergraduate")
            )
        
        # Invalid request - wrong type for audience_level
        with self.assertRaises(TypeError):
            ProcessExpressionRequest(
                expression=LaTeXExpression(r"\frac{1}{2}"),
                audience_level="undergraduate"  # Should be AudienceLevel object
            )
    
    @async_test
    async def test_batch_request_validation(self):
        """Test batch request validation."""
        # Empty batch
        with self.assertRaises(ValueError) as ctx:
            BatchProcessRequest(requests=[])
        self.assertIn("At least one request", str(ctx.exception))
        
        # Too large batch
        large_requests = [
            ProcessExpressionRequest(
                expression=LaTeXExpression(f"x_{i}"),
                audience_level=AudienceLevel("undergraduate")
            )
            for i in range(1001)
        ]
        
        with self.assertRaises(ValueError) as ctx:
            BatchProcessRequest(requests=large_requests)
        self.assertIn("cannot exceed 1000", str(ctx.exception))


class TestDTOStructure(unittest.TestCase):
    """Test DTO structure and behavior."""
    
    def test_process_expression_response_fields(self):
        """Test ProcessExpressionResponse fields."""
        response = ProcessExpressionResponse(
            expression=LaTeXExpression(r"\frac{1}{2}"),
            speech_text=SpeechText(value="one half"),
            processing_time_ms=10.5,
            cached=False,
            patterns_applied=2,
            domain_detected=MathematicalDomain("general"),
            complexity_score=1.5,
            error=None,
            metadata={"extra": "data"}
        )
        
        self.assertEqual(response.expression.content, r"\frac{1}{2}")
        self.assertEqual(response.speech_text.value, "one half")
        self.assertEqual(response.processing_time_ms, 10.5)
        self.assertFalse(response.cached)
        self.assertEqual(response.patterns_applied, 2)
        self.assertEqual(response.domain_detected.value, "general")
        self.assertEqual(response.complexity_score, 1.5)
        self.assertIsNone(response.error)
        self.assertEqual(response.metadata["extra"], "data")
    
    def test_batch_process_response_fields(self):
        """Test BatchProcessResponse fields."""
        results = [
            ProcessExpressionResponse(
                expression=LaTeXExpression(r"\frac{1}{2}"),
                speech_text=SpeechText(value="one half"),
                processing_time_ms=5.0,
                cached=False,
                patterns_applied=1
            )
        ]
        
        response = BatchProcessResponse(
            results=results,
            total_processing_time_ms=20.0,
            successful_count=1,
            failed_count=0,
            metadata={"batch_id": "123"}
        )
        
        self.assertEqual(len(response.results), 1)
        self.assertEqual(response.total_processing_time_ms, 20.0)
        self.assertEqual(response.successful_count, 1)
        self.assertEqual(response.failed_count, 0)
        self.assertEqual(response.metadata["batch_id"], "123")


if __name__ == "__main__":
    unittest.main()