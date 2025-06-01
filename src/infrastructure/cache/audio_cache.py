"""
Audio caching system for TTS output.

Caches synthesized audio to avoid redundant TTS operations.
"""

import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import asyncio
import aiofiles
import shutil

from src.domain.value_objects import AudioData, TTSOptions
from ..logging import get_logger


logger = get_logger(__name__)


class AudioCache:
    """Cache for synthesized audio data."""
    
    def __init__(
        self,
        cache_dir: Path,
        max_size_mb: int = 500,
        ttl_hours: int = 24,
        cleanup_interval_minutes: int = 60
    ):
        """
        Initialize audio cache.
        
        Args:
            cache_dir: Directory for cache storage
            max_size_mb: Maximum cache size in MB
            ttl_hours: Time to live for cached items
            cleanup_interval_minutes: Cleanup interval
        """
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.ttl = timedelta(hours=ttl_hours)
        self.cleanup_interval = timedelta(minutes=cleanup_interval_minutes)
        
        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Metadata file
        self.metadata_file = self.cache_dir / "metadata.json"
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self._load_metadata()
        
        # Cleanup task
        self._cleanup_task = None
        self._lock = asyncio.Lock()
        
    def _load_metadata(self) -> None:
        """Load cache metadata from disk."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                logger.error("Failed to load cache metadata", error=str(e))
                self.metadata = {}
    
    async def _save_metadata(self) -> None:
        """Save cache metadata to disk."""
        try:
            async with aiofiles.open(self.metadata_file, 'w') as f:
                await f.write(json.dumps(self.metadata, indent=2))
        except Exception as e:
            logger.error("Failed to save cache metadata", error=str(e))
    
    def _generate_cache_key(
        self,
        text: str,
        options: TTSOptions,
        provider: str
    ) -> str:
        """Generate cache key for audio data."""
        # Create a unique key based on all parameters
        key_data = {
            'text': text,
            'provider': provider,
            'voice_id': options.voice_id,
            'rate': options.rate,
            'pitch': options.pitch,
            'volume': options.volume,
            'format': options.format.value,
            'ssml_enabled': options.ssml_enabled
        }
        
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    async def get(
        self,
        text: str,
        options: TTSOptions,
        provider: str
    ) -> Optional[AudioData]:
        """
        Get cached audio data.
        
        Args:
            text: Input text
            options: TTS options
            provider: TTS provider name
            
        Returns:
            Cached audio data or None
        """
        cache_key = self._generate_cache_key(text, options, provider)
        
        async with self._lock:
            # Check if in metadata
            if cache_key not in self.metadata:
                return None
            
            entry = self.metadata[cache_key]
            
            # Check if expired
            created_at = datetime.fromisoformat(entry['created_at'])
            if datetime.now() - created_at > self.ttl:
                logger.debug("Cache entry expired", key=cache_key[:8])
                await self._remove_entry(cache_key)
                return None
            
            # Read audio file
            audio_file = self.cache_dir / f"{cache_key}.{entry['format']}"
            if not audio_file.exists():
                logger.warning("Cache file missing", key=cache_key[:8])
                del self.metadata[cache_key]
                return None
            
            try:
                async with aiofiles.open(audio_file, 'rb') as f:
                    audio_data = await f.read()
                
                # Update access time
                entry['last_accessed'] = datetime.now().isoformat()
                entry['access_count'] = entry.get('access_count', 0) + 1
                
                logger.debug(
                    "Cache hit",
                    key=cache_key[:8],
                    size_bytes=len(audio_data),
                    access_count=entry['access_count']
                )
                
                return AudioData(
                    data=audio_data,
                    format=options.format,
                    sample_rate=entry.get('sample_rate', 22050),
                    duration_seconds=entry.get('duration', 0.0)
                )
                
            except Exception as e:
                logger.error("Failed to read cache file", error=str(e))
                await self._remove_entry(cache_key)
                return None
    
    async def put(
        self,
        text: str,
        options: TTSOptions,
        provider: str,
        audio_data: AudioData
    ) -> None:
        """
        Store audio data in cache.
        
        Args:
            text: Input text
            options: TTS options
            provider: TTS provider name
            audio_data: Audio data to cache
        """
        cache_key = self._generate_cache_key(text, options, provider)
        
        async with self._lock:
            # Check cache size
            if await self._get_cache_size() + len(audio_data.data) > self.max_size_bytes:
                await self._evict_oldest()
            
            # Write audio file
            audio_file = self.cache_dir / f"{cache_key}.{audio_data.format.value}"
            
            try:
                async with aiofiles.open(audio_file, 'wb') as f:
                    await f.write(audio_data.data)
                
                # Update metadata
                self.metadata[cache_key] = {
                    'created_at': datetime.now().isoformat(),
                    'last_accessed': datetime.now().isoformat(),
                    'access_count': 0,
                    'size_bytes': len(audio_data.data),
                    'format': audio_data.format.value,
                    'sample_rate': audio_data.sample_rate,
                    'duration': audio_data.duration_seconds,
                    'text_preview': text[:50] + '...' if len(text) > 50 else text,
                    'provider': provider,
                    'voice_id': options.voice_id
                }
                
                await self._save_metadata()
                
                logger.debug(
                    "Cached audio",
                    key=cache_key[:8],
                    size_bytes=len(audio_data.data)
                )
                
            except Exception as e:
                logger.error("Failed to cache audio", error=str(e))
                # Clean up on failure
                audio_file.unlink(missing_ok=True)
    
    async def _get_cache_size(self) -> int:
        """Get total cache size in bytes."""
        total_size = 0
        for entry in self.metadata.values():
            total_size += entry.get('size_bytes', 0)
        return total_size
    
    async def _evict_oldest(self) -> None:
        """Evict oldest entries to make room."""
        # Sort by last access time
        sorted_entries = sorted(
            self.metadata.items(),
            key=lambda x: x[1].get('last_accessed', x[1]['created_at'])
        )
        
        # Remove oldest entries until we have enough space
        target_size = self.max_size_bytes * 0.8  # Free up to 80% capacity
        current_size = await self._get_cache_size()
        
        for cache_key, entry in sorted_entries:
            if current_size <= target_size:
                break
            
            await self._remove_entry(cache_key)
            current_size -= entry.get('size_bytes', 0)
            
            logger.debug(
                "Evicted cache entry",
                key=cache_key[:8],
                size_bytes=entry.get('size_bytes', 0)
            )
    
    async def _remove_entry(self, cache_key: str) -> None:
        """Remove a cache entry."""
        if cache_key in self.metadata:
            entry = self.metadata[cache_key]
            
            # Remove file
            audio_file = self.cache_dir / f"{cache_key}.{entry['format']}"
            audio_file.unlink(missing_ok=True)
            
            # Remove metadata
            del self.metadata[cache_key]
    
    async def clear(self) -> None:
        """Clear all cached data."""
        async with self._lock:
            # Remove all files
            for cache_key in list(self.metadata.keys()):
                await self._remove_entry(cache_key)
            
            # Clear metadata
            self.metadata = {}
            await self._save_metadata()
            
            logger.info("Audio cache cleared")
    
    async def cleanup(self) -> None:
        """Clean up expired entries."""
        async with self._lock:
            now = datetime.now()
            expired_keys = []
            
            for cache_key, entry in self.metadata.items():
                created_at = datetime.fromisoformat(entry['created_at'])
                if now - created_at > self.ttl:
                    expired_keys.append(cache_key)
            
            for cache_key in expired_keys:
                await self._remove_entry(cache_key)
            
            if expired_keys:
                await self._save_metadata()
                logger.info(
                    "Cleaned up expired cache entries",
                    count=len(expired_keys)
                )
    
    async def start_cleanup_task(self) -> None:
        """Start periodic cleanup task."""
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(self.cleanup_interval.total_seconds())
                    await self.cleanup()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error("Cleanup task error", error=str(e))
        
        self._cleanup_task = asyncio.create_task(cleanup_loop())
        logger.info("Started cache cleanup task")
    
    async def stop_cleanup_task(self) -> None:
        """Stop cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped cache cleanup task")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_size = sum(e.get('size_bytes', 0) for e in self.metadata.values())
        total_hits = sum(e.get('access_count', 0) for e in self.metadata.values())
        
        return {
            'entries': len(self.metadata),
            'total_size_mb': total_size / (1024 * 1024),
            'max_size_mb': self.max_size_bytes / (1024 * 1024),
            'usage_percent': (total_size / self.max_size_bytes * 100) if self.max_size_bytes > 0 else 0,
            'total_hits': total_hits,
            'ttl_hours': self.ttl.total_seconds() / 3600
        }