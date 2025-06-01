"""
Integration tests for CLI commands.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from click.testing import CliRunner
from unittest.mock import patch, AsyncMock, Mock
from pathlib import Path
import json

from src.presentation.cli.main import cli
from src.domain.value_objects import AudioData, AudioFormat


@pytest.mark.cli
class TestCLICommands:
    """Test cases for CLI commands."""
    
    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()
    
    @pytest.fixture
    def mock_service(self):
        """Mock MathTTS service."""
        with patch('presentation.cli.commands.get_mathtts_service') as mock_get:
            service = AsyncMock()
            
            # Mock audio response
            mock_audio = AudioData(
                data=b"mock audio data",
                format=AudioFormat.MP3,
                sample_rate=44100,
                duration_seconds=2.0
            )
            service.convert_latex_to_speech.return_value = mock_audio
            
            mock_get.return_value = service
            yield service
    
    def test_cli_help(self, runner):
        """Test CLI help command."""
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "MathTTS CLI" in result.output
        assert "convert" in result.output
        assert "batch" in result.output
    
    def test_convert_command(self, runner, mock_service, tmp_path):
        """Test convert command."""
        output_file = tmp_path / "output.mp3"
        
        result = runner.invoke(cli, [
            'convert',
            r'\frac{1}{2}',
            '--output', str(output_file),
            '--voice', 'en-US-AriaNeural',
            '--format', 'mp3'
        ])
        
        assert result.exit_code == 0
        assert "Converting LaTeX" in result.output
        assert "Saved to" in result.output
        assert output_file.exists()
        assert output_file.read_bytes() == b"mock audio data"
    
    def test_convert_with_defaults(self, runner, mock_service, tmp_path):
        """Test convert command with default options."""
        output_file = tmp_path / "output.mp3"
        
        result = runner.invoke(cli, [
            'convert',
            'x^2',
            '--output', str(output_file)
        ])
        
        assert result.exit_code == 0
        mock_service.convert_latex_to_speech.assert_called_once()
        assert output_file.exists()
    
    def test_convert_stdout(self, runner, mock_service):
        """Test convert command outputting to stdout."""
        result = runner.invoke(cli, [
            'convert',
            'x^2',
            '--stdout'
        ])
        
        assert result.exit_code == 0
        # Output should contain base64 encoded audio
        assert "bW9jayBhdWRpbyBkYXRh" in result.output  # base64 of "mock audio data"
    
    def test_batch_convert_command(self, runner, mock_service, tmp_path):
        """Test batch convert command."""
        # Create input file with LaTeX expressions
        input_file = tmp_path / "input.txt"
        input_file.write_text("\\frac{1}{2}\nx^2\n\\alpha + \\beta")
        
        output_dir = tmp_path / "output"
        
        # Mock batch results
        mock_results = [
            AudioData(
                data=f"audio{i}".encode(),
                format=AudioFormat.MP3,
                sample_rate=44100,
                duration_seconds=float(i+1)
            )
            for i in range(3)
        ]
        mock_service.batch_convert.return_value = mock_results
        
        result = runner.invoke(cli, [
            'batch',
            str(input_file),
            '--output-dir', str(output_dir),
            '--format', 'mp3'
        ])
        
        assert result.exit_code == 0
        assert "Processing 3 expressions" in result.output
        assert "Batch conversion complete" in result.output
        
        # Check output files
        assert output_dir.exists()
        assert (output_dir / "expr_0.mp3").exists()
        assert (output_dir / "expr_1.mp3").exists()
        assert (output_dir / "expr_2.mp3").exists()
    
    def test_batch_convert_json_input(self, runner, mock_service, tmp_path):
        """Test batch convert with JSON input."""
        input_file = tmp_path / "input.json"
        input_data = {
            "expressions": [
                {"latex": "\\frac{1}{2}", "id": "half"},
                {"latex": "x^2", "id": "squared"}
            ]
        }
        input_file.write_text(json.dumps(input_data))
        
        output_dir = tmp_path / "output"
        
        mock_results = [
            AudioData(data=b"audio1", format=AudioFormat.MP3, sample_rate=44100, duration_seconds=1.0),
            AudioData(data=b"audio2", format=AudioFormat.MP3, sample_rate=44100, duration_seconds=1.0)
        ]
        mock_service.batch_convert.return_value = mock_results
        
        result = runner.invoke(cli, [
            'batch',
            str(input_file),
            '--output-dir', str(output_dir),
            '--json'
        ])
        
        assert result.exit_code == 0
        assert (output_dir / "half.mp3").exists()
        assert (output_dir / "squared.mp3").exists()
    
    def test_list_voices_command(self, runner):
        """Test list voices command."""
        with patch('presentation.cli.commands.get_tts_adapter') as mock_adapter:
            from src.adapters.tts_providers import MockTTSAdapter
            adapter = MockTTSAdapter()
            mock_adapter.return_value = adapter
            
            result = runner.invoke(cli, ['list-voices'])
            
            assert result.exit_code == 0
            assert "Available voices:" in result.output
            assert "test-voice-male" in result.output
            assert "test-voice-female" in result.output
    
    def test_list_voices_with_language_filter(self, runner):
        """Test list voices with language filter."""
        with patch('presentation.cli.commands.get_tts_adapter') as mock_adapter:
            from src.adapters.tts_providers import MockTTSAdapter
            adapter = MockTTSAdapter()
            mock_adapter.return_value = adapter
            
            result = runner.invoke(cli, ['list-voices', '--language', 'en'])
            
            assert result.exit_code == 0
            assert "test-voice-male" in result.output
    
    def test_stats_command(self, runner, mock_service):
        """Test stats command."""
        mock_service.get_pattern_stats.return_value = {
            "total_patterns": 541,
            "domains": {
                "general": 100,
                "calculus": 50,
                "algebra": 80
            },
            "priority_distribution": {
                "low": 100,
                "medium": 200,
                "high": 200,
                "critical": 41
            },
            "cache_enabled": True
        }
        
        result = runner.invoke(cli, ['stats'])
        
        assert result.exit_code == 0
        assert "Pattern Statistics" in result.output
        assert "Total patterns: 541" in result.output
        assert "general: 100" in result.output
        assert "Cache enabled: Yes" in result.output
    
    def test_convert_invalid_latex(self, runner, mock_service):
        """Test convert with invalid LaTeX."""
        mock_service.convert_latex_to_speech.side_effect = ValueError("Invalid LaTeX")
        
        result = runner.invoke(cli, [
            'convert',
            'invalid',
            '--output', 'output.mp3'
        ])
        
        assert result.exit_code != 0
        assert "Error" in result.output
        assert "Invalid LaTeX" in result.output
    
    def test_convert_missing_output(self, runner):
        """Test convert without output option."""
        result = runner.invoke(cli, ['convert', 'x^2'])
        
        assert result.exit_code != 0
        assert "Must specify either --output or --stdout" in result.output
    
    def test_batch_convert_missing_file(self, runner, tmp_path):
        """Test batch convert with missing input file."""
        result = runner.invoke(cli, [
            'batch',
            str(tmp_path / 'nonexistent.txt'),
            '--output-dir', str(tmp_path / 'output')
        ])
        
        assert result.exit_code != 0
        assert "Input file not found" in result.output
    
    def test_interactive_mode(self, runner, mock_service):
        """Test interactive mode."""
        # Simulate user input
        user_input = "\\frac{1}{2}\nexit\n"
        
        with patch('click.prompt') as mock_prompt:
            mock_prompt.side_effect = ["\\frac{1}{2}", "exit"]
            
            result = runner.invoke(cli, ['interactive'])
            
            assert result.exit_code == 0
            assert "Interactive mode" in result.output
            assert "Goodbye!" in result.output
            
            # Should have called convert once
            assert mock_service.convert_latex_to_speech.call_count == 1