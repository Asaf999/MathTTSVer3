#!/usr/bin/env python3
"""Test basic MathTTS v3 functionality"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from adapters.pattern_loaders.yaml_pattern_loader import YamlPatternLoader
from infrastructure.persistence.memory_pattern_repository import MemoryPatternRepository
from domain.services.pattern_matcher import PatternMatcher
from domain.value_objects import LaTeXExpression, TTSOptions, AudioFormat
from adapters.tts_providers.edge_tts_adapter import EdgeTTSAdapter
from infrastructure.logging import configure_logging, get_logger

# Configure logging
configure_logging()
logger = get_logger(__name__)


async def test_pattern_matching():
    """Test pattern matching functionality"""
    print("\n=== Testing Pattern Matching ===")
    
    # Load patterns
    patterns_dir = Path(__file__).parent / 'patterns'
    loader = YamlPatternLoader(patterns_dir)
    
    # Load all patterns
    print("Loading patterns...")
    patterns = loader.load_all_patterns()
    print(f"Loaded {len(patterns)} patterns")
    
    # Create pattern repository and matcher
    repository = MemoryPatternRepository()
    for pattern in patterns:
        repository.add(pattern)
    
    matcher = PatternMatcher(repository)
    
    # Test expressions
    test_cases = [
        r"\frac{1}{2}",
        r"x^2 + y^2 = z^2",
        r"\int_0^1 x^2 dx",
        r"\lim_{x \to \infty} \frac{1}{x}",
        r"\alpha + \beta = \gamma",
        r"e^{i\pi} + 1 = 0",
    ]
    
    print("\nTesting pattern matching:")
    for latex in test_cases:
        expr = LaTeXExpression(latex)
        result = matcher.process_expression(expr)
        print(f"LaTeX: {latex}")
        print(f"Speech: {result.value}")
        print()


async def test_tts_synthesis():
    """Test TTS synthesis"""
    print("\n=== Testing TTS Synthesis ===")
    
    # Create TTS adapter
    tts = EdgeTTSAdapter()
    await tts.initialize()
    
    # List voices
    print("Available voices:")
    voices = await tts.list_voices(language="en")
    for voice in voices[:5]:  # Show first 5
        print(f"  - {voice.id}: {voice.name} ({voice.gender.value})")
    
    # Test synthesis
    test_text = "The integral from 0 to 1 of x squared d x equals one third"
    options = TTSOptions(
        voice_id="en-US-AriaNeural",
        rate=1.0,
        pitch=1.0,
        volume=1.0,
        format=AudioFormat.MP3
    )
    
    print(f"\nSynthesizing: '{test_text}'")
    audio_data = await tts.synthesize(test_text, options)
    print(f"Generated audio: {len(audio_data.data)} bytes, {audio_data.duration_seconds:.2f} seconds")
    
    # Save to file
    output_file = Path(__file__).parent / "test_output.mp3"
    output_file.write_bytes(audio_data.data)
    print(f"Saved to: {output_file}")
    
    await tts.close()


async def test_full_pipeline():
    """Test full LaTeX to Speech pipeline"""
    print("\n=== Testing Full Pipeline ===")
    
    # Load patterns
    patterns_dir = Path(__file__).parent / 'patterns'
    loader = YamlPatternLoader(patterns_dir)
    patterns = loader.load_all_patterns()
    
    # Create components
    repository = MemoryPatternRepository()
    for pattern in patterns:
        repository.add(pattern)
    
    matcher = PatternMatcher(repository)
    tts = EdgeTTSAdapter()
    await tts.initialize()
    
    # Test expression
    latex = r"x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}"
    print(f"LaTeX: {latex}")
    
    # Convert to speech text
    expr = LaTeXExpression(latex)
    speech_text = matcher.process_expression(expr)
    print(f"Speech: {speech_text.value}")
    
    # Synthesize
    options = TTSOptions(voice_id="en-US-AriaNeural")
    audio_data = await tts.synthesize(speech_text.value, options)
    
    # Save
    output_file = Path(__file__).parent / "quadratic_formula.mp3"
    output_file.write_bytes(audio_data.data)
    print(f"Saved audio to: {output_file}")
    
    await tts.close()


async def main():
    """Run all tests"""
    try:
        await test_pattern_matching()
        await test_tts_synthesis()
        await test_full_pipeline()
        print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())