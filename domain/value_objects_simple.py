"""
Simplified value objects for testing.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LaTeXExpression:
    """Simple LaTeX expression value object."""
    value: str
    
    def __post_init__(self):
        """Validate expression."""
        if not self.value or not self.value.strip():
            raise ValueError("LaTeX expression cannot be empty")
    
    def __str__(self):
        return self.value


@dataclass(frozen=True) 
class SpeechText:
    """Simple speech text value object."""
    value: str
    
    def __post_init__(self):
        """Validate speech text."""
        if not self.value or not self.value.strip():
            raise ValueError("Speech text cannot be empty")
        
        # Normalize whitespace
        object.__setattr__(self, 'value', ' '.join(self.value.split()))
    
    @property
    def is_ssml(self) -> bool:
        """Check if text contains SSML."""
        return "<speak>" in self.value and "</speak>" in self.value