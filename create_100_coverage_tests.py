#!/usr/bin/env python3
"""
Script to create comprehensive unit tests for 100% coverage.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def create_test_file(module_path: str, test_content: str):
    """Create a test file for a module."""
    # Convert module path to test path
    test_path = module_path.replace('src/', 'tests/unit/').replace('.py', '_test.py')
    
    # Create directory if needed
    os.makedirs(os.path.dirname(test_path), exist_ok=True)
    
    # Write test file
    with open(test_path, 'w') as f:
        f.write(test_content)
    
    print(f"Created test: {test_path}")

def main():
    """Create all test files."""
    
    # Test for domain/value_objects.py
    test_content = '''"""
Unit tests for domain value objects.
"""
import pytest
from datetime import datetime
from src.domain.value_objects import (
    LaTeXExpression, SpeechText, PatternPriority, 
    AudienceLevel, MathematicalDomain
)
from src.domain.exceptions import ValidationError, LaTeXValidationError, SecurityError


class TestLaTeXExpression:
    """Test LaTeXExpression value object."""
    
    def test_valid_expression(self):
        """Test creating valid LaTeX expression."""
        expr = LaTeXExpression(r"\\frac{1}{2}")
        assert expr.content == r"\\frac{1}{2}"
        assert "frac" in expr.commands
    
    def test_empty_expression_raises_error(self):
        """Test empty expression raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            LaTeXExpression("")
    
    def test_non_string_raises_error(self):
        """Test non-string input raises error."""
        with pytest.raises(ValueError, match="must be a string"):
            LaTeXExpression(123)
    
    def test_too_long_expression(self):
        """Test expression exceeding max length."""
        long_expr = "x" * 10001
        with pytest.raises(ValueError, match="exceeds maximum length"):
            LaTeXExpression(long_expr)
    
    def test_null_byte_raises_error(self):
        """Test null byte in expression."""
        with pytest.raises(ValueError, match="Null bytes not allowed"):
            LaTeXExpression("x\\x00y")
    
    def test_unbalanced_braces(self):
        """Test unbalanced braces."""
        with pytest.raises(LaTeXValidationError, match="Unbalanced braces"):
            LaTeXExpression("\\\\frac{1}{2")
    
    def test_unbalanced_brackets(self):
        """Test unbalanced brackets."""
        with pytest.raises(LaTeXValidationError, match="Unbalanced brackets"):
            LaTeXExpression("[1, 2")
    
    def test_unbalanced_parentheses(self):
        """Test unbalanced parentheses."""
        with pytest.raises(LaTeXValidationError, match="Unbalanced parentheses"):
            LaTeXExpression("(1 + 2")
    
    def test_improper_brace_nesting(self):
        """Test improper nesting of braces."""
        with pytest.raises(LaTeXValidationError, match="Closing brace without matching"):
            LaTeXExpression("}{")
    
    def test_max_nesting_depth(self):
        """Test max nesting depth validation."""
        deep_expr = "{" * 21 + "x" + "}" * 21
        with pytest.raises(LaTeXValidationError, match="too deeply nested"):
            LaTeXExpression(deep_expr)
    
    def test_dangerous_commands(self):
        """Test dangerous command detection."""
        dangerous_commands = [
            r"\\input{file}",
            r"\\include{file}",
            r"\\write{file}",
            r"\\def\\cmd{}"
        ]
        for cmd in dangerous_commands:
            with pytest.raises(SecurityError, match="dangerous LaTeX command"):
                LaTeXExpression(cmd)
    
    def test_excessive_repetition(self):
        """Test excessive character repetition."""
        with pytest.raises(SecurityError, match="Excessive repetition"):
            LaTeXExpression("{" * 1001)
    
    def test_long_command_name(self):
        """Test excessively long command names."""
        long_cmd = r"\\" + "a" * 51
        with pytest.raises(SecurityError, match="Excessively long command"):
            LaTeXExpression(long_cmd)
    
    def test_disallowed_command(self):
        """Test disallowed command."""
        with pytest.raises(SecurityError, match="Disallowed LaTeX command"):
            LaTeXExpression(r"\\notallowed{}")
    
    def test_extract_commands(self):
        """Test command extraction."""
        expr = LaTeXExpression(r"\\frac{\\alpha}{\\beta}")
        assert expr.commands == {"frac", "alpha", "beta"}
    
    def test_extract_variables(self):
        """Test variable extraction."""
        expr = LaTeXExpression(r"x + y = z")
        assert expr.variables == {"x", "y", "z"}
    
    def test_complexity_score(self):
        """Test complexity score calculation."""
        simple = LaTeXExpression("x")
        assert 0 <= simple.complexity_score <= 10
        
        complex_expr = LaTeXExpression(r"\\int_0^1 \\frac{\\sin(x)}{x} dx")
        assert simple.complexity_score < complex_expr.complexity_score
    
    def test_sanitize(self):
        """Test expression sanitization."""
        expr = LaTeXExpression("x + y % comment\\n  z")
        sanitized = expr.sanitize()
        assert "comment" not in sanitized
        assert "  " not in sanitized
    
    def test_str_representation(self):
        """Test string representation."""
        short = LaTeXExpression("x + y")
        assert str(short) == "x + y"
        
        long_expr = LaTeXExpression("x" * 100)
        assert str(long_expr).endswith("...")
        assert len(str(long_expr)) == 50


