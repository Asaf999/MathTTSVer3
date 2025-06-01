# MathTTS v3 Architecture

## Overview

MathTTS v3 is built using Clean Architecture principles, ensuring a clear separation of concerns and maintainability. The system is organized into distinct layers, each with specific responsibilities and dependencies flowing only inward.

## Architecture Layers

### 1. Domain Layer (Core)

The heart of the system containing pure business logic with no external dependencies.

**Key Components:**
- **Entities**: `MathematicalExpression`, `PatternEntity`
- **Value Objects**: `LaTeXExpression`, `SpeechText`, `PatternPriority`, `AudienceLevel`
- **Domain Services**: `PatternMatchingService`
- **Interfaces**: `PatternRepository`, `CacheRepository`

**Design Principles:**
- No external dependencies
- Immutable value objects
- Rich domain models with behavior
- Domain-specific exceptions

### 2. Application Layer

Contains application-specific business rules and orchestrates the flow of data.

**Key Components:**
- **Use Cases**: `ProcessExpressionUseCase`, `BatchProcessUseCase`
- **DTOs**: Request/Response objects for clean interfaces
- **Application Services**: Cross-cutting concerns

**Responsibilities:**
- Orchestrate domain objects
- Transaction management
- Authorization checks
- Input validation

### 3. Infrastructure Layer

Implements technical details and external system integrations.

**Key Components:**
- **Persistence**: `MemoryPatternRepository`, `FilePatternRepository`
- **Cache**: `LRUCacheRepository`, `RedisCacheRepository`
- **Configuration**: Settings management
- **Logging**: Structured logging implementation

**Features:**
- Pluggable implementations
- Configuration management
- Performance monitoring
- External service integration

### 4. Adapters Layer

Converts data between external formats and internal domain models.

**Key Components:**
- **Pattern Loaders**: YAML, JSON, Database loaders
- **TTS Providers**: Azure, Google, Amazon adapters
- **Legacy Integration**: Compatibility layers

**Purpose:**
- Format conversion
- Protocol adaptation
- Legacy system integration
- External API wrapping

### 5. Presentation Layer

User interface implementations.

**Key Components:**
- **REST API**: FastAPI implementation
- **CLI**: Command-line interface
- **WebSocket**: Real-time streaming API
- **Web UI**: Pattern playground

## Key Design Patterns

### 1. Repository Pattern
```python
# Domain defines interface
class PatternRepository(ABC):
    async def find_by_id(self, id: str) -> Optional[PatternEntity]:
        pass

# Infrastructure implements
class MemoryPatternRepository(PatternRepository):
    async def find_by_id(self, id: str) -> Optional[PatternEntity]:
        return self._patterns.get(id)
```

### 2. Dependency Injection
```python
# Use case depends on abstractions
class ProcessExpressionUseCase:
    def __init__(
        self,
        pattern_matcher: PatternMatchingService,
        cache_repository: CacheRepository
    ):
        self.pattern_matcher = pattern_matcher
        self.cache_repository = cache_repository
```

### 3. Value Objects
```python
@dataclass(frozen=True)
class LaTeXExpression:
    value: str
    
    def __post_init__(self):
        # Validation in constructor
        if not self.value:
            raise ValidationError("Expression cannot be empty")
```

### 4. Domain Events (Future)
```python
@dataclass
class PatternMatchedEvent:
    expression_id: str
    pattern_id: str
    timestamp: datetime
```

## Data Flow

1. **Request Flow**:
   ```
   API Request → DTO → Use Case → Domain Service → Entity
   ```

2. **Response Flow**:
   ```
   Entity → Domain Service → Use Case → DTO → API Response
   ```

3. **Pattern Matching Flow**:
   ```
   Expression → Pattern Selection → Priority Sorting → 
   Sequential Application → Post-processing → Speech Text
   ```

## Pattern System Architecture

### Pattern Structure
```yaml
pattern:
  id: "unique_id"
  name: "Human-readable name"
  pattern: "\\frac{1}{2}"  # Regex or literal
  output_template: "one half"
  priority: 1500  # 0-2000 scale
  domain: "general"
  contexts: ["inline", "display"]
  conditions:
    - type: "preceding"
      value: "equals"
  pronunciation_hints:
    emphasis: "half"
    pause_before: 100
```

### Pattern Processing Pipeline
1. **Selection**: Get patterns for domain and context
2. **Filtering**: Apply conditions
3. **Sorting**: Order by priority (highest first)
4. **Application**: Apply patterns sequentially
5. **Post-processing**: Audience-specific adjustments

## Performance Architecture

### Caching Strategy
- **L1 Cache**: In-memory LRU cache
- **L2 Cache**: Redis distributed cache
- **Cache Keys**: SHA256 hash of (expression + audience + context)
- **TTL**: 24 hours default, configurable

### Optimization Techniques
1. **Pattern Compilation**: Regex patterns compiled once
2. **Priority Short-circuiting**: Stop on first match for exclusive patterns
3. **Batch Processing**: Process multiple expressions concurrently
4. **Connection Pooling**: Reuse TTS service connections

## Security Architecture

### Input Validation
- Maximum expression length: 10,000 characters
- Maximum nesting depth: 20 levels
- Command whitelist validation
- Rate limiting per client

### API Security
- API key authentication
- JWT for session management
- CORS configuration
- Request sanitization

## Scalability Architecture

### Horizontal Scaling
```
Load Balancer
    ├── API Server 1
    ├── API Server 2
    └── API Server N
         ├── Shared Redis Cache
         └── Shared Pattern Storage
```

### Vertical Scaling
- Async/await for I/O operations
- Worker pool for CPU-intensive tasks
- Memory-mapped files for large documents
- Streaming for real-time processing

## Monitoring Architecture

### Metrics Collection
```python
# Prometheus metrics
processing_time = Histogram(
    'mathtts_processing_seconds',
    'Time to process expression'
)

cache_hits = Counter(
    'mathtts_cache_hits_total',
    'Number of cache hits'
)
```

### Health Checks
- **/health**: Basic liveness check
- **/ready**: Readiness with dependency checks
- **/metrics**: Prometheus metrics endpoint

## Testing Architecture

### Test Pyramid
```
         /\
        /  \  End-to-End Tests (5%)
       /    \
      /------\  Integration Tests (20%)
     /        \
    /----------\  Unit Tests (75%)
```

### Test Categories
1. **Unit Tests**: Pure functions, value objects
2. **Integration Tests**: Repository implementations
3. **Contract Tests**: API compatibility
4. **Performance Tests**: Benchmarks and load tests
5. **Devil Tests**: Complex edge cases

## Deployment Architecture

### Container Structure
```dockerfile
FROM python:3.11-slim
# Multi-stage build for smaller images
# Non-root user for security
# Health check included
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mathtts-api
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
```

## Future Architecture Considerations

1. **Event Sourcing**: Record all pattern applications
2. **CQRS**: Separate read and write models
3. **GraphQL**: Alternative API interface
4. **WebAssembly**: Client-side processing
5. **Federated Learning**: Improve patterns from usage