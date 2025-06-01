"""
Unit tests for infrastructure components.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import unittest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from src.infrastructure.cache import LRUCacheRepository
from src.infrastructure.config.settings import Settings
from src.infrastructure.persistence.memory_pattern_repository import MemoryPatternRepository
from src.domain.entities import PatternEntity
from src.domain.entities.pattern import PatternContext
from src.domain.value_objects import PatternPriority, MathematicalDomain
from src.domain.interfaces import DuplicatePatternError, RepositoryError


class TestLRUCacheRepository(unittest.TestCase):
    """Test cases for LRU cache repository."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cache = LRUCacheRepository(max_size=3)
    
    def async_test(coro):
        """Decorator to run async tests."""
        def wrapper(self):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(coro(self))
        return wrapper
    
    @async_test
    async def test_basic_operations(self):
        """Test basic cache operations."""
        # Test set and get
        await self.cache.set("key1", {"value": "data1"})
        result = await self.cache.get("key1")
        self.assertEqual(result["value"], "data1")
        
        # Test get non-existent key
        result = await self.cache.get("non_existent")
        self.assertIsNone(result)
        
        # Test has
        self.assertTrue(await self.cache.has("key1"))
        self.assertFalse(await self.cache.has("non_existent"))
    
    @async_test
    async def test_lru_eviction(self):
        """Test LRU eviction policy."""
        # Fill cache to capacity
        await self.cache.set("key1", {"value": "data1"})
        await self.cache.set("key2", {"value": "data2"})
        await self.cache.set("key3", {"value": "data3"})
        
        # Access key1 to make it recently used
        await self.cache.get("key1")
        
        # Add new item, should evict key2 (least recently used)
        await self.cache.set("key4", {"value": "data4"})
        
        # Verify eviction
        self.assertTrue(await self.cache.has("key1"))  # Recently accessed
        self.assertFalse(await self.cache.has("key2"))  # Evicted
        self.assertTrue(await self.cache.has("key3"))
        self.assertTrue(await self.cache.has("key4"))
    
    @async_test
    async def test_delete_operation(self):
        """Test delete operation."""
        await self.cache.set("key1", {"value": "data1"})
        
        # Delete existing key
        result = await self.cache.delete("key1")
        self.assertTrue(result)
        self.assertFalse(await self.cache.has("key1"))
        
        # Delete non-existent key
        result = await self.cache.delete("non_existent")
        self.assertFalse(result)
    
    @async_test
    async def test_clear_operation(self):
        """Test clear operation."""
        # Add multiple items
        await self.cache.set("key1", {"value": "data1"})
        await self.cache.set("key2", {"value": "data2"})
        
        # Clear cache
        await self.cache.clear()
        
        # Verify all items removed
        self.assertFalse(await self.cache.has("key1"))
        self.assertFalse(await self.cache.has("key2"))
        self.assertEqual(self.cache.size(), 0)
    
    def test_statistics(self):
        """Test cache statistics."""
        loop = asyncio.get_event_loop()
        
        # Perform operations
        loop.run_until_complete(self.cache.set("key1", {"value": "data1"}))
        loop.run_until_complete(self.cache.get("key1"))  # Hit
        loop.run_until_complete(self.cache.get("key2"))  # Miss
        loop.run_until_complete(self.cache.get("key1"))  # Hit
        
        stats = self.cache.get_stats()
        
        self.assertEqual(stats["size"], 1)
        self.assertEqual(stats["max_size"], 3)
        self.assertEqual(stats["hits"], 2)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["hit_rate"], 2/3)
    
    @async_test
    async def test_update_existing_key(self):
        """Test updating existing key."""
        await self.cache.set("key1", {"value": "original"})
        await self.cache.set("key1", {"value": "updated"})
        
        result = await self.cache.get("key1")
        self.assertEqual(result["value"], "updated")
        
        # Size should remain 1
        self.assertEqual(self.cache.size(), 1)


