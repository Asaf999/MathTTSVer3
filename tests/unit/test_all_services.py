"""
Comprehensive tests for all services.
"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import Mock, AsyncMock, patch
from src.domain.services.pattern_matching_service import PatternMatchingService
from src.domain.services.natural_language_processor import NaturalLanguageProcessor, NaturalLanguageContext
from src.domain.services.mathematical_rhythm_processor import MathematicalRhythmProcessor, RhythmContext
from src.domain.entities import PatternEntity
from src.domain.value_objects import *


class TestAllServices:
    """Test all domain services."""
    
    def test_pattern_matching_service_complete(self):
        """Test PatternMatchingService completely."""
        # Mock repository
        repo = Mock()
        repo.get_all.return_value = [
            PatternEntity(
                id="frac-1",
                name="Fraction",
                pattern=r"\\frac\{(.+?)\}\{(.+?)\}",
                output_template="\\1 over \\2",
                priority=PatternPriority(1000)
            ),
            PatternEntity(
                id="sqrt-1",
                name="Square Root",
                pattern=r"\\sqrt\{(.+?)\}",
                output_template="square root of \\1",
                priority=PatternPriority(900)
            )
        ]
        
        service = PatternMatchingService(repo)
        
        # Test find matching patterns
        expr = LaTeXExpression(r"\\frac{1}{2}")
        matches = service.find_matching_patterns(expr)
        assert len(matches) >= 1
        
        # Test apply pattern
        pattern = repo.get_all()[0]
        result = service.apply_pattern(pattern, expr)
        assert result is not None
        assert isinstance(result, SpeechText)
        
        # Test convert expression
        result = service.convert_expression(expr)
        assert isinstance(result, SpeechText)
        
        # Test with no matches
        expr_no_match = LaTeXExpression(r"\\unknown")
        result = service.convert_expression(expr_no_match)
        assert result.value == r"\\unknown"  # Fallback
        
        # Test domain filtering
        matches = service.find_matching_patterns(expr, domain="calculus")
        # Should still match general patterns
        
        # Test context filtering
        matches = service.find_matching_patterns(expr, context="inline")
        # Test passes
    
    def test_natural_language_processor_complete(self):
        """Test NaturalLanguageProcessor completely."""
        processor = NaturalLanguageProcessor()
        
        # Test basic enhancement
        context = NaturalLanguageContext()
        result = processor.enhance_mathematical_speech("x equals 5", context)
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Test different contexts
        contexts = [
            NaturalLanguageContext(is_definition=True),
            NaturalLanguageContext(is_theorem=True),
            NaturalLanguageContext(is_proof=True),
            NaturalLanguageContext(audience_level="elementary"),
            NaturalLanguageContext(audience_level="graduate"),
            NaturalLanguageContext(teaching_mode=True)
        ]
        
        for ctx in contexts:
            result = processor.enhance_mathematical_speech("test expression", ctx)
            assert isinstance(result, str)
        
        # Test internal methods
        text = "derivative of x"
        result = processor._add_contextual_articles(text, context)
        assert isinstance(result, str)
        
        result = processor._enhance_mathematical_phrasing(text, context)
        assert isinstance(result, str)
        
        result = processor._add_semantic_understanding(text, context)
        assert isinstance(result, str)
        
        result = processor._add_storytelling_flow(text, context)
        assert isinstance(result, str)
    
    def test_mathematical_rhythm_processor_complete(self):
        """Test MathematicalRhythmProcessor completely."""
        processor = MathematicalRhythmProcessor()
        
        # Test basic rhythm
        text = "x equals 5"
        result = processor.add_mathematical_rhythm(text)
        assert isinstance(result, str)
        
        # Test with context
        contexts = [
            RhythmContext(is_definition=True),
            RhythmContext(is_theorem=True),
            RhythmContext(is_proof=True),
            RhythmContext(is_complex_expression=True),
            RhythmContext(audience_level="elementary"),
            RhythmContext(teaching_mode=True)
        ]
        
        for ctx in contexts:
            result = processor.add_mathematical_rhythm(text, ctx)
            assert isinstance(result, str)
        
        # Test internal methods
        result = processor._add_operation_pauses("x plus y equals z")
        assert "<pause:" in result
        
        result = processor._add_emphasis_markup("therefore x equals 5")
        assert "<emphasis" in result
        
        result = processor._add_conceptual_pauses("x, which means y", RhythmContext())
        assert isinstance(result, str)
        
        result = processor._add_breathing_points("This is a very long sentence " * 10)
        assert isinstance(result, str)
        
        result = processor._add_dramatic_pauses("Theorem: x equals y", RhythmContext(is_theorem=True))
        assert isinstance(result, str)
        
        result = processor._optimize_rhythm_flow("<pause:200ms> <pause:300ms> test")
        assert isinstance(result, str)
        
        # Test utility methods
        time_est = processor.get_reading_time_estimate("Test <pause:500ms> text")
        assert time_est > 0
        
        ssml = processor.create_ssml_output("Test <pause:300ms> text")
        assert ssml.startswith("<speak>")
        
        metrics = processor.analyze_rhythm_quality("Test <pause:300ms> text")
        assert "rhythm_score" in metrics
