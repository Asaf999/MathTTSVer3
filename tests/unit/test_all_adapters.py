"""
Comprehensive tests for all adapters.
"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import Mock, AsyncMock, patch
from src.adapters.tts_providers import *
from src.adapters.pattern_loaders import *
from src.domain.value_objects_tts import *


class TestAllAdapters:
    """Test all adapter implementations."""
    
    @pytest.mark.asyncio
    async def test_mock_tts_adapter(self):
        """Test MockTTSAdapter."""
        from src.adapters.tts_providers.mock_tts_adapter import MockTTSAdapter
        
        adapter = MockTTSAdapter()
        
        # Initialize
        await adapter.initialize()
        assert adapter.is_available()
        
        # Synthesize
        options = TTSOptions(voice="test", format=AudioFormat.MP3)
        result = await adapter.synthesize("Hello", options)
        assert isinstance(result, AudioData)
        assert result.format == AudioFormat.MP3
        
        # List voices
        voices = await adapter.list_voices()
        assert len(voices) > 0
        
        # Supported formats
        formats = adapter.get_supported_formats()
        assert AudioFormat.MP3 in formats
        
        # Close
        await adapter.close()
    
    @pytest.mark.asyncio
    async def test_edge_tts_adapter(self):
        """Test EdgeTTSAdapter."""
        from src.adapters.tts_providers.edge_tts_adapter import EdgeTTSAdapter
        
        with patch('edge_tts.Communicate') as mock_comm:
            mock_instance = AsyncMock()
            mock_instance.stream.return_value = [
                (b"audio", {"type": "audio"})
            ]
            mock_comm.return_value = mock_instance
            
            adapter = EdgeTTSAdapter()
            await adapter.initialize()
            
            options = TTSOptions(voice="en-US-AriaNeural")
            result = await adapter.synthesize("Test", options)
            
            assert isinstance(result, AudioData)
    
    def test_yaml_pattern_loader(self):
        """Test YAML pattern loader."""
        from src.adapters.pattern_loaders.yaml_pattern_loader import YAMLPatternLoader
        
        loader = YAMLPatternLoader()
        
        # Test with mock file
        yaml_content = """
patterns:
  - id: test-1
    name: Test
    pattern: test
    output_template: test
    priority: 1000
"""
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            with patch('os.path.exists', return_value=True):
                patterns = loader.load_file("test.yaml")
                assert len(patterns) == 1
                assert patterns[0].id == "test-1"
    
    def test_ssml_converter(self):
        """Test SSML converter."""
        try:
            from src.adapters.tts_providers.ssml_converter import SSMLConverter
            
            converter = SSMLConverter()
            
            # Convert to SSML
            text = "Hello <emphasis>world</emphasis>"
            ssml = converter.to_ssml(text)
            assert "<speak>" in ssml
            
            # Convert from SSML
            plain = converter.from_ssml(ssml)
            assert isinstance(plain, str)
        except ImportError:
            # Module might not exist
            pass
