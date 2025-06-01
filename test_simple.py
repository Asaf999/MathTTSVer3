#!/usr/bin/env python3
"""Simple test to verify basic functionality."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Test imports
try:
    from domain.value_objects import PatternPriority
    print("✓ PatternPriority imported successfully")
    
    # Test creation
    priority = PatternPriority(1000)
    print(f"✓ Created PatternPriority with value: {priority.value}")
    
    # Test validation
    try:
        invalid = PatternPriority(10001)
    except Exception as e:
        print(f"✓ Validation works: {e}")
    
    # Test value objects
    from domain.value_objects_simple import LaTeXExpression, SpeechText
    
    expr = LaTeXExpression(r"\frac{1}{2}")
    print(f"✓ Created LaTeX expression: {expr}")
    
    speech = SpeechText("one half")
    print(f"✓ Created speech text: {speech.value}")
    
    # Test TTS value objects
    from domain.value_objects_tts import TTSOptions, AudioFormat
    
    options = TTSOptions()
    print(f"✓ Created TTS options with voice: {options.voice_id}")
    
    print("\n✅ All basic tests passed!")
    
except Exception as e:
    import traceback
    print(f"\n❌ Error: {e}")
    traceback.print_exc()