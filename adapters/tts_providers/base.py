"""
Base TTS provider adapter interface.

This module defines the abstract base class for all TTS provider adapters.
Each concrete adapter must implement these methods to integrate with the system.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from src.domain.value_objects import SpeechText


class AudioFormat(str, Enum):
    """Supported audio output formats."""
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    WEBM = "webm"


class VoiceGender(str, Enum):
    """Voice gender options."""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


@dataclass
class Voice:
    """Voice information."""
    id: str
    name: str
    language: str
    gender: VoiceGender
    description: Optional[str] = None
    styles: Optional[List[str]] = None
    
    @property
    def display_name(self) -> str:
        """Get display name for the voice."""
        return self.name or self.id


@dataclass
class TTSOptions:
    """TTS synthesis options."""
    voice_id: str
    rate: float = 1.0  # Speech rate multiplier (0.5-2.0)
    pitch: float = 1.0  # Pitch multiplier (0.5-2.0)
    volume: float = 1.0  # Volume multiplier (0.0-1.0)
    format: AudioFormat = AudioFormat.MP3
    sample_rate: int = 24000  # Sample rate in Hz
    style: Optional[str] = None  # Voice style (if supported)
    
    def validate(self) -> None:
        """Validate option values."""
        if not 0.5 <= self.rate <= 2.0:
            raise ValueError(f"Rate must be between 0.5 and 2.0, got {self.rate}")
        if not 0.5 <= self.pitch <= 2.0:
            raise ValueError(f"Pitch must be between 0.5 and 2.0, got {self.pitch}")
        if not 0.0 <= self.volume <= 1.0:
            raise ValueError(f"Volume must be between 0.0 and 1.0, got {self.volume}")


@dataclass
class AudioData:
    """Audio synthesis result."""
    data: bytes
    format: AudioFormat
    sample_rate: int
    duration_seconds: Optional[float] = None
    
    def save(self, path: Union[str, Path]) -> None:
        """Save audio data to file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.data)
    
    @property
    def size_bytes(self) -> int:
        """Get audio data size in bytes."""
        return len(self.data)


class TTSProviderError(Exception):
    """Base exception for TTS provider errors."""
    pass


class TTSProviderAdapter(ABC):
    """
    Abstract base class for TTS provider adapters.
    
    Each TTS provider (Azure, Google, Amazon, etc.) must implement
    this interface to integrate with the MathTTS system.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the TTS provider.
        
        Args:
            config: Provider-specific configuration
        """
        self.config = config or {}
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the provider (e.g., authenticate, establish connections).
        
        This method should be called before using the provider.
        
        Raises:
            TTSProviderError: If initialization fails
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """
        Close the provider and clean up resources.
        
        This method should be called when done using the provider.
        """
        pass
    
    @abstractmethod
    async def synthesize(
        self,
        text: Union[str, SpeechText],
        options: TTSOptions
    ) -> AudioData:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize (plain text or SpeechText with SSML)
            options: TTS synthesis options
            
        Returns:
            Audio data with synthesized speech
            
        Raises:
            TTSProviderError: If synthesis fails
        """
        pass
    
    @abstractmethod
    async def list_voices(
        self,
        language: Optional[str] = None
    ) -> List[Voice]:
        """
        List available voices.
        
        Args:
            language: Optional language filter (e.g., "en-US")
            
        Returns:
            List of available voices
            
        Raises:
            TTSProviderError: If listing fails
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is available and configured.
        
        Returns:
            True if provider can be used, False otherwise
        """
        pass
    
    @abstractmethod
    def supports_ssml(self) -> bool:
        """
        Check if the provider supports SSML input.
        
        Returns:
            True if SSML is supported, False otherwise
        """
        pass
    
    @abstractmethod
    def supports_streaming(self) -> bool:
        """
        Check if the provider supports streaming synthesis.
        
        Returns:
            True if streaming is supported, False otherwise
        """
        pass
    
    async def synthesize_batch(
        self,
        texts: List[Union[str, SpeechText]],
        options: TTSOptions
    ) -> List[AudioData]:
        """
        Synthesize multiple texts in batch.
        
        Default implementation processes sequentially.
        Providers can override for parallel processing.
        
        Args:
            texts: List of texts to synthesize
            options: TTS synthesis options
            
        Returns:
            List of audio data results
            
        Raises:
            TTSProviderError: If any synthesis fails
        """
        results = []
        for text in texts:
            audio = await self.synthesize(text, options)
            results.append(audio)
        return results
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return self.__class__.__name__.replace("Adapter", "")
    
    def validate_options(self, options: TTSOptions) -> None:
        """
        Validate TTS options for this provider.
        
        Args:
            options: Options to validate
            
        Raises:
            ValueError: If options are invalid
        """
        options.validate()
    
    async def __aenter__(self) -> "TTSProviderAdapter":
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()


class MockTTSProviderAdapter(TTSProviderAdapter):
    """Mock TTS provider for testing."""
    
    async def initialize(self) -> None:
        """Initialize mock provider."""
        self._initialized = True
    
    async def close(self) -> None:
        """Close mock provider."""
        self._initialized = False
    
    async def synthesize(
        self,
        text: Union[str, SpeechText],
        options: TTSOptions
    ) -> AudioData:
        """Generate mock audio data."""
        text_content = text if isinstance(text, str) else text.plain_text
        # Generate mock audio data (silent WAV header + data)
        wav_header = b"RIFF" + b"\x00" * 40  # Simplified WAV header
        mock_data = wav_header + b"\x00" * len(text_content) * 100
        
        return AudioData(
            data=mock_data,
            format=options.format,
            sample_rate=options.sample_rate,
            duration_seconds=len(text_content) * 0.1  # Mock duration
        )
    
    async def list_voices(
        self,
        language: Optional[str] = None
    ) -> List[Voice]:
        """List mock voices."""
        voices = [
            Voice(
                id="mock-voice-1",
                name="Mock Voice 1",
                language="en-US",
                gender=VoiceGender.FEMALE
            ),
            Voice(
                id="mock-voice-2",
                name="Mock Voice 2",
                language="en-US",
                gender=VoiceGender.MALE
            ),
        ]
        
        if language:
            voices = [v for v in voices if v.language == language]
        
        return voices
    
    def is_available(self) -> bool:
        """Mock provider is always available."""
        return True
    
    def supports_ssml(self) -> bool:
        """Mock provider supports SSML."""
        return True
    
    def supports_streaming(self) -> bool:
        """Mock provider doesn't support streaming."""
        return False