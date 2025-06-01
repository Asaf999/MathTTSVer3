#!/usr/bin/env python3
"""
Simple test runner script to verify tests are working.
"""

import subprocess
import sys
from pathlib import Path

def run_tests():
    """Run tests with proper environment setup."""
    # Add src to Python path
    project_root = Path(__file__).parent
    src_path = project_root / "src"
    
    # Set PYTHONPATH
    import os
    os.environ['PYTHONPATH'] = str(src_path)
    
    # Run unit tests first
    print("Running unit tests...")
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/unit/",
        "-v",
        "--tb=short",
        "-k", "test_create_valid_priority"  # Run just one test first
    ], cwd=project_root)
    
    if result.returncode != 0:
        print("\nTests failed!")
        return 1
    
    print("\nTests passed!")
    return 0

if __name__ == "__main__":
    sys.exit(run_tests())