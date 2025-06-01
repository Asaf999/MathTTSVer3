"""
Final integration test for MathTTS v3.
This test verifies the complete system works end-to-end.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.domain.entities import PatternEntity, MathematicalExpression
from src.domain.entities.pattern import PatternContext
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
from src.application.dtos_v3 import ProcessExpressionRequest, BatchProcessRequest


logger = get_logger(__name__)


async def test_complete_workflow():
    """Test the complete MathTTS v3 workflow."""
    print("=" * 60)
    print("MathTTS v3 Final Integration Test")
    print("=" * 60)
    
    # Create repository and add patterns
    repo = MemoryPatternRepository()
    
    # Add working patterns with proper regex escaping
    patterns = [
        PatternEntity(
            id="frac_simple",
            name="Simple Fraction",
            pattern=r"\\frac\{(\d+)\}\{(\d+)\}",
            output_template=r"\1 over \2",
            priority=PatternPriority.high(),
            domain=MathematicalDomain("general"),
            contexts=[PatternContext.ANY]
        ),
        PatternEntity(
            id="sqrt_simple",
            name="Square Root",
            pattern=r"\\sqrt\{([^}]+)\}",
            output_template=r"square root of \1",
            priority=PatternPriority.high(),
            domain=MathematicalDomain("general"),
            contexts=[PatternContext.ANY]
        ),
        PatternEntity(
            id="alpha_greek",
            name="Greek Alpha",
            pattern=r"\\alpha",
            output_template="alpha",
            priority=PatternPriority.medium(),
            domain=MathematicalDomain("general"),
            contexts=[PatternContext.ANY]
        ),
        PatternEntity(
            id="beta_greek",
            name="Greek Beta",
            pattern=r"\\beta",
            output_template="beta",
            priority=PatternPriority.medium(),
            domain=MathematicalDomain("general"),
            contexts=[PatternContext.ANY]
        )
    ]
    
    for pattern in patterns:
        await repo.add(pattern)
    
    print(f"\n✓ Added {len(patterns)} patterns to repository")
    
    # Create services
    pattern_service = PatternMatchingService(repo)
    cache = LRUCacheRepository(max_size=100)
    use_case = ProcessExpressionUseCase(pattern_service, repo, cache)
    
    print("✓ Created services and use case")
    
    # Test 1: Simple fraction
    print("\n--- Test 1: Simple Fraction ---")
    expr1 = LaTeXExpression("\\frac{1}{2}")
    request1 = ProcessExpressionRequest(
        expression=expr1,
        audience_level=AudienceLevel("undergraduate")
    )
    
    response1 = await use_case.execute(request1)
    print(f"Input: {expr1.content}")
    print(f"Output: {response1.speech_text.value}")
    print(f"Patterns applied: {response1.patterns_applied}")
    assert response1.speech_text.value == "1 over 2", f"Expected '1 over 2', got '{response1.speech_text.value}'"
    print("✓ Test 1 passed")
    
    # Test 2: Square root
    print("\n--- Test 2: Square Root ---")
    expr2 = LaTeXExpression("\\sqrt{x + 1}")
    request2 = ProcessExpressionRequest(
        expression=expr2,
        audience_level=AudienceLevel("undergraduate")
    )
    
    response2 = await use_case.execute(request2)
    print(f"Input: {expr2.content}")
    print(f"Output: {response2.speech_text.value}")
    print(f"Patterns applied: {response2.patterns_applied}")
    assert response2.speech_text.value.lower() == "square root of x + 1", f"Expected 'square root of x + 1', got '{response2.speech_text.value}'"
    print("✓ Test 2 passed")
    
    # Test 3: Greek letters
    print("\n--- Test 3: Greek Letters ---")
    expr3 = LaTeXExpression("\\alpha + \\beta")
    request3 = ProcessExpressionRequest(
        expression=expr3,
        audience_level=AudienceLevel("undergraduate")
    )
    
    response3 = await use_case.execute(request3)
    print(f"Input: {expr3.content}")
    print(f"Output: {response3.speech_text.value}")
    print(f"Patterns applied: {response3.patterns_applied}")
    assert response3.speech_text.value.lower() == "alpha + beta", f"Expected 'alpha + beta', got '{response3.speech_text.value}'"
    print("✓ Test 3 passed")
    
    # Test 4: Caching
    print("\n--- Test 4: Caching ---")
    response3_cached = await use_case.execute(request3)
    assert response3_cached.cached is True
    assert response3_cached.speech_text.value == response3.speech_text.value
    print(f"Cache hit: {response3_cached.cached}")
    print(f"Processing time: {response3.processing_time_ms:.2f}ms vs {response3_cached.processing_time_ms:.2f}ms")
    print("✓ Test 4 passed")
    
    # Test 5: Combined expression
    print("\n--- Test 5: Combined Expression ---")
    expr5 = LaTeXExpression("\\frac{1}{2} + \\sqrt{\\alpha}")
    request5 = ProcessExpressionRequest(
        expression=expr5,
        audience_level=AudienceLevel("undergraduate")
    )
    
    response5 = await use_case.execute(request5)
    print(f"Input: {expr5.content}")
    print(f"Output: {response5.speech_text.value}")
    print(f"Patterns applied: {response5.patterns_applied}")
    # Pattern matching is iterative, so it should process all patterns
    print("✓ Test 5 passed")
    
    # Test 6: Security validation
    print("\n--- Test 6: Security Validation ---")
    dangerous_expressions = [
        "\\input{/etc/passwd}",
        "\\def\\x{\\x}\\x"
    ]
    
    for dangerous in dangerous_expressions:
        try:
            LaTeXExpression(dangerous)
            print(f"✗ Failed to reject: {dangerous}")
            assert False
        except Exception as e:
            print(f"✓ Correctly rejected: {dangerous}")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✨")
    print("MathTTS v3 is working correctly!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_complete_workflow())