class TestSpeechText:
    """Test SpeechText value object."""
    
    def test_valid_speech_text(self):
        """Test creating valid speech text."""
        text = SpeechText("Hello world")
        assert text.value == "Hello world"
    
    def test_empty_text_raises_error(self):
        """Test empty text raises error."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            SpeechText("")
    
    def test_with_ssml(self):
        """Test creating new instance with SSML."""
        text = SpeechText("Hello")
        with_ssml = text.with_ssml("<speak>Hello</speak>")
        assert with_ssml.ssml == "<speak>Hello</speak>"
        assert with_ssml.value == "Hello"
        assert text.ssml is None  # Original unchanged
    
    def test_with_hint(self):
        """Test adding pronunciation hints."""
        text = SpeechText("Hello")
        with_hint = text.with_hint("emphasis", "strong")
        assert with_hint.pronunciation_hints["emphasis"] == "strong"
        assert text.pronunciation_hints == {}  # Original unchanged


class TestPatternPriority:
    """Test PatternPriority value object."""
    
    def test_valid_priority(self):
        """Test creating valid priority."""
        priority = PatternPriority(1000)
        assert priority.value == 1000
    
    def test_priority_bounds(self):
        """Test priority bounds validation."""
        with pytest.raises(ValidationError):
            PatternPriority(-1)
        
        with pytest.raises(ValidationError):
            PatternPriority(2001)
    
    def test_priority_comparison(self):
        """Test priority comparison."""
        low = PatternPriority(100)
        high = PatternPriority(1000)
        assert low < high
        assert low <= high
        assert not (high < low)
    
    def test_factory_methods(self):
        """Test priority factory methods."""
        assert PatternPriority.critical().value == 1500
        assert PatternPriority.high().value == 1000
        assert PatternPriority.medium().value == 500
        assert PatternPriority.low().value == 250


class TestAudienceLevel:
    """Test AudienceLevel value object."""
    
    def test_valid_levels(self):
        """Test valid audience levels."""
        levels = ["elementary", "high_school", "undergraduate", "graduate", "research"]
        for level in levels:
            audience = AudienceLevel(level)
            assert audience.value == level
    
    def test_invalid_level(self):
        """Test invalid audience level."""
        with pytest.raises(ValidationError, match="Invalid audience level"):
            AudienceLevel("invalid")
    
    def test_is_advanced(self):
        """Test advanced level check."""
        assert AudienceLevel("graduate").is_advanced
        assert AudienceLevel("research").is_advanced
        assert not AudienceLevel("undergraduate").is_advanced
    
    def test_is_basic(self):
        """Test basic level check."""
        assert AudienceLevel("elementary").is_basic
        assert AudienceLevel("high_school").is_basic
        assert not AudienceLevel("undergraduate").is_basic


class TestMathematicalDomain:
    """Test MathematicalDomain value object."""
    
    def test_valid_domains(self):
        """Test valid mathematical domains."""
        domains = ["algebra", "calculus", "statistics", "logic"]
        for domain in domains:
            math_domain = MathematicalDomain(domain)
            assert math_domain.value == domain
    
    def test_invalid_domain(self):
        """Test invalid domain."""
        with pytest.raises(ValidationError, match="Invalid mathematical domain"):
            MathematicalDomain("invalid")
    
    def test_general_domain(self):
        """Test general domain factory."""
        general = MathematicalDomain.general()
        assert general.value == "general"
    
    def test_is_analysis_related(self):
        """Test analysis-related domain check."""
        assert MathematicalDomain("calculus").is_analysis_related()
        assert MathematicalDomain("real_analysis").is_analysis_related()
        assert not MathematicalDomain("algebra").is_analysis_related()
'''
    create_test_file('src/domain/value_objects.py', test_content)
    
    # Test for domain/entities.py
    test_content = '''"""
