"""
In-memory pattern repository implementation.

This repository stores patterns in memory and provides all the functionality
required by the PatternRepository interface.
"""

from typing import Optional, List, Dict, Any
import asyncio
from collections import defaultdict

from src.domain.interfaces import PatternRepository, RepositoryError, DuplicatePatternError
from src.domain.entities import PatternEntity
from src.domain.value_objects import MathematicalDomain, PatternPriority


class MemoryPatternRepository(PatternRepository):
    """In-memory implementation of pattern repository."""
    
    def __init__(self) -> None:
        """Initialize repository."""
        self._patterns: Dict[str, PatternEntity] = {}
        self._lock = asyncio.Lock()
    
    async def add(self, pattern: PatternEntity) -> None:
        """Add a pattern to the repository."""
        async with self._lock:
            if pattern.id in self._patterns:
                raise DuplicatePatternError(f"Pattern with ID '{pattern.id}' already exists")
            self._patterns[pattern.id] = pattern
    
    async def get_by_id(self, pattern_id: str) -> Optional[PatternEntity]:
        """Retrieve a pattern by its ID."""
        return self._patterns.get(pattern_id)
    
    async def get_all(self) -> List[PatternEntity]:
        """Retrieve all patterns from the repository."""
        return list(self._patterns.values())
    
    async def find_by_domain(self, domain: MathematicalDomain) -> List[PatternEntity]:
        """Find patterns by mathematical domain."""
        return [
            pattern for pattern in self._patterns.values()
            if pattern.domain == domain
        ]
    
    async def find_by_priority_range(
        self,
        min_priority: PatternPriority,
        max_priority: PatternPriority
    ) -> List[PatternEntity]:
        """Find patterns within a priority range."""
        return [
            pattern for pattern in self._patterns.values()
            if min_priority.value <= pattern.priority.value <= max_priority.value
        ]
    
    async def find_by_context(self, context: str) -> List[PatternEntity]:
        """Find patterns applicable to a specific context."""
        return [
            pattern for pattern in self._patterns.values()
            if context in pattern.contexts
        ]
    
    async def find_by_filters(self, filters: Dict[str, Any]) -> List[PatternEntity]:
        """Find patterns matching multiple filter criteria."""
        results = list(self._patterns.values())
        
        # Apply domain filter
        if "domain" in filters:
            domain = filters["domain"]
            if isinstance(domain, str):
                domain = MathematicalDomain(domain.upper())
            results = [p for p in results if p.domain == domain]
        
        # Apply contexts filter
        if "contexts" in filters:
            contexts = filters["contexts"]
            if isinstance(contexts, str):
                contexts = [contexts]
            results = [
                p for p in results
                if any(context in p.contexts for context in contexts)
            ]
        
        # Apply priority filters
        if "min_priority" in filters:
            min_priority = filters["min_priority"]
            if isinstance(min_priority, int):
                min_priority = PatternPriority(min_priority)
            results = [p for p in results if p.priority.value >= min_priority.value]
        
        if "max_priority" in filters:
            max_priority = filters["max_priority"]
            if isinstance(max_priority, int):
                max_priority = PatternPriority(max_priority)
            results = [p for p in results if p.priority.value <= max_priority.value]
        
        # Apply enabled filter
        if "enabled" in filters:
            enabled = filters["enabled"]
            # Assuming patterns have an enabled property (we'll add this)
            results = [p for p in results if getattr(p, 'enabled', True) == enabled]
        
        return results
    
    async def update(self, pattern: PatternEntity) -> None:
        """Update an existing pattern."""
        async with self._lock:
            if pattern.id not in self._patterns:
                raise RepositoryError(f"Pattern with ID '{pattern.id}' not found")
            self._patterns[pattern.id] = pattern
    
    async def delete(self, pattern_id: str) -> bool:
        """Delete a pattern by its ID."""
        async with self._lock:
            if pattern_id in self._patterns:
                del self._patterns[pattern_id]
                return True
            return False
    
    async def count(self) -> int:
        """Get the total number of patterns."""
        return len(self._patterns)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get repository statistics."""
        patterns = list(self._patterns.values())
        
        # Domain statistics
        domain_counts = defaultdict(int)
        for pattern in patterns:
            domain_counts[pattern.domain.value] += 1
        
        # Priority statistics
        priority_counts = {
            "critical": 0,
            "high": 0, 
            "medium": 0,
            "low": 0
        }
        
        for pattern in patterns:
            priority_val = pattern.priority.value
            if priority_val >= 1500:
                priority_counts["critical"] += 1
            elif priority_val >= 1000:
                priority_counts["high"] += 1
            elif priority_val >= 500:
                priority_counts["medium"] += 1
            else:
                priority_counts["low"] += 1
        
        # Context statistics
        context_counts = defaultdict(int)
        for pattern in patterns:
            for context in pattern.contexts:
                context_counts[context] += 1
        
        return {
            "total_patterns": len(patterns),
            "domains": dict(domain_counts),
            "priorities": priority_counts,
            "contexts": dict(context_counts)
        }
    
    async def clear(self) -> None:
        """Remove all patterns from the repository."""
        async with self._lock:
            self._patterns.clear()
    
    # Additional utility methods
    async def find_by_pattern_text(self, pattern_text: str) -> List[PatternEntity]:
        """Find patterns by their pattern text (for debugging)."""
        return [
            pattern for pattern in self._patterns.values()
            if pattern.pattern == pattern_text
        ]
    
    async def search(self, query: str) -> List[PatternEntity]:
        """Search patterns by description or ID."""
        query_lower = query.lower()
        return [
            pattern for pattern in self._patterns.values()
            if (query_lower in pattern.id.lower() or
                (pattern.description and query_lower in pattern.description.lower()))
        ]