class TestMemoryPatternRepository(unittest.TestCase):
    """Test cases for in-memory pattern repository."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.repo = MemoryPatternRepository()
        self.test_pattern = PatternEntity(
            id="test_pattern",
            name="Test Pattern",
            pattern=r"\\test",
            output_template="test",
            priority=PatternPriority.medium(),
            domain=MathematicalDomain("general"),
            contexts=[PatternContext.ANY]
        )
    
    def async_test(coro):
        """Decorator to run async tests."""
        def wrapper(self):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(coro(self))
        return wrapper
    
    @async_test
    async def test_add_and_get(self):
        """Test adding and retrieving patterns."""
        # Add pattern
        await self.repo.add(self.test_pattern)
        
        # Get by ID
        retrieved = await self.repo.get_by_id("test_pattern")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, "test_pattern")
        
        # Get non-existent
        retrieved = await self.repo.get_by_id("non_existent")
        self.assertIsNone(retrieved)
    
    @async_test
    async def test_duplicate_pattern_error(self):
        """Test duplicate pattern error."""
        await self.repo.add(self.test_pattern)
        
        # Try to add same pattern again
        with self.assertRaises(DuplicatePatternError):
            await self.repo.add(self.test_pattern)
    
    @async_test
    async def test_get_all(self):
        """Test getting all patterns."""
        # Add multiple patterns
        pattern1 = self.test_pattern
        pattern2 = PatternEntity(
            id="pattern2",
            name="Pattern 2",
            pattern=r"\\alpha",
            output_template="alpha",
            priority=PatternPriority.high(),
            domain=MathematicalDomain("general"),
            contexts=[PatternContext.ANY]
        )
        
        await self.repo.add(pattern1)
        await self.repo.add(pattern2)
        
        all_patterns = await self.repo.get_all()
        self.assertEqual(len(all_patterns), 2)
        pattern_ids = [p.id for p in all_patterns]
        self.assertIn("test_pattern", pattern_ids)
        self.assertIn("pattern2", pattern_ids)
    
    @async_test
    async def test_find_by_domain(self):
        """Test finding patterns by domain."""
        # Add patterns with different domains
        general_pattern = self.test_pattern
        calculus_pattern = PatternEntity(
            id="calc_pattern",
            name="Calculus Pattern",
            pattern=r"\\int",
            output_template="integral",
            priority=PatternPriority.high(),
            domain=MathematicalDomain("calculus"),
            contexts=[PatternContext.ANY]
        )
        
        await self.repo.add(general_pattern)
        await self.repo.add(calculus_pattern)
        
        # Find by domain
        general_patterns = await self.repo.find_by_domain(MathematicalDomain("general"))
        self.assertEqual(len(general_patterns), 1)
        self.assertEqual(general_patterns[0].id, "test_pattern")
        
        calculus_patterns = await self.repo.find_by_domain(MathematicalDomain("calculus"))
        self.assertEqual(len(calculus_patterns), 1)
        self.assertEqual(calculus_patterns[0].id, "calc_pattern")
    
    @async_test
    async def test_find_by_priority_range(self):
        """Test finding patterns by priority range."""
        # Add patterns with different priorities
        low = PatternEntity(
            id="low",
            name="Low Priority",
            pattern=r"\\low",
            output_template="low",
            priority=PatternPriority.low(),
            domain=MathematicalDomain("general"),
            contexts=[PatternContext.ANY]
        )
        medium = self.test_pattern  # Has medium priority
        high = PatternEntity(
            id="high",
            name="High Priority",
            pattern=r"\\high",
            output_template="high",
            priority=PatternPriority.high(),
            domain=MathematicalDomain("general"),
            contexts=[PatternContext.ANY]
        )
        
        await self.repo.add(low)
        await self.repo.add(medium)
        await self.repo.add(high)
        
        # Find medium to high priority
        patterns = await self.repo.find_by_priority_range(
            PatternPriority.medium(),
            PatternPriority.high()
        )
        
        self.assertEqual(len(patterns), 2)
        pattern_ids = [p.id for p in patterns]
        self.assertIn("test_pattern", pattern_ids)
        self.assertIn("high", pattern_ids)
        self.assertNotIn("low", pattern_ids)
    
    @async_test
    async def test_update_pattern(self):
        """Test updating a pattern."""
        await self.repo.add(self.test_pattern)
        
        # Create updated version
        updated_pattern = PatternEntity(
            id="test_pattern",  # Same ID
            name="Updated Pattern",
            pattern=r"\\updated",
            output_template="updated",
            priority=PatternPriority.high(),
            domain=MathematicalDomain("general"),
            contexts=[PatternContext.ANY]
        )
        
        await self.repo.update(updated_pattern)
        
        # Verify update
        retrieved = await self.repo.get_by_id("test_pattern")
        self.assertEqual(retrieved.name, "Updated Pattern")
        self.assertEqual(retrieved.pattern, r"\\updated")
    
    @async_test
    async def test_update_non_existent(self):
        """Test updating non-existent pattern."""
        pattern = PatternEntity(
            id="non_existent",
            name="Pattern",
            pattern=r"\\test",
            output_template="test",
            priority=PatternPriority.medium(),
            domain=MathematicalDomain("general"),
            contexts=[PatternContext.ANY]
        )
        
        with self.assertRaises(RepositoryError):
            await self.repo.update(pattern)
    
    @async_test
    async def test_delete_pattern(self):
        """Test deleting a pattern."""
        await self.repo.add(self.test_pattern)
        
        # Delete existing
        result = await self.repo.delete("test_pattern")
        self.assertTrue(result)
        
        # Verify deleted
        retrieved = await self.repo.get_by_id("test_pattern")
        self.assertIsNone(retrieved)
        
        # Delete non-existent
        result = await self.repo.delete("non_existent")
        self.assertFalse(result)
    
    @async_test
    async def test_statistics(self):
        """Test repository statistics."""
        # Add patterns with various properties
        patterns = [
            PatternEntity(
                id=f"pattern_{i}",
                name=f"Pattern {i}",
                pattern=rf"\\test{i}",
                output_template=f"test{i}",
                priority=PatternPriority.high() if i < 2 else PatternPriority.low(),
                domain=MathematicalDomain("calculus") if i < 1 else MathematicalDomain("general"),
                contexts=[PatternContext.INLINE, PatternContext.DISPLAY]
            )
            for i in range(3)
        ]
        
        for pattern in patterns:
            await self.repo.add(pattern)
        
        stats = await self.repo.get_statistics()
        
        self.assertEqual(stats["total_patterns"], 3)
        self.assertEqual(stats["domains"]["calculus"], 1)
        self.assertEqual(stats["domains"]["general"], 2)
        self.assertEqual(stats["priorities"]["high"], 2)
        self.assertEqual(stats["priorities"]["low"], 1)
        self.assertEqual(stats["contexts"]["INLINE"], 3)
        self.assertEqual(stats["contexts"]["DISPLAY"], 3)


class TestSettings(unittest.TestCase):
    """Test cases for settings configuration."""
    
    @patch.dict(os.environ, {
        "PROJECT_NAME": "TestProject",
        "VERSION": "1.0.0",
        "DEBUG": "true",
        "LOG_LEVEL": "DEBUG",
        "CACHE_SIZE": "500",
        "CACHE_TTL": "1800"
    })
    def test_settings_from_env(self):
        """Test loading settings from environment variables."""
        settings = Settings()
        
        self.assertEqual(settings.project_name, "TestProject")
        self.assertEqual(settings.version, "1.0.0")
        self.assertTrue(settings.debug)
        self.assertEqual(settings.log_level, "DEBUG")
        self.assertEqual(settings.cache_size, 500)
        self.assertEqual(settings.cache_ttl, 1800)
    
    def test_settings_defaults(self):
        """Test default settings values."""
        settings = Settings()
        
        self.assertEqual(settings.project_name, "MathTTS v3")
        self.assertEqual(settings.version, "3.0.0")
        self.assertFalse(settings.debug)
        self.assertEqual(settings.log_level, "INFO")
        self.assertEqual(settings.cache_size, 1000)
        self.assertEqual(settings.cache_ttl, 3600)
    
    @patch.dict(os.environ, {"PATTERNS_DIR": "/custom/patterns"})
    def test_custom_patterns_dir(self):
        """Test custom patterns directory."""
        settings = Settings()
        self.assertEqual(settings.patterns_dir, Path("/custom/patterns"))
    
    def test_database_url_construction(self):
        """Test database URL construction."""
        settings = Settings()
        expected_url = "postgresql://mathtts:mathtts@localhost:5432/mathtts"
        self.assertEqual(settings.database_url, expected_url)
    
    @patch.dict(os.environ, {
        "REDIS_HOST": "redis.example.com",
        "REDIS_PORT": "6380",
        "REDIS_DB": "1"
    })
    def test_redis_configuration(self):
        """Test Redis configuration."""
        settings = Settings()
        
        self.assertEqual(settings.redis_host, "redis.example.com")
        self.assertEqual(settings.redis_port, 6380)
        self.assertEqual(settings.redis_db, 1)


if __name__ == "__main__":
    unittest.main()