Unit tests for domain entities.
"""
import pytest
from datetime import datetime
from src.domain.entities import PatternEntity, ConversionRecord
from src.domain.value_objects import PatternPriority


class TestPatternEntity:
    """Test PatternEntity."""
    
    def test_valid_pattern(self):
        """Test creating valid pattern."""
        pattern = PatternEntity(
            id="test-1",
            name="Test Pattern",
            pattern=r"\\\\frac\\{(.+?)\\}\\{(.+?)\\}",
            output_template="\\\\1 over \\\\2"
        )
        assert pattern.id == "test-1"
        assert pattern.name == "Test Pattern"
    
    def test_empty_id_raises_error(self):
        """Test empty ID raises error."""
        with pytest.raises(ValueError, match="ID cannot be empty"):
            PatternEntity(
                id="",
                name="Test",
                pattern="test",
                output_template="test"
            )
    
    def test_empty_name_raises_error(self):
        """Test empty name raises error."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            PatternEntity(
                id="test",
                name="",
                pattern="test",
                output_template="test"
            )
    
    def test_empty_pattern_raises_error(self):
        """Test empty pattern raises error."""
        with pytest.raises(ValueError, match="regex cannot be empty"):
            PatternEntity(
                id="test",
                name="Test",
                pattern="",
                output_template="test"
            )
    
    def test_empty_output_raises_error(self):
        """Test empty output template raises error."""
        with pytest.raises(ValueError, match="Output template cannot be empty"):
            PatternEntity(
                id="test",
                name="Test",
                pattern="test",
                output_template=""
            )
    
    def test_equality(self):
        """Test pattern equality."""
        p1 = PatternEntity(
            id="test-1",
            name="Test",
            pattern="test",
            output_template="test"
        )
        p2 = PatternEntity(
            id="test-1",
            name="Different",
            pattern="different",
            output_template="different"
        )
        p3 = PatternEntity(
            id="test-2",
            name="Test",
            pattern="test",
            output_template="test"
        )
        
        assert p1 == p2  # Same ID
        assert p1 != p3  # Different ID
        assert p1 != "not a pattern"
    
    def test_hash(self):
        """Test pattern hashing."""
        p1 = PatternEntity(
            id="test-1",
            name="Test",
            pattern="test",
            output_template="test"
        )
        p2 = PatternEntity(
            id="test-1",
            name="Different",
            pattern="test",
            output_template="test"
        )
        
        assert hash(p1) == hash(p2)  # Same ID
    
    def test_str_representation(self):
        """Test string representation."""
        pattern = PatternEntity(
            id="test-1",
            name="Test Pattern",
            pattern="test",
            output_template="test"
        )
        str_repr = str(pattern)
        assert "test-1" in str_repr
        assert "Test Pattern" in str_repr
    
    def test_update(self):
        """Test pattern update."""
        original = PatternEntity(
            id="test-1",
            name="Original",
            pattern="test",
            output_template="test"
        )
        
        updated = original.update(name="Updated", description="New desc")
        
        assert updated.name == "Updated"
        assert updated.description == "New desc"
        assert updated.id == original.id  # ID unchanged
        assert original.name == "Original"  # Original unchanged
    
    def test_priority_checks(self):
        """Test priority checking methods."""
        low = PatternEntity(
            id="low",
            name="Low",
            pattern="test",
            output_template="test",
            priority=PatternPriority(100)
        )
        high = PatternEntity(
            id="high",
            name="High",
            pattern="test",
            output_template="test",
            priority=PatternPriority(1200)
        )
        critical = PatternEntity(
            id="critical",
            name="Critical",
            pattern="test",
            output_template="test",
            priority=PatternPriority(1600)
        )
        
        assert not low.is_high_priority
        assert not low.is_critical
        assert high.is_high_priority
        assert not high.is_critical
        assert critical.is_high_priority
        assert critical.is_critical
    
    def test_matches_domain(self):
        """Test domain matching."""
        pattern = PatternEntity(
            id="test",
            name="Test",
            pattern="test",
            output_template="test",
            domain="calculus"
        )
        
        assert pattern.matches_domain("calculus")
        assert pattern.matches_domain("general")
        assert not pattern.matches_domain("algebra")
    
    def test_tag_operations(self):
        """Test tag operations."""
        pattern = PatternEntity(
            id="test",
            name="Test",
            pattern="test",
            output_template="test",
            tags=["math", "basic"]
        )
        
        assert pattern.has_tag("math")
        assert not pattern.has_tag("advanced")
        
        # Add tag
        with_tag = pattern.add_tag("advanced")
        assert with_tag.has_tag("advanced")
        assert not pattern.has_tag("advanced")  # Original unchanged
        
        # Add existing tag (no change)
        same = with_tag.add_tag("advanced")
        assert same == with_tag
        
        # Remove tag
        without = with_tag.remove_tag("basic")
        assert not without.has_tag("basic")
        assert with_tag.has_tag("basic")  # Original unchanged
        
        # Remove non-existing tag (no change)
        same2 = without.remove_tag("nonexistent")
        assert same2 == without


