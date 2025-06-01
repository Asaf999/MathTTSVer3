"""
TTS-related value objects for the domain layer.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class AudioFormat(Enum):
    """Audio format enumeration."""
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    FLAC = "flac"
    
    @property
    def extension(self) -> str:
        """Get file extension for format."""
        return f".{self.value}"
    
    @property
    def mime_type(self) -> str:
        """Get MIME type for format."""
        mime_types = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "ogg": "audio/ogg",
            "flac": "audio/flac"
        }
        return mime_types[self.value]


class VoiceGender(Enum):
    """Voice gender enumeration."""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class TTSOptions:
    """TTS synthesis options."""
    voice_id: str = "en-US-AriaNeural"
    rate: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    format: AudioFormat = AudioFormat.MP3
    language: str = "en-US"
    
    def __post_init__(self):
        """Validate options."""
        if not 0.25 <= self.rate <= 3.0:
            raise ValueError("Rate must be between 0.25 and 3.0")
        
        if not 0.5 <= self.pitch <= 2.0:
            raise ValueError("Pitch must be between 0.5 and 2.0")
        
        if not 0.0 <= self.volume <= 1.0:
            raise ValueError("Volume must be between 0.0 and 1.0")


@dataclass(frozen=True)
class AudioData:
    """Audio data value object."""
    data: bytes
    format: AudioFormat
    sample_rate: int
    duration_seconds: float
    
    def __post_init__(self):
        """Validate audio data."""
        if not self.data:
            raise ValueError("Audio data cannot be empty")
        
        if self.sample_rate <= 0:
            raise ValueError("Sample rate must be positive")
        
        if self.duration_seconds <= 0:
            raise ValueError("Duration must be positive")
    
    @property
    def size_bytes(self) -> int:
        """Get size of audio data in bytes."""
        return len(self.data)


@dataclass(frozen=True)
class VoiceInfo:
    """Voice information."""
    id: str
    name: str
    language: str
    gender: VoiceGender
    provider: str
    locale: Optional[str] = None
    
    def __post_init__(self):
        """Validate voice info."""
        if not self.id:
            raise ValueError("Voice ID cannot be empty")
        
        if not self.name:
            raise ValueError("Voice name cannot be empty")