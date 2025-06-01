"""
Standalone integration test for MathTTS v3.
This version runs without pytest dependency.
"""

import asyncio
import tempfile
from pathlib import Path
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
from src.adapters.pattern_loaders import YAMLPatternLoader


logger = get_logger(__name__)


async def create_test_repository():
    """Create and populate a pattern repository."""
    repo = MemoryPatternRepository()
    
    # Add test patterns
    patterns = [
        PatternEntity(
            id="frac_basic",
            name="Basic Fraction",
            pattern=r"\\frac\{(\d+)\}\{(\d+)\}",
            output_template="$1 over $2",
            priority=PatternPriority.high(),
            domain=MathematicalDomain("general"),
            contexts=[PatternContext.ANY],
            description="Basic fraction pattern"
        ),
        PatternEntity(
            id="sqrt_basic", 
            name="Square Root",
            pattern=r"\\sqrt\{([^}]+)\}",
            output_template="square root of $1",
            priority=PatternPriority.high(),
            domain=MathematicalDomain("general"),
            contexts=[PatternContext.ANY],
            description="Basic square root pattern"
        ),
        PatternEntity(
            id="sum_notation",
            name="Summation",
            pattern=r"\\sum_\{([^}]+)\}\^\{([^}]+)\}",
            output_template="sum from $1 to $2 of",
            priority=PatternPriority.critical(),
            domain=MathematicalDomain("calculus"),
            contexts=[PatternContext.ANY],
            description="Summation notation"
        ),
        PatternEntity(
            id="greek_alpha",
            name="Alpha",
            pattern=r"\\alpha",
            output_template="alpha",
            priority=PatternPriority.medium(),
            domain=MathematicalDomain("general"),
            contexts=[PatternContext.ANY],
            description="Greek letter alpha"
        )
    ]
    
    for pattern in patterns:
        await repo.add(pattern)
    
    return repo


async def test_end_to_end_processing():
    """Test complete expression processing flow."""
    print("\n=== Testing End-to-End Processing ===")
    
    # Setup
    repo = await create_test_repository()
    cache = LRUCacheRepository(max_size=100)
    pattern_service = PatternMatchingService(repo)
    use_case = ProcessExpressionUseCase(pattern_service, repo, cache)
    
    # Create request
    latex_expr = LaTeXExpression("\\frac{1}{2} + \\sqrt{x}")
    request = ProcessExpressionRequest(
        expression=latex_expr,
        audience_level=AudienceLevel("undergraduate"),
        domain=MathematicalDomain("general"),
        context="inline"
    )
    
    # Execute processing
    response = await use_case.execute(request)
    
    # Verify response
    print(f"Input: {latex_expr.content}")
    print(f"Output: {response.speech_text.value}")
    print(f"Processing time: {response.processing_time_ms:.2f}ms")
    print(f"Cached: {response.cached}")
    print(f"Patterns applied: {response.patterns_applied}")
    
    assert response.speech_text.value == "1 over 2 + square root of x"
    assert response.processing_time_ms > 0
    assert response.cached is False
    assert response.patterns_applied == 2
    
    print("✓ End-to-end processing test passed")


async def test_caching_behavior():
    """Test that caching works correctly."""
    print("\n=== Testing Caching Behavior ===")
    
    # Setup
    repo = await create_test_repository()
    cache = LRUCacheRepository(max_size=100)
    pattern_service = PatternMatchingService(repo)
    use_case = ProcessExpressionUseCase(pattern_service, repo, cache)
    
    # Create request
    latex_expr = LaTeXExpression("\\alpha + \\beta")
    request = ProcessExpressionRequest(
        expression=latex_expr,
        audience_level=AudienceLevel("undergraduate")
    )
    
    # First execution (cache miss)
    response1 = await use_case.execute(request)
    print(f"First execution - Cached: {response1.cached}, Time: {response1.processing_time_ms:.2f}ms")
    
    # Second execution (cache hit)
    response2 = await use_case.execute(request)
    print(f"Second execution - Cached: {response2.cached}, Time: {response2.processing_time_ms:.2f}ms")
    
    assert response1.cached is False
    assert response2.cached is True
    assert response2.speech_text.value == response1.speech_text.value
    assert response2.processing_time_ms < response1.processing_time_ms
    
    print("✓ Caching behavior test passed")