class TestConversionRecord:
    """Test ConversionRecord."""
    
    def test_valid_record(self):
        """Test creating valid conversion record."""
        record = ConversionRecord(
            latex_input="\\\\frac{1}{2}",
            speech_output="one half"
        )
        assert record.latex_input == "\\\\frac{1}{2}"
        assert record.speech_output == "one half"
        assert record.id  # Auto-generated
    
    def test_empty_input_raises_error(self):
        """Test empty input raises error."""
        with pytest.raises(ValueError, match="LaTeX input cannot be empty"):
            ConversionRecord(latex_input="")
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        record = ConversionRecord(
            latex_input="\\\\frac{1}{2}",
            speech_output="one half",
            voice_id="voice-1",
            format="wav",
            metadata={"rate": 1.5, "pitch": 0.8}
        )
        
        cache_key = record.cache_key
        assert "\\\\frac{1}{2}" in cache_key
        assert "voice-1" in cache_key
        assert "wav" in cache_key
        assert "1.5" in cache_key
        assert "0.8" in cache_key
    
    def test_mark_as_cached(self):
        """Test marking record as cached."""
        record = ConversionRecord(
            latex_input="\\\\frac{1}{2}",
            speech_output="one half",
            cached=False
        )
        
        cached = record.mark_as_cached()
        assert cached.cached
        assert not record.cached  # Original unchanged
        assert cached.id == record.id
        assert cached.latex_input == record.latex_input
'''
    create_test_file('src/domain/entities.py', test_content)
    
    # Test for domain/services/pattern_matching_service.py
    test_content = '''"""
Unit tests for pattern matching service.
"""
import pytest
from unittest.mock import Mock, MagicMock
from src.domain.services.pattern_matching_service import PatternMatchingService
from src.domain.entities import PatternEntity
from src.domain.value_objects import PatternPriority, LaTeXExpression, SpeechText


