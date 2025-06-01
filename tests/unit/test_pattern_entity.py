"""
Unit tests for PatternEntity.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from src.domain.entities import PatternEntity
from src.domain.value_objects import PatternPriority


class TestPatternEntity:
    """Test cases for PatternEntity."""
    
    def test_create_pattern_entity(self):
        """Test creating a pattern entity with valid data."""
        pattern = PatternEntity(
            id="test_pattern",
            name="Test Pattern",
            description="A test pattern",
            pattern=r"\\test",
            output_template="test",
            priority=PatternPriority(1000),
            domain="test",
            tags=["test"],
            examples=[r"\test"],
            metadata={"key": "value"}
        )
        
        assert pattern.id == "test_pattern"
        assert pattern.name == "Test Pattern"
        assert pattern.description == "A test pattern"
        assert pattern.pattern == r"\\test"
        assert pattern.output_template == "test"
        assert pattern.priority.value == 1000
        assert pattern.domain == "test"
        assert pattern.tags == ["test"]
        assert pattern.examples == [r"\test"]
        assert pattern.metadata == {"key": "value"}
    
    def test_pattern_entity_defaults(self):
        """Test pattern entity with default values."""
        pattern = PatternEntity(
            id="minimal",
            name="Minimal Pattern",
            pattern=r"\\min",
            output_template="minimal"
        )
        
        assert pattern.description == ""
        assert pattern.priority.value == 1000  # Default priority
        assert pattern.domain == "general"
        assert pattern.tags == []
        assert pattern.examples == []
        assert pattern.metadata == {}
    
    def test_pattern_entity_equality(self):
        """Test pattern entity equality based on ID."""
        pattern1 = PatternEntity(
            id="same_id",
            name="Pattern 1",
            pattern=r"\\p1",
            output_template="p1"
        )
        
        pattern2 = PatternEntity(
            id="same_id",
            name="Pattern 2",
            pattern=r"\\p2",
            output_template="p2"
        )
        
        pattern3 = PatternEntity(
            id="different_id",
            name="Pattern 1",
            pattern=r"\\p1",
            output_template="p1"
        )
        
        assert pattern1 == pattern2  # Same ID
        assert pattern1 != pattern3  # Different ID
    
    def test_pattern_entity_hash(self):
        """Test pattern entity hashing."""
        pattern1 = PatternEntity(
            id="test",
            name="Test",
            pattern=r"\\test",
            output_template="test"
        )
        
        pattern2 = PatternEntity(
            id="test",
            name="Different",
            pattern=r"\\different",
            output_template="different"
        )
        
        # Same ID should have same hash
        assert hash(pattern1) == hash(pattern2)
        
        # Can be used in sets
        pattern_set = {pattern1, pattern2}
        assert len(pattern_set) == 1
    
    def test_pattern_entity_str(self):
        """Test string representation of pattern entity."""
        pattern = PatternEntity(
            id="test_str",
            name="Test String",
            pattern=r"\\str",
            output_template="string",
            priority=PatternPriority(1500)
        )
        
        str_repr = str(pattern)
        assert "test_str" in str_repr
        assert "Test String" in str_repr
        assert "1500" in str_repr
    
    def test_pattern_entity_validation(self):
        """Test pattern entity validation."""
        # Test empty ID
        with pytest.raises(ValueError):
            PatternEntity(
                id="",
                name="Test",
                pattern=r"\\test",
                output_template="test"
            )
        
        # Test empty pattern
        with pytest.raises(ValueError):
            PatternEntity(
                id="test",
                name="Test",
                pattern="",
                output_template="test"
            )
        
        # Test empty output template
        with pytest.raises(ValueError):
            PatternEntity(
                id="test",
                name="Test",
                pattern=r"\\test",
                output_template=""
            )
    
    def test_pattern_entity_immutability(self):
        """Test that pattern entity is effectively immutable."""
        pattern = PatternEntity(
            id="immutable",
            name="Immutable Pattern",
            pattern=r"\\immut",
            output_template="immutable"
        )
        
        # These should raise AttributeError
        with pytest.raises(AttributeError):
            pattern.id = "changed"
        
        with pytest.raises(AttributeError):
            pattern.name = "Changed"
        
        with pytest.raises(AttributeError):
            pattern.pattern = r"\\changed"