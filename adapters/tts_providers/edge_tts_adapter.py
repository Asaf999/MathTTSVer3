"""
Edge-TTS provider adapter.

This adapter integrates Microsoft Edge's text-to-speech service,
which provides high-quality neural voices for free.
"""

import asyncio
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
import tempfile
import edge_tts

from .base import (
    TTSProviderAdapter,
    TTSProviderError,
    TTSOptions,
    AudioData,
    AudioFormat,
    Voice,
    VoiceGender,
    SpeechText
)
from .ssml_converter import SSMLConverter
from src.infrastructure.logging import get_logger


logger = get_logger(__name__)


class EdgeTTSAdapter(TTSProviderAdapter):
    """Adapter for Microsoft Edge TTS service."""
    
    # Mapping of edge-tts voices to our Voice model
    VOICE_MAPPING = {
        "en-US-AriaNeural": ("Aria", VoiceGender.FEMALE, "Natural, conversational"),
        "en-US-JennyNeural": ("Jenny", VoiceGender.FEMALE, "General purpose"),
        "en-US-GuyNeural": ("Guy", VoiceGender.MALE, "General purpose"),
        "en-US-EricNeural": ("Eric", VoiceGender.MALE, "News narration"),
        "en-GB-SoniaNeural": ("Sonia", VoiceGender.FEMALE, "British accent"),
        "en-GB-RyanNeural": ("Ryan", VoiceGender.MALE, "British accent"),
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Edge-TTS adapter."""
        super().__init__(config)
        self._voice_list: Optional[List[Dict[str, Any]]] = None
        self._ssml_converter = SSMLConverter(provider="edge-tts")
    
    async def initialize(self) -> None:
        """
        Initialize the Edge-TTS provider.
        
        Edge-TTS doesn't require authentication, but we'll
        pre-fetch the voice list for better performance.
        """
        try:
            logger.info("Initializing Edge-TTS provider")
            self._voice_list = await edge_tts.list_voices()
            self._initialized = True
            logger.info(
                "Edge-TTS provider initialized",
                voice_count=len(self._voice_list) if self._voice_list else 0
            )
        except Exception as e:
            logger.error("Failed to initialize Edge-TTS", error=str(e))
            raise TTSProviderError(f"Failed to initialize Edge-TTS: {e}")
    
    async def close(self) -> None:
        """Close the provider (no-op for Edge-TTS)."""
        self._initialized = False
        logger.info("Edge-TTS provider closed")
    
    async def synthesize(
        self,
        text: Union[str, SpeechText],
        options: TTSOptions
    ) -> AudioData:
        """
        Synthesize speech using Edge-TTS.
        
        Args:
            text: Text to synthesize
            options: TTS options
            
        Returns:
            Synthesized audio data
        """
        if not self._initialized:
            await self.initialize()
        
        # Extract text content
        if isinstance(text, SpeechText):
            # Convert to SSML if enabled and we have a SpeechText object
            if options.ssml_enabled and hasattr(text, 'ssml'):
                text_content = self._ssml_converter.convert(text)
                is_ssml = True
            else:
                text_content = text.plain_text
                is_ssml = False
        else:
            text_content = text
            is_ssml = False
        
        # Validate options
        self.validate_options(options)
        
        try:
            logger.debug(
                "Synthesizing with Edge-TTS",
                text_length=len(text_content),
                voice=options.voice_id,
                rate=options.rate,
                pitch=options.pitch,
                volume=options.volume
            )
            
            # Create communicate object
            communicate = edge_tts.Communicate(
                text_content,
                options.voice_id,
                rate=self._format_rate(options.rate),
                pitch=self._format_pitch(options.pitch),
                volume=self._format_volume(options.volume)
            )
            
            # Synthesize to temporary file
            with tempfile.NamedTemporaryFile(
                suffix=f".{options.format.value}",
                delete=False
            ) as tmp_file:
                tmp_path = tmp_file.name
            
            try:
                await communicate.save(tmp_path)
                
                # Read the audio data
                audio_data = Path(tmp_path).read_bytes()
                
                # Calculate duration (approximate based on text length)
                # Edge-TTS doesn't provide duration directly
                words = len(text_content.split())
                duration = words * 0.4  # Approximate 150 words per minute
                
                logger.info(
                    "Edge-TTS synthesis completed",
                    size_bytes=len(audio_data),
                    duration_seconds=duration
                )
                
                return AudioData(
                    data=audio_data,
                    format=options.format,
                    sample_rate=options.sample_rate,
                    duration_seconds=duration
                )
                
            finally:
                # Clean up temporary file
                Path(tmp_path).unlink(missing_ok=True)
                
        except Exception as e:
            logger.error(
                "Edge-TTS synthesis failed",
                error=str(e),
                voice=options.voice_id
            )
            raise TTSProviderError(f"Edge-TTS synthesis failed: {e}")
    
    async def list_voices(
        self,
        language: Optional[str] = None
    ) -> List[Voice]:
        """
        List available voices from Edge-TTS.
        
        Args:
            language: Optional language filter
            
        Returns:
            List of available voices
        """
        if not self._initialized:
            await self.initialize()
        
        if not self._voice_list:
            self._voice_list = await edge_tts.list_voices()
        
        voices = []
        for voice_data in self._voice_list:
            # Filter by language if specified
            if language and not voice_data["Locale"].startswith(language):
                continue
            
            # Create Voice object
            voice_id = voice_data["ShortName"]
            
            # Determine gender
            gender = VoiceGender.NEUTRAL
            if voice_data.get("Gender") == "Female":
                gender = VoiceGender.FEMALE
            elif voice_data.get("Gender") == "Male":
                gender = VoiceGender.MALE
            
            # Get friendly name and description from mapping if available
            if voice_id in self.VOICE_MAPPING:
                name, mapped_gender, description = self.VOICE_MAPPING[voice_id]
                gender = mapped_gender
            else:
                name = voice_data.get("FriendlyName", voice_id)
                description = None
            
            voice = Voice(
                id=voice_id,
                name=name,
                language=voice_data["Locale"],
                gender=gender,
                description=description
            )
            voices.append(voice)
        
        logger.debug(
            "Listed Edge-TTS voices",
            total_count=len(voices),
            language_filter=language
        )
        
        return voices
    
    def is_available(self) -> bool:
        """Check if Edge-TTS is available."""
        try:
            # Edge-TTS is generally available if the module is installed
            import edge_tts
            return True
        except ImportError:
            return False
    
    def supports_ssml(self) -> bool:
        """Edge-TTS supports SSML."""
        return True
    
    def supports_streaming(self) -> bool:
        """Edge-TTS supports streaming synthesis."""
        return True
    
    async def synthesize_batch(
        self,
        texts: List[Union[str, SpeechText]],
        options: TTSOptions
    ) -> List[AudioData]:
        """
        Synthesize multiple texts in parallel.
        
        Edge-TTS handles parallel requests well.
        """
        tasks = [
            self.synthesize(text, options)
            for text in texts
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check for errors
        audio_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    "Batch synthesis failed for item",
                    index=i,
                    error=str(result)
                )
                raise TTSProviderError(
                    f"Batch synthesis failed for item {i}: {result}"
                )
            audio_results.append(result)
        
        return audio_results
    
    def _format_rate(self, rate: float) -> str:
        """Format rate for Edge-TTS (percentage change)."""
        # Edge-TTS expects rate as percentage change
        # 1.0 = normal, 0.5 = -50%, 2.0 = +100%
        percentage = (rate - 1.0) * 100
        return f"{percentage:+.0f}%"
    
    def _format_pitch(self, pitch: float) -> str:
        """Format pitch for Edge-TTS (percentage change)."""
        # Similar to rate
        percentage = (pitch - 1.0) * 100
        return f"{percentage:+.0f}%"
    
    def _format_volume(self, volume: float) -> str:
        """Format volume for Edge-TTS (percentage)."""
        # Edge-TTS expects volume as percentage (0-100)
        percentage = volume * 100
        return f"{percentage:.0f}%"