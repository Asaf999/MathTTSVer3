"""
Integration tests for the complete pattern matching pipeline.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
import asyncio
from pathlib import Path

from src.adapters.pattern_loaders import YAMLPatternLoader
from src.infrastructure.persistence import MemoryPatternRepository
from src.domain.services import PatternMatcher
from src.domain.value_objects import LaTeXExpression
from src.application.services import MathTTSService
from src.adapters.tts_providers import EdgeTTSAdapter, MockTTSAdapter
from src.infrastructure.cache import AudioCache


@pytest.mark.integration
class TestPatternMatchingPipeline:
    """Test the complete pattern matching pipeline."""
    
    @pytest.fixture
    async def pattern_loader(self, mock_patterns_dir):
        """Create pattern loader with test patterns."""
        loader = YAMLPatternLoader(mock_patterns_dir)
        return loader
    
    @pytest.fixture
    async def loaded_repository(self, pattern_loader):
        """Create repository loaded with patterns."""
        patterns = pattern_loader.load_all_patterns()
        repo = MemoryPatternRepository()
        for pattern in patterns:
            repo.add(pattern)
        return repo
    
    @pytest.fixture
    def pattern_matcher(self, loaded_repository):
        """Create pattern matcher with loaded patterns."""
        return PatternMatcher(loaded_repository)
    
    async def test_yaml_to_repository_pipeline(self, pattern_loader):
        """Test loading patterns from YAML to repository."""
        patterns = pattern_loader.load_all_patterns()
        
        assert len(patterns) > 0
        
        # Verify patterns have expected properties
        for pattern in patterns:
            assert pattern.id
            assert pattern.name
            assert pattern.pattern
            assert pattern.output_template
            assert pattern.priority.value > 0
    
    async def test_expression_to_speech_pipeline(self, pattern_matcher):
        """Test converting LaTeX to speech text."""
        test_cases = [
            (r"\frac{1}{2}", "1 over 2"),
            (r"x^2", "x to the power of 2"),
            (r"\frac{3}{4} + x^2", "3 over 4 + x to the power of 2")
        ]
        
        for latex, expected_contains in test_cases:
            expr = LaTeXExpression(latex)
            result = pattern_matcher.process_expression(expr)
            
            # Check that expected text is in result
            for word in expected_contains.split():
                assert word in result.value
    
    async def test_complex_expression_pipeline(self, loaded_repository):
        """Test processing complex mathematical expressions."""
        # Add more patterns for complex testing
        from src.domain.entities import PatternEntity
        from src.domain.value_objects import PatternPriority
        
        additional_patterns = [
            PatternEntity(
                id="integral",
                name="Integral",
                pattern=r"\\int",
                output_template="integral",
                priority=PatternPriority(1200)
            ),
            PatternEntity(
                id="subscript",
                name="Subscript",
                pattern=r"_(\d+)",
                output_template=r" sub \1",
                priority=PatternPriority(700)
            ),
            PatternEntity(
                id="dx",
                name="Differential x",
                pattern=r"dx",
                output_template="d x",
                priority=PatternPriority(500)
            )
        ]
        
        for pattern in additional_patterns:
            loaded_repository.add(pattern)
        
        matcher = PatternMatcher(loaded_repository)
        
        # Test complex integral
        expr = LaTeXExpression(r"\int_0^1 x^2 dx")
        result = matcher.process_expression(expr)
        
        assert "integral" in result.value
        assert "sub 0" in result.value
        assert "to the power of 1" in result.value
        assert "to the power of 2" in result.value
        assert "d x" in result.value
    
    async def test_pattern_priority_in_pipeline(self, mock_patterns_dir):
        """Test that pattern priority works correctly in full pipeline."""
        # Create custom patterns with overlapping matches
        custom_dir = mock_patterns_dir / "custom"
        custom_dir.mkdir()
        
        custom_patterns = """
metadata:
  category: "priority_test"
  version: "1.0.0"

