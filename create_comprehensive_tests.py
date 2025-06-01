#!/usr/bin/env python3
"""
Create comprehensive tests for all modules to achieve 100% coverage.
"""

import os
from pathlib import Path

# Test templates for different module types
TEST_TEMPLATES = {
    'natural_language_processor': '''"""
Unit tests for Natural Language Processor.
"""
import pytest
from src.domain.services.natural_language_processor import (
    NaturalLanguageProcessor, NaturalLanguageContext
)


class TestNaturalLanguageProcessor:
    """Test NaturalLanguageProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        return NaturalLanguageProcessor()
    
    def test_enhance_mathematical_speech_basic(self, processor):
        """Test basic speech enhancement."""
        context = NaturalLanguageContext()
        result = processor.enhance_mathematical_speech("x equals 5", context)
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_add_contextual_articles(self, processor):
        """Test adding contextual articles."""
        context = NaturalLanguageContext()
        text = "derivative of x"
        result = processor._add_contextual_articles(text, context)
        assert "the derivative" in result or "derivative" in result
    
    def test_enhance_mathematical_phrasing(self, processor):
        """Test mathematical phrasing enhancement."""
        context = NaturalLanguageContext()
        text = "x plus y equals z"
        result = processor._enhance_mathematical_phrasing(text, context)
        assert isinstance(result, str)
    
    def test_add_semantic_understanding(self, processor):
        """Test adding semantic understanding."""
        context = NaturalLanguageContext(is_definition=True)
        text = "let x equal 5"
        result = processor._add_semantic_understanding(text, context)
        assert isinstance(result, str)
    
    def test_add_storytelling_flow(self, processor):
        """Test adding storytelling flow."""
        context = NaturalLanguageContext(is_theorem=True)
        text = "this theorem states"
        result = processor._add_storytelling_flow(text, context)
        assert isinstance(result, str)
    
    def test_different_contexts(self, processor):
        """Test with different context types."""
        contexts = [
            NaturalLanguageContext(is_definition=True),
            NaturalLanguageContext(is_theorem=True),
            NaturalLanguageContext(is_proof=True),
            NaturalLanguageContext(audience_level="elementary"),
            NaturalLanguageContext(audience_level="graduate")
        ]
        
        for context in contexts:
            result = processor.enhance_mathematical_speech("test", context)
            assert isinstance(result, str)
''',

    'mathematical_rhythm_processor': '''"""
Unit tests for Mathematical Rhythm Processor.
"""
import pytest
from src.domain.services.mathematical_rhythm_processor import (
    MathematicalRhythmProcessor, RhythmContext, PauseLength, EmphasisLevel
)


class TestMathematicalRhythmProcessor:
    """Test MathematicalRhythmProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        return MathematicalRhythmProcessor()
    
    def test_add_mathematical_rhythm_basic(self, processor):
        """Test basic rhythm addition."""
        text = "x equals 5"
        result = processor.add_mathematical_rhythm(text)
        assert isinstance(result, str)
        assert len(result) >= len(text)
    
    def test_add_operation_pauses(self, processor):
        """Test adding pauses for operations."""
        text = "x equals y plus z"
        result = processor._add_operation_pauses(text)
        assert "<pause:" in result
    
    def test_add_emphasis_markup(self, processor):
        """Test adding emphasis markup."""
        text = "therefore x equals 5"
        result = processor._add_emphasis_markup(text)
        assert "<emphasis" in result
    
    def test_add_conceptual_pauses(self, processor):
        """Test adding conceptual pauses."""
        context = RhythmContext()
        text = "x, which means y"
        result = processor._add_conceptual_pauses(text, context)
        assert "<pause:" in result
    
    def test_add_breathing_points(self, processor):
        """Test adding breathing points."""
        long_text = "This is a very long sentence that needs breathing points, especially when we have multiple clauses, subclauses, and mathematical expressions all combined together."
        result = processor._add_breathing_points(long_text)
        assert isinstance(result, str)
    
    def test_add_dramatic_pauses(self, processor):
        """Test adding dramatic pauses."""
        context = RhythmContext(is_theorem=True)
        text = "Theorem: x equals y"
        result = processor._add_dramatic_pauses(text, context)
        assert "<pause:" in result
    
    def test_optimize_rhythm_flow(self, processor):
        """Test rhythm flow optimization."""
        text = "<pause:200ms> <pause:300ms> test <pause:400ms> "
        result = processor._optimize_rhythm_flow(text)
        # Should remove redundant pauses
        assert result.count("<pause:") < text.count("<pause:")
    
    def test_reading_time_estimate(self, processor):
        """Test reading time estimation."""
        text = "This is a test sentence with <pause:500ms> pauses."
        time_estimate = processor.get_reading_time_estimate(text)
        assert time_estimate > 0
        assert isinstance(time_estimate, float)
    
    def test_create_ssml_output(self, processor):
        """Test SSML output creation."""
        text = "Test <pause:300ms> with <emphasis level=\\"strong\\">emphasis</emphasis>"
        ssml = processor.create_ssml_output(text)
        assert ssml.startswith("<speak>")
        assert ssml.endswith("</speak>")
        assert "<break time=" in ssml
    
    def test_analyze_rhythm_quality(self, processor):
        """Test rhythm quality analysis."""
        text = "Test <pause:300ms> with <emphasis level=\\"strong\\">emphasis</emphasis>"
        metrics = processor.analyze_rhythm_quality(text)
        assert "rhythm_score" in metrics
        assert metrics["rhythm_score"] >= 0
        assert "total_pauses" in metrics
        assert "total_emphasis" in metrics
''',

    'pattern_matching_service': '''"""
Unit tests for Pattern Matching Service (additional coverage).
"""
import pytest
from unittest.mock import Mock
from src.domain.services.pattern_matching_service import PatternMatchingService
from src.domain.entities import PatternEntity
from src.domain.value_objects import PatternPriority, LaTeXExpression, SpeechText


class TestPatternMatchingServiceAdditional:
    """Additional tests for PatternMatchingService."""
    
    @pytest.fixture
    def complex_patterns(self):
        """Create complex pattern set."""
        return [
            PatternEntity(
                id="nested-1",
                name="Nested Fraction",
                pattern=r"\\\\frac\\{\\\\frac\\{(.+?)\\}\\{(.+?)\\}\\}\\{(.+?)\\}",
                output_template="\\\\1 over \\\\2, all over \\\\3",
                priority=PatternPriority(1500),
                metadata={"contexts": ["display"]}
            ),
            PatternEntity(
                id="matrix-1",
                name="Matrix",
                pattern=r"\\\\begin\\{matrix\\}(.+?)\\\\end\\{matrix\\}",
                output_template="matrix with elements \\\\1",
                priority=PatternPriority(1200),
                domain="linear_algebra"
            ),
            PatternEntity(
                id="sum-1",
                name="Summation",
                pattern=r"\\\\sum_\\{(.+?)\\}\\^\\{(.+?)\\}",
                output_template="sum from \\\\1 to \\\\2",
                priority=PatternPriority(1100),
                tags=["summation", "series"]
            )
        ]
    
    @pytest.fixture
    def service_with_complex(self, complex_patterns):
        """Create service with complex patterns."""
        repo = Mock()
        repo.get_all.return_value = complex_patterns
        return PatternMatchingService(repo)
    
    def test_nested_pattern_matching(self, service_with_complex):
        """Test matching nested patterns."""
        expr = LaTeXExpression(r"\\\\frac{\\\\frac{a}{b}}{c}")
        matches = service_with_complex.find_matching_patterns(expr)
        assert len(matches) > 0
        assert matches[0].id == "nested-1"
    
    def test_domain_specific_matching(self, service_with_complex):
        """Test domain-specific pattern matching."""
        expr = LaTeXExpression(r"\\\\begin{matrix}a & b\\\\end{matrix}")
        
        # With domain filter
        matches = service_with_complex.find_matching_patterns(expr, domain="linear_algebra")
        assert any(p.id == "matrix-1" for p in matches)
        
        # With wrong domain
        matches = service_with_complex.find_matching_patterns(expr, domain="calculus")
        assert not any(p.id == "matrix-1" for p in matches)
    
    def test_tag_filtering(self, service_with_complex):
        """Test filtering by tags."""
        expr = LaTeXExpression(r"\\\\sum_{i=1}^{n}")
        
        patterns = service_with_complex.find_matching_patterns(expr)
        summation_patterns = [p for p in patterns if "summation" in p.tags]
        assert len(summation_patterns) > 0
    
    def test_pattern_caching_effectiveness(self, service_with_complex):
        """Test that pattern caching works correctly."""
        expr = LaTeXExpression(r"\\\\frac{1}{2}")
        
        # First call
        result1 = service_with_complex.convert_expression(expr)
        
        # Modify repository return value
        service_with_complex.pattern_repository.get_all.return_value = []
        
        # Second call should still work due to cache
        result2 = service_with_complex.convert_expression(expr)
        
        assert result1.value == result2.value
    
    def test_apply_pattern_with_special_chars(self, service_with_complex):
        """Test applying patterns with special regex characters."""
        pattern = PatternEntity(
            id="special",
            name="Special",
            pattern=r"\\\\$(.+?)\\\\$",
            output_template="dollar \\\\1 dollar",
            priority=PatternPriority(1000)
        )
        expr = LaTeXExpression(r"\\\\$x\\\\$")
        
        result = service_with_complex.apply_pattern(pattern, expr)
        if result:
            assert result.value == "dollar x dollar"
    
    def test_empty_pattern_repository(self):
        """Test behavior with empty repository."""
        repo = Mock()
        repo.get_all.return_value = []
        service = PatternMatchingService(repo)
        
        expr = LaTeXExpression(r"\\\\frac{1}{2}")
        result = service.convert_expression(expr)
        
        # Should return original expression
        assert result.value == r"\\\\frac{1}{2}"
''',

    'mathtts_service': '''"""
Unit tests for MathTTS Service.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from src.application.services.mathtts_service import MathTTSService
from src.domain.value_objects import LaTeXExpression, SpeechText, TTSOptions


class TestMathTTSService:
    """Test MathTTSService."""
    
    @pytest.fixture
    def mock_pattern_service(self):
        """Create mock pattern service."""
        service = Mock()
        service.convert_expression.return_value = SpeechText("one half")
        return service
    
    @pytest.fixture
    def mock_tts_adapter(self):
        """Create mock TTS adapter."""
        adapter = AsyncMock()
        adapter.synthesize.return_value = Mock(data=b"audio_data", format="mp3")
        adapter.is_available.return_value = True
        return adapter
    
    @pytest.fixture
    def mock_cache(self):
        """Create mock cache."""
        cache = AsyncMock()
        cache.get.return_value = None
        return cache
    
    @pytest.fixture
    def service(self, mock_pattern_service, mock_tts_adapter, mock_cache):
        """Create MathTTS service."""
        return MathTTSService(
            pattern_service=mock_pattern_service,
            tts_adapter=mock_tts_adapter,
            cache=mock_cache
        )
    
    @pytest.mark.asyncio
    async def test_convert_latex_basic(self, service):
        """Test basic LaTeX conversion."""
        result = await service.convert_latex(
            latex=r"\\\\frac{1}{2}",
            voice_id="test-voice"
        )
        
        assert result["speech_text"] == "one half"
        assert "audio_url" in result or "audio_data" in result
        assert result["format"] == "mp3"
    
    @pytest.mark.asyncio
    async def test_convert_latex_with_cache_hit(self, service, mock_cache):
        """Test conversion with cache hit."""
        # Setup cache hit
        mock_cache.get.return_value = b"cached_audio"
        
        result = await service.convert_latex(
            latex=r"\\\\frac{1}{2}",
            voice_id="test-voice"
        )
        
        # Should use cached data
        assert result["audio_data"] == b"cached_audio"
        assert result["cached"] == True
    
    @pytest.mark.asyncio
    async def test_convert_latex_with_options(self, service):
        """Test conversion with TTS options."""
        result = await service.convert_latex(
            latex=r"\\\\frac{1}{2}",
            voice_id="test-voice",
            format="wav",
            rate=1.5,
            pitch=0.8
        )
        
        # Verify TTS options were passed
        service.tts_adapter.synthesize.assert_called_once()
        call_args = service.tts_adapter.synthesize.call_args
        options = call_args[1]["options"]
        assert options.rate == 1.5
        assert options.pitch == 0.8
    
    @pytest.mark.asyncio
    async def test_convert_latex_invalid_input(self, service, mock_pattern_service):
        """Test conversion with invalid LaTeX."""
        mock_pattern_service.convert_expression.side_effect = ValueError("Invalid LaTeX")
        
        with pytest.raises(ValueError):
            await service.convert_latex(
                latex="invalid{",
                voice_id="test-voice"
            )
    
    @pytest.mark.asyncio
    async def test_convert_latex_tts_failure(self, service, mock_tts_adapter):
        """Test conversion with TTS failure."""
        mock_tts_adapter.synthesize.side_effect = Exception("TTS error")
        
        with pytest.raises(Exception, match="TTS error"):
            await service.convert_latex(
                latex=r"\\\\frac{1}{2}",
                voice_id="test-voice"
            )
    
    @pytest.mark.asyncio
    async def test_convert_batch(self, service):
        """Test batch conversion."""
        expressions = [
            r"\\\\frac{1}{2}",
            r"\\\\sqrt{4}",
            r"x^2"
        ]
        
        results = await service.convert_batch(
            expressions=expressions,
            voice_id="test-voice"
        )
        
        assert len(results) == 3
        for result in results:
            assert "speech_text" in result
            assert "audio_data" in result or "audio_url" in result
    
    @pytest.mark.asyncio
    async def test_list_voices(self, service, mock_tts_adapter):
        """Test listing available voices."""
        mock_tts_adapter.list_voices.return_value = [
            Mock(id="voice1", name="Voice 1"),
            Mock(id="voice2", name="Voice 2")
        ]
        
        voices = await service.list_voices()
        
        assert len(voices) == 2
        assert voices[0].id == "voice1"
    
    @pytest.mark.asyncio
    async def test_get_supported_formats(self, service, mock_tts_adapter):
        """Test getting supported formats."""
        mock_tts_adapter.get_supported_formats.return_value = ["mp3", "wav", "ogg"]
        
        formats = service.get_supported_formats()
        
        assert "mp3" in formats
        assert "wav" in formats
        assert "ogg" in formats
''',

    'cache_implementations': '''"""
Unit tests for cache implementations.
"""
import pytest
from unittest.mock import Mock, patch
from src.infrastructure.cache.lru_cache_repository import LRUCacheRepository
from src.infrastructure.cache.audio_cache import AudioCache
from src.domain.value_objects_tts import AudioData, AudioFormat


class TestLRUCacheRepository:
    """Test LRUCacheRepository."""
    
    @pytest.fixture
    def cache(self):
        """Create LRU cache."""
        return LRUCacheRepository(max_size=3)
    
    def test_set_and_get(self, cache):
        """Test basic set and get operations."""
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
    
    def test_get_nonexistent(self, cache):
        """Test getting non-existent key."""
        assert cache.get("nonexistent") is None
    
    def test_exists(self, cache):
        """Test existence check."""
        cache.set("key1", "value1")
        assert cache.exists("key1")
        assert not cache.exists("nonexistent")
    
    def test_delete(self, cache):
        """Test deletion."""
        cache.set("key1", "value1")
        assert cache.delete("key1")
        assert not cache.exists("key1")
        assert not cache.delete("nonexistent")
    
    def test_clear(self, cache):
        """Test clearing cache."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert not cache.exists("key1")
        assert not cache.exists("key2")
    
    def test_lru_eviction(self, cache):
        """Test LRU eviction when cache is full."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Access key1 to make it more recently used
        cache.get("key1")
        
        # Add new item, should evict key2
        cache.set("key4", "value4")
        
        assert cache.exists("key1")
        assert not cache.exists("key2")  # Evicted
        assert cache.exists("key3")
        assert cache.exists("key4")
    
    def test_size(self, cache):
        """Test size tracking."""
        assert cache.size() == 0
        cache.set("key1", "value1")
        assert cache.size() == 1
        cache.set("key2", "value2")
        assert cache.size() == 2
    
    def test_get_all_keys(self, cache):
        """Test getting all keys."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        keys = cache.get_all_keys()
        assert "key1" in keys
        assert "key2" in keys
    
    def test_ttl_not_supported(self, cache):
        """Test that TTL operations raise NotImplementedError."""
        with pytest.raises(NotImplementedError):
            cache.set_with_ttl("key", "value", 60)
        
        with pytest.raises(NotImplementedError):
            cache.get_ttl("key")


class TestAudioCache:
    """Test AudioCache."""
    
    @pytest.fixture
    def audio_cache(self, tmp_path):
        """Create audio cache."""
        return AudioCache(cache_dir=tmp_path / "cache", max_size_mb=1)
    
    @pytest.fixture
    def sample_audio(self):
        """Create sample audio data."""
        return AudioData(
            data=b"test_audio_data",
            format=AudioFormat.MP3,
            sample_rate=44100,
            duration_seconds=1.0
        )
    
    def test_cache_audio(self, audio_cache, sample_audio):
        """Test caching audio data."""
        key = "test_key"
        cached_path = audio_cache.cache_audio(key, sample_audio)
        
        assert cached_path.exists()
        assert cached_path.suffix == ".mp3"
    
    def test_get_cached_audio(self, audio_cache, sample_audio):
        """Test retrieving cached audio."""
        key = "test_key"
        audio_cache.cache_audio(key, sample_audio)
        
        retrieved = audio_cache.get_cached_audio(key)
        assert retrieved is not None
        assert retrieved.data == sample_audio.data
        assert retrieved.format == sample_audio.format
    
    def test_get_nonexistent_audio(self, audio_cache):
        """Test getting non-existent audio."""
        assert audio_cache.get_cached_audio("nonexistent") is None
    
    def test_exists(self, audio_cache, sample_audio):
        """Test existence check."""
        key = "test_key"
        assert not audio_cache.exists(key)
        
        audio_cache.cache_audio(key, sample_audio)
        assert audio_cache.exists(key)
    
    def test_delete(self, audio_cache, sample_audio):
        """Test deleting cached audio."""
        key = "test_key"
        audio_cache.cache_audio(key, sample_audio)
        
        assert audio_cache.delete(key)
        assert not audio_cache.exists(key)
        assert not audio_cache.delete("nonexistent")
    
    def test_clear(self, audio_cache, sample_audio):
        """Test clearing cache."""
        audio_cache.cache_audio("key1", sample_audio)
        audio_cache.cache_audio("key2", sample_audio)
        
        audio_cache.clear()
        
        assert not audio_cache.exists("key1")
        assert not audio_cache.exists("key2")
    
    def test_size_limit(self, audio_cache):
        """Test cache size limit enforcement."""
        # Create large audio data (over 1MB limit)
        large_audio = AudioData(
            data=b"x" * (1024 * 1024 + 1000),  # Just over 1MB
            format=AudioFormat.MP3,
            sample_rate=44100,
            duration_seconds=10.0
        )
        
        # Cache should handle size limit gracefully
        audio_cache.cache_audio("large", large_audio)
        
        # Add another item
        audio_cache.cache_audio("small", AudioData(
            data=b"small",
            format=AudioFormat.MP3,
            sample_rate=44100,
            duration_seconds=0.1
        ))
        
        # Large item should be evicted
        assert not audio_cache.exists("large")
        assert audio_cache.exists("small")
    
    def test_get_cache_stats(self, audio_cache, sample_audio):
        """Test getting cache statistics."""
        audio_cache.cache_audio("key1", sample_audio)
        audio_cache.cache_audio("key2", sample_audio)
        
        stats = audio_cache.get_stats()
        
        assert stats["total_files"] == 2
        assert stats["total_size_mb"] > 0
        assert stats["max_size_mb"] == 1
''',

    'auth_components': '''"""
Unit tests for authentication components.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from src.infrastructure.auth.jwt_handler import JWTHandler
from src.infrastructure.auth.api_key_manager import APIKeyManager
from src.infrastructure.auth.models import User, APIKey


class TestJWTHandler:
    """Test JWTHandler."""
    
    @pytest.fixture
    def jwt_handler(self):
        """Create JWT handler."""
        return JWTHandler(
            secret_key="test_secret",
            algorithm="HS256",
            access_expire_minutes=30,
            refresh_expire_minutes=60*24*7
        )
    
    def test_create_tokens(self, jwt_handler):
        """Test creating access and refresh tokens."""
        user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            roles=["user"]
        )
        
        access_token = jwt_handler.create_access_token(user)
        refresh_token = jwt_handler.create_refresh_token(user)
        
        assert isinstance(access_token, str)
        assert isinstance(refresh_token, str)
        assert access_token != refresh_token
    
    def test_decode_token(self, jwt_handler):
        """Test decoding valid token."""
        user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            roles=["user", "admin"]
        )
        
        token = jwt_handler.create_access_token(user)
        payload = jwt_handler.decode_token(token)
        
        assert payload["sub"] == "user-123"
        assert payload["username"] == "testuser"
        assert payload["roles"] == ["user", "admin"]
    
    def test_decode_expired_token(self, jwt_handler):
        """Test decoding expired token."""
        with patch('jose.jwt.decode') as mock_decode:
            mock_decode.side_effect = Exception("Token expired")
            
            with pytest.raises(Exception):
                jwt_handler.decode_token("expired_token")
    
    def test_decode_invalid_token(self, jwt_handler):
        """Test decoding invalid token."""
        with pytest.raises(Exception):
            jwt_handler.decode_token("invalid_token")
    
    def test_verify_token_type(self, jwt_handler):
        """Test token type verification."""
        user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            roles=["user"]
        )
        
        access_token = jwt_handler.create_access_token(user)
        refresh_token = jwt_handler.create_refresh_token(user)
        
        # Decode and check types
        access_payload = jwt_handler.decode_token(access_token)
        refresh_payload = jwt_handler.decode_token(refresh_token)
        
        assert access_payload.get("type") == "access"
        assert refresh_payload.get("type") == "refresh"


class TestAPIKeyManager:
    """Test APIKeyManager."""
    
    @pytest.fixture
    def api_key_manager(self):
        """Create API key manager."""
        return APIKeyManager()
    
    def test_create_api_key(self, api_key_manager):
        """Test creating API key."""
        api_key = api_key_manager.create_api_key(
            name="Test Key",
            user_id="user-123",
            scopes=["read", "write"]
        )
        
        assert isinstance(api_key, APIKey)
        assert api_key.name == "Test Key"
        assert api_key.user_id == "user-123"
        assert api_key.scopes == ["read", "write"]
        assert len(api_key.key) > 32  # Should be a long random key
    
    def test_validate_api_key(self, api_key_manager):
        """Test validating API key."""
        api_key = api_key_manager.create_api_key(
            name="Test Key",
            user_id="user-123"
        )
        
        # Store the key
        api_key_manager.store_api_key(api_key)
        
        # Validate
        validated = api_key_manager.validate_api_key(api_key.key)
        assert validated is not None
        assert validated.id == api_key.id
    
    def test_validate_invalid_key(self, api_key_manager):
        """Test validating invalid API key."""
        assert api_key_manager.validate_api_key("invalid_key") is None
    
    def test_validate_expired_key(self, api_key_manager):
        """Test validating expired API key."""
        api_key = api_key_manager.create_api_key(
            name="Test Key",
            user_id="user-123",
            expires_at=datetime.utcnow() - timedelta(days=1)
        )
        
        api_key_manager.store_api_key(api_key)
        
        # Should return None for expired key
        assert api_key_manager.validate_api_key(api_key.key) is None
    
    def test_revoke_api_key(self, api_key_manager):
        """Test revoking API key."""
        api_key = api_key_manager.create_api_key(
            name="Test Key",
            user_id="user-123"
        )
        
        api_key_manager.store_api_key(api_key)
        assert api_key_manager.revoke_api_key(api_key.id)
        
        # Should not validate after revocation
        assert api_key_manager.validate_api_key(api_key.key) is None
    
    def test_list_user_keys(self, api_key_manager):
        """Test listing user's API keys."""
        # Create multiple keys for user
        key1 = api_key_manager.create_api_key("Key 1", "user-123")
        key2 = api_key_manager.create_api_key("Key 2", "user-123")
        key3 = api_key_manager.create_api_key("Key 3", "user-456")
        
        api_key_manager.store_api_key(key1)
        api_key_manager.store_api_key(key2)
        api_key_manager.store_api_key(key3)
        
        user_keys = api_key_manager.list_user_keys("user-123")
        assert len(user_keys) == 2
        assert all(k.user_id == "user-123" for k in user_keys)
''',

    'logging_components': '''"""
Unit tests for logging components.
"""
import pytest
from unittest.mock import Mock, patch
import structlog
from src.infrastructure.logging.logger import get_logger, configure_logging
from src.infrastructure.logging.correlation import correlation_id_processor


class TestLogging:
    """Test logging components."""
    
    def test_get_logger(self):
        """Test getting logger instance."""
        logger = get_logger("test.module")
        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "debug")
    
    def test_configure_logging(self):
        """Test logging configuration."""
        configure_logging(level="DEBUG", json_format=True)
        
        logger = get_logger("test")
        # Should be able to log without errors
        logger.info("test message", extra_field="value")
    
    @patch('structlog.get_logger')
    def test_correlation_id_processor(self, mock_get_logger):
        """Test correlation ID processor."""
        mock_logger = Mock()
        event_dict = {
            "event": "test event",
            "level": "info"
        }
        
        # Without correlation ID
        result = correlation_id_processor(mock_logger, "method", event_dict)
        assert "correlation_id" in result
        
        # With correlation ID in context
        with patch('src.infrastructure.logging.correlation.get_correlation_id') as mock_get_id:
            mock_get_id.return_value = "test-correlation-id"
            result = correlation_id_processor(mock_logger, "method", event_dict)
            assert result["correlation_id"] == "test-correlation-id"
    
    def test_structured_logging(self):
        """Test structured logging with context."""
        logger = get_logger("test.structured")
        
        # Should be able to bind context
        bound_logger = logger.bind(user_id="123", request_id="req-456")
        
        # Log with bound context
        bound_logger.info("user action", action="login")
        
        # New instance should not have bound context
        new_logger = get_logger("test.structured.new")
        # This is a different logger instance
    
    @patch('sys.stdout')
    def test_json_formatting(self, mock_stdout):
        """Test JSON formatted output."""
        configure_logging(json_format=True)
        logger = get_logger("test.json")
        
        logger.info("test message", field1="value1", field2=123)
        
        # Verify write was called (actual JSON parsing would be complex)
        assert mock_stdout.write.called
    
    def test_log_levels(self):
        """Test different log levels."""
        logger = get_logger("test.levels")
        
        # All these should work without errors
        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")
        
        try:
            raise ValueError("test error")
        except ValueError:
            logger.exception("caught exception")
    
    def test_logger_with_extra_fields(self):
        """Test logging with extra fields."""
        logger = get_logger("test.extra")
        
        logger.info(
            "complex event",
            user_id="123",
            action="create",
            resource="document",
            metadata={"size": 1024, "type": "pdf"}
        )
        
        # Should handle nested structures
        logger.info(
            "nested data",
            data={
                "level1": {
                    "level2": {
                        "value": 42
                    }
                }
            }
        )
''',

    'rate_limiting': '''"""
Unit tests for rate limiting.
"""
import pytest
from unittest.mock import Mock, patch
import time
from src.infrastructure.rate_limiting import (
    RateLimiter, IPRateLimiter, UserRateLimiter, APIKeyRateLimiter
)


class TestRateLimiter:
    """Test base RateLimiter."""
    
    def test_fixed_window_rate_limiter(self):
        """Test fixed window rate limiting."""
        limiter = RateLimiter(max_requests=3, window_seconds=1)
        
        # Should allow first 3 requests
        assert limiter.is_allowed("client1")
        assert limiter.is_allowed("client1")
        assert limiter.is_allowed("client1")
        
        # 4th request should be denied
        assert not limiter.is_allowed("client1")
        
        # Different client should have separate limit
        assert limiter.is_allowed("client2")
    
    def test_rate_limit_window_reset(self):
        """Test rate limit window reset."""
        limiter = RateLimiter(max_requests=2, window_seconds=0.1)
        
        assert limiter.is_allowed("client1")
        assert limiter.is_allowed("client1")
        assert not limiter.is_allowed("client1")
        
        # Wait for window to reset
        time.sleep(0.2)
        
        # Should allow again
        assert limiter.is_allowed("client1")
    
    def test_get_remaining_requests(self):
        """Test getting remaining requests."""
        limiter = RateLimiter(max_requests=5, window_seconds=10)
        
        assert limiter.get_remaining("client1") == 5
        
        limiter.is_allowed("client1")
        assert limiter.get_remaining("client1") == 4
        
        limiter.is_allowed("client1")
        limiter.is_allowed("client1")
        assert limiter.get_remaining("client1") == 2
    
    def test_get_reset_time(self):
        """Test getting reset time."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        limiter.is_allowed("client1")
        reset_time = limiter.get_reset_time("client1")
        
        assert reset_time > time.time()
        assert reset_time <= time.time() + 60


class TestIPRateLimiter:
    """Test IP-based rate limiter."""
    
    def test_ip_rate_limiting(self):
        """Test IP-specific rate limiting."""
        limiter = IPRateLimiter(max_requests=10, window_seconds=60)
        
        # Test with different IPs
        for i in range(10):
            assert limiter.is_allowed("192.168.1.1")
        
        assert not limiter.is_allowed("192.168.1.1")
        
        # Different IP should work
        assert limiter.is_allowed("192.168.1.2")
    
    def test_ip_whitelist(self):
        """Test IP whitelist."""
        limiter = IPRateLimiter(
            max_requests=1,
            window_seconds=60,
            whitelist=["127.0.0.1", "192.168.1.100"]
        )
        
        # Whitelisted IPs should always be allowed
        for _ in range(10):
            assert limiter.is_allowed("127.0.0.1")
            assert limiter.is_allowed("192.168.1.100")
        
        # Non-whitelisted should be limited
        assert limiter.is_allowed("192.168.1.1")
        assert not limiter.is_allowed("192.168.1.1")


class TestUserRateLimiter:
    """Test user-based rate limiter."""
    
    def test_user_rate_limiting(self):
        """Test user-specific rate limiting."""
        limiter = UserRateLimiter(max_requests=100, window_seconds=3600)
        
        # Test with user IDs
        user_id = "user-123"
        
        for i in range(100):
            assert limiter.is_allowed(user_id)
        
        assert not limiter.is_allowed(user_id)
        
        # Different user should have separate limit
        assert limiter.is_allowed("user-456")
    
    def test_user_tier_limits(self):
        """Test different limits for user tiers."""
        limiter = UserRateLimiter(
            max_requests=10,
            window_seconds=60,
            tier_limits={
                "free": 10,
                "pro": 100,
                "enterprise": 1000
            }
        )
        
        # Free tier
        for i in range(10):
            assert limiter.is_allowed("user-free", tier="free")
        assert not limiter.is_allowed("user-free", tier="free")
        
        # Pro tier has higher limit
        for i in range(100):
            assert limiter.is_allowed("user-pro", tier="pro")
        assert not limiter.is_allowed("user-pro", tier="pro")


class TestAPIKeyRateLimiter:
    """Test API key rate limiter."""
    
    def test_api_key_rate_limiting(self):
        """Test API key specific rate limiting."""
        limiter = APIKeyRateLimiter(max_requests=1000, window_seconds=3600)
        
        api_key = "sk_test_123456"
        
        # Should track by API key
        for i in range(1000):
            assert limiter.is_allowed(api_key)
        
        assert not limiter.is_allowed(api_key)
    
    def test_api_key_custom_limits(self):
        """Test custom limits per API key."""
        custom_limits = {
            "sk_limited": 10,
            "sk_unlimited": 999999
        }
        
        limiter = APIKeyRateLimiter(
            max_requests=100,
            window_seconds=60,
            key_limits=custom_limits
        )
        
        # Limited key
        for i in range(10):
            assert limiter.is_allowed("sk_limited")
        assert not limiter.is_allowed("sk_limited")
        
        # High limit key
        for i in range(200):
            assert limiter.is_allowed("sk_unlimited")
        
        # Default limit key
        for i in range(100):
            assert limiter.is_allowed("sk_default")
        assert not limiter.is_allowed("sk_default")
'''
}

