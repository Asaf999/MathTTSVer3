"""
Domain entities for MathTTS.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from .value_objects import PatternPriority


@dataclass
class PatternEntity:
    """
    Pattern entity representing a LaTeX to speech pattern.
    
    This is the core domain entity for pattern matching.
    """
    
    id: str
    name: str
    pattern: str
    output_template: str
    description: str = ""
    priority: PatternPriority = field(default_factory=lambda: PatternPriority(1000))
    domain: str = "general"
    tags: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate entity after initialization."""
        if not self.id:
            raise ValueError("Pattern ID cannot be empty")
        
        if not self.name:
            raise ValueError("Pattern name cannot be empty")
        
        if not self.pattern:
            raise ValueError("Pattern regex cannot be empty")
        
        if not self.output_template:
            raise ValueError("Output template cannot be empty")
    
    def __eq__(self, other):
        """Patterns are equal if they have the same ID."""
        if not isinstance(other, PatternEntity):
            return False
        return self.id == other.id
    
    def __hash__(self):
        """Hash based on ID."""
        return hash(self.id)
    
    def __str__(self):
        """String representation."""
        return f"PatternEntity(id={self.id}, name={self.name}, priority={self.priority.value})"
    
    def update(self, **kwargs):
        """
        Update pattern attributes.
        
        Returns a new instance with updated values.
        """
        data = {
            "id": self.id,
            "name": self.name,
            "pattern": self.pattern,
            "output_template": self.output_template,
            "description": self.description,
            "priority": self.priority,
            "domain": self.domain,
            "tags": self.tags.copy(),
            "examples": self.examples.copy(),
            "metadata": self.metadata.copy(),
            "created_at": self.created_at,
            "updated_at": datetime.now()
        }
        
        data.update(kwargs)
        return PatternEntity(**data)
    
    @property
    def is_high_priority(self) -> bool:
        """Check if this is a high priority pattern."""
        return self.priority.value >= PatternPriority.HIGH
    
    @property
    def is_critical(self) -> bool:
        """Check if this is a critical priority pattern."""
        return self.priority.value >= PatternPriority.CRITICAL
    
    def matches_domain(self, domain: str) -> bool:
        """Check if pattern matches a domain."""
        return self.domain == domain or domain == "general"
    
    def has_tag(self, tag: str) -> bool:
        """Check if pattern has a specific tag."""
        return tag in self.tags
    
    def add_tag(self, tag: str) -> "PatternEntity":
        """Add a tag to the pattern."""
        if tag not in self.tags:
            new_tags = self.tags.copy()
            new_tags.append(tag)
            return self.update(tags=new_tags)
        return self
    
    def remove_tag(self, tag: str) -> "PatternEntity":
        """Remove a tag from the pattern."""
        if tag in self.tags:
            new_tags = self.tags.copy()
            new_tags.remove(tag)
            return self.update(tags=new_tags)
        return self


@dataclass
class ConversionRecord:
    """
    Record of a LaTeX to speech conversion.
    
    Used for tracking conversions, analytics, and caching.
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    latex_input: str = ""
    speech_output: str = ""
    pattern_ids_used: List[str] = field(default_factory=list)
    voice_id: str = ""
    format: str = "mp3"
    duration_seconds: float = 0.0
    cached: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate record."""
        if not self.latex_input:
            raise ValueError("LaTeX input cannot be empty")
    
    @property
    def cache_key(self) -> str:
        """Generate cache key for this conversion."""
        # Include relevant fields in cache key
        parts = [
            self.latex_input,
            self.voice_id,
            self.format,
            str(self.metadata.get("rate", 1.0)),
            str(self.metadata.get("pitch", 1.0))
        ]
        return "_".join(parts)
    
    def mark_as_cached(self) -> "ConversionRecord":
        """Mark this record as cached."""
        return ConversionRecord(
            id=self.id,
            latex_input=self.latex_input,
            speech_output=self.speech_output,
            pattern_ids_used=self.pattern_ids_used,
            voice_id=self.voice_id,
            format=self.format,
            duration_seconds=self.duration_seconds,
            cached=True,
            timestamp=self.timestamp,
            metadata=self.metadata
        )