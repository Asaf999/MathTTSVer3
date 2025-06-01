"""
Comprehensive tests for all entities.
"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from src.domain.entities import *
from src.domain.value_objects import *


class TestAllEntities:
    """Test all domain entities."""
    
    def test_pattern_entity_complete(self):
        """Test PatternEntity completely."""
        pattern = PatternEntity(
            id="test-1",
            name="Test Pattern",
            pattern=r"\frac{(.+?)}{(.+?)}",
            output_template="\1 over \2",
            description="Test description",
            priority=PatternPriority(1000),
            domain="calculus",
            tags=["fraction", "basic"],
            examples=[r"\frac{1}{2}"],
            metadata={"author": "test"}
        )
        
        # Test all properties
        assert pattern.id == "test-1"
        assert pattern.name == "Test Pattern"
        assert pattern.is_high_priority
        assert not pattern.is_critical
        
        # Test methods
        assert pattern.matches_domain("calculus")
        assert pattern.matches_domain("general")
        assert pattern.has_tag("fraction")
        
        # Test update
        updated = pattern.update(name="Updated Pattern")
        assert updated.name == "Updated Pattern"
        assert pattern.name == "Test Pattern"  # Original unchanged
        
        # Test tag operations
        with_tag = pattern.add_tag("new")
        assert with_tag.has_tag("new")
        
        without_tag = with_tag.remove_tag("basic")
        assert not without_tag.has_tag("basic")
        
        # Test equality and hash
        pattern2 = PatternEntity(
            id="test-1",  # Same ID
            name="Different",
            pattern="different",
            output_template="different"
        )
        assert pattern == pattern2
        assert hash(pattern) == hash(pattern2)
        
        # Test validation
        with pytest.raises(ValueError):
            PatternEntity(id="", name="Test", pattern="test", output_template="test")
    
    def test_conversion_record_complete(self):
        """Test ConversionRecord completely."""
        record = ConversionRecord(
            latex_input=r"\frac{1}{2}",
            speech_output="one half",
            pattern_ids_used=["frac-1"],
            voice_id="test-voice",
            format="mp3",
            duration_seconds=1.5,
            cached=False,
            metadata={"rate": 1.0}
        )
        
        # Test properties
        assert record.latex_input == r"\frac{1}{2}"
        assert record.cache_key  # Should generate key
        
        # Test methods
        cached_record = record.mark_as_cached()
        assert cached_record.cached
        assert not record.cached  # Original unchanged
        
        # Test validation
        with pytest.raises(ValueError):
            ConversionRecord(latex_input="")
    
    def test_mathematical_expression_entity(self):
        """Test MathematicalExpression if exists."""
        try:
            from src.domain.entities.mathematical_expression import MathematicalExpression
            
            expr = MathematicalExpression(
                latex=LaTeXExpression(r"\frac{1}{2}"),
                domain="calculus",
                complexity_score=2.5
            )
            
            assert expr.latex.content == r"\frac{1}{2}"
            assert expr.domain == "calculus"
            assert expr.complexity_score == 2.5
        except ImportError:
            # Entity might not exist
            pass
