# MathTTS v3 - LaTeX to Speech Conversion System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

MathTTS v3 is a sophisticated text-to-speech system specifically designed for mathematical expressions. It converts LaTeX mathematical notation into natural, human-readable speech using advanced pattern matching and modern TTS providers.

## 🔥 Key Features

- **Natural Speech Generation**: Converts complex LaTeX expressions to professor-quality speech
- **Multiple TTS Providers**: Support for Edge-TTS, Azure, Google Cloud, and Amazon Polly
- **Pattern-Based Processing**: Extensible YAML-based pattern system for mathematical notation
- **Clean Architecture**: Built following clean architecture principles for maintainability
- **High Performance**: Sub-10ms response times with intelligent caching
- **REST API**: Full-featured API with OpenAPI documentation
- **CLI Interface**: Command-line tool for batch processing and development
- **Domain Awareness**: Automatic detection of mathematical domains (calculus, algebra, etc.)
- **Audience Targeting**: Adjustable complexity levels from elementary to research

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd MathTTSVer3

# Install dependencies
pip install -r requirements.txt

# Setup the application
python main.py setup

# Start the API server
python main.py api

# Or use the CLI
python main.py cli process "\\frac{d}{dx}\\sin(x)"
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# API will be available at http://localhost:8000
# Grafana dashboard at http://localhost:3000
```

## 📚 Usage Examples

### CLI Usage

```bash
# Process a single expression
python main.py cli process "\\frac{1}{2}" --speak

# Process multiple expressions from file
python main.py cli batch expressions.txt --output-dir results/

# List available voices
python main.py cli voices --language en-US

# Show available patterns
python main.py cli patterns --domain calculus
```

### API Usage

```bash
# Process expression via API
curl -X POST "http://localhost:8000/api/v1/expressions/process" \
  -H "Content-Type: application/json" \
  -d '{
    "expression": "\\frac{d}{dx}\\sin(x)",
    "audience_level": "undergraduate",
    "domain": "calculus"
  }'

# Synthesize speech audio
curl -X POST "http://localhost:8000/api/v1/expressions/synthesize" \
  -H "Content-Type: application/json" \
  -d '{
    "expression": "\\int_0^1 x^2 dx",
    "voice_id": "en-US-AriaNeural",
    "format": "mp3"
  }'
```

### Python Integration

```python
from src.domain.value_objects import LaTeXExpression, AudienceLevel
from src.application.use_cases import ProcessExpressionUseCase
from src.application.dtos import ProcessExpressionRequest

# Setup components (see integration tests for full example)
# ...

# Process expression
expression = LaTeXExpression("\\frac{\\partial f}{\\partial x}")
request = ProcessExpressionRequest(
    expression=expression,
    audience_level=AudienceLevel.UNDERGRADUATE,
    context="inline"
)

result = await use_case.execute(request)
print(result.speech_text.plain_text)
# Output: "the partial derivative of f with respect to x"
```

## 🏗️ Architecture

MathTTS v3 follows **Clean Architecture** principles:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   REST API  │  │     CLI     │  │   Web Interface     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     Adapters Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ TTS Providers│  │Pattern Load.│  │   Legacy Systems    │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                  Infrastructure Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Caching   │  │   Logging   │  │   Configuration     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                   Application Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Use Cases  │  │    DTOs     │  │     Services        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     Domain Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Entities  │  │Value Objects│  │  Domain Services    │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

- **Domain Layer**: Core business logic (LaTeX expressions, patterns, speech text)
- **Application Layer**: Use cases and application services
- **Infrastructure**: Cross-cutting concerns (caching, logging, configuration)
- **Adapters**: External system integration (TTS providers, pattern loaders)
- **Presentation**: User interfaces (REST API, CLI, future web UI)

## 🔧 Configuration

Configuration is managed via environment variables or `.env` files:

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration
nano .env
```

Key configuration options:

- **TTS_DEFAULT_PROVIDER**: Primary TTS provider (edge-tts, azure, google, amazon)
- **CACHE_TYPE**: Caching backend (memory, redis)
- **API_RATE_LIMIT_REQUESTS**: API rate limiting
- **PATTERN_PATTERNS_DIR**: Location of pattern YAML files

## 📊 Monitoring

The system includes comprehensive monitoring:

- **Health Checks**: `/api/v1/health` endpoint
- **Metrics**: Prometheus metrics at `/metrics`
- **Logging**: Structured JSON logging with correlation IDs
- **Grafana Dashboards**: Pre-configured dashboards for monitoring

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test categories
pytest tests/test_domain.py
pytest tests/test_integration.py

# Run performance tests
pytest tests/test_performance.py -m performance
```

## 📈 Performance

- **Response Time**: <10ms for cached expressions, <100ms for new expressions
- **Throughput**: 1000+ requests/second (with Redis caching)
- **Memory Usage**: ~50MB base, scales with cache size
- **Pattern Matching**: Priority-based O(n) pattern matching

## 🔌 Extensibility

### Adding New TTS Providers

1. Implement `TTSProviderAdapter` interface
2. Add provider configuration
3. Register in provider factory

### Adding New Patterns

Create YAML files in the `patterns/` directory:

```yaml
pattern:
  id: "my_pattern"
  pattern: "\\\\mycommand\\{([^}]+)\\}"
  output_template: "my command with \\1"
  priority: 1000
  domain: "algebra"
  contexts: ["inline", "display"]
  description: "My custom pattern"
```

### Adding New Domains

1. Extend `MathematicalDomain` enum
2. Add domain-specific patterns
3. Update documentation

## 🛠️ Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install

# Run code formatting
black src/
ruff check src/

# Type checking
mypy src/
```

### Project Structure

```
MathTTSVer3/
├── src/
│   ├── domain/           # Core business logic
│   ├── application/      # Use cases and services
│   ├── infrastructure/   # Cross-cutting concerns
│   ├── adapters/        # External integrations
│   └── presentation/    # User interfaces
├── patterns/            # Pattern definitions
├── tests/              # Test suite
├── docs/               # Documentation
├── monitoring/         # Monitoring configuration
└── main.py            # Application entry point
```

## 🚢 Deployment

### Docker

```bash
# Build image
docker build -t mathtts:v3 .

# Run container
docker run -p 8000:8000 mathtts:v3
```

### Kubernetes

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/
```

### Environment Variables

Production deployment requires:

- TTS provider credentials (Azure, Google, or AWS)
- Redis URL for distributed caching
- Prometheus metrics endpoint configuration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following the clean architecture
4. Add comprehensive tests
5. Update documentation
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built upon patterns from MathSpeak v2
- Inspired by clean architecture principles
- Uses Microsoft Edge TTS for high-quality speech synthesis
- FastAPI for modern async web framework

## 📞 Support

- 📧 Email: support@mathtts.com
- 📚 Documentation: [docs/](docs/)
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions

---

**MathTTS v3** - Making mathematics accessible through natural speech! 🎯🔊