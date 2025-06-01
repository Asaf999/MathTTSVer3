"""
Tests for infrastructure layer components.

This module tests configuration, logging, and other infrastructure components.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock

from src.infrastructure.config import Settings, get_settings, Environment, LogLevel
from src.infrastructure.logging import Logger, get_logger, correlation_id
from src.infrastructure.cache import LRUCacheRepository


class TestSettings:
    """Test configuration management."""
    
    def test_default_settings(self):
        """Test default configuration values."""
        settings = Settings()
        
        assert settings.app_name == "MathTTS"
        assert settings.app_version == "3.0.0"
        assert settings.environment == Environment.DEVELOPMENT
        assert settings.log_level == LogLevel.INFO
        assert settings.debug is False
    
    def test_environment_variables(self):
        """Test configuration from environment variables."""
        with patch.dict('os.environ', {
            'APP_NAME': 'TestApp',
            'LOG_LEVEL': 'DEBUG',
            'CACHE_MAX_SIZE': '2000'
        }):
            settings = Settings()
            
            assert settings.app_name == 'TestApp'
            assert settings.log_level == LogLevel.DEBUG
            assert settings.cache.max_size == 2000
    
    def test_patterns_dir_validation(self):
        """Test patterns directory validation."""
        settings = Settings()
        
        # Should create absolute path
        assert settings.patterns.patterns_dir.is_absolute()
        
        # Should point to patterns directory
        assert settings.patterns.patterns_dir.name == "patterns"


class TestLogger:
    """Test logging infrastructure."""
    
    def test_logger_creation(self):
        """Test logger instance creation."""
        logger = get_logger("test")
        
        assert isinstance(logger, Logger)
        assert logger is not None
    
    def test_correlation_id(self):
        """Test correlation ID context variable."""
        test_id = "test-123"
        
        # Initially should be None
        assert correlation_id.get() is None
        
        # Set correlation ID
        correlation_id.set(test_id)
        assert correlation_id.get() == test_id
    
    def test_logger_binding(self):
        """Test logger context binding."""
        logger = get_logger("test")
        
        bound_logger = logger.bind(user_id="123", action="test")
        
        # Should return new logger instance
        assert isinstance(bound_logger, Logger)
        assert bound_logger is not logger


class TestLRUCacheRepository:
    """Test LRU cache implementation."""
    
    @pytest.fixture
    def cache(self):
        """Create cache instance for testing."""
        return LRUCacheRepository(max_size=3)
    
    @pytest.mark.asyncio
    async def test_cache_basic_operations(self, cache):
        """Test basic cache operations."""
        # Test set and get
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"
        
        # Test non-existent key
        result = await cache.get("nonexistent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_eviction(self, cache):
        """Test LRU eviction policy."""
        # Fill cache to capacity
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")
        
        # Add one more item (should evict key1)
        await cache.set("key4", "value4")
        
        # key1 should be evicted
        result = await cache.get("key1")
        assert result is None
        
        # Other keys should still exist
        assert await cache.get("key2") == "value2"
        assert await cache.get("key3") == "value3"
        assert await cache.get("key4") == "value4"
    
    @pytest.mark.asyncio
    async def test_cache_lru_order(self, cache):
        """Test LRU ordering."""
        # Add items
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")
        
        # Access key1 (should move it to front)
        await cache.get("key1")
        
        # Add new item (should evict key2, not key1)
        await cache.set("key4", "value4")
        
        # key2 should be evicted, key1 should still exist
        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") is None
        assert await cache.get("key3") == "value3"
        assert await cache.get("key4") == "value4"
    
    @pytest.mark.asyncio
    async def test_cache_update(self, cache):
        """Test cache value updates."""
        # Set initial value
        await cache.set("key1", "value1")
        
        # Update value
        await cache.set("key1", "updated_value")
        
        # Should return updated value
        result = await cache.get("key1")
        assert result == "updated_value"
    
    @pytest.mark.asyncio
    async def test_cache_delete(self, cache):
        """Test cache deletion."""
        # Set value
        await cache.set("key1", "value1")
        assert await cache.get("key1") == "value1"
        
        # Delete value
        await cache.delete("key1")
        assert await cache.get("key1") is None
    
    @pytest.mark.asyncio
    async def test_cache_clear(self, cache):
        """Test cache clearing."""
        # Add multiple items
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        
        # Clear cache
        await cache.clear()
        
        # All items should be gone
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, cache):
        """Test cache statistics."""
        # Initial stats
        stats = cache.get_stats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.size == 0
        
        # Add item and access it
        await cache.set("key1", "value1")
        await cache.get("key1")  # Hit
        await cache.get("key2")  # Miss
        
        # Check updated stats
        stats = cache.get_stats()
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.size == 1


class TestIntegration:
    """Integration tests for infrastructure components."""
    
    def test_settings_singleton(self):
        """Test that get_settings returns singleton."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
    
    def test_logger_with_settings(self):
        """Test logger integration with settings."""
        # This would test actual log output in a real scenario
        logger = get_logger("integration_test")
        
        # Should not raise exceptions
        logger.info("Test message")
        logger.debug("Debug message")
        logger.warning("Warning message")
    
    @pytest.mark.asyncio
    async def test_cache_with_realistic_data(self):
        """Test cache with realistic LaTeX expressions."""
        cache = LRUCacheRepository(max_size=100)
        
        # Test with LaTeX-like keys and speech text values
        expressions = [
            ("\\frac{1}{2}", "one half"),
            ("\\sin(x)", "sine of x"),
            ("\\int_0^1 x dx", "the integral from zero to one of x dx"),
            ("x^2 + y^2", "x squared plus y squared")
        ]
        
        # Store expressions
        for expr, speech in expressions:
            await cache.set(expr, speech)
        
        # Retrieve and verify
        for expr, expected_speech in expressions:
            actual_speech = await cache.get(expr)
            assert actual_speech == expected_speech
        
        # Verify stats
        stats = cache.get_stats()
        assert stats.size == len(expressions)