"""
Unit tests for repository implementations.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from src.domain.entities import PatternEntity
from src.domain.value_objects import PatternPriority
from src.infrastructure.persistence import MemoryPatternRepository, FilePatternRepository
from pathlib import Path
import json


class TestMemoryPatternRepository:
    """Test cases for in-memory pattern repository."""
    
    def test_add_pattern(self, sample_pattern):
        """Test adding a pattern to repository."""
        repo = MemoryPatternRepository()
        repo.add(sample_pattern)
        
        retrieved = repo.get_by_id(sample_pattern.id)
        assert retrieved == sample_pattern
    
    def test_get_by_id_not_found(self):
        """Test getting non-existent pattern by ID."""
        repo = MemoryPatternRepository()
        assert repo.get_by_id("non_existent") is None
    
    def test_get_all_patterns(self, sample_pattern):
        """Test getting all patterns."""
        repo = MemoryPatternRepository()
        
        patterns = [
            sample_pattern,
            PatternEntity(
                id="another",
                name="Another pattern",
                pattern=r"\\test",
                output_template="test",
                priority=PatternPriority(500)
            )
        ]
        
        for pattern in patterns:
            repo.add(pattern)
        
        all_patterns = repo.get_all()
        assert len(all_patterns) == 2
        assert all(p in patterns for p in all_patterns)
    
    def test_get_by_domain(self, sample_pattern):
        """Test getting patterns by domain."""
        repo = MemoryPatternRepository()
        
        # Add patterns with different domains
        repo.add(sample_pattern)  # domain="test"
        repo.add(PatternEntity(
            id="math_pattern",
            name="Math pattern",
            pattern=r"\\math",
            output_template="math",
            domain="mathematics"
        ))
        
        test_patterns = repo.get_by_domain("test")
        assert len(test_patterns) == 1
        assert test_patterns[0].domain == "test"
        
        math_patterns = repo.get_by_domain("mathematics")
        assert len(math_patterns) == 1
        assert math_patterns[0].domain == "mathematics"
    
    def test_get_by_priority_range(self):
        """Test getting patterns within priority range."""
        repo = MemoryPatternRepository()
        
        # Add patterns with different priorities
        patterns = [
            ("low", 100),
            ("medium", 500),
            ("high", 1000),
            ("very_high", 1500)
        ]
        
        for id_, priority in patterns:
            repo.add(PatternEntity(
                id=id_,
                name=f"{id_} priority",
                pattern=rf"\\{id_}",
                output_template=id_,
                priority=PatternPriority(priority)
            ))
        
        # Get patterns with priority 400-1200
        mid_patterns = repo.get_by_priority_range(400, 1200)
        assert len(mid_patterns) == 2
        assert all(400 <= p.priority.value <= 1200 for p in mid_patterns)
    
    def test_update_pattern(self, sample_pattern):
        """Test updating an existing pattern."""
        repo = MemoryPatternRepository()
        repo.add(sample_pattern)
        
        # Create updated pattern with same ID
        updated = PatternEntity(
            id=sample_pattern.id,
            name="Updated pattern",
            pattern=r"\\updated",
            output_template="updated",
            priority=PatternPriority(2000)
        )
        
        repo.update(updated)
        
        retrieved = repo.get_by_id(sample_pattern.id)
        assert retrieved.name == "Updated pattern"
        assert retrieved.pattern == r"\\updated"
        assert retrieved.priority.value == 2000
    
    def test_update_non_existent(self):
        """Test updating non-existent pattern."""
        repo = MemoryPatternRepository()
        
        pattern = PatternEntity(
            id="non_existent",
            name="Test",
            pattern=r"\\test",
            output_template="test"
        )
        
        with pytest.raises(ValueError, match="not found"):
            repo.update(pattern)
    
    def test_delete_pattern(self, sample_pattern):
        """Test deleting a pattern."""
        repo = MemoryPatternRepository()
        repo.add(sample_pattern)
        
        assert repo.delete(sample_pattern.id) is True
        assert repo.get_by_id(sample_pattern.id) is None
    
    def test_delete_non_existent(self):
        """Test deleting non-existent pattern."""
        repo = MemoryPatternRepository()
        assert repo.delete("non_existent") is False
    
    def test_exists_check(self, sample_pattern):
        """Test checking if pattern exists."""
        repo = MemoryPatternRepository()
        
        assert repo.exists(sample_pattern.id) is False
        repo.add(sample_pattern)
        assert repo.exists(sample_pattern.id) is True
    
    def test_count_patterns(self):
        """Test counting patterns."""
        repo = MemoryPatternRepository()
        
        assert repo.count() == 0
        
        for i in range(5):
            repo.add(PatternEntity(
                id=f"pattern_{i}",
                name=f"Pattern {i}",
                pattern=rf"\\p{i}",
                output_template=f"p{i}"
            ))
        
        assert repo.count() == 5
    
    def test_clear_repository(self, sample_pattern):
        """Test clearing all patterns."""
        repo = MemoryPatternRepository()
        repo.add(sample_pattern)
        
        assert repo.count() == 1
        repo.clear()
        assert repo.count() == 0
        assert repo.get_all() == []


class TestFilePatternRepository:
    """Test cases for file-based pattern repository."""
    
    def test_save_and_load(self, tmp_path, sample_pattern):
        """Test saving and loading patterns from file."""
        file_path = tmp_path / "patterns.json"
        repo = FilePatternRepository(file_path)
        
        repo.add(sample_pattern)
        repo.save()
        
        # Create new repository and load
        new_repo = FilePatternRepository(file_path)
        new_repo.load()
        
        retrieved = new_repo.get_by_id(sample_pattern.id)
        assert retrieved is not None
        assert retrieved.id == sample_pattern.id
        assert retrieved.name == sample_pattern.name
    
    def test_load_non_existent_file(self, tmp_path):
        """Test loading from non-existent file."""
        file_path = tmp_path / "non_existent.json"
        repo = FilePatternRepository(file_path)
        
        # Should not raise error, just start empty
        repo.load()
        assert repo.count() == 0
    
    def test_save_creates_directories(self, tmp_path):
        """Test that save creates parent directories."""
        file_path = tmp_path / "nested" / "dirs" / "patterns.json"
        repo = FilePatternRepository(file_path)
        
        repo.add(PatternEntity(
            id="test",
            name="Test",
            pattern=r"\\test",
            output_template="test"
        ))
        
        repo.save()
        assert file_path.exists()
    
    def test_persistence_across_instances(self, tmp_path):
        """Test that data persists across repository instances."""
        file_path = tmp_path / "patterns.json"
        
        # First instance - add patterns
        repo1 = FilePatternRepository(file_path)
        patterns = [
            PatternEntity(
                id=f"p{i}",
                name=f"Pattern {i}",
                pattern=rf"\\p{i}",
                output_template=f"p{i}"
            )
            for i in range(3)
        ]
        
        for pattern in patterns:
            repo1.add(pattern)
        repo1.save()
        
        # Second instance - load and verify
        repo2 = FilePatternRepository(file_path)
        repo2.load()
        
        assert repo2.count() == 3
        for pattern in patterns:
            retrieved = repo2.get_by_id(pattern.id)
            assert retrieved is not None
            assert retrieved.name == pattern.name
    
    def test_auto_save_on_modification(self, tmp_path, sample_pattern):
        """Test auto-save functionality if enabled."""
        file_path = tmp_path / "patterns.json"
        repo = FilePatternRepository(file_path, auto_save=True)
        
        repo.add(sample_pattern)
        
        # Check file was created and contains pattern
        assert file_path.exists()
        
        # Load in new repository to verify
        new_repo = FilePatternRepository(file_path)
        new_repo.load()
        assert new_repo.exists(sample_pattern.id)
    
    def test_file_corruption_handling(self, tmp_path):
        """Test handling of corrupted file."""
        file_path = tmp_path / "patterns.json"
        
        # Write invalid JSON
        file_path.write_text("{ invalid json }")
        
        repo = FilePatternRepository(file_path)
        
        # Should handle gracefully
        with pytest.raises(json.JSONDecodeError):
            repo.load()