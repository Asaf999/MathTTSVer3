"""Pattern loaders for loading patterns from various sources."""

import yaml
from pathlib import Path
from typing import List, Dict, Any
import logging

from src.domain.entities import PatternEntity
from src.domain.value_objects import PatternPriority
from src.domain.interfaces import PatternLoader

logger = logging.getLogger(__name__)


class YAMLPatternLoader:
    """Load patterns from YAML files."""
    
    def load_from_file(self, file_path: Path) -> List[PatternEntity]:
        """Load patterns from a YAML file."""
        if not file_path.exists():
            raise FileNotFoundError(f"Pattern file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data:
            return []
        
        patterns = []
        for pattern_data in data.get('patterns', []):
            try:
                pattern = self._create_pattern_from_dict(pattern_data)
                patterns.append(pattern)
            except Exception as e:
                logger.error(f"Error loading pattern {pattern_data.get('id', 'unknown')}: {e}")
        
        return patterns
    
    def load_from_directory(self, directory: Path) -> List[PatternEntity]:
        """Load patterns from all YAML files in a directory."""
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Invalid directory: {directory}")
        
        patterns = []
        
        # First check for master patterns file
        master_file = directory / "master_patterns.yaml"
        if master_file.exists():
            patterns.extend(self._load_from_master_file(master_file, directory))
        else:
            # Load all YAML files in directory
            for yaml_file in directory.glob("*.yaml"):
                if yaml_file.name != "master_patterns.yaml":
                    try:
                        patterns.extend(self.load_from_file(yaml_file))
                    except Exception as e:
                        logger.error(f"Error loading {yaml_file}: {e}")
        
        return patterns
    
    def _load_from_master_file(self, master_file: Path, base_dir: Path) -> List[PatternEntity]:
        """Load patterns based on master file configuration."""
        with open(master_file, 'r', encoding='utf-8') as f:
            master_data = yaml.safe_load(f)
        
        patterns = []
        
        for file_config in master_data.get('pattern_files', []):
            if not file_config.get('enabled', True):
                continue
            
            file_path = base_dir / file_config['path']
            if file_path.exists():
                try:
                    patterns.extend(self.load_from_file(file_path))
                except Exception as e:
                    logger.error(f"Error loading {file_path}: {e}")
        
        return patterns
    
    def _create_pattern_from_dict(self, data: Dict[str, Any]) -> PatternEntity:
        """Create a pattern entity from dictionary data."""
        return PatternEntity(
            id=data['id'],
            name=data['name'],
            pattern=data['pattern'],
            output_template=data['output_template'],
            description=data.get('description', ''),
            priority=PatternPriority(data.get('priority', 1000)),
            domain=data.get('domain', 'general'),
            tags=data.get('tags', []),
            examples=data.get('examples', []),
            metadata=data.get('metadata', {})
        )
    
    def validate_patterns(self, patterns: List[PatternEntity]) -> List[str]:
        """Validate patterns and return errors."""
        errors = []
        seen_ids = set()
        
        for pattern in patterns:
            # Check for duplicate IDs
            if pattern.id in seen_ids:
                errors.append(f"Duplicate pattern ID: {pattern.id}")
            seen_ids.add(pattern.id)
            
            # Validate pattern regex
            try:
                import re
                re.compile(pattern.pattern)
            except re.error as e:
                errors.append(f"Invalid regex in pattern {pattern.id}: {e}")
            
            # Check output template has placeholders
            if '\\' not in pattern.output_template and not any(f"\\{i}" in pattern.output_template for i in range(10)):
                logger.warning(f"Pattern {pattern.id} output template has no placeholders")
        
        return errors