async def test_batch_processing():
    """Test batch processing of multiple expressions."""
    print("\n=== Testing Batch Processing ===")
    
    # Setup
    repo = await create_test_repository()
    cache = LRUCacheRepository(max_size=100)
    pattern_service = PatternMatchingService(repo)
    use_case = ProcessExpressionUseCase(pattern_service, repo, cache)
    
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
    batch_response = await use_case.execute_batch(batch_request)
    
    print(f"Batch size: {len(requests)}")
    print(f"Successful: {batch_response.successful_count}")
    print(f"Failed: {batch_response.failed_count}")
    print(f"Total time: {batch_response.total_processing_time_ms:.2f}ms")
    
    for i, result in enumerate(batch_response.results):
        print(f"  Result {i+1}: {result.speech_text.value}")
    
    assert batch_response.successful_count == 3
    assert batch_response.failed_count == 0
    
    print("✓ Batch processing test passed")


async def test_security_validation():
    """Test security validation in LaTeX expressions."""
    print("\n=== Testing Security Validation ===")
    
    # Test dangerous commands
    dangerous_expressions = [
        "\\input{/etc/passwd}",
        "\\write18{rm -rf /}",
        "\\def\\x{\\x}\\x",
        "\\csname @gobble\\endcsname",
        "\\catcode`\\@=11"
    ]
    
    for expr in dangerous_expressions:
        try:
            LaTeXExpression(expr)
            print(f"✗ FAILED: {expr} should have been rejected")
            assert False
        except Exception as e:
            print(f"✓ Correctly rejected: {expr}")
            print(f"  Reason: {str(e)[:60]}...")
    
    # Test valid expressions
    valid_expressions = [
        "\\frac{1}{2}",
        "\\sqrt{x^2 + y^2}",
        "\\int_{0}^{\\infty} e^{-x} dx",
        "\\sum_{n=1}^{\\infty} \\frac{1}{n^2}"
    ]
    
    for expr in valid_expressions:
        try:
            latex_expr = LaTeXExpression(expr)
            print(f"✓ Correctly accepted: {expr}")
        except Exception as e:
            print(f"✗ FAILED: {expr} should have been accepted")
            print(f"  Error: {e}")
            assert False
    
    print("✓ Security validation test passed")


async def test_yaml_pattern_loading():
    """Test YAML pattern loading functionality."""
    print("\n=== Testing YAML Pattern Loading ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
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
        
        yaml_file = Path(tmpdir) / "test_patterns.yaml"
        yaml_file.write_text(yaml_content)
        
        # Load patterns
        loader = YAMLPatternLoader(patterns_dir=Path(tmpdir))
        patterns = await loader.load_patterns()
        
        print(f"Loaded {len(patterns)} patterns from YAML")
        for pattern in patterns:
            print(f"  - {pattern.id}: {pattern.pattern} → {pattern.output_template}")
        
        assert len(patterns) == 2
        assert patterns[0].id == "test_pattern_1"
        assert patterns[1].id == "test_pattern_2"
        
        print("✓ YAML pattern loading test passed")


async def test_full_system_workflow():
    """Test complete system workflow from YAML loading to speech output."""
    print("\n=== Testing Full System Workflow ===")
    
    # Create temporary directory for patterns
    with tempfile.TemporaryDirectory() as tmpdir:
        patterns_dir = Path(tmpdir)
        
        # Create pattern file
        pattern_file = patterns_dir / "math_patterns.yaml"
        pattern_file.write_text("""
patterns:
  - pattern:
      id: fraction_to_speech
      pattern: "\\\\frac\\{([^}]+)\\}\\{([^}]+)\\}"
      output_template: "$1 divided by $2"
      priority: 1000
      domain: general
      contexts: ["inline", "display"]
  - pattern:
      id: power_to_speech
      pattern: "([a-zA-Z0-9]+)\\^\\{([^}]+)\\}"
      output_template: "$1 to the power of $2"
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
        
        print(f"Expression: {expr.content}")
        print(f"Speech output: {response.speech_text.value}")
        print(f"Patterns applied: {response.patterns_applied}")
        print(f"Processing time: {response.processing_time_ms:.2f}ms")
        
        assert response.speech_text is not None
        assert response.patterns_applied > 0
        
        print("✓ Full system workflow test passed")


async def run_all_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("MathTTS v3 Integration Tests")
    print("=" * 60)
    
    tests = [
        test_end_to_end_processing,
        test_caching_behavior,
        test_batch_processing,
        test_security_validation,
        test_yaml_pattern_loading,
        test_full_system_workflow
    ]
    
    failed = 0
    for test in tests:
        try:
            await test()
        except Exception as e:
            print(f"\n✗ Test {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Tests completed: {len(tests) - failed}/{len(tests)} passed")
    if failed == 0:
        print("All tests passed! ✨")
    else:
        print(f"{failed} tests failed ❌")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)