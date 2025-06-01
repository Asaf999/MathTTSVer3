"""
Pytest configuration and fixtures for MathTTS Ver3 tests.
"""

import pytest
import asyncio
from pathlib import Path
import sys
import tempfile
import shutil
from typing import Generator, AsyncGenerator

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.domain.entities import PatternEntity
from src.domain.value_objects import PatternPriority
from src.domain.value_objects_simple import LaTeXExpression
from src.domain.value_objects_tts import TTSOptions
from src.infrastructure.persistence import MemoryPatternRepository
from src.adapters.pattern_loaders import YAMLPatternLoader


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_pattern() -> PatternEntity:
    """Create a sample pattern for testing."""
    return PatternEntity(
        id="test_fraction",
        name="Test Fraction",
        description="Test pattern for fractions",
        pattern=r"\\frac\{(\d+)\}\{(\d+)\}",
        output_template=r"\1 over \2",
        priority=PatternPriority(1000),
        domain="test",
        tags=["test", "fraction"],
        examples=[r"\frac{1}{2}"],
        metadata={}
    )


@pytest.fixture
def pattern_repository() -> MemoryPatternRepository:
    """Create an empty pattern repository."""
    return MemoryPatternRepository()


@pytest.fixture
def loaded_pattern_repository() -> MemoryPatternRepository:
    """Create a pattern repository with test patterns."""
    repo = MemoryPatternRepository()
    
    # Add various test patterns
    patterns = [
        PatternEntity(
            id="fraction_half",
            name="One half",
            pattern=r"\\frac\{1\}\{2\}",
            output_template="one half",
            priority=PatternPriority(1500),
            domain="fractions"
        ),
        PatternEntity(
            id="superscript",
            name="Superscript",
            pattern=r"\^(\d+)",
            output_template=r"to the power of \1",
            priority=PatternPriority(800),
            domain="exponents"
        ),
        PatternEntity(
            id="greek_alpha",
            name="Greek letter alpha",
            pattern=r"\\alpha",
            output_template="alpha",
            priority=PatternPriority(500),
            domain="symbols"
        )
    ]
    
    for pattern in patterns:
        repo.add(pattern)
    
    return repo


@pytest.fixture
def latex_expressions() -> list[str]:
    """Sample LaTeX expressions for testing."""
    return [
        r"\frac{1}{2}",
        r"x^2 + y^2 = z^2",
        r"\int_0^1 x^2 dx",
        r"\alpha + \beta = \gamma",
        r"\lim_{x \to \infty} \frac{1}{x}",
        r"e^{i\pi} + 1 = 0"
    ]


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_patterns_dir(temp_dir: Path) -> Path:
    """Create a mock patterns directory with test patterns."""
    patterns_dir = temp_dir / "patterns"
    patterns_dir.mkdir()
    
    # Create master patterns file
    master_content = """
pattern_files:
  - path: test_patterns.yaml
    enabled: true
"""
    (patterns_dir / "master_patterns.yaml").write_text(master_content)
    
    # Create test patterns file
    test_patterns_content = """
metadata:
  category: "test"
  version: "1.0.0"

patterns:
  - id: "test_fraction"
    name: "Test Fraction"
    pattern: "\\\\frac\\{(\\d+)\\}\\{(\\d+)\\}"
    output_template: "\\1 over \\2"
    priority: 1000
    tags: ["test", "fraction"]
    
  - id: "test_power"
    name: "Test Power"
    pattern: "(\\w+)\\^(\\d+)"
    output_template: "\\1 to the power of \\2"
    priority: 900
    tags: ["test", "power"]
"""
    (patterns_dir / "test_patterns.yaml").write_text(test_patterns_content)
    
    return patterns_dir


@pytest.fixture
def tts_options() -> TTSOptions:
    """Create default TTS options for testing."""
    return TTSOptions(
        voice_id="test-voice",
        rate=1.0,
        pitch=1.0,
        volume=1.0
    )


@pytest.fixture
async def mock_audio_data() -> bytes:
    """Create mock audio data for testing."""
    # Simple WAV header + some data
    return b"RIFF" + b"\x00" * 40 + b"\xFF" * 1000


@pytest.fixture
def env_setup(monkeypatch):
    """Set up test environment variables."""
    test_env = {
        "ENVIRONMENT": "test",
        "DEBUG": "true",
        "LOG_LEVEL": "DEBUG",
        "APP_VERSION": "test",
        "PATTERNS_DIR": "patterns",
        "TTS_PROVIDER": "mock",
        "EDGE_TTS_VOICE": "test-voice",
        "CACHE_ENABLED": "false",
        "API_HOST": "127.0.0.1",
        "API_PORT": "8001"
    }
    
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)
    
    return test_env