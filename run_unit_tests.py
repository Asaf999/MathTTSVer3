#!/usr/bin/env python3
"""
Script to run unit tests for MathTTS v3.
"""

import sys
import os
import unittest
import asyncio

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure asyncio for tests
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def run_tests():
    """Run all unit tests."""
    print("=" * 70)
    print("Running MathTTS v3 Unit Tests")
    print("=" * 70)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover('tests/unit', pattern='test_*.py')
    
    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\nAll tests passed! ✅")
        return 0
    else:
        print("\nSome tests failed ❌")
        return 1


if __name__ == "__main__":
    # Suppress deprecation warnings for cleaner output
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    
    sys.exit(run_tests())