"""
Optimized YAML pattern loader with parallel loading and validation.
"""

import asyncio
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Set
import yaml

from src.adapters.pattern_loaders import YAMLPatternLoader
from src.domain.entities import PatternEntity
from src.infrastructure.logging import get_logger
from .profiler import profile_async_function, PerformanceOptimizer

logger = get_logger(__name__)


class OptimizedYAMLPatternLoader(YAMLPatternLoader):
    """
    Optimized YAML pattern loader with performance enhancements.
    
    Optimizations:
    1. Parallel file loading
    2. Pattern deduplication
    3. File content caching with modification time checking
    4. Batch validation
    5. Lazy pattern compilation
    """
    
    def __init__(self, patterns_dir: Path, cache_dir: Optional[Path] = None):
        super().__init__(patterns_dir)
        
        # Cache directory for preprocessed patterns
        self.cache_dir = cache_dir or Path.home() / ".cache" / "mathtts" / "patterns"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory caches
        self._file_cache: Dict[str, Dict] = {}
        self._pattern_hash_map: Dict[str, str] = {}  # pattern_hash -> pattern_id
    
    @profile_async_function("optimized_loader.load_patterns")
    async def load_patterns(self) -> List[PatternEntity]:
        """Load patterns with optimizations."""
        if not self.patterns_dir.exists() or not self.patterns_dir.is_dir():
            logger.warning(f"Patterns directory does not exist: {self.patterns_dir}")
            return []
        
        # Get all pattern files
        pattern_files = list(self.patterns_dir.glob("*.yaml")) + list(self.patterns_dir.glob("*.yml"))
        
        if not pattern_files:
            logger.info(f"No pattern files found in {self.patterns_dir}")
            return []
        
        logger.info(f"Loading patterns from {len(pattern_files)} files")
        
        # Load files in parallel
        patterns = await self._load_files_parallel(pattern_files)
        
        # Deduplicate patterns
        patterns = self._deduplicate_patterns(patterns)
        
        # Sort by priority for better cache locality
        patterns.sort(key=lambda p: p.priority.value, reverse=True)
        
        logger.info(f"Successfully loaded {len(patterns)} unique patterns")
        return patterns
    
    async def _load_files_parallel(self, pattern_files: List[Path]) -> List[PatternEntity]:
        """Load pattern files in parallel."""
        # Use performance optimizer for parallel loading
        optimizer = PerformanceOptimizer()
        
        async def load_single_file(file_path: Path) -> List[PatternEntity]:
            try:
                # Check cache first
                cached = self._get_cached_patterns(file_path)
                if cached is not None:
                    return cached
                
                # Load from file
                patterns = await self._load_from_file(file_path)
                
                # Cache the result
                self._cache_patterns(file_path, patterns)
                
                return patterns
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")
                return []
        
        # Load all files in parallel with concurrency limit
        file_results = await optimizer.parallel_map(
            load_single_file,
            pattern_files,
            max_workers=10
        )
        
        # Flatten results
        all_patterns = []
        for patterns in file_results:
            all_patterns.extend(patterns)
        
        return all_patterns
    
    def _get_cached_patterns(self, file_path: Path) -> Optional[List[PatternEntity]]:
        """Get cached patterns if file hasn't changed."""
        # Check file modification time
        file_stat = file_path.stat()
        file_mtime = file_stat.st_mtime
        file_size = file_stat.st_size
        
        # Create cache key
        cache_key = f"{file_path.name}_{file_mtime}_{file_size}"
        
        # Check in-memory cache
        if cache_key in self._file_cache:
            logger.debug(f"In-memory cache hit for {file_path.name}")
            return self._file_cache[cache_key]
        
        # Check disk cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                
                # Reconstruct pattern entities
                patterns = []
                for pattern_data in cached_data["patterns"]:
                    pattern = self._pattern_from_dict(pattern_data)
                    patterns.append(pattern)
                
                # Update in-memory cache
                self._file_cache[cache_key] = patterns
                
                logger.debug(f"Disk cache hit for {file_path.name}")
                return patterns
                
            except Exception as e:
                logger.warning(f"Failed to load cache for {file_path}: {e}")
        
        return None
    
    def _cache_patterns(self, file_path: Path, patterns: List[PatternEntity]) -> None:
        """Cache patterns for a file."""
        # Get file info
        file_stat = file_path.stat()
        file_mtime = file_stat.st_mtime
        file_size = file_stat.st_size
        
        # Create cache key
        cache_key = f"{file_path.name}_{file_mtime}_{file_size}"
        
        # Update in-memory cache
        self._file_cache[cache_key] = patterns
        
        # Save to disk cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            cached_data = {
                "file": str(file_path),
                "mtime": file_mtime,
                "patterns": [self._pattern_to_dict(p) for p in patterns]
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cached_data, f)
                
        except Exception as e:
            logger.warning(f"Failed to cache patterns for {file_path}: {e}")
    
    def _pattern_to_dict(self, pattern: PatternEntity) -> Dict:
        """Convert pattern to dictionary for caching."""
        return {
            "id": pattern.id,
            "name": pattern.name,
            "pattern": pattern.pattern,
            "output_template": pattern.output_template,
            "priority": pattern.priority.value,
            "domain": pattern.domain.value,
            "contexts": [str(c.value) for c in pattern.contexts],
            "description": pattern.description
        }
    
    def _pattern_from_dict(self, data: Dict) -> PatternEntity:
        """Create pattern from cached dictionary."""
        # Convert contexts back to enum values
        from src.domain.entities.pattern import PatternContext
        contexts = []
        for ctx_str in data["contexts"]:
            try:
                # Handle both string and int context values
                if ctx_str.isdigit():
                    contexts.append(PatternContext(int(ctx_str)))
                else:
                    contexts.append(PatternContext[ctx_str.upper()])
            except (ValueError, KeyError):
                contexts.append(PatternContext.ANY)
        
        return PatternEntity(
            id=data["id"],
            name=data["name"],
            pattern=data["pattern"],
            output_template=data["output_template"],
            priority=PatternPriority(data["priority"]),
            domain=MathematicalDomain(data["domain"]),
            contexts=contexts,
            description=data.get("description", "")
        )
    
    def _deduplicate_patterns(self, patterns: List[PatternEntity]) -> List[PatternEntity]:
        """Remove duplicate patterns based on content hash."""
        unique_patterns = []
        seen_hashes = set()
        
        for pattern in patterns:
            # Create content hash
            pattern_hash = self._get_pattern_hash(pattern)
            
            if pattern_hash not in seen_hashes:
                seen_hashes.add(pattern_hash)
                unique_patterns.append(pattern)
                self._pattern_hash_map[pattern_hash] = pattern.id
            else:
                # Log duplicate
                original_id = self._pattern_hash_map.get(pattern_hash)
                logger.debug(f"Skipping duplicate pattern {pattern.id} (same as {original_id})")
        
        return unique_patterns
    
    def _get_pattern_hash(self, pattern: PatternEntity) -> str:
        """Get content hash for pattern deduplication."""
        # Hash based on functional content
        content = f"{pattern.pattern}|{pattern.output_template}|{pattern.domain.value}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def validate_patterns_parallel(self, patterns: List[PatternEntity]) -> Dict[str, List[str]]:
        """Validate patterns in parallel."""
        optimizer = PerformanceOptimizer()
        
        async def validate_single(pattern: PatternEntity) -> Optional[Tuple[str, List[str]]]:
            errors = []
            
            try:
                # Validate pattern compilation
                import re
                re.compile(pattern.pattern)
            except re.error as e:
                errors.append(f"Invalid regex: {e}")
            
            # Validate output template
            if not pattern.output_template:
                errors.append("Empty output template")
            
            # Check for common issues
            if pattern.pattern.count("(") != pattern.pattern.count(")"):
                errors.append("Unbalanced parentheses in pattern")
            
            if errors:
                return (pattern.id, errors)
            return None
        
        # Validate all patterns in parallel
        results = await optimizer.parallel_map(
            validate_single,
            patterns,
            max_workers=20
        )
        
        # Collect errors
        validation_errors = {}
        for result in results:
            if result:
                pattern_id, errors = result
                validation_errors[pattern_id] = errors
        
        return validation_errors
    
    def cleanup_cache(self, max_age_days: int = 7) -> None:
        """Clean up old cache files."""
        import time
        
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                file_age = current_time - cache_file.stat().st_mtime
                if file_age > max_age_seconds:
                    cache_file.unlink()
                    logger.debug(f"Removed old cache file: {cache_file.name}")
            except Exception as e:
                logger.warning(f"Failed to clean cache file {cache_file}: {e}")


from src.domain.value_objects import PatternPriority, MathematicalDomain