"""
Mock TTS adapter for testing.
"""

from typing import List, Optional
from domain.interfaces import TTSAdapter
from domain.value_objects import TTSOptions, AudioData, AudioFormat, VoiceInfo, VoiceGender


class MockTTSAdapter(TTSAdapter):
    """Mock TTS adapter for testing purposes."""
    
    def __init__(self):
        """Initialize mock adapter."""
        self._initialized = False
        self._voices = [
            VoiceInfo(
                id="test-voice-male",
                name="Test Voice Male",
                language="en-US",
                gender=VoiceGender.MALE,
                provider="mock"
            ),
            VoiceInfo(
                id="test-voice-female",
                name="Test Voice Female",
                language="en-US",
                gender=VoiceGender.FEMALE,
                provider="mock"
            )
        ]
    
    async def initialize(self) -> None:
        """Initialize the mock adapter."""
        self._initialized = True
    
    async def close(self) -> None:
        """Close the mock adapter."""
        self._initialized = False
    
    def is_available(self) -> bool:
        """Check if mock adapter is available."""
        return self._initialized
    
    async def synthesize(self, text: str, options: TTSOptions) -> AudioData:
        """
        Mock speech synthesis.
        
        Args:
            text: Text to synthesize
            options: TTS options
            
        Returns:
            Mock audio data
        """
        if not self._initialized:
            raise RuntimeError("Mock adapter not initialized")
        
        # Create mock audio data
        mock_data = b"mock audio data"
        
        # Simulate different data based on format
        if options.format == AudioFormat.WAV:
            mock_data = b"RIFF" + b"\x00" * 40 + mock_data
        elif options.format == AudioFormat.MP3:
            mock_data = b"ID3" + mock_data
        
        # Simulate duration based on text length
        duration = len(text) * 0.05  # ~50ms per character
        
        return AudioData(
            data=mock_data,
            format=options.format,
            sample_rate=44100,
            duration_seconds=max(1.0, duration)  # Minimum 1 second
        )
    
    async def list_voices(self, language: Optional[str] = None) -> List[VoiceInfo]:
        """
        List available mock voices.
        
        Args:
            language: Optional language filter
            
        Returns:
            List of mock voices
        """
        if language:
            return [v for v in self._voices if v.language.startswith(language)]
        return self._voices.copy()
    
    def get_supported_formats(self) -> List[AudioFormat]:
        """Get supported audio formats."""
        return [AudioFormat.MP3, AudioFormat.WAV, AudioFormat.OGG]
    
    def estimate_duration(self, text: str, rate: float = 1.0) -> float:
        """
        Estimate audio duration.
        
        Args:
            text: Text to estimate
            rate: Speech rate
            
        Returns:
            Estimated duration in seconds
        """
        # Simple estimation: ~150 words per minute at normal rate
        words = len(text.split())
        minutes = words / (150 * rate)
        return minutes * 60