class TestPatternMatchingService:
    """Test PatternMatchingService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create mock pattern repository."""
        repo = Mock()
        repo.get_all.return_value = [
            PatternEntity(
                id="frac-1",
                name="Fraction",
                pattern=r"\\\\frac\\{(.+?)\\}\\{(.+?)\\}",
                output_template="\\\\1 over \\\\2",
                priority=PatternPriority(1000)
            ),
            PatternEntity(
                id="sqrt-1",
                name="Square Root",
                pattern=r"\\\\sqrt\\{(.+?)\\}",
                output_template="square root of \\\\1",
                priority=PatternPriority(900)
            ),
            PatternEntity(
                id="simple-1",
                name="Simple",
                pattern=r"x",
                output_template="x",
                priority=PatternPriority(100)
            )
        ]
        return repo
    
    @pytest.fixture
    def service(self, mock_repository):
        """Create pattern matching service."""
        return PatternMatchingService(mock_repository)
    
    def test_find_matching_patterns(self, service):
        """Test finding matching patterns."""
        expr = LaTeXExpression(r"\\\\frac{1}{2}")
        
        matches = service.find_matching_patterns(expr)
        
        assert len(matches) == 1
        assert matches[0].id == "frac-1"
    
    def test_find_multiple_matches(self, service):
        """Test finding multiple matching patterns."""
        expr = LaTeXExpression(r"x")
        
        matches = service.find_matching_patterns(expr)
        
        assert len(matches) == 1
        assert matches[0].id == "simple-1"
    
    def test_no_matches(self, service):
        """Test when no patterns match."""
        expr = LaTeXExpression(r"\\\\unknown{}")
        
        matches = service.find_matching_patterns(expr)
        
        assert len(matches) == 0
    
    def test_apply_pattern(self, service, mock_repository):
        """Test applying a pattern."""
        pattern = mock_repository.get_all()[0]  # Fraction pattern
        expr = LaTeXExpression(r"\\\\frac{1}{2}")
        
        result = service.apply_pattern(pattern, expr)
        
        assert isinstance(result, SpeechText)
        assert result.value == "1 over 2"
    
    def test_apply_pattern_with_groups(self, service):
        """Test applying pattern with multiple groups."""
        pattern = PatternEntity(
            id="test",
            name="Test",
            pattern=r"(\\\\w+)\\s*=\\s*(\\\\d+)",
            output_template="\\\\1 equals \\\\2",
            priority=PatternPriority(500)
        )
        expr = LaTeXExpression(r"x = 5")
        
        result = service.apply_pattern(pattern, expr)
        
        assert result.value == "x equals 5"
    
    def test_apply_pattern_no_match(self, service):
        """Test applying pattern that doesn't match."""
        pattern = PatternEntity(
            id="test",
            name="Test",
            pattern=r"\\\\frac",
            output_template="fraction",
            priority=PatternPriority(500)
        )
        expr = LaTeXExpression(r"\\\\sqrt{4}")
        
        result = service.apply_pattern(pattern, expr)
        
        assert result is None
    
    def test_convert_expression(self, service, mock_repository):
        """Test converting full expression."""
        expr = LaTeXExpression(r"\\\\frac{1}{2}")
        
        result = service.convert_expression(expr)
        
        assert isinstance(result, SpeechText)
        assert result.value == "1 over 2"
    
    def test_convert_expression_fallback(self, service):
        """Test fallback when no patterns match."""
        expr = LaTeXExpression(r"\\\\unknown{}")
        
        result = service.convert_expression(expr)
        
        assert result.value == r"\\\\unknown{}"
    
    def test_priority_ordering(self, service, mock_repository):
        """Test patterns are tried in priority order."""
        # Add a higher priority pattern that also matches
        high_priority = PatternEntity(
            id="frac-high",
            name="High Priority Fraction",
            pattern=r"\\\\frac\\{1\\}\\{2\\}",
            output_template="one half",
            priority=PatternPriority(1500)
        )
        
        patterns = mock_repository.get_all()
        patterns.append(high_priority)
        mock_repository.get_all.return_value = patterns
        
        expr = LaTeXExpression(r"\\\\frac{1}{2}")
        result = service.convert_expression(expr)
        
        assert result.value == "one half"  # High priority pattern used
    
    def test_domain_filtering(self, service, mock_repository):
        """Test filtering patterns by domain."""
        calculus_pattern = PatternEntity(
            id="calc-1",
            name="Calculus",
            pattern=r"\\\\int",
            output_template="integral",
            domain="calculus",
            priority=PatternPriority(1000)
        )
        
        patterns = mock_repository.get_all()
        patterns.append(calculus_pattern)
        mock_repository.get_all.return_value = patterns
        
        expr = LaTeXExpression(r"\\\\int")
        
        # Test with domain filter
        matches = service.find_matching_patterns(expr, domain="calculus")
        assert any(p.id == "calc-1" for p in matches)
        
        # Test with different domain
        matches = service.find_matching_patterns(expr, domain="algebra")
        assert not any(p.id == "calc-1" for p in matches)
    
    def test_context_filtering(self, service, mock_repository):
        """Test filtering patterns by context."""
        inline_pattern = PatternEntity(
            id="inline-1",
            name="Inline",
            pattern=r"x",
            output_template="x inline",
            metadata={"contexts": ["inline"]},
            priority=PatternPriority(1000)
        )
        
        patterns = mock_repository.get_all()
        patterns.append(inline_pattern)
        mock_repository.get_all.return_value = patterns
        
        expr = LaTeXExpression(r"x")
        
        # Test with context filter
        matches = service.find_matching_patterns(expr, context="inline")
        assert any(p.id == "inline-1" for p in matches)
        
        # Test with different context
        matches = service.find_matching_patterns(expr, context="display")
        assert not any(p.id == "inline-1" for p in matches)
    
    def test_caching(self, service, mock_repository):
        """Test pattern caching."""
        expr = LaTeXExpression(r"\\\\frac{1}{2}")
        
        # First call
        result1 = service.convert_expression(expr)
        
        # Second call - should use cache
        result2 = service.convert_expression(expr)
        
        assert result1.value == result2.value
        # Repository should only be called once due to caching
        mock_repository.get_all.assert_called_once()
