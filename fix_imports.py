#!/usr/bin/env python3
"""
Fix import issues in the project.
"""
import os
import re
from pathlib import Path

def fix_file_imports(filepath: Path):
    """Fix imports in a file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Fix relative imports that go beyond top-level
    content = re.sub(r'from \.\.\.(\w+)', r'from src.\1', content)
    content = re.sub(r'from \.\.\.\.(\w+)', r'from src.\1', content)
    
    # Fix domain.interfaces imports
    content = content.replace('from interfaces import TTSAdapter', 'from ..interfaces import TTSAdapter')
    
    # Fix imports in test files
    if 'tests/' in str(filepath):
        # Replace relative imports with absolute
        content = re.sub(r'from application\.', 'from src.application.', content)
        content = re.sub(r'from domain\.', 'from src.domain.', content)
        content = re.sub(r'from infrastructure\.', 'from src.infrastructure.', content)
        content = re.sub(r'from presentation\.', 'from src.presentation.', content)
        content = re.sub(r'from adapters\.', 'from src.adapters.', content)
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed imports in: {filepath}")

def main():
    """Fix all import issues."""
    # Fix src files
    for py_file in Path('src').rglob('*.py'):
        fix_file_imports(py_file)
    
    # Fix test files
    for py_file in Path('tests').rglob('*.py'):
        fix_file_imports(py_file)
    
    # Fix the specific TTSAdapter import issue
    interfaces_init = Path('src/domain/interfaces/__init__.py')
    with open(interfaces_init, 'r') as f:
        content = f.read()
    
    new_content = '''"""Domain interfaces and protocols for MathTTS v3."""

from .pattern_repository import (
    PatternRepository,
    RepositoryError,
    PatternNotFoundError,
    DuplicatePatternError,
    InvalidPatternError
)

# Import TTSAdapter from the parent domain module
from ..interfaces import TTSAdapter

__all__ = [
    "PatternRepository",
    "RepositoryError", 
    "PatternNotFoundError",
    "DuplicatePatternError",
    "InvalidPatternError",
    "TTSAdapter"
]'''
    
    with open(interfaces_init, 'w') as f:
        f.write(new_content)
    
    print("Import fixes complete!")

if __name__ == "__main__":
    main()