"""Persistence implementations for repositories."""

from typing import List, Optional, Dict, Any
import json
from pathlib import Path
from datetime import datetime

from src.domain.entities import PatternEntity
from src.domain.value_objects import PatternPriority
from src.domain.interfaces import PatternRepository


class MemoryPatternRepository(PatternRepository):
    """In-memory implementation of pattern repository."""
    
    def __init__(self):
        """Initialize empty repository."""
        self._patterns: Dict[str, PatternEntity] = {}
        self._domain_index: Dict[str, List[str]] = {}
        self._tag_index: Dict[str, List[str]] = {}
    
    def add(self, pattern: PatternEntity) -> None:
        """Add a pattern to the repository."""
        self._patterns[pattern.id] = pattern
        
        # Update domain index
        if pattern.domain not in self._domain_index:
            self._domain_index[pattern.domain] = []
        if pattern.id not in self._domain_index[pattern.domain]:
            self._domain_index[pattern.domain].append(pattern.id)
        
        # Update tag index
        for tag in pattern.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = []
            if pattern.id not in self._tag_index[tag]:
                self._tag_index[tag].append(pattern.id)
    
    def get(self, pattern_id: str) -> Optional[PatternEntity]:
        """Get a pattern by ID."""
        return self._patterns.get(pattern_id)
    
    def update(self, pattern: PatternEntity) -> None:
        """Update an existing pattern."""
        if pattern.id not in self._patterns:
            raise ValueError(f"Pattern {pattern.id} not found")
        
        # Remove from old indexes
        old_pattern = self._patterns[pattern.id]
        if old_pattern.domain in self._domain_index:
            self._domain_index[old_pattern.domain].remove(pattern.id)
        for tag in old_pattern.tags:
            if tag in self._tag_index:
                self._tag_index[tag].remove(pattern.id)
        
        # Add to repository with new indexes
        self.add(pattern)
    
    def delete(self, pattern_id: str) -> None:
        """Delete a pattern."""
        if pattern_id not in self._patterns:
            raise ValueError(f"Pattern {pattern_id} not found")
        
        pattern = self._patterns[pattern_id]
        
        # Remove from indexes
        if pattern.domain in self._domain_index:
            self._domain_index[pattern.domain].remove(pattern_id)
        for tag in pattern.tags:
            if tag in self._tag_index:
                self._tag_index[tag].remove(pattern_id)
        
        # Remove pattern
        del self._patterns[pattern_id]
    
    def find_by_domain(self, domain: str) -> List[PatternEntity]:
        """Find patterns by domain."""
        pattern_ids = self._domain_index.get(domain, [])
        return [self._patterns[pid] for pid in pattern_ids if pid in self._patterns]
    
    def find_by_tag(self, tag: str) -> List[PatternEntity]:
        """Find patterns by tag."""
        pattern_ids = self._tag_index.get(tag, [])
        return [self._patterns[pid] for pid in pattern_ids if pid in self._patterns]
    
    def find_by_priority_range(self, min_priority: int, max_priority: int) -> List[PatternEntity]:
        """Find patterns within a priority range."""
        return [
            p for p in self._patterns.values()
            if min_priority <= p.priority.value <= max_priority
        ]
    
    def get_all(self) -> List[PatternEntity]:
        """Get all patterns."""
        return list(self._patterns.values())
    
    def count(self) -> int:
        """Count total patterns."""
        return len(self._patterns)
    
    def clear(self) -> None:
        """Clear all patterns."""
        self._patterns.clear()
        self._domain_index.clear()
        self._tag_index.clear()


class FilePatternRepository(PatternRepository):
    """File-based pattern repository."""
    
    def __init__(self, file_path: Path):
        """Initialize with file path."""
        self.file_path = file_path
        self._patterns: Dict[str, PatternEntity] = {}
        self._load()
    
    def _load(self) -> None:
        """Load patterns from file."""
        if self.file_path.exists():
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                for pattern_data in data.get('patterns', []):
                    pattern = self._deserialize_pattern(pattern_data)
                    self._patterns[pattern.id] = pattern
    
    def _save(self) -> None:
        """Save patterns to file."""
        data = {
            'patterns': [self._serialize_pattern(p) for p in self._patterns.values()],
            'saved_at': datetime.now().isoformat()
        }
        with open(self.file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _serialize_pattern(self, pattern: PatternEntity) -> Dict[str, Any]:
        """Serialize pattern to dict."""
        return {
            'id': pattern.id,
            'name': pattern.name,
            'pattern': pattern.pattern,
            'output_template': pattern.output_template,
            'description': pattern.description,
            'priority': pattern.priority.value,
            'domain': pattern.domain,
            'tags': pattern.tags,
            'examples': pattern.examples,
            'metadata': pattern.metadata,
            'created_at': pattern.created_at.isoformat(),
            'updated_at': pattern.updated_at.isoformat()
        }
    
    def _deserialize_pattern(self, data: Dict[str, Any]) -> PatternEntity:
        """Deserialize pattern from dict."""
        return PatternEntity(
            id=data['id'],
            name=data['name'],
            pattern=data['pattern'],
            output_template=data['output_template'],
            description=data.get('description', ''),
            priority=PatternPriority(data.get('priority', 1000)),
            domain=data.get('domain', 'general'),
            tags=data.get('tags', []),
            examples=data.get('examples', []),
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat()))
        )
    
    def add(self, pattern: PatternEntity) -> None:
        """Add a pattern."""
        self._patterns[pattern.id] = pattern
        self._save()
    
    def get(self, pattern_id: str) -> Optional[PatternEntity]:
        """Get a pattern by ID."""
        return self._patterns.get(pattern_id)
    
    def update(self, pattern: PatternEntity) -> None:
        """Update a pattern."""
        if pattern.id not in self._patterns:
            raise ValueError(f"Pattern {pattern.id} not found")
        self._patterns[pattern.id] = pattern
        self._save()
    
    def delete(self, pattern_id: str) -> None:
        """Delete a pattern."""
        if pattern_id not in self._patterns:
            raise ValueError(f"Pattern {pattern_id} not found")
        del self._patterns[pattern_id]
        self._save()
    
    def find_by_domain(self, domain: str) -> List[PatternEntity]:
        """Find patterns by domain."""
        return [p for p in self._patterns.values() if p.domain == domain]
    
    def find_by_tag(self, tag: str) -> List[PatternEntity]:
        """Find patterns by tag."""
        return [p for p in self._patterns.values() if tag in p.tags]
    
    def find_by_priority_range(self, min_priority: int, max_priority: int) -> List[PatternEntity]:
        """Find patterns within priority range."""
        return [
            p for p in self._patterns.values()
            if min_priority <= p.priority.value <= max_priority
        ]
    
    def get_all(self) -> List[PatternEntity]:
        """Get all patterns."""
        return list(self._patterns.values())
    
    def count(self) -> int:
        """Count patterns."""
        return len(self._patterns)
    
    def clear(self) -> None:
        """Clear all patterns."""
        self._patterns.clear()
        self._save()