'''
    create_test_file('src/domain/services/pattern_matching_service.py', test_content)
    
    # Create more test files...
    print("\nCreating comprehensive tests for all modules...")
    
    # Test for application layer
    test_content = '''"""
Unit tests for application use cases.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from src.application.use_cases.process_expression import (
    ProcessExpressionUseCase,
    ProcessExpressionRequest,
    ProcessExpressionResponse
)
from src.domain.value_objects import LaTeXExpression, SpeechText
from src.domain.services.pattern_matching_service import PatternMatchingService


class TestProcessExpressionUseCase:
    """Test ProcessExpressionUseCase."""
    
    @pytest.fixture
    def mock_pattern_service(self):
        """Create mock pattern matching service."""
        service = Mock(spec=PatternMatchingService)
        service.convert_expression.return_value = SpeechText("one half")
        return service
    
    @pytest.fixture
    def mock_tts_service(self):
        """Create mock TTS service."""
        service = AsyncMock()
        service.synthesize.return_value = b"audio_data"
        return service
    
    @pytest.fixture
    def use_case(self, mock_pattern_service, mock_tts_service):
        """Create use case."""
        return ProcessExpressionUseCase(
            pattern_service=mock_pattern_service,
            tts_service=mock_tts_service
        )
    
    @pytest.mark.asyncio
    async def test_process_expression(self, use_case):
        """Test processing expression."""
        request = ProcessExpressionRequest(
            latex=r"\\\\frac{1}{2}",
            voice_id="voice-1",
            format="mp3"
        )
        
        response = await use_case.execute(request)
        
        assert isinstance(response, ProcessExpressionResponse)
        assert response.speech_text == "one half"
        assert response.audio_data == b"audio_data"
        assert response.format == "mp3"
    
    @pytest.mark.asyncio
    async def test_process_with_options(self, use_case):
        """Test processing with additional options."""
        request = ProcessExpressionRequest(
            latex=r"\\\\frac{1}{2}",
            voice_id="voice-1",
            format="wav",
            rate=1.5,
            pitch=0.8
        )
        
        response = await use_case.execute(request)
        
        assert response.format == "wav"
    
    @pytest.mark.asyncio
    async def test_process_invalid_latex(self, use_case, mock_pattern_service):
        """Test processing invalid LaTeX."""
        mock_pattern_service.convert_expression.side_effect = ValueError("Invalid LaTeX")
        
        request = ProcessExpressionRequest(
            latex="invalid{",
            voice_id="voice-1"
        )
        
        with pytest.raises(ValueError):
            await use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_tts_failure(self, use_case, mock_tts_service):
        """Test TTS synthesis failure."""
        mock_tts_service.synthesize.side_effect = Exception("TTS error")
        
        request = ProcessExpressionRequest(
            latex=r"\\\\frac{1}{2}",
            voice_id="voice-1"
        )
        
        with pytest.raises(Exception, match="TTS error"):
            await use_case.execute(request)
'''
    create_test_file('src/application/use_cases/process_expression.py', test_content)
    
    # Test for infrastructure auth
    test_content = '''"""
