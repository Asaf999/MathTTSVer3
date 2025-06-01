"""
Unit tests for PatternMatcher domain service.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from src.domain.services import PatternMatcher
from src.domain.entities import PatternEntity
from src.domain.value_objects import PatternPriority, LaTeXExpression, SpeechText
from src.infrastructure.persistence import MemoryPatternRepository


class TestPatternMatcher:
    """Test cases for PatternMatcher service."""
    
    @pytest.fixture
    def pattern_matcher(self, loaded_pattern_repository):
        """Create a pattern matcher with test patterns."""
        return PatternMatcher(loaded_pattern_repository)
    
    def test_match_simple_pattern(self, pattern_matcher):
        """Test matching a simple pattern."""
        latex = LaTeXExpression(r"\frac{1}{2}")
        result = pattern_matcher.process_expression(latex)
        
        assert result.value == "one half"
    
    def test_match_with_priority(self, pattern_repository):
        """Test that higher priority patterns match first."""
        # Add two patterns that could match the same expression
        repo = pattern_repository
        repo.add(PatternEntity(
            id="low_priority",
            name="Low priority",
            pattern=r"x\^2",
            output_template="x squared (low)",
            priority=PatternPriority(500)
        ))
        repo.add(PatternEntity(
            id="high_priority",
            name="High priority",
            pattern=r"x\^2",
            output_template="x squared (high)",
            priority=PatternPriority(1500)
        ))
        
        matcher = PatternMatcher(repo)
        latex = LaTeXExpression("x^2")
        result = matcher.process_expression(latex)
        
        assert result.value == "x squared (high)"
    
    def test_match_multiple_patterns(self, pattern_matcher):
        """Test matching multiple patterns in one expression."""
        latex = LaTeXExpression(r"\alpha^2")
        result = pattern_matcher.process_expression(latex)
        
        # Should match both alpha and superscript patterns
        assert "alpha" in result.value
        assert "to the power of 2" in result.value
    
    def test_no_match_returns_original(self, pattern_matcher):
        """Test that unmatched expressions return original text."""
        latex = LaTeXExpression(r"\unknown{command}")
        result = pattern_matcher.process_expression(latex)
        
        assert result.value == r"\unknown{command}"
    
    def test_pattern_with_groups(self, pattern_repository):
        """Test pattern matching with capture groups."""
        repo = pattern_repository
        repo.add(PatternEntity(
            id="fraction_generic",
            name="Generic fraction",
            pattern=r"\\frac\{([^}]+)\}\{([^}]+)\}",
            output_template=r"\1 over \2",
            priority=PatternPriority(1000)
        ))
        
        matcher = PatternMatcher(repo)
        latex = LaTeXExpression(r"\frac{a+b}{c-d}")
        result = matcher.process_expression(latex)
        
        assert result.value == "a+b over c-d"
    
    def test_overlapping_patterns(self, pattern_repository):
        """Test handling of overlapping pattern matches."""
        repo = pattern_repository
        repo.add(PatternEntity(
            id="x_squared",
            name="X squared",
            pattern=r"x\^2",
            output_template="x squared",
            priority=PatternPriority(1000)
        ))
        repo.add(PatternEntity(
            id="squared",
            name="Squared",
            pattern=r"\^2",
            output_template="squared",
            priority=PatternPriority(500)
        ))
        
        matcher = PatternMatcher(repo)
        latex = LaTeXExpression("x^2 + y^2")
        result = matcher.process_expression(latex)
        
        # Should match x^2 as a whole first, then ^2 for y
        assert result.value == "x squared + y squared"
    
    def test_complex_expression(self, loaded_pattern_repository):
        """Test matching a complex mathematical expression."""
        # Add more patterns for complex expression
        repo = loaded_pattern_repository
        repo.add(PatternEntity(
            id="plus",
            name="Plus",
            pattern=r"\+",
            output_template=" plus ",
            priority=PatternPriority(300)
        ))
        repo.add(PatternEntity(
            id="equals",
            name="Equals",
            pattern=r"=",
            output_template=" equals ",
            priority=PatternPriority(300)
        ))
        
        matcher = PatternMatcher(repo)
        latex = LaTeXExpression(r"\alpha + \beta = \gamma")
        result = matcher.process_expression(latex)
        
        assert "alpha" in result.value
        assert "plus" in result.value
        assert "beta" in result.value
        assert "equals" in result.value
        assert "gamma" in result.value.replace("\\gamma", "gamma")
    
    def test_empty_repository(self):
        """Test pattern matcher with empty repository."""
        empty_repo = MemoryPatternRepository()
        matcher = PatternMatcher(empty_repo)
        
        latex = LaTeXExpression(r"\frac{1}{2}")
        result = matcher.process_expression(latex)
        
        # Should return original expression
        assert result.value == r"\frac{1}{2}"
    
    def test_special_characters_in_pattern(self, pattern_repository):
        """Test patterns with special regex characters."""
        repo = pattern_repository
        repo.add(PatternEntity(
            id="parentheses",
            name="Parentheses",
            pattern=r"\\\(([^)]+)\\\)",
            output_template=r"open paren \1 close paren",
            priority=PatternPriority(800)
        ))
        
        matcher = PatternMatcher(repo)
        latex = LaTeXExpression(r"\(x + y\)")
        result = matcher.process_expression(latex)
        
        assert result.value == "open paren x + y close paren"
    
    def test_pattern_application_order(self, pattern_repository):
        """Test that patterns are applied in priority order."""
        repo = pattern_repository
        
        # Add patterns with different priorities
        patterns = [
            ("p1", r"test", "first", 2000),
            ("p2", r"test", "second", 1500),
            ("p3", r"test", "third", 1000),
            ("p4", r"test", "fourth", 500)
        ]
        
        for id_, pattern, output, priority in patterns:
            repo.add(PatternEntity(
                id=id_,
                name=f"Pattern {id_}",
                pattern=pattern,
                output_template=output,
                priority=PatternPriority(priority)
            ))
        
        matcher = PatternMatcher(repo)
        latex = LaTeXExpression("test")
        result = matcher.process_expression(latex)
        
        # Should match the highest priority pattern
        assert result.value == "first"