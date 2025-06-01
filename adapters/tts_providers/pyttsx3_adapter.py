"""
pyttsx3 provider adapter.

This adapter integrates pyttsx3 which provides offline text-to-speech
using system voices (SAPI5 on Windows, NSSpeechSynthesizer on macOS,
espeak on Linux).
"""

import asyncio
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
import tempfile
from concurrent.futures import ThreadPoolExecutor
import threading
import platform

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
from src.infrastructure.logging import get_logger


logger = get_logger(__name__)


class Pyttsx3Adapter(TTSProviderAdapter):
    """Adapter for pyttsx3 offline TTS."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize pyttsx3 adapter."""
        super().__init__(config)
        self._executor = ThreadPoolExecutor(max_workers=1)  # pyttsx3 is not thread-safe
        self._engine = None
        self._engine_lock = threading.Lock()
        self._available_voices = []
        
    async def initialize(self) -> None:
        """Initialize the pyttsx3 provider."""
        try:
            logger.info("Initializing pyttsx3 provider")
            
            # Initialize in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self._executor,
                self._initialize_engine
            )
            
            self._initialized = True
            logger.info(
                "pyttsx3 provider initialized",
                platform=platform.system(),
                voice_count=len(self._available_voices)
            )
            
        except Exception as e:
            logger.error("Failed to initialize pyttsx3", error=str(e))
            raise TTSProviderError(f"Failed to initialize pyttsx3: {e}")
    
    def _initialize_engine(self) -> None:
        """Initialize pyttsx3 engine (synchronous)."""
        try:
            import pyttsx3
        except ImportError:
            raise TTSProviderError("pyttsx3 not installed. Run: pip install pyttsx3")
        
        with self._engine_lock:
            self._engine = pyttsx3.init()
            
            # Get available voices
            voices = self._engine.getProperty('voices')
            self._available_voices = voices or []
            
            # Set default properties
            self._engine.setProperty('rate', 150)  # Words per minute
            self._engine.setProperty('volume', 1.0)  # 0-1
    
    async def close(self) -> None:
        """Close the provider."""
        if self._engine:
            with self._engine_lock:
                try:
                    self._engine.stop()
                except:
                    pass
        
        self._executor.shutdown(wait=True)
        self._initialized = False
        logger.info("pyttsx3 provider closed")
    
    async def synthesize(
        self,
        text: Union[str, SpeechText],
        options: TTSOptions
    ) -> AudioData:
        """Synthesize speech using pyttsx3."""
        if not self._initialized:
            await self.initialize()
        
        # Extract text content
        if isinstance(text, SpeechText):
            text_content = text.plain_text
        else:
            text_content = text
        
        # Validate options
        self.validate_options(options)
        
        try:
            logger.debug(
                "Synthesizing with pyttsx3",
                text_length=len(text_content),
                voice=options.voice_id,
                rate=options.rate,
                volume=options.volume
            )
            
            # Run synthesis in thread pool
            loop = asyncio.get_event_loop()
            audio_file = await loop.run_in_executor(
                self._executor,
                self._synthesize_sync,
                text_content,
                options
            )
            
            # Read the audio data
            audio_data = Path(audio_file).read_bytes()
            
            # Clean up
            Path(audio_file).unlink(missing_ok=True)
            
            # Estimate duration
            words = len(text_content.split())
            wpm = 150 * options.rate  # Base rate * rate multiplier
            duration = (words / wpm) * 60 if wpm > 0 else 1.0
            
            logger.info(
                "pyttsx3 synthesis completed",
                size_bytes=len(audio_data),
                duration_seconds=duration
            )
            
            return AudioData(
                data=audio_data,
                format=options.format,
                sample_rate=22050,  # Default for most engines
                duration_seconds=duration
            )
            
        except Exception as e:
            logger.error(
                "pyttsx3 synthesis failed",
                error=str(e)
            )
            raise TTSProviderError(f"pyttsx3 synthesis failed: {e}")
    
    def _synthesize_sync(
        self,
        text: str,
        options: TTSOptions
    ) -> str:
        """Synchronous synthesis for thread pool execution."""
        with self._engine_lock:
            # Set voice
            try:
                for voice in self._available_voices:
                    if voice.id == options.voice_id:
                        self._engine.setProperty('voice', voice.id)
                        break
            except:
                logger.warning(f"Failed to set voice: {options.voice_id}")
            
            # Set properties
            # Convert our normalized values to pyttsx3 values
            rate = self._engine.getProperty('rate')
            self._engine.setProperty('rate', int(rate * options.rate))
            self._engine.setProperty('volume', options.volume)
            
            # Note: pyttsx3 doesn't support pitch adjustment
            if options.pitch != 1.0:
                logger.warning(
                    "pyttsx3 doesn't support pitch adjustment",
                    requested_pitch=options.pitch
                )
            
            # Save to file
            with tempfile.NamedTemporaryFile(
                suffix=f'.{options.format.value}',
                delete=False
            ) as tmp_file:
                tmp_path = tmp_file.name
            
            self._engine.save_to_file(text, tmp_path)
            self._engine.runAndWait()
            
            return tmp_path
    
    async def list_voices(
        self,
        language: Optional[str] = None
    ) -> List[Voice]:
        """List available voices from pyttsx3."""
        if not self._initialized:
            await self.initialize()
        
        voices = []
        
        for voice_obj in self._available_voices:
            # Filter by language if specified
            if language:
                voice_lang = getattr(voice_obj, 'languages', [])
                if voice_lang and not any(language in lang for lang in voice_lang):
                    continue
            
            # Determine gender from voice properties
            gender = VoiceGender.NEUTRAL
            voice_name = voice_obj.name.lower() if voice_obj.name else ""
            
            if any(indicator in voice_name for indicator in ['female', 'woman', 'girl']):
                gender = VoiceGender.FEMALE
            elif any(indicator in voice_name for indicator in ['male', 'man', 'boy']):
                gender = VoiceGender.MALE
            
            # Get language
            voice_languages = getattr(voice_obj, 'languages', [])
            voice_language = voice_languages[0] if voice_languages else 'en'
            
            voice = Voice(
                id=voice_obj.id,
                name=voice_obj.name or voice_obj.id,
                language=voice_language,
                gender=gender,
                description=f"{platform.system()} system voice"
            )
            voices.append(voice)
        
        logger.debug(
            "Listed pyttsx3 voices",
            total_count=len(voices),
            language_filter=language
        )
        
        return voices
    
    def is_available(self) -> bool:
        """Check if pyttsx3 is available."""
        try:
            import pyttsx3
            # Try to initialize engine
            engine = pyttsx3.init()
            engine.stop()
            return True
        except:
            return False
    
    def supports_ssml(self) -> bool:
        """pyttsx3 does not support SSML."""
        return False
    
    def supports_streaming(self) -> bool:
        """pyttsx3 does not support streaming."""
        return False