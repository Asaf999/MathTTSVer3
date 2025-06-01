"""Domain interfaces and protocols for MathTTS v3."""

from .pattern_repository import (
    PatternRepository,
    RepositoryError,
    PatternNotFoundError,
    DuplicatePatternError,
    InvalidPatternError
)

# Import TTSAdapter from the parent domain module
from ..interfaces import TTSAdapter

__all__ = [
    "PatternRepository",
    "RepositoryError", 
    "PatternNotFoundError",
    "DuplicatePatternError",
    "InvalidPatternError",
    "TTSAdapter"
]