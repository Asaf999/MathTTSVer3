"""
Comprehensive tests for application layer.
"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import Mock, AsyncMock, patch
from src.application.services.mathtts_service import MathTTSService
from src.application.use_cases.process_expression import *
from src.application.dtos import *
from src.application.dtos_v3 import *
from src.domain.value_objects import *


class TestAllApplication:
    """Test all application layer components."""
    
    @pytest.mark.asyncio
    async def test_mathtts_service_complete(self):
        """Test MathTTSService completely."""
        # Mock dependencies
        pattern_service = Mock()
        pattern_service.convert_expression.return_value = SpeechText("one half")
        
        tts_adapter = AsyncMock()
        tts_adapter.synthesize.return_value = Mock(data=b"audio", format="mp3")
        tts_adapter.is_available.return_value = True
        tts_adapter.list_voices.return_value = []
        tts_adapter.get_supported_formats.return_value = ["mp3", "wav"]
        
        cache = AsyncMock()
        cache.get.return_value = None
        
        service = MathTTSService(
            pattern_service=pattern_service,
            tts_adapter=tts_adapter,
            cache=cache
        )
        
        # Test convert_latex
        result = await service.convert_latex(r"\\frac{1}{2}", "test-voice")
        assert "speech_text" in result
        assert result["speech_text"] == "one half"
        
        # Test with cache hit
        cache.get.return_value = b"cached_audio"
        result = await service.convert_latex(r"\\frac{1}{2}", "test-voice")
        assert result.get("cached") == True
        
        # Test convert_batch
        results = await service.convert_batch([r"\\frac{1}{2}", r"x^2"], "test-voice")
        assert len(results) == 2
        
        # Test list_voices
        voices = await service.list_voices()
        assert isinstance(voices, list)
        
        # Test get_supported_formats
        formats = service.get_supported_formats()
        assert "mp3" in formats
    
    @pytest.mark.asyncio
    async def test_process_expression_use_case_complete(self):
        """Test ProcessExpressionUseCase completely."""
        # Mock dependencies
        pattern_service = Mock()
        pattern_service.convert_expression.return_value = SpeechText("one half")
        
        tts_service = AsyncMock()
        tts_service.synthesize.return_value = b"audio_data"
        
        use_case = ProcessExpressionUseCase(
            pattern_service=pattern_service,
            tts_service=tts_service
        )
        
        # Test execute
        request = ProcessExpressionRequest(
            latex=r"\\frac{1}{2}",
            voice_id="test-voice",
            format="mp3"
        )
        
        response = await use_case.execute(request)
        assert isinstance(response, ProcessExpressionResponse)
        assert response.speech_text == "one half"
        assert response.audio_data == b"audio_data"
    
    def test_all_dtos(self):
        """Test all DTOs."""
        # Test v3 DTOs
        req = ProcessExpressionRequest(
            latex="test",
            voice_id="voice",
            format="mp3",
            rate=1.0,
            pitch=1.0
        )
        assert req.latex == "test"
        
        resp = ProcessExpressionResponse(
            speech_text="test",
            audio_data=b"data",
            format="mp3",
            cached=False
        )
        assert resp.speech_text == "test"
        
        # Test other DTOs
        batch_req = BatchProcessRequest(
            expressions=["test1", "test2"],
            voice_id="voice"
        )
        assert len(batch_req.expressions) == 2
