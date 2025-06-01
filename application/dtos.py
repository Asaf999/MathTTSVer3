"""Application layer DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ProcessingStatus(Enum):
    """Processing status enumeration."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CACHED = "cached"


@dataclass
class ProcessExpressionRequest:
    """Request to process a mathematical expression."""
    
    latex: str
    audience_level: str = "undergraduate"
    output_format: str = "text"  # text, ssml, audio
    context: dict[str, Any] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> None:
        """Validate request."""
        if not self.latex:
            raise ValueError("LaTeX expression is required")
        
        valid_levels = {
            "elementary", "high_school", "undergraduate", 
            "graduate", "research"
        }
        if self.audience_level not in valid_levels:
            raise ValueError(f"Invalid audience level: {self.audience_level}")
        
        valid_formats = {"text", "ssml", "audio"}
        if self.output_format not in valid_formats:
            raise ValueError(f"Invalid output format: {self.output_format}")


@dataclass
class ProcessExpressionResponse:
    """Response from processing a mathematical expression."""
    
    request_id: str
    status: ProcessingStatus
    speech_text: Optional[str] = None
    ssml: Optional[str] = None
    audio_url: Optional[str] = None
    processing_time_ms: float = 0.0
    cache_hit: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    @classmethod
    def success(
        cls,
        request_id: str,
        speech_text: str,
        processing_time_ms: float,
        cache_hit: bool = False,
        **kwargs: Any
    ) -> ProcessExpressionResponse:
        """Create success response."""
        return cls(
            request_id=request_id,
            status=ProcessingStatus.COMPLETED,
            speech_text=speech_text,
            processing_time_ms=processing_time_ms,
            cache_hit=cache_hit,
            **kwargs
        )
    
    @classmethod
    def failure(
        cls,
        request_id: str,
        error: str,
        processing_time_ms: float = 0.0
    ) -> ProcessExpressionResponse:
        """Create failure response."""
        return cls(
            request_id=request_id,
            status=ProcessingStatus.FAILED,
            error=error,
            processing_time_ms=processing_time_ms
        )


@dataclass
class BatchProcessRequest:
    """Request to process multiple expressions."""
    
    expressions: list[ProcessExpressionRequest]
    parallel: bool = True
    stop_on_error: bool = False
    
    def validate(self) -> None:
        """Validate batch request."""
        if not self.expressions:
            raise ValueError("At least one expression is required")
        
        for expr in self.expressions:
            expr.validate()


@dataclass
class BatchProcessResponse:
    """Response from batch processing."""
    
    request_id: str
    total_expressions: int
    successful: int
    failed: int
    results: list[ProcessExpressionResponse]
    total_time_ms: float
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_expressions == 0:
            return 0.0
        return (self.successful / self.total_expressions) * 100


@dataclass
class PatternTestRequest:
    """Request to test a pattern."""
    
    pattern: dict[str, Any]
    test_expressions: list[str]
    
    def validate(self) -> None:
        """Validate pattern test request."""
        required_fields = {"pattern", "output_template"}
        if not all(field in self.pattern for field in required_fields):
            raise ValueError(f"Pattern must have fields: {required_fields}")
        
        if not self.test_expressions:
            raise ValueError("At least one test expression is required")


@dataclass
class PatternTestResponse:
    """Response from pattern testing."""
    
    pattern_id: str
    total_tests: int
    matches: int
    results: list[dict[str, Any]]
    match_rate: float
    average_confidence: float


@dataclass
class HealthCheckResponse:
    """Health check response."""
    
    status: str  # healthy, degraded, unhealthy
    version: str
    uptime_seconds: float
    checks: dict[str, bool]
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MetricsResponse:
    """Metrics response."""
    
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time_ms: float
    cache_hit_rate: float
    patterns_loaded: int
    active_connections: int
    memory_usage_mb: float
    timestamp: datetime = field(default_factory=datetime.utcnow)