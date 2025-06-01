"""
Unit tests for adapter components.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import unittest
import asyncio
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, mock_open

from src.adapters.pattern_loaders import YAMLPatternLoader
from src.adapters.tts_providers.edge_tts_provider import EdgeTTSProvider
from src.domain.entities import PatternEntity
from src.domain.value_objects import (
    PatternPriority,
    MathematicalDomain,
    SpeechText
)


class TestYAMLPatternLoader(unittest.TestCase):
    """Test cases for YAML pattern loader."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.patterns_dir = Path(self.temp_dir)
        self.loader = YAMLPatternLoader(self.patterns_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def async_test(coro):
        """Decorator to run async tests."""
        def wrapper(self):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(coro(self))
        return wrapper
    
    @async_test
    async def test_load_single_pattern_file(self):
        """Test loading patterns from a single YAML file."""
        # Create test YAML file
        yaml_content = {
            "patterns": [
                {
                    "pattern": {
                        "id": "test_pattern_1",
                        "pattern": r"\\alpha",
                        "output_template": "alpha",
                        "priority": 500,
                        "domain": "general",
                        "contexts": ["inline"],
                        "description": "Greek letter alpha"
                    }
                }
            ]
        }
        
        pattern_file = self.patterns_dir / "test_patterns.yaml"
        with open(pattern_file, 'w') as f:
            yaml.dump(yaml_content, f)
        
        # Load patterns
        patterns = await self.loader.load_patterns()
        
        # Verify
        self.assertEqual(len(patterns), 1)
        pattern = patterns[0]
        self.assertEqual(pattern.id, "test_pattern_1")
        self.assertEqual(pattern.pattern, r"\\alpha")
        self.assertEqual(pattern.output_template, "alpha")
        self.assertEqual(pattern.priority.value, 500)
        self.assertEqual(pattern.domain.value, "general")
    
    @async_test
    async def test_load_multiple_patterns(self):
        """Test loading multiple patterns from a file."""
        yaml_content = {
            "patterns": [
                {
                    "pattern": {
                        "id": "pattern_1",
                        "pattern": r"\\alpha",
                        "output_template": "alpha",
                        "priority": 500,
                        "domain": "general",
                        "contexts": ["inline"]
                    }
                },
                {
                    "pattern": {
                        "id": "pattern_2",
                        "pattern": r"\\beta",
                        "output_template": "beta",
                        "priority": 600,
                        "domain": "general",
                        "contexts": ["inline", "display"]
                    }
                }
            ]
        }
        
        pattern_file = self.patterns_dir / "patterns.yaml"
        with open(pattern_file, 'w') as f:
            yaml.dump(yaml_content, f)
        
        patterns = await self.loader.load_patterns()
        
        self.assertEqual(len(patterns), 2)
        pattern_ids = [p.id for p in patterns]
        self.assertIn("pattern_1", pattern_ids)
        self.assertIn("pattern_2", pattern_ids)
    
    @async_test
    async def test_load_from_multiple_files(self):
        """Test loading patterns from multiple YAML files."""
        # Create first file
        yaml1 = {
            "patterns": [{
                "pattern": {
                    "id": "file1_pattern",
                    "pattern": r"\\test1",
                    "output_template": "test1",
                    "priority": 500,
                    "domain": "general",
                    "contexts": ["inline"]
                }
            }]
        }
        
        # Create second file
        yaml2 = {
            "patterns": [{
                "pattern": {
                    "id": "file2_pattern",
                    "pattern": r"\\test2",
                    "output_template": "test2",
                    "priority": 600,
                    "domain": "calculus",
                    "contexts": ["display"]
                }
            }]
        }
        
        with open(self.patterns_dir / "patterns1.yaml", 'w') as f:
            yaml.dump(yaml1, f)
        
        with open(self.patterns_dir / "patterns2.yml", 'w') as f:
            yaml.dump(yaml2, f)
        
        patterns = await self.loader.load_patterns()
        
        self.assertEqual(len(patterns), 2)
        pattern_ids = [p.id for p in patterns]
        self.assertIn("file1_pattern", pattern_ids)
        self.assertIn("file2_pattern", pattern_ids)
    
    @async_test
    async def test_handle_invalid_yaml(self):
        """Test handling of invalid YAML files."""
        # Create invalid YAML
        invalid_yaml = "invalid: yaml: content: {"
        
        pattern_file = self.patterns_dir / "invalid.yaml"
        with open(pattern_file, 'w') as f:
            f.write(invalid_yaml)
        
        # Should not raise, just log error
        patterns = await self.loader.load_patterns()
        self.assertEqual(len(patterns), 0)
    
    @async_test
    async def test_handle_missing_directory(self):
        """Test handling of missing patterns directory."""
        non_existent_dir = Path("/non/existent/directory")
        loader = YAMLPatternLoader(non_existent_dir)
        
        patterns = await loader.load_patterns()
        self.assertEqual(len(patterns), 0)
    
    @async_test
    async def test_save_patterns(self):
        """Test saving patterns to YAML."""
        patterns = [
            PatternEntity(
                id="save_test_1",
                name="Save Test 1",
                pattern=r"\\test",
                output_template="test",
                priority=PatternPriority.medium(),
                domain=MathematicalDomain("general"),
                contexts=["ANY"]
            ),
            PatternEntity(
                id="save_test_2",
                name="Save Test 2",
                pattern=r"\\test2",
                output_template="test2",
                priority=PatternPriority.high(),
                domain=MathematicalDomain("calculus"),
                contexts=["INLINE"]
            )
        ]
        
        output_file = self.patterns_dir / "saved_patterns.yaml"
        await self.loader.save_patterns(patterns, output_file)
        
        # Verify file exists and can be loaded
        self.assertTrue(output_file.exists())
        
        # Load saved patterns
        with open(output_file, 'r') as f:
            data = yaml.safe_load(f)
        
        self.assertIn("metadata", data)
        self.assertIn("patterns", data)
        self.assertEqual(len(data["patterns"]), 2)
        self.assertEqual(data["metadata"]["pattern_count"], 2)
    
    def test_validate_pattern_file_valid(self):
        """Test validation of valid pattern file."""
        valid_yaml = {
            "patterns": [{
                "pattern": {
                    "id": "valid_pattern",
                    "pattern": r"\\valid",
                    "output_template": "valid",
                    "priority": 500,
                    "domain": "general",
                    "contexts": ["inline"]
                }
            }]
        }
        
        pattern_file = self.patterns_dir / "valid.yaml"
        with open(pattern_file, 'w') as f:
            yaml.dump(valid_yaml, f)
        
        errors = self.loader.validate_pattern_file(pattern_file)
        self.assertEqual(len(errors), 0)
    
    def test_validate_pattern_file_invalid(self):
        """Test validation of invalid pattern file."""
        invalid_yaml = {
            "patterns": [{
                "pattern": {
                    # Missing required fields
                    "pattern": r"\\invalid",
                    "priority": 3000  # Out of range
                }
            }]
        }
        
        pattern_file = self.patterns_dir / "invalid.yaml"
        with open(pattern_file, 'w') as f:
            yaml.dump(invalid_yaml, f)
        
        errors = self.loader.validate_pattern_file(pattern_file)
        self.assertGreater(len(errors), 0)
        
        # Check specific errors
        error_messages = " ".join(errors)
        self.assertIn("Missing required field 'id'", error_messages)
        self.assertIn("Missing required field 'output_template'", error_messages)
        self.assertIn("Priority must be integer between 0-2000", error_messages)
    
    @async_test
    async def test_pattern_creation_defaults(self):
        """Test pattern creation with default values."""
        yaml_content = {
            "patterns": [{
                "pattern": {
                    "id": "minimal_pattern",
                    "pattern": r"\\minimal",
                    "output_template": "minimal"
                    # No priority, domain, contexts specified
                }
            }]
        }
        
        pattern_file = self.patterns_dir / "minimal.yaml"
        with open(pattern_file, 'w') as f:
            yaml.dump(yaml_content, f)
        
        patterns = await self.loader.load_patterns()
        
        self.assertEqual(len(patterns), 1)
        pattern = patterns[0]
        
        # Check defaults
        self.assertEqual(pattern.priority.value, 500)  # Default medium priority
        self.assertEqual(pattern.domain.value, "general")  # Default domain
        self.assertEqual(len(pattern.contexts), 1)  # Default context
    
    @async_test
    async def test_context_string_to_list_conversion(self):
        """Test conversion of single context string to list."""
        yaml_content = {
            "patterns": [{
                "pattern": {
                    "id": "context_test",
                    "pattern": r"\\test",
                    "output_template": "test",
                    "contexts": "inline"  # String instead of list
                }
            }]
        }
        
        pattern_file = self.patterns_dir / "context_test.yaml"
        with open(pattern_file, 'w') as f:
            yaml.dump(yaml_content, f)
        
        patterns = await self.loader.load_patterns()
        
        self.assertEqual(len(patterns), 1)
        # Should be converted to list
        self.assertIsInstance(patterns[0].contexts, list)


class TestEdgeTTSProvider(unittest.TestCase):
    """Test cases for Edge TTS provider."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.provider = EdgeTTSProvider(
            voice="en-US-AriaNeural",
            rate="+0%",
            pitch="+0Hz",
            volume="+0%"
        )
    
    def async_test(coro):
        """Decorator to run async tests."""
        def wrapper(self):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(coro(self))
        return wrapper
    
    @async_test
    @patch('edge_tts.Communicate')
    async def test_synthesize_text(self, mock_communicate):
        """Test text synthesis."""
        # Mock edge_tts
        mock_instance = AsyncMock()
        mock_instance.stream.return_value = [
            (b"audio_chunk_1", {"type": "audio"}),
            (b"audio_chunk_2", {"type": "audio"})
        ]
        mock_communicate.return_value = mock_instance
        
        # Test synthesis
        speech_text = SpeechText(value="Hello world")
        audio_data = await self.provider.synthesize(speech_text)
        
        # Verify
        self.assertEqual(audio_data, b"audio_chunk_1audio_chunk_2")
        mock_communicate.assert_called_once_with(
            "Hello world",
            "en-US-AriaNeural",
            rate="+0%",
            pitch="+0Hz",
            volume="+0%"
        )
    
    @async_test
    @patch('edge_tts.Communicate')
    async def test_synthesize_with_ssml(self, mock_communicate):
        """Test synthesis with SSML."""
        mock_instance = AsyncMock()
        mock_instance.stream.return_value = [
            (b"audio_data", {"type": "audio"})
        ]
        mock_communicate.return_value = mock_instance
        
        # Test with SSML
        speech_text = SpeechText(
            value="Hello world",
            ssml='<speak>Hello <emphasis>world</emphasis></speak>'
        )
        
        await self.provider.synthesize(speech_text)
        
        # Should use SSML when provided
        mock_communicate.assert_called_once_with(
            '<speak>Hello <emphasis>world</emphasis></speak>',
            "en-US-AriaNeural",
            rate="+0%",
            pitch="+0Hz",
            volume="+0%"
        )
    
    @async_test
    @patch('edge_tts.Communicate')
    async def test_list_voices(self, mock_communicate):
        """Test listing available voices."""
        voices = await self.provider.list_voices()
        
        # Should return list of voice info
        self.assertIsInstance(voices, list)
        self.assertGreater(len(voices), 0)
        
        # Check voice structure
        for voice in voices:
            self.assertIn("id", voice)
            self.assertIn("name", voice)
            self.assertIn("language", voice)
            self.assertIn("gender", voice)
    
    def test_get_supported_languages(self):
        """Test getting supported languages."""
        languages = self.provider.get_supported_languages()
        
        self.assertIsInstance(languages, list)
        self.assertIn("en", languages)
        self.assertIn("es", languages)
        self.assertIn("fr", languages)
        self.assertIn("de", languages)
    
    @async_test
    @patch('edge_tts.Communicate')
    async def test_synthesis_error_handling(self, mock_communicate):
        """Test error handling during synthesis."""
        # Mock edge_tts to raise error
        mock_communicate.side_effect = Exception("Network error")
        
        speech_text = SpeechText(value="Test")
        
        # Should raise exception
        with self.assertRaises(Exception) as ctx:
            await self.provider.synthesize(speech_text)
        
        self.assertIn("Network error", str(ctx.exception))
    
    @async_test
    @patch('edge_tts.Communicate')
    async def test_empty_audio_handling(self, mock_communicate):
        """Test handling of empty audio response."""
        mock_instance = AsyncMock()
        mock_instance.stream.return_value = []  # No audio chunks
        mock_communicate.return_value = mock_instance
        
        speech_text = SpeechText(value="Test")
        audio_data = await self.provider.synthesize(speech_text)
        
        # Should return empty bytes
        self.assertEqual(audio_data, b"")
    
    def test_voice_configuration(self):
        """Test voice configuration."""
        # Test with different voice
        provider = EdgeTTSProvider(
            voice="es-ES-AlvaroNeural",
            rate="+10%",
            pitch="-5Hz",
            volume="+20%"
        )
        
        self.assertEqual(provider.voice, "es-ES-AlvaroNeural")
        self.assertEqual(provider.rate, "+10%")
        self.assertEqual(provider.pitch, "-5Hz")
        self.assertEqual(provider.volume, "+20%")
    
    def test_default_configuration(self):
        """Test default configuration."""
        provider = EdgeTTSProvider()
        
        self.assertEqual(provider.voice, "en-US-AriaNeural")
        self.assertEqual(provider.rate, "+0%")
        self.assertEqual(provider.pitch, "+0Hz")
        self.assertEqual(provider.volume, "+0%")


if __name__ == "__main__":
    unittest.main()