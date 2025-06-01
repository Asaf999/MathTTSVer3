"""
Unit tests for value objects.
"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from src.domain.value_objects import PatternPriority
from src.domain.value_objects_simple import LaTeXExpression, SpeechText
from src.domain.value_objects_tts import TTSOptions, AudioData, AudioFormat, VoiceGender
from src.domain.exceptions import ValidationError


class TestPatternPriority:
    """Test cases for PatternPriority value object."""
    
    def test_create_valid_priority(self):
        """Test creating valid priority values."""
        priority = PatternPriority(1000)
        assert priority.value == 1000
        
        priority_min = PatternPriority(0)
        assert priority_min.value == 0
        
        priority_max = PatternPriority(2000)
        assert priority_max.value == 2000
    
    def test_priority_validation(self):
        """Test priority validation."""
        # Too low
        with pytest.raises(ValidationError, match="Priority must be between"):
            PatternPriority(-1)
        
        # Too high
        with pytest.raises(ValidationError, match="Priority must be between"):
            PatternPriority(2001)
        
        # Negative
        with pytest.raises(ValidationError, match="Priority must be between"):
            PatternPriority(-100)
    
    def test_priority_comparison(self):
        """Test priority comparison."""
        p1 = PatternPriority(1000)
        p2 = PatternPriority(1500)
        p3 = PatternPriority(1000)
        
        assert p1 < p2
        assert p2 > p1
        assert p1 == p3
        assert p1 <= p3
        assert p2 >= p1
        assert p1 != p2
    
    def test_priority_hash(self):
        """Test priority hashing."""
        p1 = PatternPriority(1000)
        p2 = PatternPriority(1000)
        p3 = PatternPriority(2000)
        
        assert hash(p1) == hash(p2)
        assert hash(p1) != hash(p3)


class TestLaTeXExpression:
    """Test cases for LaTeXExpression value object."""
    
    def test_create_valid_expression(self):
        """Test creating valid LaTeX expressions."""
        expr = LaTeXExpression(r"\frac{1}{2}")
        assert expr.value == r"\frac{1}{2}"
        
        expr_complex = LaTeXExpression(r"\int_0^1 x^2 dx")
        assert expr_complex.value == r"\int_0^1 x^2 dx"
    
    def test_expression_validation(self):
        """Test expression validation."""
        # Empty expression
        with pytest.raises(ValueError, match="LaTeX expression cannot be empty"):
            LaTeXExpression("")
        
        # Whitespace only
        with pytest.raises(ValueError, match="LaTeX expression cannot be empty"):
            LaTeXExpression("   ")
    
    def test_expression_normalization(self):
        """Test expression normalization."""
        # Does not strip whitespace (but validates non-empty)
        expr = LaTeXExpression("  \\alpha  ")
        assert expr.value == "  \\alpha  "
        
        # Preserves internal whitespace
        expr = LaTeXExpression("x + y = z")
        assert expr.value == "x + y = z"
    
    def test_expression_equality(self):
        """Test expression equality."""
        expr1 = LaTeXExpression(r"\frac{1}{2}")
        expr2 = LaTeXExpression(r"\frac{1}{2}")
        expr3 = LaTeXExpression(r"\frac{2}{3}")
        
        assert expr1 == expr2
        assert expr1 != expr3
    
    def test_expression_str(self):
        """Test string representation."""
        expr = LaTeXExpression(r"\alpha + \beta")
        assert str(expr) == r"\alpha + \beta"


class TestSpeechText:
    """Test cases for SpeechText value object."""
    
    def test_create_valid_speech_text(self):
        """Test creating valid speech text."""
        text = SpeechText("one half")
        assert text.value == "one half"
        
        text_complex = SpeechText("x squared plus y squared equals z squared")
        assert text_complex.value == "x squared plus y squared equals z squared"
    
    def test_speech_text_validation(self):
        """Test speech text validation."""
        # Empty text
        with pytest.raises(ValueError, match="Speech text cannot be empty"):
            SpeechText("")
        
        # Whitespace only
        with pytest.raises(ValueError, match="Speech text cannot be empty"):
            SpeechText("   ")
    
    def test_speech_text_normalization(self):
        """Test speech text normalization."""
        # Multiple spaces
        text = SpeechText("one  half   plus   one  third")
        assert text.value == "one half plus one third"
        
        # Leading/trailing whitespace
        text = SpeechText("  alpha beta  ")
        assert text.value == "alpha beta"
    
    def test_speech_text_ssml(self):
        """Test SSML detection."""
        text_plain = SpeechText("plain text")
        assert not text_plain.is_ssml
        
        text_ssml = SpeechText("<speak>SSML text</speak>")
        assert text_ssml.is_ssml


class TestTTSOptions:
    """Test cases for TTSOptions value object."""
    
    def test_create_default_options(self):
        """Test creating TTS options with defaults."""
        options = TTSOptions()
        
        assert options.voice_id == "en-US-AriaNeural"
        assert options.rate == 1.0
        assert options.pitch == 1.0
        assert options.volume == 1.0
        assert options.format == AudioFormat.MP3
        assert options.language == "en-US"
    
    def test_create_custom_options(self):
        """Test creating TTS options with custom values."""
        options = TTSOptions(
            voice_id="custom-voice",
            rate=1.5,
            pitch=0.8,
            volume=0.9,
            format=AudioFormat.WAV,
            language="fr-FR"
        )
        
        assert options.voice_id == "custom-voice"
        assert options.rate == 1.5
        assert options.pitch == 0.8
        assert options.volume == 0.9
        assert options.format == AudioFormat.WAV
        assert options.language == "fr-FR"
    
    def test_options_validation(self):
        """Test TTS options validation."""
        # Invalid rate
        with pytest.raises(ValueError, match="Rate must be between"):
            TTSOptions(rate=0.2)
        
        with pytest.raises(ValueError, match="Rate must be between"):
            TTSOptions(rate=3.1)
        
        # Invalid pitch
        with pytest.raises(ValueError, match="Pitch must be between"):
            TTSOptions(pitch=0.4)
        
        with pytest.raises(ValueError, match="Pitch must be between"):
            TTSOptions(pitch=2.1)
        
        # Invalid volume
        with pytest.raises(ValueError, match="Volume must be between"):
            TTSOptions(volume=-0.1)
        
        with pytest.raises(ValueError, match="Volume must be between"):
            TTSOptions(volume=1.1)
    
    def test_options_equality(self):
        """Test TTS options equality."""
        options1 = TTSOptions(voice_id="test", rate=1.2)
        options2 = TTSOptions(voice_id="test", rate=1.2)
        options3 = TTSOptions(voice_id="test", rate=1.3)
        
        assert options1 == options2
        assert options1 != options3


class TestAudioData:
    """Test cases for AudioData value object."""
    
    def test_create_audio_data(self):
        """Test creating audio data."""
        data = b"fake audio data"
        audio = AudioData(
            data=data,
            format=AudioFormat.MP3,
            sample_rate=44100,
            duration_seconds=2.5
        )
        
        assert audio.data == data
        assert audio.format == AudioFormat.MP3
        assert audio.sample_rate == 44100
        assert audio.duration_seconds == 2.5
        assert audio.size_bytes == len(data)
    
    def test_audio_data_validation(self):
        """Test audio data validation."""
        # Empty data
        with pytest.raises(ValueError, match="Audio data cannot be empty"):
            AudioData(
                data=b"",
                format=AudioFormat.MP3,
                sample_rate=44100,
                duration_seconds=1.0
            )
        
        # Invalid sample rate
        with pytest.raises(ValueError, match="Sample rate must be positive"):
            AudioData(
                data=b"data",
                format=AudioFormat.MP3,
                sample_rate=0,
                duration_seconds=1.0
            )
        
        # Invalid duration
        with pytest.raises(ValueError, match="Duration must be positive"):
            AudioData(
                data=b"data",
                format=AudioFormat.MP3,
                sample_rate=44100,
                duration_seconds=0
            )
    
    def test_audio_data_properties(self):
        """Test audio data computed properties."""
        data = b"x" * 1000
        audio = AudioData(
            data=data,
            format=AudioFormat.WAV,
            sample_rate=48000,
            duration_seconds=2.0
        )
        
        assert audio.size_bytes == 1000
        assert audio.format == AudioFormat.WAV
        assert audio.sample_rate == 48000


class TestAudioFormat:
    """Test cases for AudioFormat enum."""
    
    def test_audio_format_values(self):
        """Test audio format enum values."""
        assert AudioFormat.MP3.value == "mp3"
        assert AudioFormat.WAV.value == "wav"
        assert AudioFormat.OGG.value == "ogg"
        assert AudioFormat.FLAC.value == "flac"
    
    def test_audio_format_extensions(self):
        """Test audio format file extensions."""
        assert AudioFormat.MP3.extension == ".mp3"
        assert AudioFormat.WAV.extension == ".wav"
        assert AudioFormat.OGG.extension == ".ogg"
        assert AudioFormat.FLAC.extension == ".flac"
    
    def test_audio_format_mime_types(self):
        """Test audio format MIME types."""
        assert AudioFormat.MP3.mime_type == "audio/mpeg"
        assert AudioFormat.WAV.mime_type == "audio/wav"
        assert AudioFormat.OGG.mime_type == "audio/ogg"
        assert AudioFormat.FLAC.mime_type == "audio/flac"


class TestVoiceGender:
    """Test cases for VoiceGender enum."""
    
    def test_voice_gender_values(self):
        """Test voice gender enum values."""
        assert VoiceGender.MALE.value == "male"
        assert VoiceGender.FEMALE.value == "female"
        assert VoiceGender.NEUTRAL.value == "neutral"