"""
Structured logging infrastructure for MathTTS v3.

This module provides centralized logging with support for:
- Structured logging with context
- Multiple output formats (JSON, text)
- Performance tracking
- Error tracking with stack traces
- Correlation IDs for request tracing
"""

import logging
import sys
from typing import Any, Dict, Optional, Union
from pathlib import Path
from datetime import datetime
from contextvars import ContextVar
import traceback
import json

import structlog
from structlog.processors import CallsiteParameter
from structlog.types import EventDict, WrappedLogger

from ..config import get_settings, LogLevel


# Context variable for request correlation
correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def add_correlation_id(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add correlation ID to log events."""
    if cid := correlation_id.get():
        event_dict["correlation_id"] = cid
    return event_dict


def add_timestamp(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add ISO timestamp to log events."""
    event_dict["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return event_dict


def add_app_context(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add application context to log events."""
    settings = get_settings()
    event_dict["app"] = {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment.value
    }
    return event_dict


def extract_error_info(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Extract detailed error information."""
    if "exception" in event_dict:
        exc_info = event_dict.pop("exception")
        if exc_info:
            exc_type, exc_value, exc_tb = exc_info
            event_dict["error"] = {
                "type": exc_type.__name__,
                "message": str(exc_value),
                "traceback": traceback.format_tb(exc_tb)
            }
    return event_dict


def setup_logging() -> structlog.BoundLogger:
    """
    Configure and return the application logger.
    
    Returns:
        Configured structlog logger instance
    """
    settings = get_settings()
    
    # Configure Python's logging
    log_level = getattr(logging, settings.log_level.value)
    
    # Base configuration
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        stream=sys.stdout
    )
    
    # Configure processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        add_timestamp,
        add_app_context,
        add_correlation_id,
        extract_error_info,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Add callsite information in debug mode
    if settings.debug:
        processors.insert(
            0,
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    CallsiteParameter.FILENAME,
                    CallsiteParameter.LINENO,
                    CallsiteParameter.FUNC_NAME,
                ]
            )
        )
    
    # Choose renderer based on format
    if settings.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Set up file logging if configured
    if settings.log_file:
        file_handler = logging.FileHandler(settings.log_file)
        file_handler.setLevel(log_level)
        logging.getLogger().addHandler(file_handler)
    
    return structlog.get_logger()


class Logger:
    """
    Application logger with domain-specific methods.
    
    This class wraps structlog and provides convenient methods
    for common logging scenarios in the MathTTS application.
    """
    
    def __init__(self, name: Optional[str] = None):
        """Initialize logger with optional name."""
        self._logger = structlog.get_logger(name) if name else setup_logging()
    
    def bind(self, **kwargs: Any) -> "Logger":
        """
        Bind context variables to the logger.
        
        Args:
            **kwargs: Context variables to bind
            
        Returns:
            New logger instance with bound context
        """
        new_logger = Logger.__new__(Logger)
        new_logger._logger = self._logger.bind(**kwargs)
        return new_logger
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._logger.info(message, **kwargs)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._logger.debug(message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self._logger.error(message, **kwargs)
    
    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception with traceback."""
        self._logger.exception(message, **kwargs)
    
    def expression_processed(
        self,
        expression: str,
        output: str,
        duration_ms: float,
        cached: bool = False,
        **kwargs: Any
    ) -> None:
        """Log successful expression processing."""
        self._logger.info(
            "Expression processed",
            expression=expression[:100] + "..." if len(expression) > 100 else expression,
            output_length=len(output),
            duration_ms=duration_ms,
            cached=cached,
            **kwargs
        )
    
    def pattern_matched(
        self,
        pattern_id: str,
        pattern: str,
        input_text: str,
        output: str,
        **kwargs: Any
    ) -> None:
        """Log pattern match."""
        self._logger.debug(
            "Pattern matched",
            pattern_id=pattern_id,
            pattern=pattern,
            input_text=input_text[:50] + "..." if len(input_text) > 50 else input_text,
            output=output[:50] + "..." if len(output) > 50 else output,
            **kwargs
        )
    
    def cache_hit(self, key: str, **kwargs: Any) -> None:
        """Log cache hit."""
        self._logger.debug("Cache hit", key=key[:50], **kwargs)
    
    def cache_miss(self, key: str, **kwargs: Any) -> None:
        """Log cache miss."""
        self._logger.debug("Cache miss", key=key[:50], **kwargs)
    
    def tts_request(
        self,
        provider: str,
        text: str,
        voice: str,
        duration_ms: float,
        **kwargs: Any
    ) -> None:
        """Log TTS provider request."""
        self._logger.info(
            "TTS request completed",
            provider=provider,
            text_length=len(text),
            voice=voice,
            duration_ms=duration_ms,
            **kwargs
        )
    
    def api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        **kwargs: Any
    ) -> None:
        """Log API request."""
        self._logger.info(
            "API request",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            **kwargs
        )
    
    def performance_warning(
        self,
        operation: str,
        duration_ms: float,
        threshold_ms: float,
        **kwargs: Any
    ) -> None:
        """Log performance warning."""
        self._logger.warning(
            "Performance threshold exceeded",
            operation=operation,
            duration_ms=duration_ms,
            threshold_ms=threshold_ms,
            exceeded_by_ms=duration_ms - threshold_ms,
            **kwargs
        )


# Global logger instance
_logger: Optional[Logger] = None


def get_logger(name: Optional[str] = None) -> Logger:
    """
    Get logger instance.
    
    Args:
        name: Optional logger name
        
    Returns:
        Logger instance
    """
    global _logger
    if _logger is None or name is not None:
        return Logger(name)
    return _logger


def init_logger() -> Logger:
    """Initialize and return the global logger."""
    global _logger
    _logger = Logger()
    return _logger