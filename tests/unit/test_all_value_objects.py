"""
Comprehensive tests for all value objects.
"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.domain.value_objects import *
from src.domain.value_objects_simple import *
from src.domain.value_objects_tts import *
from src.domain.exceptions import *


class TestAllValueObjects:
    """Test all value objects comprehensively."""
    
    def test_latex_expression_all_methods(self):
        """Test all LaTeXExpression methods."""
        # Valid expression
        expr = LaTeXExpression(r"\frac{1}{2}")
        assert expr.value == r"\frac{1}{2}"
        
        # Test properties
        assert isinstance(expr.normalized, str)
        assert expr.is_empty == False
        assert expr.length > 0
        
        # Test methods
        assert expr.contains("frac")
        assert not expr.contains("xyz")
        
        # Test validation
        with pytest.raises(ValueError):
            LaTeXExpression("")
        
        # Test long expression
        with pytest.raises(ValueError):
            LaTeXExpression("x" * 2000)
    
    def test_speech_text_all_methods(self):
        """Test all SpeechText methods."""
        text = SpeechText("Hello world")
        assert text.value == "Hello world"
        
        # Test with SSML
        text_ssml = SpeechText("Hello", ssml="<speak>Hello</speak>")
        assert text_ssml.ssml == "<speak>Hello</speak>"
        
        # Test empty
        with pytest.raises(ValueError):
            SpeechText("")
    
    def test_pattern_priority_all_cases(self):
        """Test PatternPriority comprehensively."""
        # Valid priorities
        p1 = PatternPriority(1000)
        p2 = PatternPriority(500)
        
        # Comparison
        assert p1 > p2
        assert p2 < p1
        assert p1 >= p2
        assert p2 <= p1
        assert p1 != p2
        
        # Bounds
        with pytest.raises(ValueError):
            PatternPriority(-1)
        with pytest.raises(ValueError):
            PatternPriority(2001)
        
        # Factory methods
        assert PatternPriority.high().value == 1000
        assert PatternPriority.medium().value == 500
        assert PatternPriority.low().value == 250
    
    def test_audience_level_all_cases(self):
        """Test AudienceLevel."""
        levels = ["elementary", "high_school", "undergraduate", "graduate", "research"]
        
        for level in levels:
            audience = AudienceLevel(level)
            assert audience.value == level
        
        # Invalid
        with pytest.raises(ValueError):
            AudienceLevel("invalid")
        
        # Properties
        assert AudienceLevel("graduate").is_advanced
        assert AudienceLevel("elementary").is_basic
    
    def test_mathematical_domain_all_cases(self):
        """Test MathematicalDomain."""
        domains = ["algebra", "calculus", "statistics", "logic", "general"]
        
        for domain in domains:
            d = MathematicalDomain(domain)
            assert d.value == domain
        
        # Invalid
        with pytest.raises(ValueError):
            MathematicalDomain("invalid")
        
        # Properties
        assert MathematicalDomain("calculus").is_analysis_related()
        assert not MathematicalDomain("algebra").is_analysis_related()
    
    def test_tts_options_all_fields(self):
        """Test TTSOptions."""
        from src.domain.value_objects_tts import TTSOptions, AudioFormat
        
        options = TTSOptions(
            voice="test-voice",
            format=AudioFormat.MP3,
            rate=1.5,
            pitch=0.8,
            volume=0.9
        )
        
        assert options.voice == "test-voice"
        assert options.format == AudioFormat.MP3
        assert options.rate == 1.5
        assert options.pitch == 0.8
        assert options.volume == 0.9
    
    def test_audio_data_all_fields(self):
        """Test AudioData."""
        from src.domain.value_objects_tts import AudioData, AudioFormat
        
        audio = AudioData(
            data=b"test_audio",
            format=AudioFormat.MP3,
            sample_rate=44100,
            duration_seconds=1.0
        )
        
        assert audio.data == b"test_audio"
        assert audio.format == AudioFormat.MP3
        assert audio.sample_rate == 44100
        assert audio.duration_seconds == 1.0
    
    def test_voice_info_all_fields(self):
        """Test VoiceInfo."""
        from src.domain.value_objects_tts import VoiceInfo, VoiceGender
        
        voice = VoiceInfo(
            id="test-voice",
            name="Test Voice",
            language="en-US",
            gender=VoiceGender.FEMALE,
            description="Test voice"
        )
        
        assert voice.id == "test-voice"
        assert voice.name == "Test Voice"
        assert voice.language == "en-US"
        assert voice.gender == VoiceGender.FEMALE