Unit tests for authentication infrastructure.
"""
import pytest
from datetime import datetime, timedelta
from jose import jwt
from src.infrastructure.auth.jwt_manager import JWTManager
from src.infrastructure.auth.models import User, TokenData


class TestJWTManager:
    """Test JWTManager."""
    
    @pytest.fixture
    def jwt_manager(self):
        """Create JWT manager."""
        return JWTManager(
            secret_key="test_secret",
            algorithm="HS256",
            access_token_expire_minutes=30
        )
    
    def test_create_access_token(self, jwt_manager):
        """Test creating access token."""
        user = User(
            id="user-1",
            username="testuser",
            email="test@example.com"
        )
        
        token = jwt_manager.create_access_token(user)
        
        assert isinstance(token, str)
        
        # Decode and verify
        payload = jwt.decode(
            token,
            "test_secret",
            algorithms=["HS256"]
        )
        assert payload["sub"] == "user-1"
        assert payload["username"] == "testuser"
    
    def test_create_refresh_token(self, jwt_manager):
        """Test creating refresh token."""
        user = User(
            id="user-1",
            username="testuser",
            email="test@example.com"
        )
        
        token = jwt_manager.create_refresh_token(user)
        
        assert isinstance(token, str)
        
        # Decode and verify
        payload = jwt.decode(
            token,
            "test_secret",
            algorithms=["HS256"]
        )
        assert payload["sub"] == "user-1"
        assert payload["type"] == "refresh"
    
    def test_verify_token(self, jwt_manager):
        """Test verifying valid token."""
        user = User(
            id="user-1",
            username="testuser",
            email="test@example.com"
        )
        
        token = jwt_manager.create_access_token(user)
        token_data = jwt_manager.verify_token(token)
        
        assert isinstance(token_data, TokenData)
        assert token_data.user_id == "user-1"
        assert token_data.username == "testuser"
    
    def test_verify_expired_token(self, jwt_manager):
        """Test verifying expired token."""
        # Create token with past expiration
        payload = {
            "sub": "user-1",
            "username": "testuser",
            "exp": datetime.utcnow() - timedelta(minutes=1)
        }
        
        expired_token = jwt.encode(
            payload,
            "test_secret",
            algorithm="HS256"
        )
        
        with pytest.raises(Exception):
            jwt_manager.verify_token(expired_token)
    
    def test_verify_invalid_token(self, jwt_manager):
        """Test verifying invalid token."""
        with pytest.raises(Exception):
            jwt_manager.verify_token("invalid_token")
    
    def test_verify_wrong_secret(self, jwt_manager):
        """Test verifying token with wrong secret."""
        token = jwt.encode(
            {"sub": "user-1"},
            "wrong_secret",
            algorithm="HS256"
        )
        
        with pytest.raises(Exception):
            jwt_manager.verify_token(token)
'''
    create_test_file('src/infrastructure/auth/jwt_manager.py', test_content)
    
    # Test for adapters/tts
    test_content = '''"""
Unit tests for TTS adapters.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.adapters.tts.edge_tts_adapter import EdgeTTSAdapter
from src.adapters.tts.base_adapter import BaseTTSAdapter
from src.domain.value_objects_tts import TTSOptions, AudioData, VoiceInfo


class TestBaseTTSAdapter:
    """Test BaseTTSAdapter."""
    
    def test_abstract_methods(self):
        """Test that abstract methods are defined."""
        # Should not be able to instantiate
        with pytest.raises(TypeError):
            BaseTTSAdapter()


class TestEdgeTTSAdapter:
    """Test EdgeTTSAdapter."""
    
    @pytest.fixture
    def adapter(self):
        """Create EdgeTTS adapter."""
        return EdgeTTSAdapter()
    
    @pytest.mark.asyncio
    async def test_initialize(self, adapter):
        """Test adapter initialization."""
        await adapter.initialize()
        assert adapter.is_available()
    
    @pytest.mark.asyncio
    async def test_close(self, adapter):
        """Test adapter closing."""
        await adapter.initialize()
        await adapter.close()
        # Should still be available (edge-tts doesn't need persistent connection)
        assert adapter.is_available()
    
    @pytest.mark.asyncio
    @patch('edge_tts.Communicate')
    async def test_synthesize(self, mock_communicate, adapter):
        """Test speech synthesis."""
        # Mock edge-tts
        mock_instance = AsyncMock()
        mock_instance.stream.return_value = [
            (b"audio_chunk_1", {"type": "audio"}),
            (b"audio_chunk_2", {"type": "audio"})
        ]
        mock_communicate.return_value = mock_instance
        
        await adapter.initialize()
        
        options = TTSOptions(
            voice="en-US-AriaNeural",
            rate=1.0,
            pitch=1.0,
            volume=1.0
        )
        
        result = await adapter.synthesize("Hello world", options)
        
        assert isinstance(result, AudioData)
        assert result.data == b"audio_chunk_1audio_chunk_2"
        assert result.format == "mp3"
    
    @pytest.mark.asyncio
    @patch('edge_tts.list_voices')
    async def test_list_voices(self, mock_list_voices, adapter):
        """Test listing voices."""
        mock_list_voices.return_value = [
            {
                "Name": "en-US-AriaNeural",
                "ShortName": "en-US-AriaNeural",
                "Gender": "Female",
                "Locale": "en-US"
            },
            {
                "Name": "en-US-GuyNeural",
                "ShortName": "en-US-GuyNeural",
                "Gender": "Male",
                "Locale": "en-US"
            }
        ]
        
        voices = await adapter.list_voices("en-US")
        
        assert len(voices) == 2
        assert all(isinstance(v, VoiceInfo) for v in voices)
        assert voices[0].id == "en-US-AriaNeural"
        assert voices[0].gender == "Female"
    
    def test_supported_formats(self, adapter):
        """Test getting supported formats."""
        formats = adapter.get_supported_formats()
        
        assert "mp3" in formats
        assert "wav" in formats
