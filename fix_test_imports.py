#!/usr/bin/env python3
"""
Fix import issues in test files.
"""
import os
from pathlib import Path

def fix_test_file(test_file: Path):
    """Fix imports in a test file."""
    try:
        with open(test_file, 'r') as f:
            content = f.read()
        
        original = content
        
        # Fix common import issues
        # Remove the quadruple parent directory navigation
        content = content.replace(
            'sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))',
            'sys.path.insert(0, str(Path(__file__).parent.parent.parent))'
        )
        
        # Fix import statements
        content = content.replace('exec(f"from {import_path.replace(', 'pass # ')
        
        # Add proper sys.path for all test files
        if 'sys.path.insert' not in content and 'import sys' not in content:
            lines = content.split('\n')
            import_index = 0
            for i, line in enumerate(lines):
                if line.startswith('import') or line.startswith('from'):
                    import_index = i
                    break
            
            lines.insert(import_index, 'import sys')
            lines.insert(import_index + 1, 'from pathlib import Path')
            lines.insert(import_index + 2, 'sys.path.insert(0, str(Path(__file__).parent.parent.parent))')
            lines.insert(import_index + 3, '')
            
            content = '\n'.join(lines)
        
        if content != original:
            with open(test_file, 'w') as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"Error fixing {test_file}: {e}")
    
    return False

def main():
    """Fix all test imports."""
    fixed_count = 0
    
    for test_file in Path('tests').rglob('*.py'):
        if '__pycache__' in str(test_file):
            continue
        
        if fix_test_file(test_file):
            fixed_count += 1
    
    print(f"Fixed {fixed_count} test files")

if __name__ == "__main__":
    main()