patterns:
  - id: "high_priority_x2"
    name: "High priority x squared"
    pattern: "x\\^2"
    output_template: "x squared (high priority)"
    priority: 2000
    
  - id: "low_priority_power"
    name: "Low priority power"
    pattern: "\\^(\\d+)"
    output_template: "to the \\1 power (low priority)"
    priority: 500
"""
        (custom_dir / "priority_test.yaml").write_text(custom_patterns)
        
        # Update master patterns
        master_content = """
pattern_files:
  - path: test_patterns.yaml
    enabled: true
  - path: custom/priority_test.yaml
    enabled: true
"""
        (mock_patterns_dir / "master_patterns.yaml").write_text(master_content)
        
        # Load and test
        loader = YAMLPatternLoader(mock_patterns_dir)
        patterns = loader.load_all_patterns()
        
        repo = MemoryPatternRepository()
        for pattern in patterns:
            repo.add(pattern)
        
        matcher = PatternMatcher(repo)
        
        expr = LaTeXExpression("x^2 + y^3")
        result = matcher.process_expression(expr)
        
        # x^2 should match high priority pattern
        assert "x squared (high priority)" in result.value
        # y^3 should match low priority pattern
        assert "to the 3 power (low priority)" in result.value
    
    async def test_pattern_loader_error_handling(self, tmp_path):
        """Test pattern loader handles errors gracefully."""
        # Create invalid YAML
        patterns_dir = tmp_path / "invalid_patterns"
        patterns_dir.mkdir()
        
        (patterns_dir / "master_patterns.yaml").write_text("invalid: yaml: content:")
        
        loader = YAMLPatternLoader(patterns_dir)
        patterns = loader.load_all_patterns()
        
        # Should return empty list on error
        assert patterns == []
    
    async def test_special_characters_pipeline(self, loaded_repository):
        """Test handling of special characters through pipeline."""
        # Add patterns for special characters
        special_patterns = [
            PatternEntity(
                id="pi",
                name="Pi",
                pattern=r"\\pi",
                output_template="pi",
                priority=PatternPriority(1000)
            ),
            PatternEntity(
                id="infinity",
                name="Infinity",
                pattern=r"\\infty",
                output_template="infinity",
                priority=PatternPriority(1000)
            ),
            PatternEntity(
                id="sum",
                name="Sum",
                pattern=r"\\sum",
                output_template="sum",
                priority=PatternPriority(1200)
            )
        ]
        
        for pattern in special_patterns:
            loaded_repository.add(pattern)
        
        matcher = PatternMatcher(loaded_repository)
        
        # Test expression with special characters
        expr = LaTeXExpression(r"\sum_{i=1}^{\infty} \frac{1}{i^2} = \frac{\pi^2}{6}")
        result = matcher.process_expression(expr)
        
        assert "sum" in result.value
        assert "infinity" in result.value
        assert "pi" in result.value
    
    @pytest.mark.asyncio
    async def test_full_mathtts_service_pipeline(self, temp_dir):
        """Test the complete MathTTS service pipeline."""
        # Create mock TTS adapter
        tts_adapter = MockTTSAdapter()
        await tts_adapter.initialize()
        
        # Create audio cache
        cache = AudioCache(cache_dir=temp_dir / "cache")
        
        # Create pattern repository with test patterns
        repo = MemoryPatternRepository()
        repo.add(PatternEntity(
            id="fraction",
            name="Fraction",
            pattern=r"\\frac\{(\d+)\}\{(\d+)\}",
            output_template=r"\1 over \2",
            priority=PatternPriority(1000)
        ))
        
        # Create MathTTS service
        service = MathTTSService(
            pattern_repository=repo,
            tts_adapter=tts_adapter,
            audio_cache=cache
        )
        
        # Test conversion
        latex = r"\frac{1}{2}"
        audio_data = await service.convert_latex_to_speech(latex)
        
        assert audio_data is not None
        assert audio_data.data == b"mock audio data"
        assert audio_data.duration_seconds == 1.0
        
        # Test caching
        audio_data2 = await service.convert_latex_to_speech(latex)
        assert audio_data2.data == audio_data.data
        
        await tts_adapter.close()