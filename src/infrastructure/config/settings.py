"""
Configuration management for MathTTS v3.

This module provides centralized configuration management using Pydantic settings.
It supports environment variables, .env files, and default values.
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field, validator
from enum import Enum


class Environment(str, Enum):
    """Application environment."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class TTSProvider(str, Enum):
    """Available TTS providers."""
    EDGE_TTS = "edge-tts"
    AZURE = "azure"
    GOOGLE = "google"
    AMAZON = "amazon"
    PYTTSX3 = "pyttsx3"  # Offline fallback


class CacheSettings(BaseSettings):
    """Cache configuration."""
    type: str = Field(default="memory", description="Cache type: memory, redis")
    max_size: int = Field(default=1000, description="Maximum cache entries")
    ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds")
    
    # Redis-specific settings
    redis_url: Optional[str] = Field(default=None, description="Redis connection URL")
    redis_prefix: str = Field(default="mathtts:", description="Redis key prefix")
    
    class Config:
        env_prefix = "CACHE_"


class TTSSettings(BaseSettings):
    """TTS provider configuration."""
    default_provider: TTSProvider = Field(
        default=TTSProvider.EDGE_TTS,
        description="Default TTS provider"
    )
    fallback_provider: TTSProvider = Field(
        default=TTSProvider.PYTTSX3,
        description="Fallback TTS provider for offline mode"
    )
    
    # Provider-specific settings
    azure_key: Optional[str] = Field(default=None, description="Azure Speech API key")
    azure_region: Optional[str] = Field(default=None, description="Azure region")
    
    google_credentials_path: Optional[str] = Field(
        default=None,
        description="Path to Google Cloud credentials JSON"
    )
    
    amazon_access_key_id: Optional[str] = Field(default=None)
    amazon_secret_access_key: Optional[str] = Field(default=None)
    amazon_region: str = Field(default="us-east-1")
    
    # Voice settings
    default_voice: str = Field(default="en-US-AriaNeural", description="Default voice")
    default_rate: float = Field(default=1.0, description="Speech rate multiplier")
    default_pitch: float = Field(default=1.0, description="Speech pitch multiplier")
    
    class Config:
        env_prefix = "TTS_"


class APISettings(BaseSettings):
    """API configuration."""
    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    workers: int = Field(default=1, description="Number of workers")
    
    # Security
    api_key_enabled: bool = Field(default=False, description="Enable API key auth")
    api_keys: List[str] = Field(default_factory=list, description="Valid API keys")
    
    # Rate limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests: int = Field(default=100, description="Requests per minute")
    
    # CORS
    cors_enabled: bool = Field(default=True)
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    
    class Config:
        env_prefix = "API_"


class PatternSettings(BaseSettings):
    """Pattern configuration."""
    patterns_dir: Path = Field(
        default=Path("patterns"),
        description="Directory containing pattern YAML files"
    )
    auto_reload: bool = Field(
        default=True,
        description="Auto-reload patterns on file change"
    )
    validation_strict: bool = Field(
        default=True,
        description="Strict pattern validation"
    )
    
    @validator("patterns_dir")
    def validate_patterns_dir(cls, v: Path) -> Path:
        """Ensure patterns directory exists."""
        if not v.is_absolute():
            # Make relative to project root
            v = Path(__file__).parent.parent.parent.parent / v
        return v
    
    class Config:
        env_prefix = "PATTERN_"


class Settings(BaseSettings):
    """Main application settings."""
    
    # Application
    app_name: str = Field(default="MathTTS", description="Application name")
    app_version: str = Field(default="3.0.0", description="Application version")
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Application environment"
    )
    debug: bool = Field(default=False, description="Debug mode")
    
    # Logging
    log_level: LogLevel = Field(default=LogLevel.INFO)
    log_format: str = Field(
        default="json",
        description="Log format: json, text"
    )
    log_file: Optional[Path] = Field(default=None, description="Log file path")
    
    # Sub-configurations
    cache: CacheSettings = Field(default_factory=CacheSettings)
    tts: TTSSettings = Field(default_factory=TTSSettings)
    api: APISettings = Field(default_factory=APISettings)
    patterns: PatternSettings = Field(default_factory=PatternSettings)
    
    # Performance
    max_expression_length: int = Field(
        default=10000,
        description="Maximum LaTeX expression length"
    )
    max_nesting_depth: int = Field(
        default=20,
        description="Maximum nesting depth for expressions"
    )
    processing_timeout: float = Field(
        default=30.0,
        description="Expression processing timeout in seconds"
    )
    
    @validator("debug")
    def set_debug_from_env(cls, v: bool, values: Dict[str, Any]) -> bool:
        """Set debug mode based on environment."""
        if "environment" in values and values["environment"] == Environment.DEVELOPMENT:
            return True
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Force reload settings from environment."""
    global _settings
    _settings = Settings()
    return _settings