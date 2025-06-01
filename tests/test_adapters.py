"""
Tests for adapter layer components.

This module tests TTS providers, pattern loaders, and other adapters.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

from src.adapters.tts_providers import (
    MockTTSProviderAdapter,
    EdgeTTSAdapter,
    TTSOptions,
    AudioFormat,
    VoiceGender
)
from src.adapters.pattern_loaders import YAMLPatternLoader
from src.domain.value_objects import SpeechText


class TestMockTTSProvider:
    """Test mock TTS provider."""
    
    @pytest.mark.asyncio
    async def test_mock_provider_lifecycle(self):
        """Test mock provider initialization and cleanup."""
        provider = MockTTSProviderAdapter()
        
        # Should not be initialized initially
        assert not provider._initialized
        
        # Initialize
        await provider.initialize()
        assert provider._initialized
        
        # Close
        await provider.close()
        assert not provider._initialized
    
    @pytest.mark.asyncio
    async def test_mock_provider_synthesis(self):
        """Test mock audio synthesis."""
        provider = MockTTSProviderAdapter()
        await provider.initialize()
        
        options = TTSOptions(
            voice_id="mock-voice-1",
            format=AudioFormat.MP3
        )
        
        # Test with string input
        audio_data = await provider.synthesize("Hello world", options)
        
        assert audio_data.format == AudioFormat.MP3
        assert audio_data.size_bytes > 0
        assert audio_data.duration_seconds is not None
        
        # Test with SpeechText input
        speech_text = SpeechText(
            value="Hello world",
            ssml="<speak>Hello world</speak>"
        )
        audio_data = await provider.synthesize(speech_text, options)
        
        assert audio_data.format == AudioFormat.MP3
        assert audio_data.size_bytes > 0
    
    @pytest.mark.asyncio
    async def test_mock_provider_voices(self):
        """Test mock voice listing."""
        provider = MockTTSProviderAdapter()
        await provider.initialize()
        
        # Test all voices
        voices = await provider.list_voices()
        assert len(voices) == 2
        assert all(voice.language == "en-US" for voice in voices)
        
        # Test filtered voices
        filtered_voices = await provider.list_voices(language="en-US")
        assert len(filtered_voices) == 2
        
        # Test non-matching filter
        filtered_voices = await provider.list_voices(language="fr-FR")
        assert len(filtered_voices) == 0
    
    def test_mock_provider_capabilities(self):
        """Test mock provider capabilities."""
        provider = MockTTSProviderAdapter()
        
        assert provider.is_available() is True
        assert provider.supports_ssml() is True
        assert provider.supports_streaming() is False
    
    @pytest.mark.asyncio
    async def test_mock_provider_batch(self):
        """Test mock provider batch processing."""
        provider = MockTTSProviderAdapter()
        await provider.initialize()
        
        options = TTSOptions(voice_id="mock-voice-1")
        texts = ["Hello", "World", "Test"]
        
        results = await provider.synthesize_batch(texts, options)
        
        assert len(results) == 3
        assert all(isinstance(result.data, bytes) for result in results)


class TestEdgeTTSAdapter:
    """Test Edge-TTS adapter."""
    
    @pytest.mark.asyncio
    async def test_edge_tts_availability(self):
        """Test Edge-TTS availability check."""
        provider = EdgeTTSAdapter()
        
        # Should be available if edge-tts is installed
        assert provider.is_available() in [True, False]  # Depends on installation
    
    def test_edge_tts_capabilities(self):
        """Test Edge-TTS capabilities."""
        provider = EdgeTTSAdapter()
        
        assert provider.supports_ssml() is True
        assert provider.supports_streaming() is True
    
    def test_edge_tts_voice_mapping(self):
        """Test Edge-TTS voice mapping."""
        provider = EdgeTTSAdapter()
        
        # Test voice mapping
        assert "en-US-AriaNeural" in provider.VOICE_MAPPING
        aria_info = provider.VOICE_MAPPING["en-US-AriaNeural"]
        assert aria_info[0] == "Aria"
        assert aria_info[1] == VoiceGender.FEMALE
    
    def test_edge_tts_format_helpers(self):
        """Test Edge-TTS formatting helper methods."""
        provider = EdgeTTSAdapter()
        
        # Test rate formatting
        assert provider._format_rate(1.0) == "+0%"
        assert provider._format_rate(1.5) == "+50%"
        assert provider._format_rate(0.8) == "-20%"
        
        # Test pitch formatting
        assert provider._format_pitch(1.0) == "+0%"
        assert provider._format_pitch(1.2) == "+20%"
        
        # Test volume formatting
        assert provider._format_volume(1.0) == "100%"
        assert provider._format_volume(0.5) == "50%"
    
    @pytest.mark.asyncio
    @patch('edge_tts.list_voices')
    async def test_edge_tts_voice_listing(self, mock_list_voices):
        """Test Edge-TTS voice listing with mocked data."""
        # Mock voice data
        mock_voices = [
            {
                "ShortName": "en-US-AriaNeural",
                "FriendlyName": "Microsoft Aria Online (Natural) - English (United States)",
                "Locale": "en-US",
                "Gender": "Female"
            },
            {
                "ShortName": "en-GB-SoniaNeural",
                "FriendlyName": "Microsoft Sonia Online (Natural) - English (United Kingdom)",
                "Locale": "en-GB",
                "Gender": "Female"
            }
        ]
        mock_list_voices.return_value = mock_voices
        
        provider = EdgeTTSAdapter()
        await provider.initialize()
        
        # Test all voices
        voices = await provider.list_voices()
        assert len(voices) == 2
        
        # Test language filtering
        us_voices = await provider.list_voices(language="en-US")
        assert len(us_voices) == 1
        assert us_voices[0].id == "en-US-AriaNeural"
        
        # Test non-matching filter
        fr_voices = await provider.list_voices(language="fr-FR")
        assert len(fr_voices) == 0


class TestYAMLPatternLoader:
    """Test YAML pattern loader."""
    
    @pytest.fixture
    def temp_patterns_dir(self):
        """Create temporary directory with test patterns."""
        import tempfile
        import yaml
        
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create test pattern files
        pattern1 = {
            "pattern": {
                "id": "test_fraction",
                "pattern": "\\\\frac\\{([^}]+)\\}\\{([^}]+)\\}",
                "output_template": "\\1 over \\2",
                "priority": 1000,
                "domain": "algebra",
                "contexts": ["inline", "display"],
                "description": "Basic fractions"
            }
        }
        
        pattern2 = {
            "pattern": {
                "id": "test_sin",
                "pattern": "\\\\sin\\(([^)]+)\\)",
                "output_template": "sine of \\1",
                "priority": 800,
                "domain": "calculus",
                "contexts": ["inline"],
                "description": "Sine function"
            }
        }
        
        # Write pattern files
        with open(temp_dir / "fractions.yaml", "w") as f:
            yaml.dump(pattern1, f)
        
        with open(temp_dir / "trigonometry.yaml", "w") as f:
            yaml.dump(pattern2, f)
        
        yield temp_dir
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_pattern_loading(self, temp_patterns_dir):
        """Test loading patterns from YAML files."""
        loader = YAMLPatternLoader(temp_patterns_dir)
        patterns = await loader.load_patterns()
        
        assert len(patterns) == 2
        
        # Check pattern IDs
        pattern_ids = [p.id for p in patterns]
        assert "test_fraction" in pattern_ids
        assert "test_sin" in pattern_ids
        
        # Check pattern details
        fraction_pattern = next(p for p in patterns if p.id == "test_fraction")
        assert fraction_pattern.domain.value == "algebra"
        assert fraction_pattern.priority.value == 1000
        assert "inline" in fraction_pattern.contexts
        assert "display" in fraction_pattern.contexts
    
    @pytest.mark.asyncio
    async def test_pattern_loading_empty_dir(self):
        """Test loading from empty directory."""
        import tempfile
        
        empty_dir = Path(tempfile.mkdtemp())
        try:
            loader = YAMLPatternLoader(empty_dir)
            patterns = await loader.load_patterns()
            
            assert len(patterns) == 0
            
        finally:
            empty_dir.rmdir()
    
    @pytest.mark.asyncio
    async def test_pattern_loading_invalid_yaml(self):
        """Test handling of invalid YAML files."""
        import tempfile
        
        temp_dir = Path(tempfile.mkdtemp())
        try:
            # Create invalid YAML file
            with open(temp_dir / "invalid.yaml", "w") as f:
                f.write("invalid: yaml: content: [\n")
            
            loader = YAMLPatternLoader(temp_dir)
            
            # Should handle invalid YAML gracefully
            patterns = await loader.load_patterns()
            assert len(patterns) == 0  # Should skip invalid files
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)


class TestTTSOptions:
    """Test TTS options validation."""
    
    def test_valid_options(self):
        """Test valid TTS options."""
        options = TTSOptions(
            voice_id="test-voice",
            rate=1.5,
            pitch=0.8,
            volume=0.9
        )
        
        # Should not raise exception
        options.validate()
    
    def test_invalid_rate(self):
        """Test invalid rate values."""
        options = TTSOptions(
            voice_id="test-voice",
            rate=3.0  # Too high
        )
        
        with pytest.raises(ValueError, match="Rate must be between"):
            options.validate()
    
    def test_invalid_pitch(self):
        """Test invalid pitch values."""
        options = TTSOptions(
            voice_id="test-voice",
            pitch=0.3  # Too low
        )
        
        with pytest.raises(ValueError, match="Pitch must be between"):
            options.validate()
    
    def test_invalid_volume(self):
        """Test invalid volume values."""
        options = TTSOptions(
            voice_id="test-voice",
            volume=1.5  # Too high
        )
        
        with pytest.raises(ValueError, match="Volume must be between"):
            options.validate()


class TestIntegration:
    """Integration tests for adapters."""
    
    @pytest.mark.asyncio
    async def test_provider_context_manager(self):
        """Test TTS provider as context manager."""
        async with MockTTSProviderAdapter() as provider:
            assert provider._initialized
            
            # Should be able to use provider
            voices = await provider.list_voices()
            assert len(voices) > 0
        
        # Should be closed after context
        assert not provider._initialized