"""
Application DTOs for MathTTS v3.

These DTOs provide a clean interface between the application layer
and external layers while maintaining domain integrity.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any, Dict
from datetime import datetime

from ..domain.value_objects import (
    LaTeXExpression,
    SpeechText,
    AudienceLevel,
    MathematicalDomain
)


@dataclass
class ProcessExpressionRequest:
    """Request to process a mathematical expression."""
    
    expression: LaTeXExpression
    audience_level: AudienceLevel
    domain: Optional[MathematicalDomain] = None
    context: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate request after initialization."""
        if not isinstance(self.expression, LaTeXExpression):
            raise TypeError("expression must be a LaTeXExpression")
        if not isinstance(self.audience_level, AudienceLevel):
            raise TypeError("audience_level must be an AudienceLevel")
        if self.domain and not isinstance(self.domain, MathematicalDomain):
            raise TypeError("domain must be a MathematicalDomain")


@dataclass
class ProcessExpressionResponse:
    """Response from processing a mathematical expression."""
    
    expression: LaTeXExpression
    speech_text: SpeechText
    processing_time_ms: float
    cached: bool
    patterns_applied: int
    domain_detected: Optional[MathematicalDomain] = None
    complexity_score: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchProcessRequest:
    """Request to process multiple expressions."""
    
    requests: List[ProcessExpressionRequest]
    parallel: bool = True
    stop_on_error: bool = False
    
    def __post_init__(self) -> None:
        """Validate batch request."""
        if not self.requests:
            raise ValueError("At least one request is required")
        if len(self.requests) > 1000:
            raise ValueError("Batch size cannot exceed 1000 expressions")


@dataclass  
class BatchProcessResponse:
    """Response from batch processing."""
    
    results: List[ProcessExpressionResponse]
    total_processing_time_ms: float
    successful_count: int
    failed_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PatternStatistics:
    """Statistics about pattern usage."""
    
    pattern_id: str
    usage_count: int
    last_used: Optional[datetime] = None
    average_processing_time_ms: Optional[float] = None
    success_rate: Optional[float] = None


@dataclass
class SystemStatistics:
    """Overall system statistics."""
    
    total_expressions_processed: int
    cache_hit_rate: float
    average_processing_time_ms: float
    patterns_statistics: List[PatternStatistics]
    errors_count: int
    uptime_seconds: float
    memory_usage_mb: float