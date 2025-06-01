"""
Domain interfaces (protocols).
"""

from typing import Protocol, List, Optional
from abc import abstractmethod

from .entities import PatternEntity
from .value_objects_tts import TTSOptions, AudioData, VoiceInfo


class PatternRepository(Protocol):
    """Interface for pattern repository."""
    
    @abstractmethod
    def add(self, pattern: PatternEntity) -> None:
        """Add a pattern."""
        pass
    
    @abstractmethod
    def get_by_id(self, pattern_id: str) -> Optional[PatternEntity]:
        """Get pattern by ID."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[PatternEntity]:
        """Get all patterns."""
        pass
    
    @abstractmethod
    def get_by_domain(self, domain: str) -> List[PatternEntity]:
        """Get patterns by domain."""
        pass
    
    @abstractmethod
    def update(self, pattern: PatternEntity) -> None:
        """Update a pattern."""
        pass
    
    @abstractmethod
    def delete(self, pattern_id: str) -> bool:
        """Delete a pattern."""
        pass
    
    @abstractmethod
    def exists(self, pattern_id: str) -> bool:
        """Check if pattern exists."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Count patterns."""
        pass


class TTSAdapter(Protocol):
    """Interface for TTS adapters."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the adapter."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close the adapter."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if adapter is available."""
        pass
    
    @abstractmethod
    async def synthesize(self, text: str, options: TTSOptions) -> AudioData:
        """Synthesize speech from text."""
        pass
    
    @abstractmethod
    async def list_voices(self, language: Optional[str] = None) -> List[VoiceInfo]:
        """List available voices."""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List:
        """Get supported audio formats."""
        pass