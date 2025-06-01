"""
Integration tests for API endpoints.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, Mock
import base64

from src.presentation.api.app import app
from src.domain.value_objects import AudioData, AudioFormat
from src.adapters.tts_providers import MockTTSAdapter


@pytest.mark.api
class TestAPIEndpoints:
    """Test cases for FastAPI endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock application dependencies."""
        with patch('presentation.api.dependencies.get_mathtts_service') as mock_service:
            # Create mock service
            service = AsyncMock()
            
            # Mock audio data response
            mock_audio = AudioData(
                data=b"mock audio data",
                format=AudioFormat.MP3,
                sample_rate=44100,
                duration_seconds=2.0
            )
            
            service.convert_latex_to_speech.return_value = mock_audio
            service.get_pattern_stats.return_value = {
                "total_patterns": 541,
                "domains": {"general": 100, "calculus": 50},
                "priority_distribution": {"low": 100, "medium": 200, "high": 200, "critical": 41},
                "cache_enabled": True
            }
            
            mock_service.return_value = service
            yield service
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_convert_latex_endpoint(self, client, mock_dependencies):
        """Test LaTeX to speech conversion endpoint."""
        latex = r"\frac{1}{2}"
        
        response = client.post(
            "/api/v1/convert",
            json={
                "latex": latex,
                "voice_id": "en-US-AriaNeural",
                "rate": 1.0,
                "format": "mp3"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["latex"] == latex
        assert data["format"] == "mp3"
        assert data["duration_seconds"] == 2.0
        assert "audio_base64" in data
        
        # Verify base64 encoding
        audio_bytes = base64.b64decode(data["audio_base64"])
        assert audio_bytes == b"mock audio data"
    
    def test_convert_latex_with_defaults(self, client, mock_dependencies):
        """Test conversion with default options."""
        response = client.post(
            "/api/v1/convert",
            json={"latex": "x^2"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["latex"] == "x^2"
        
        # Should use default voice and format
        mock_dependencies.convert_latex_to_speech.assert_called_once()
        call_args = mock_dependencies.convert_latex_to_speech.call_args
        assert call_args[0][0] == "x^2"
    
    def test_convert_invalid_latex(self, client):
        """Test conversion with invalid LaTeX."""
        response = client.post(
            "/api/v1/convert",
            json={"latex": ""}
        )
        
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("latex" in str(e) for e in errors)
    
    def test_batch_convert_endpoint(self, client, mock_dependencies):
        """Test batch conversion endpoint."""
        expressions = [r"\frac{1}{2}", "x^2", r"\alpha + \beta"]
        
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
        mock_dependencies.batch_convert.return_value = mock_results
        
        response = client.post(
            "/api/v1/batch-convert",
            json={
                "expressions": expressions,
                "voice_id": "en-US-AriaNeural",
                "format": "mp3"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["results"]) == 3
        for i, result in enumerate(data["results"]):
            assert result["latex"] == expressions[i]
            assert result["duration_seconds"] == float(i+1)
            assert base64.b64decode(result["audio_base64"]) == f"audio{i}".encode()
    
    def test_get_patterns_stats(self, client, mock_dependencies):
        """Test pattern statistics endpoint."""
        response = client.get("/api/v1/patterns/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_patterns"] == 541
        assert data["domains"]["general"] == 100
        assert data["priority_distribution"]["high"] == 200
        assert data["cache_enabled"] is True
    
    def test_list_voices_endpoint(self, client):
        """Test list voices endpoint."""
        with patch('presentation.api.dependencies.get_tts_adapter') as mock_adapter:
            adapter = MockTTSAdapter()
            mock_adapter.return_value = adapter
            
            response = client.get("/api/v1/voices")
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data["voices"]) == 2
            assert any(v["gender"] == "male" for v in data["voices"])
            assert any(v["gender"] == "female" for v in data["voices"])
    
    def test_list_voices_with_language_filter(self, client):
        """Test list voices with language filter."""
        with patch('presentation.api.dependencies.get_tts_adapter') as mock_adapter:
            adapter = MockTTSAdapter()
            mock_adapter.return_value = adapter
            
            response = client.get("/api/v1/voices?language=en")
            
            assert response.status_code == 200
            data = response.json()
            
            assert all(v["language"].startswith("en") for v in data["voices"])
    
    def test_convert_with_invalid_voice(self, client, mock_dependencies):
        """Test conversion with invalid voice ID."""
        mock_dependencies.convert_latex_to_speech.side_effect = ValueError("Invalid voice ID")
        
        response = client.post(
            "/api/v1/convert",
            json={
                "latex": "x^2",
                "voice_id": "invalid-voice"
            }
        )
        
        assert response.status_code == 400
        assert "Invalid voice ID" in response.json()["detail"]
    
    def test_convert_with_invalid_format(self, client):
        """Test conversion with invalid audio format."""
        response = client.post(
            "/api/v1/convert",
            json={
                "latex": "x^2",
                "format": "invalid"
            }
        )
        
        assert response.status_code == 422
    
    def test_api_documentation(self, client):
        """Test that API documentation is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
        
        response = client.get("/redoc")
        assert response.status_code == 200
        
        response = client.get("/openapi.json")
        assert response.status_code == 200
        openapi = response.json()
        assert openapi["info"]["title"] == "MathTTS API"