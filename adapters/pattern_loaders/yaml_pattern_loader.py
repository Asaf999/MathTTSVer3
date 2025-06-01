"""
YAML pattern loader adapter.

This module loads LaTeX pattern definitions from YAML files
and converts them to PatternEntity objects.
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import yaml

from domain.entities.pattern import PatternEntity
from domain.value_objects import PatternPriority


logger = logging.getLogger(__name__)


class YamlPatternLoader:
    """Loader for patterns defined in YAML format."""
    
    def __init__(self, patterns_dir: Path) -> None:
        """
        Initialize pattern loader.
        
        Args:
            patterns_dir: Directory containing YAML pattern files
        """
        self.patterns_dir = Path(patterns_dir)
        self._compiled_patterns = {}
    
    def load_all_patterns(self) -> List[PatternEntity]:
        """
        Load all patterns from YAML files.
        
        Returns:
            List of loaded pattern entities
        """
        # Load master configuration
        master_file = self.patterns_dir / "master_patterns.yaml"
        if not master_file.exists():
            logger.warning(f"Master patterns file not found: {master_file}")
            return []
        
        try:
            with open(master_file, 'r') as f:
                master_config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load master config: {e}")
            return []
        
        patterns = []
        
        # Load each pattern file
        for file_config in master_config.get('pattern_files', []):
            if not file_config.get('enabled', True):
                continue
                
            file_path = self.patterns_dir / file_config['path']
            if file_path.exists():
                file_patterns = self._load_pattern_file(file_path)
                patterns.extend(file_patterns)
        
        # Sort by priority (highest first)
        patterns.sort(key=lambda p: p.priority.value, reverse=True)
        
        logger.info(f"Loaded {len(patterns)} patterns")
        return patterns
    
    def _load_pattern_file(self, file_path: Path) -> List[PatternEntity]:
        """Load patterns from a single YAML file."""
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load pattern file {file_path}: {e}")
            return []
        
        patterns = []
        
        for pattern_data in data.get('patterns', []):
            try:
                pattern = self._create_pattern_entity(pattern_data)
                if pattern:
                    patterns.append(pattern)
            except Exception as e:
                logger.error(f"Failed to create pattern from {pattern_data.get('id', 'unknown')}: {e}")
        
        return patterns
    
    def _create_pattern_entity(self, data: Dict[str, Any]) -> Optional[PatternEntity]:
        """Create a PatternEntity from YAML data."""
        try:
            # Compile regex pattern
            pattern_str = data.get('pattern', '')
            if pattern_str not in self._compiled_patterns:
                self._compiled_patterns[pattern_str] = re.compile(pattern_str)
            
            # Create entity
            entity = PatternEntity(
                id=data.get('id', ''),
                name=data.get('name', ''),
                description=data.get('description', ''),
                pattern=pattern_str,
                output_template=data.get('output_template', ''),
                priority=PatternPriority(data.get('priority', 1000)),
                domain=data.get('domain', 'general'),
                tags=data.get('tags', []),
                examples=data.get('examples', []),
                metadata={
                    'contexts': data.get('contexts', []),
                    'pronunciation_hints': data.get('pronunciation_hints', {}),
                    'conditions': data.get('conditions', []),
                    'post_processing': data.get('post_processing', [])
                }
            )
            
            return entity
            
        except Exception as e:
            logger.error(f"Error creating pattern entity: {e}")
            return None
    
    def get_compiled_pattern(self, pattern_str: str) -> re.Pattern:
        """Get compiled regex pattern."""
        if pattern_str not in self._compiled_patterns:
            self._compiled_patterns[pattern_str] = re.compile(pattern_str)
        return self._compiled_patterns[pattern_str]


# For backwards compatibility
YAMLPatternLoader = YamlPatternLoader