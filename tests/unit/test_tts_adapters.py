"""
Unit tests for TTS adapters.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.adapters.tts_providers import EdgeTTSAdapter, GTTSAdapter, Pyttsx3Adapter, MockTTSAdapter
from src.domain.value_objects import TTSOptions, AudioFormat, VoiceGender


@pytest.mark.tts
class TestMockTTSAdapter:
    """Test cases for MockTTSAdapter."""
    
    @pytest.mark.asyncio
    async def test_initialize_and_close(self):
        """Test adapter initialization and closing."""
        adapter = MockTTSAdapter()
        
        assert not adapter.is_available()
        
        await adapter.initialize()
        assert adapter.is_available()
        
        await adapter.close()
        assert not adapter.is_available()
    
    @pytest.mark.asyncio
    async def test_synthesize_text(self):
        """Test text synthesis."""
        adapter = MockTTSAdapter()
        await adapter.initialize()
        
        text = "one half plus one third"
        options = TTSOptions()
        
        audio = await adapter.synthesize(text, options)
        
        assert audio.data == b"ID3mock audio data"  # MP3 format
        assert audio.format == AudioFormat.MP3
        assert audio.sample_rate == 44100
        assert audio.duration_seconds >= 1.0
    
    @pytest.mark.asyncio
    async def test_synthesize_different_formats(self):
        """Test synthesis with different audio formats."""
        adapter = MockTTSAdapter()
        await adapter.initialize()
        
        text = "test"
        
        # Test WAV format
        wav_options = TTSOptions(format=AudioFormat.WAV)
        wav_audio = await adapter.synthesize(text, wav_options)
        assert wav_audio.data.startswith(b"RIFF")
        assert wav_audio.format == AudioFormat.WAV
        
        # Test MP3 format
        mp3_options = TTSOptions(format=AudioFormat.MP3)
        mp3_audio = await adapter.synthesize(text, mp3_options)
        assert mp3_audio.data.startswith(b"ID3")
        assert mp3_audio.format == AudioFormat.MP3
    
    @pytest.mark.asyncio
    async def test_list_voices(self):
        """Test listing available voices."""
        adapter = MockTTSAdapter()
        await adapter.initialize()
        
        # List all voices
        all_voices = await adapter.list_voices()
        assert len(all_voices) == 2
        assert any(v.gender == VoiceGender.MALE for v in all_voices)
        assert any(v.gender == VoiceGender.FEMALE for v in all_voices)
        
        # Filter by language
        en_voices = await adapter.list_voices("en")
        assert len(en_voices) == 2
        assert all(v.language.startswith("en") for v in en_voices)
    
    def test_get_supported_formats(self):
        """Test getting supported formats."""
        adapter = MockTTSAdapter()
        formats = adapter.get_supported_formats()
        
        assert AudioFormat.MP3 in formats
        assert AudioFormat.WAV in formats
        assert AudioFormat.OGG in formats
    
    def test_estimate_duration(self):
        """Test duration estimation."""
        adapter = MockTTSAdapter()
        
        # Normal rate
        text = " ".join(["word"] * 150)  # 150 words
        duration = adapter.estimate_duration(text, rate=1.0)
        assert abs(duration - 60.0) < 1.0  # ~1 minute
        
        # Faster rate
        duration_fast = adapter.estimate_duration(text, rate=1.5)
        assert duration_fast < duration


@pytest.mark.tts
class TestEdgeTTSAdapter:
    """Test cases for EdgeTTSAdapter."""
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test adapter initialization."""
        with patch('edge_tts.list_voices', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = [
                {"ShortName": "en-US-AriaNeural", "Gender": "Female"},
                {"ShortName": "en-US-GuyNeural", "Gender": "Male"}
            ]
            
            adapter = EdgeTTSAdapter()
            await adapter.initialize()
            
            assert adapter.is_available()
            mock_list.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_synthesize_with_ssml(self):
        """Test synthesis with SSML support."""
        with patch('edge_tts.Communicate') as mock_communicate:
            mock_instance = AsyncMock()
            mock_communicate.return_value = mock_instance
            
            # Mock the async generator
            async def mock_stream():
                yield {"type": "audio", "data": b"test audio"}
            
            mock_instance.stream.return_value = mock_stream()
            
            adapter = EdgeTTSAdapter()
            adapter._voices = [{"ShortName": "en-US-AriaNeural"}]
            
            text = "one half"
            options = TTSOptions()
            
            audio = await adapter.synthesize(text, options)
            
            # Should use SSML converter
            assert mock_communicate.called
            call_args = mock_communicate.call_args[0]
            assert "<speak>" in call_args[0]  # SSML formatted
    
    @pytest.mark.asyncio
    async def test_list_voices_filtered(self):
        """Test listing voices with language filter."""
        adapter = EdgeTTSAdapter()
        adapter._voices = [
            {"ShortName": "en-US-AriaNeural", "Gender": "Female", "Locale": "en-US"},
            {"ShortName": "fr-FR-DeniseNeural", "Gender": "Female", "Locale": "fr-FR"},
            {"ShortName": "en-GB-RyanNeural", "Gender": "Male", "Locale": "en-GB"}
        ]
        
        # Filter by English
        en_voices = await adapter.list_voices("en")
        assert len(en_voices) == 2
        assert all("en" in v.id for v in en_voices)
        
        # Filter by French
        fr_voices = await adapter.list_voices("fr")
        assert len(fr_voices) == 1
        assert fr_voices[0].id == "fr-FR-DeniseNeural"


@pytest.mark.tts
class TestGTTSAdapter:
    """Test cases for GTTSAdapter."""
    
    @pytest.mark.asyncio
    async def test_initialize_and_check_availability(self):
        """Test adapter initialization and availability check."""
        adapter = GTTSAdapter()
        await adapter.initialize()
        
        assert adapter.is_available()
    
    @pytest.mark.asyncio
    async def test_synthesize_text(self):
        """Test text synthesis with gTTS."""
        with patch('gtts.gTTS') as mock_gtts:
            mock_instance = Mock()
            mock_gtts.return_value = mock_instance
            
            # Mock the write_to_fp method
            def mock_write(fp):
                fp.write(b"mock mp3 data")
            mock_instance.write_to_fp = mock_write
            
            adapter = GTTSAdapter()
            await adapter.initialize()
            
            text = "test speech"
            options = TTSOptions(language="en-US")
            
            audio = await adapter.synthesize(text, options)
            
            assert audio.format == AudioFormat.MP3
            assert audio.data == b"mock mp3 data"
            mock_gtts.assert_called_once_with(text=text, lang="en", slow=False)
    
    @pytest.mark.asyncio
    async def test_list_voices(self):
        """Test listing available voices/languages."""
        adapter = GTTSAdapter()
        await adapter.initialize()
        
        voices = await adapter.list_voices()
        
        # Should have common languages
        voice_ids = [v.id for v in voices]
        assert "en" in voice_ids
        assert "es" in voice_ids
        assert "fr" in voice_ids
        
        # All should be neutral gender (gTTS doesn't specify)
        assert all(v.gender == VoiceGender.NEUTRAL for v in voices)


@pytest.mark.tts
class TestPyttsx3Adapter:
    """Test cases for Pyttsx3Adapter."""
    
    @pytest.mark.asyncio
    async def test_initialize_with_mock_engine(self):
        """Test adapter initialization with mock engine."""
        with patch('pyttsx3.init') as mock_init:
            mock_engine = Mock()
            mock_init.return_value = mock_engine
            
            # Mock voices
            mock_voice1 = Mock()
            mock_voice1.id = "voice1"
            mock_voice1.name = "Voice 1"
            
            mock_voice2 = Mock()
            mock_voice2.id = "voice2"
            mock_voice2.name = "Voice 2"
            
            mock_engine.getProperty.return_value = [mock_voice1, mock_voice2]
            
            adapter = Pyttsx3Adapter()
            await adapter.initialize()
            
            assert adapter.is_available()
            mock_engine.getProperty.assert_called_with('voices')
    
    @pytest.mark.asyncio
    async def test_synthesize_to_file(self):
        """Test synthesis to file."""
        with patch('pyttsx3.init') as mock_init:
            mock_engine = Mock()
            mock_init.return_value = mock_engine
            
            adapter = Pyttsx3Adapter()
            adapter._engine = mock_engine
            
            # Mock file content
            with patch('builtins.open', create=True) as mock_open:
                mock_file = Mock()
                mock_file.read.return_value = b"mock audio data"
                mock_open.return_value.__enter__.return_value = mock_file
                
                text = "test speech"
                options = TTSOptions(rate=1.2, volume=0.8)
                
                audio = await adapter.synthesize(text, options)
                
                # Check engine configuration
                mock_engine.setProperty.assert_any_call('rate', 144)  # 120 * 1.2
                mock_engine.setProperty.assert_any_call('volume', 0.8)
                
                # Check synthesis
                mock_engine.save_to_file.assert_called_once()
                mock_engine.runAndWait.assert_called_once()
                
                assert audio.data == b"mock audio data"
                assert audio.format == AudioFormat.WAV
    
    def test_estimate_duration(self):
        """Test duration estimation."""
        adapter = Pyttsx3Adapter()
        
        text = "This is a test sentence with several words."
        duration = adapter.estimate_duration(text, rate=1.0)
        
        # Should be reasonable duration
        assert 1.0 < duration < 5.0
        
        # Faster rate should reduce duration
        duration_fast = adapter.estimate_duration(text, rate=1.5)
        assert duration_fast < duration