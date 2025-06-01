"""Pattern entity."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Optional, Pattern

from src.domain.exceptions import PatternError, ValidationError
from src.domain.value_objects import MathematicalDomain, PatternPriority


class PatternType(Enum):
    """Pattern type enumeration."""
    
    REGEX = auto()
    LITERAL = auto()
    TEMPLATE = auto()
    COMPOSITE = auto()


class PatternContext(Enum):
    """Pattern context enumeration."""
    
    INLINE = auto()
    DISPLAY = auto()
    EQUATION = auto()
    THEOREM = auto()
    PROOF = auto()
    ANY = auto()


@dataclass
class PronunciationHint:
    """Pronunciation hint for pattern output."""
    
    emphasis: Optional[str] = None
    pause_before: Optional[int] = None  # milliseconds
    pause_after: Optional[int] = None  # milliseconds
    rate: Optional[float] = None  # speaking rate multiplier
    pitch: Optional[float] = None  # pitch multiplier
    volume: Optional[float] = None  # volume multiplier


@dataclass
class PatternCondition:
    """Condition for pattern application."""
    
    type: str  # "preceding", "following", "contains", "context"
    value: str
    negate: bool = False
    
    def evaluate(self, context: dict[str, Any]) -> bool:
        """Evaluate condition against context."""
        # Implementation depends on condition type
        result = False
        
        if self.type == "context":
            result = context.get("type") == self.value
        elif self.type == "preceding":
            result = context.get("preceding", "").endswith(self.value)
        elif self.type == "following":
            result = context.get("following", "").startswith(self.value)
        elif self.type == "contains":
            full_text = context.get("full_text", "")
            result = self.value in full_text
            
        return not result if self.negate else result


@dataclass
class PatternEntity:
    """Pattern entity representing a transformation rule."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    pattern: str = ""
    pattern_type: PatternType = PatternType.REGEX
    output_template: str = ""
    priority: PatternPriority = field(default_factory=PatternPriority.medium)
    domain: MathematicalDomain = field(default_factory=MathematicalDomain.general)
    contexts: list[PatternContext] = field(default_factory=lambda: [PatternContext.ANY])
    conditions: list[PatternCondition] = field(default_factory=list)
    pronunciation_hints: PronunciationHint = field(default_factory=PronunciationHint)
    examples: list[dict[str, str]] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    author: str = "system"
    active: bool = True
    
    # Runtime fields
    _compiled_pattern: Optional[Pattern[str]] = field(default=None, init=False, repr=False)
    _match_count: int = field(default=0, init=False, repr=False)
    _error_count: int = field(default=0, init=False, repr=False)
    
    def __post_init__(self) -> None:
        """Validate and compile pattern."""
        self.validate()
        if self.pattern_type == PatternType.REGEX:
            self._compile_pattern()
    
    def validate(self) -> None:
        """Validate pattern entity."""
        if not self.pattern:
            raise ValidationError("Pattern cannot be empty", field="pattern")
            
        if not self.output_template:
            raise ValidationError("Output template cannot be empty", field="output_template")
            
        if not self.name:
            self.name = f"pattern_{self.id[:8]}"
            
        # Validate examples
        for example in self.examples:
            if "input" not in example or "output" not in example:
                raise ValidationError(
                    "Pattern examples must have 'input' and 'output' fields",
                    field="examples"
                )
    
    def _compile_pattern(self) -> None:
        """Compile regex pattern."""
        try:
            self._compiled_pattern = re.compile(self.pattern)
        except re.error as e:
            raise PatternError(
                f"Invalid regex pattern: {e}",
                pattern_id=self.id
            )
    
    def matches(self, text: str, context: Optional[dict[str, Any]] = None) -> bool:
        """Check if pattern matches text."""
        # Check conditions first
        if context and self.conditions:
            if not all(cond.evaluate(context) for cond in self.conditions):
                return False
        
        # Check pattern
        if self.pattern_type == PatternType.REGEX:
            if self._compiled_pattern:
                return bool(self._compiled_pattern.search(text))
        elif self.pattern_type == PatternType.LITERAL:
            return self.pattern in text
            
        return False
    
    def apply(self, text: str, context: Optional[dict[str, Any]] = None) -> tuple[str, bool]:
        """Apply pattern to text.
        
        Returns:
            Tuple of (transformed_text, was_applied)
        """
        if not self.matches(text, context):
            return text, False
            
        try:
            if self.pattern_type == PatternType.REGEX and self._compiled_pattern:
                result = self._compiled_pattern.sub(self.output_template, text)
                self._match_count += 1
                return result, True
            elif self.pattern_type == PatternType.LITERAL:
                result = text.replace(self.pattern, self.output_template)
                self._match_count += 1
                return result, True
        except Exception as e:
            self._error_count += 1
            raise PatternError(
                f"Error applying pattern: {e}",
                pattern_id=self.id
            )
            
        return text, False
    
    def find_all_matches(self, text: str) -> list[tuple[int, int, str]]:
        """Find all matches in text.
        
        Returns:
            List of (start, end, matched_text) tuples
        """
        matches = []
        
        if self.pattern_type == PatternType.REGEX and self._compiled_pattern:
            for match in self._compiled_pattern.finditer(text):
                matches.append((match.start(), match.end(), match.group()))
        elif self.pattern_type == PatternType.LITERAL:
            start = 0
            while True:
                pos = text.find(self.pattern, start)
                if pos == -1:
                    break
                end = pos + len(self.pattern)
                matches.append((pos, end, self.pattern))
                start = end
                
        return matches
    
    def get_statistics(self) -> dict[str, Any]:
        """Get pattern usage statistics."""
        return {
            "id": self.id,
            "name": self.name,
            "match_count": self._match_count,
            "error_count": self._error_count,
            "success_rate": (
                self._match_count / (self._match_count + self._error_count)
                if (self._match_count + self._error_count) > 0
                else 0.0
            ),
            "priority": self.priority.value,
            "domain": self.domain.value,
            "active": self.active
        }
    
    def update(self, **kwargs: Any) -> None:
        """Update pattern fields."""
        allowed_fields = {
            "name", "description", "output_template", "priority",
            "conditions", "pronunciation_hints", "examples", "tags", "active"
        }
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(self, key, value)
                
        self.updated_at = datetime.utcnow()
        self.version = self._increment_version()
    
    def _increment_version(self) -> str:
        """Increment version number."""
        parts = self.version.split(".")
        parts[-1] = str(int(parts[-1]) + 1)
        return ".".join(parts)
    
    def clone(self) -> PatternEntity:
        """Create a clone of this pattern."""
        return PatternEntity(
            id=str(uuid.uuid4()),
            name=f"{self.name}_copy",
            description=self.description,
            pattern=self.pattern,
            pattern_type=self.pattern_type,
            output_template=self.output_template,
            priority=self.priority,
            domain=self.domain,
            contexts=self.contexts.copy(),
            conditions=self.conditions.copy(),
            pronunciation_hints=self.pronunciation_hints,
            examples=self.examples.copy(),
            tags=self.tags.copy(),
            author=self.author,
            active=self.active
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "pattern": self.pattern,
            "pattern_type": self.pattern_type.name,
            "output_template": self.output_template,
            "priority": self.priority.value,
            "domain": self.domain.value,
            "contexts": [ctx.name for ctx in self.contexts],
            "conditions": [
                {"type": c.type, "value": c.value, "negate": c.negate}
                for c in self.conditions
            ],
            "pronunciation_hints": {
                k: v for k, v in self.pronunciation_hints.__dict__.items()
                if v is not None
            },
            "examples": self.examples,
            "tags": list(self.tags),
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "author": self.author,
            "active": self.active,
            "statistics": self.get_statistics()
        }