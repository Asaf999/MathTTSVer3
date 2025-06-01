"""Logging infrastructure for MathTTS v3."""

try:
    from .logger import (
        Logger,
        get_logger,
        init_logger,
        correlation_id,
        setup_logging
    )
except ImportError:
    # Fallback to simple logger for testing
    from .simple_logger import get_logger, SimpleLogger as Logger
    init_logger = lambda: None
    correlation_id = lambda: "test-correlation-id"
    setup_logging = lambda: None

__all__ = [
    "Logger",
    "get_logger",
    "init_logger",
    "correlation_id",
    "setup_logging"
]