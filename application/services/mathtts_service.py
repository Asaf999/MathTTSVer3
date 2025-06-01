"""
Main MathTTS service implementation.
"""

from typing import Optional, Dict, Any
import logging

from domain.interfaces import PatternRepository, TTSAdapter
from domain.services import PatternMatcher
from domain.value_objects import LaTeXExpression, TTSOptions, AudioData
from infrastructure.cache import AudioCache


logger = logging.getLogger(__name__)


class MathTTSService:
    """
    Main application service for converting LaTeX to speech.
    
    This service orchestrates the pattern matching and TTS conversion process.
    """
    
    def __init__(
        self,
        pattern_repository: PatternRepository,
        tts_adapter: TTSAdapter,
        audio_cache: Optional[AudioCache] = None
    ):
        """
        Initialize MathTTS service.
        
        Args:
            pattern_repository: Repository containing LaTeX patterns
            tts_adapter: TTS provider adapter
            audio_cache: Optional audio cache
        """
        self.pattern_repository = pattern_repository
        self.tts_adapter = tts_adapter
        self.audio_cache = audio_cache
        self.pattern_matcher = PatternMatcher(pattern_repository)
    
    async def convert_latex_to_speech(
        self,
        latex: str,
        options: Optional[TTSOptions] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AudioData:
        """
        Convert LaTeX expression to speech audio.
        
        Args:
            latex: LaTeX expression to convert
            options: TTS options (voice, rate, etc.)
            metadata: Optional metadata for caching
            
        Returns:
            Audio data containing the speech
        """
        # Use default options if not provided
        if options is None:
            options = TTSOptions()
        
        # Check cache first
        cache_key = None
        if self.audio_cache:
            cache_key = self.audio_cache.generate_key(latex, options, metadata)
            cached_audio = await self.audio_cache.get(cache_key)
            if cached_audio:
                logger.info(f"Cache hit for LaTeX: {latex[:50]}...")
                return cached_audio
        
        # Convert LaTeX to speech text
        latex_expr = LaTeXExpression(latex)
        speech_text = self.pattern_matcher.process_expression(latex_expr)
        
        logger.info(f"Converted LaTeX '{latex[:50]}...' to '{speech_text.value[:50]}...'")
        
        # Synthesize speech
        audio_data = await self.tts_adapter.synthesize(speech_text.value, options)
        
        # Cache the result
        if self.audio_cache and cache_key:
            await self.audio_cache.put(cache_key, audio_data, metadata)
        
        return audio_data
    
    async def batch_convert(
        self,
        latex_expressions: list[str],
        options: Optional[TTSOptions] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> list[AudioData]:
        """
        Convert multiple LaTeX expressions to speech.
        
        Args:
            latex_expressions: List of LaTeX expressions
            options: TTS options to use for all expressions
            metadata: Optional metadata for caching
            
        Returns:
            List of audio data for each expression
        """
        results = []
        
        for latex in latex_expressions:
            try:
                audio = await self.convert_latex_to_speech(latex, options, metadata)
                results.append(audio)
            except Exception as e:
                logger.error(f"Failed to convert '{latex}': {e}")
                # Continue with other expressions
                continue
        
        return results
    
    def get_pattern_stats(self) -> Dict[str, Any]:
        """
        Get statistics about loaded patterns.
        
        Returns:
            Dictionary with pattern statistics
        """
        all_patterns = self.pattern_repository.get_all()
        
        # Group by domain
        domains = {}
        for pattern in all_patterns:
            domain = pattern.domain
            if domain not in domains:
                domains[domain] = 0
            domains[domain] += 1
        
        # Priority distribution
        priority_ranges = {
            "low": 0,      # 1-500
            "medium": 0,   # 501-1000
            "high": 0,     # 1001-1500
            "critical": 0  # 1501+
        }
        
        for pattern in all_patterns:
            priority = pattern.priority.value
            if priority <= 500:
                priority_ranges["low"] += 1
            elif priority <= 1000:
                priority_ranges["medium"] += 1
            elif priority <= 1500:
                priority_ranges["high"] += 1
            else:
                priority_ranges["critical"] += 1
        
        return {
            "total_patterns": len(all_patterns),
            "domains": domains,
            "priority_distribution": priority_ranges,
            "cache_enabled": self.audio_cache is not None
        }
    
    async def warmup_cache(self, common_expressions: list[str]) -> int:
        """
        Pre-generate audio for common expressions.
        
        Args:
            common_expressions: List of common LaTeX expressions
            
        Returns:
            Number of expressions cached
        """
        if not self.audio_cache:
            return 0
        
        cached_count = 0
        options = TTSOptions()  # Use default options
        
        for latex in common_expressions:
            try:
                await self.convert_latex_to_speech(latex, options)
                cached_count += 1
            except Exception as e:
                logger.warning(f"Failed to cache '{latex}': {e}")
        
        return cached_count