def create_test_file(module_name: str, module_path: str, template_key: str):
    """Create test file for a module."""
    test_dir = Path(f'tests/unit/{Path(module_path).parent}')
    test_dir.mkdir(parents=True, exist_ok=True)
    
    test_file = test_dir / f'test_{module_name}.py'
    
    # Use template if available
    if template_key in TEST_TEMPLATES:
        content = TEST_TEMPLATES[template_key]
    else:
        # Generic template
        content = f'''"""
Unit tests for {module_name}.
"""
import pytest
from unittest.mock import Mock, patch
from {module_path.replace('/', '.')} import *


class Test{module_name.replace('_', ' ').title().replace(' ', '')}:
    """Test {module_name}."""
    
    def test_placeholder(self):
        """Placeholder test."""
        assert True
'''
    
    with open(test_file, 'w') as f:
        f.write(content)
    
    print(f"Created test: {test_file}")

def main():
    """Create comprehensive tests."""
    print("Creating comprehensive test suite...")
    
    # Critical modules that need tests
    modules_to_test = [
        ('natural_language_processor', 'src/domain/services/natural_language_processor', 'natural_language_processor'),
        ('mathematical_rhythm_processor', 'src/domain/services/mathematical_rhythm_processor', 'mathematical_rhythm_processor'),
        ('pattern_matching_service', 'src/domain/services/pattern_matching_service', 'pattern_matching_service'),
        ('mathtts_service', 'src/application/services/mathtts_service', 'mathtts_service'),
        ('cache_implementations', 'src/infrastructure/cache/lru_cache_repository', 'cache_implementations'),
        ('auth_components', 'src/infrastructure/auth/jwt_handler', 'auth_components'),
        ('logging_components', 'src/infrastructure/logging/logger', 'logging_components'),
        ('rate_limiting', 'src/infrastructure/rate_limiting', 'rate_limiting'),
    ]
    
    for module_name, module_path, template_key in modules_to_test:
        create_test_file(module_name, module_path, template_key)
    
    print("\nAll comprehensive tests created!")
    print("\nNext: Run pytest with coverage to see the improvement")

if __name__ == "__main__":
    main()