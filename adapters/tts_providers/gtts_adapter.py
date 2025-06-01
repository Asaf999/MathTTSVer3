"""
Google Text-to-Speech (gTTS) provider adapter.

This adapter integrates the gTTS library which uses Google Translate's
text-to-speech API. It's free but has limitations.
"""

import asyncio
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
import tempfile
from concurrent.futures import ThreadPoolExecutor
import io

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


class GTTSAdapter(TTSProviderAdapter):
    """Adapter for Google Text-to-Speech (gTTS) service."""
    
    # gTTS supported languages (subset)
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'ja': 'Japanese',
        'ko': 'Korean',
        'zh': 'Chinese'
    }
    
    # TLD to accent mapping for English
    ENGLISH_ACCENTS = {
        'com': 'United States',
        'co.uk': 'United Kingdom',
        'ca': 'Canada',
        'co.in': 'India',
        'com.au': 'Australia',
        'ie': 'Ireland',
        'co.za': 'South Africa'
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize gTTS adapter."""
        super().__init__(config)
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._gtts_available = False
        
    async def initialize(self) -> None:
        """Initialize the gTTS provider."""
        try:
            logger.info("Initializing gTTS provider")
            
            # Check if gTTS is available
            try:
                import gtts
                self._gtts_available = True
            except ImportError:
                raise TTSProviderError("gTTS not installed. Run: pip install gtts")
            
            self._initialized = True
            logger.info("gTTS provider initialized")
            
        except Exception as e:
            logger.error("Failed to initialize gTTS", error=str(e))
            raise TTSProviderError(f"Failed to initialize gTTS: {e}")
    
    async def close(self) -> None:
        """Close the provider."""
        self._executor.shutdown(wait=True)
        self._initialized = False
        logger.info("gTTS provider closed")
    
    async def synthesize(
        self,
        text: Union[str, SpeechText],
        options: TTSOptions
    ) -> AudioData:
        """
        Synthesize speech using gTTS.
        
        Note: gTTS has limited options - no rate/pitch/volume control.
        """
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
            # Import gTTS
            from gtts import gTTS
            
            # Extract language and TLD from voice_id
            # Format: "lang-TLD" e.g., "en-com", "en-co.uk"
            parts = options.voice_id.split('-', 1)
            lang = parts[0] if parts else 'en'
            tld = parts[1] if len(parts) > 1 else 'com'
            
            logger.debug(
                "Synthesizing with gTTS",
                text_length=len(text_content),
                language=lang,
                tld=tld
            )
            
            # Create gTTS object
            # gTTS doesn't support rate/pitch/volume adjustments
            if options.rate != 1.0 or options.pitch != 1.0 or options.volume != 1.0:
                logger.warning(
                    "gTTS doesn't support rate/pitch/volume adjustments",
                    rate=options.rate,
                    pitch=options.pitch,
                    volume=options.volume
                )
            
            # Run gTTS in thread pool (it's blocking)
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                self._executor,
                self._synthesize_sync,
                text_content,
                lang,
                tld,
                options.format
            )
            
            # Estimate duration (gTTS doesn't provide it)
            words = len(text_content.split())
            duration = words * 0.4  # Approximate 150 words per minute
            
            logger.info(
                "gTTS synthesis completed",
                size_bytes=len(audio_data),
                duration_seconds=duration
            )
            
            return AudioData(
                data=audio_data,
                format=options.format,
                sample_rate=24000,  # gTTS default
                duration_seconds=duration
            )
            
        except Exception as e:
            logger.error(
                "gTTS synthesis failed",
                error=str(e)
            )
            raise TTSProviderError(f"gTTS synthesis failed: {e}")
    
    def _synthesize_sync(
        self,
        text: str,
        lang: str,
        tld: str,
        format: AudioFormat
    ) -> bytes:
        """Synchronous synthesis for thread pool execution."""
        from gtts import gTTS
        
        # Create gTTS instance
        tts = gTTS(text=text, lang=lang, tld=tld, slow=False)
        
        # Save to bytes buffer
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        return fp.read()
    
    async def list_voices(
        self,
        language: Optional[str] = None
    ) -> List[Voice]:
        """List available voices from gTTS."""
        if not self._initialized:
            await self.initialize()
        
        voices = []
        
        # Add voices for each supported language
        for lang_code, lang_name in self.SUPPORTED_LANGUAGES.items():
            if language and not lang_code.startswith(language):
                continue
            
            if lang_code == 'en':
                # Add different English accents
                for tld, accent in self.ENGLISH_ACCENTS.items():
                    voice = Voice(
                        id=f"{lang_code}-{tld}",
                        name=f"{lang_name} ({accent})",
                        language=lang_code,
                        gender=VoiceGender.NEUTRAL,  # gTTS doesn't specify gender
                        description=f"Google TTS {accent} accent"
                    )
                    voices.append(voice)
            else:
                # Single voice per language
                voice = Voice(
                    id=lang_code,
                    name=lang_name,
                    language=lang_code,
                    gender=VoiceGender.NEUTRAL,
                    description=f"Google TTS {lang_name}"
                )
                voices.append(voice)
        
        logger.debug(
            "Listed gTTS voices",
            total_count=len(voices),
            language_filter=language
        )
        
        return voices
    
    def is_available(self) -> bool:
        """Check if gTTS is available."""
        try:
            import gtts
            # gTTS requires internet connection
            # We could check connectivity here
            return True
        except ImportError:
            return False
    
    def supports_ssml(self) -> bool:
        """gTTS does not support SSML."""
        return False
    
    def supports_streaming(self) -> bool:
        """gTTS does not support streaming."""
        return False