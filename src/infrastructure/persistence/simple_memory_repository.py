"""
Simple synchronous in-memory pattern repository for testing.
"""

from typing import Optional, List, Dict
from src.domain.entities import PatternEntity


class MemoryPatternRepository:
    """Simple in-memory pattern repository."""
    
    def __init__(self):
        """Initialize repository."""
        self._patterns: Dict[str, PatternEntity] = {}
    
    def add(self, pattern: PatternEntity) -> None:
        """Add a pattern to the repository."""
        if pattern.id in self._patterns:
            raise ValueError(f"Pattern with ID '{pattern.id}' already exists")
        self._patterns[pattern.id] = pattern
    
    def get_by_id(self, pattern_id: str) -> Optional[PatternEntity]:
        """Get pattern by ID."""
        return self._patterns.get(pattern_id)
    
    def get_all(self) -> List[PatternEntity]:
        """Get all patterns."""
        return list(self._patterns.values())
    
    def get_by_domain(self, domain: str) -> List[PatternEntity]:
        """Get patterns by domain."""
        return [p for p in self._patterns.values() if p.domain == domain]
    
    def get_by_priority_range(self, min_priority: int, max_priority: int) -> List[PatternEntity]:
        """Get patterns within priority range."""
        return [
            p for p in self._patterns.values()
            if min_priority <= p.priority.value <= max_priority
        ]
    
    def update(self, pattern: PatternEntity) -> None:
        """Update a pattern."""
        if pattern.id not in self._patterns:
            raise ValueError(f"Pattern with ID '{pattern.id}' not found")
        self._patterns[pattern.id] = pattern
    
    def delete(self, pattern_id: str) -> bool:
        """Delete a pattern."""
        if pattern_id in self._patterns:
            del self._patterns[pattern_id]
            return True
        return False
    
    def exists(self, pattern_id: str) -> bool:
        """Check if pattern exists."""
        return pattern_id in self._patterns
    
    def count(self) -> int:
        """Count patterns."""
        return len(self._patterns)
    
    def clear(self) -> None:
        """Clear all patterns."""
        self._patterns.clear()


class FilePatternRepository(MemoryPatternRepository):
    """File-based pattern repository."""
    
    def __init__(self, file_path, auto_save=False):
        """Initialize with file path."""
        super().__init__()
        self.file_path = file_path
        self.auto_save = auto_save
    
    def save(self):
        """Save patterns to file."""
        import json
        from pathlib import Path
        
        # Ensure directory exists
        Path(self.file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Convert patterns to dict for JSON serialization
        data = {
            pid: {
                "id": p.id,
                "name": p.name,
                "pattern": p.pattern,
                "output_template": p.output_template,
                "description": p.description,
                "priority": p.priority.value,
                "domain": p.domain,
                "tags": p.tags,
                "examples": p.examples,
                "metadata": p.metadata
            }
            for pid, p in self._patterns.items()
        }
        
        with open(self.file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self):
        """Load patterns from file."""
        import json
        from pathlib import Path
        
        if not Path(self.file_path).exists():
            return
        
        with open(self.file_path, 'r') as f:
            data = json.load(f)
        
        self._patterns.clear()
        
        for pid, pdata in data.items():
            from src.domain.value_objects import PatternPriority
            pattern = PatternEntity(
                id=pdata["id"],
                name=pdata["name"],
                pattern=pdata["pattern"],
                output_template=pdata["output_template"],
                description=pdata.get("description", ""),
                priority=PatternPriority(pdata.get("priority", 1000)),
                domain=pdata.get("domain", "general"),
                tags=pdata.get("tags", []),
                examples=pdata.get("examples", []),
                metadata=pdata.get("metadata", {})
            )
            self._patterns[pattern.id] = pattern
    
    def add(self, pattern: PatternEntity) -> None:
        """Add pattern and optionally save."""
        super().add(pattern)
        if self.auto_save:
            self.save()