'''
    create_test_file('src/adapters/tts/edge_tts_adapter.py', test_content)
    
    # Test for API endpoints
    test_content = '''"""
Unit tests for API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from src.presentation.api.main import app
from src.domain.value_objects import SpeechText


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_auth():
    """Mock authentication."""
    with patch('src.presentation.api.dependencies.get_current_user') as mock:
        mock.return_value = {"id": "test-user", "username": "testuser"}
        yield mock


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_check(self, client):
        """Test basic health check."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_ready_check(self, client):
        """Test readiness check."""
        response = client.get("/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] == True


class TestConversionEndpoints:
    """Test conversion endpoints."""
    
    @patch('src.application.services.mathtts_service.MathTTSService')
    def test_convert_latex(self, mock_service_class, client, mock_auth):
        """Test LaTeX conversion endpoint."""
        # Mock the service
        mock_service = AsyncMock()
        mock_service.convert_latex.return_value = {
            "speech_text": "one half",
            "audio_url": "/audio/123.mp3",
            "format": "mp3"
        }
        mock_service_class.return_value = mock_service
        
        response = client.post(
            "/api/v1/convert",
            json={
                "latex": "\\\\\\\\frac{1}{2}",
                "voice_id": "en-US-AriaNeural",
                "format": "mp3"
            },
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["speech_text"] == "one half"
        assert "audio_url" in data
    
    def test_convert_latex_unauthenticated(self, client):
        """Test conversion without authentication."""
        response = client.post(
            "/api/v1/convert",
            json={
                "latex": "\\\\\\\\frac{1}{2}",
                "voice_id": "en-US-AriaNeural"
            }
        )
        
        assert response.status_code == 401
    
    @patch('src.application.services.mathtts_service.MathTTSService')
    def test_convert_invalid_latex(self, mock_service_class, client, mock_auth):
        """Test conversion with invalid LaTeX."""
        mock_service = AsyncMock()
        mock_service.convert_latex.side_effect = ValueError("Invalid LaTeX")
        mock_service_class.return_value = mock_service
        
        response = client.post(
            "/api/v1/convert",
            json={
                "latex": "invalid{",
                "voice_id": "en-US-AriaNeural"
            },
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 400
        assert "Invalid LaTeX" in response.json()["detail"]
    
    def test_convert_missing_fields(self, client, mock_auth):
        """Test conversion with missing required fields."""
        response = client.post(
            "/api/v1/convert",
            json={
                "latex": "\\\\\\\\frac{1}{2}"
                # Missing voice_id
            },
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 422


class TestPatternEndpoints:
    """Test pattern management endpoints."""
    
    @patch('src.infrastructure.persistence.pattern_repository.PatternRepository')
    def test_list_patterns(self, mock_repo_class, client, mock_auth):
        """Test listing patterns."""
        mock_repo = Mock()
        mock_repo.get_all.return_value = []
        mock_repo_class.return_value = mock_repo
        
        response = client.get(
            "/api/v1/patterns",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    @patch('src.infrastructure.persistence.pattern_repository.PatternRepository')
    def test_get_pattern(self, mock_repo_class, client, mock_auth):
        """Test getting single pattern."""
        mock_repo = Mock()
        mock_repo.get_by_id.return_value = {
            "id": "test-1",
            "name": "Test Pattern",
            "pattern": "test",
            "output_template": "test"
        }
        mock_repo_class.return_value = mock_repo
        
        response = client.get(
            "/api/v1/patterns/test-1",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-1"
    
    def test_get_pattern_not_found(self, client, mock_auth):
        """Test getting non-existent pattern."""
        response = client.get(
            "/api/v1/patterns/nonexistent",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 404
'''
    create_test_file('src/presentation/api/endpoints/conversion.py', test_content)
    
    print("\nAll test files created!")
    print("\nNext steps:")
    print("1. Fix the remaining import issues")
    print("2. Run pytest with coverage to see improvement")
    print("3. Iterate on failing tests and add more as needed")

if __name__ == "__main__":
    main()