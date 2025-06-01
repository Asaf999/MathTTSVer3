"""
Pydantic schemas for API request/response models.

This module defines the external API contract using Pydantic models.
These are separate from domain models to maintain clean architecture.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

from src.domain.value_objects import AudienceLevel, MathematicalDomain
from src.adapters.tts_providers import AudioFormat


class AudienceLevelEnum(str, Enum):
    """API enum for audience levels."""
    ELEMENTARY = "elementary"
    MIDDLE_SCHOOL = "middle_school"
    HIGH_SCHOOL = "high_school"
    UNDERGRADUATE = "undergraduate"
    RESEARCH = "research"


class MathematicalDomainEnum(str, Enum):
    """API enum for mathematical domains."""
    ALGEBRA = "algebra"
    CALCULUS = "calculus"
    LINEAR_ALGEBRA = "linear_algebra"
    REAL_ANALYSIS = "real_analysis"
    COMPLEX_ANALYSIS = "complex_analysis"
    TOPOLOGY = "topology"
    DIFFERENTIAL_GEOMETRY = "differential_geometry"
    PROBABILITY = "probability"
    STATISTICS = "statistics"
    NUMERICAL_ANALYSIS = "numerical_analysis"
    COMBINATORICS = "combinatorics"
    ALGORITHMS = "algorithms"
    LOGIC = "logic"


class AudioFormatEnum(str, Enum):
    """API enum for audio formats."""
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    WEBM = "webm"


# Expression Processing Schemas

class ExpressionProcessRequest(BaseModel):
    """Request schema for processing a single expression."""
    
    expression: str = Field(
        ...,
        description="LaTeX mathematical expression to process",
        example="\\frac{d}{dx}\\sin(x) = \\cos(x)",
        min_length=1,
        max_length=10000
    )
    audience_level: AudienceLevelEnum = Field(
        default=AudienceLevelEnum.HIGH_SCHOOL,
        description="Target audience complexity level"
    )
    domain: Optional[MathematicalDomainEnum] = Field(
        default=None,
        description="Mathematical domain hint for better context"
    )
    context: Optional[str] = Field(
        default=None,
        description="Expression context (inline, display, equation, etc.)",
        example="inline"
    )
    
    @validator("expression")
    def validate_expression(cls, v: str) -> str:
        """Validate LaTeX expression."""
        if not v.strip():
            raise ValueError("Expression cannot be empty")
        return v.strip()


class ExpressionProcessResponse(BaseModel):
    """Response schema for processed expression."""
    
    expression: str = Field(..., description="Original LaTeX expression")
    speech_text: str = Field(..., description="Natural speech text output")
    ssml: Optional[str] = Field(None, description="SSML markup for advanced TTS")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    cached: bool = Field(..., description="Whether result was retrieved from cache")
    patterns_applied: int = Field(..., description="Number of patterns applied")
    domain_detected: Optional[str] = Field(None, description="Detected mathematical domain")
    complexity_score: Optional[float] = Field(None, description="Expression complexity score")


class SingleExpressionRequest(BaseModel):
    """Single expression request for batch processing."""
    
    expression: str = Field(..., min_length=1, max_length=10000)
    audience_level: AudienceLevelEnum = AudienceLevelEnum.HIGH_SCHOOL
    domain: Optional[MathematicalDomainEnum] = None
    context: Optional[str] = None


class BatchExpressionRequest(BaseModel):
    """Request schema for batch expression processing."""
    
    expressions: List[SingleExpressionRequest] = Field(
        ...,
        description="List of expressions to process",
        min_items=1,
        max_items=50
    )


class BatchExpressionResponse(BaseModel):
    """Response schema for batch processing."""
    
    results: List[ExpressionProcessResponse] = Field(..., description="Processing results")
    total_processing_time_ms: float = Field(..., description="Total processing time")
    successful_count: int = Field(..., description="Number of successful processes")
    failed_count: int = Field(..., description="Number of failed processes")


# TTS Synthesis Schemas

class TTSRequest(BaseModel):
    """Request schema for TTS synthesis."""
    
    expression: str = Field(..., description="LaTeX expression to synthesize")
    voice_id: str = Field(
        default="en-US-AriaNeural",
        description="Voice ID for synthesis"
    )
    audience_level: AudienceLevelEnum = AudienceLevelEnum.HIGH_SCHOOL
    domain: Optional[MathematicalDomainEnum] = None
    context: Optional[str] = None
    
    # Audio parameters
    rate: float = Field(
        default=1.0,
        description="Speech rate multiplier (0.5-2.0)",
        ge=0.5,
        le=2.0
    )
    pitch: float = Field(
        default=1.0,
        description="Speech pitch multiplier (0.5-2.0)",
        ge=0.5,
        le=2.0
    )
    volume: float = Field(
        default=1.0,
        description="Speech volume multiplier (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    format: AudioFormatEnum = Field(
        default=AudioFormatEnum.MP3,
        description="Audio output format"
    )
    sample_rate: int = Field(
        default=24000,
        description="Audio sample rate in Hz",
        gt=0
    )


class TTSResponse(BaseModel):
    """Response schema for TTS synthesis."""
    
    expression: str = Field(..., description="Original LaTeX expression")
    speech_text: str = Field(..., description="Generated speech text")
    audio_size_bytes: int = Field(..., description="Audio file size in bytes")
    audio_format: str = Field(..., description="Audio format")
    duration_seconds: Optional[float] = Field(None, description="Audio duration")
    voice_id: str = Field(..., description="Voice used for synthesis")
    processing_time_ms: float = Field(..., description="Total processing time")
    download_url: Optional[str] = Field(None, description="Audio download URL")


# Voice Management Schemas

class VoiceInfo(BaseModel):
    """Voice information schema."""
    
    id: str = Field(..., description="Voice identifier")
    name: str = Field(..., description="Human-readable voice name")
    language: str = Field(..., description="Voice language code")
    gender: str = Field(..., description="Voice gender")
    description: Optional[str] = Field(None, description="Voice description")
    styles: Optional[List[str]] = Field(None, description="Available voice styles")


class VoiceListResponse(BaseModel):
    """Response schema for voice listing."""
    
    voices: List[VoiceInfo] = Field(..., description="Available voices")
    total_count: int = Field(..., description="Total number of voices")


# Pattern Management Schemas

class PatternInfo(BaseModel):
    """Pattern information schema."""
    
    id: str = Field(..., description="Pattern identifier")
    pattern: str = Field(..., description="Pattern regex or literal")
    output_template: str = Field(..., description="Output template")
    priority: int = Field(..., description="Pattern priority")
    domain: str = Field(..., description="Mathematical domain")
    contexts: List[str] = Field(..., description="Applicable contexts")
    description: Optional[str] = Field(None, description="Pattern description")


class PatternListResponse(BaseModel):
    """Response schema for pattern listing."""
    
    patterns: List[PatternInfo] = Field(..., description="Available patterns")
    total_count: int = Field(..., description="Total number of patterns")
    domains: List[str] = Field(..., description="Available domains")


class PatternTestRequest(BaseModel):
    """Request schema for testing a pattern."""
    
    pattern: str = Field(..., description="Pattern to test")
    test_expression: str = Field(..., description="Expression to test against")
    context: Optional[str] = Field(None, description="Test context")


class PatternTestResponse(BaseModel):
    """Response schema for pattern testing."""
    
    matched: bool = Field(..., description="Whether pattern matched")
    output: Optional[str] = Field(None, description="Pattern output if matched")
    match_groups: Optional[List[str]] = Field(None, description="Regex match groups")


# Health and Status Schemas

class HealthResponse(BaseModel):
    """Health check response schema."""
    
    status: str = Field(..., description="Overall health status")
    timestamp: str = Field(..., description="Check timestamp")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")
    
    # Component health
    database: str = Field(..., description="Database health")
    cache: str = Field(..., description="Cache health")
    tts_provider: str = Field(..., description="TTS provider health")
    
    # Performance metrics
    uptime_seconds: float = Field(..., description="Application uptime")
    memory_usage_mb: Optional[float] = Field(None, description="Memory usage")
    cache_hit_rate: Optional[float] = Field(None, description="Cache hit rate")


class MetricsResponse(BaseModel):
    """Metrics response schema."""
    
    expressions_processed_total: int = Field(..., description="Total expressions processed")
    expressions_processed_cached: int = Field(..., description="Cached expressions served")
    average_processing_time_ms: float = Field(..., description="Average processing time")
    patterns_loaded: int = Field(..., description="Number of patterns loaded")
    voices_available: int = Field(..., description="Number of voices available")
    
    # Performance metrics
    cache_hit_rate: float = Field(..., description="Cache hit rate percentage")
    memory_usage_mb: float = Field(..., description="Current memory usage")
    uptime_seconds: float = Field(..., description="Application uptime")


# Error Schemas

class ErrorResponse(BaseModel):
    """Standard error response schema."""
    
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    request_id: Optional[str] = Field(None, description="Request correlation ID")
    timestamp: Optional[str] = Field(None, description="Error timestamp")