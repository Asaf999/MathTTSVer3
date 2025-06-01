"""Enhanced structured logging with correlation IDs and performance tracking."""

import logging
import time
import json
import sys
from typing import Any, Dict, Optional, Union, Callable
from contextvars import ContextVar
from datetime import datetime
from functools import wraps
import traceback
import uuid

import structlog
from structlog.processors import CallsiteParameter
from structlog.types import EventDict, WrappedLogger


# Context variables for request tracking
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


class StructuredLogger:
    """Enhanced structured logger with context management."""
    
    def __init__(self, name: str):
        """Initialize logger."""
        self.logger = structlog.get_logger(name)
        self._timers: Dict[str, float] = {}
    
    def bind(self, **kwargs) -> 'StructuredLogger':
        """Bind context to logger."""
        self.logger = self.logger.bind(**kwargs)
        return self
    
    def unbind(self, *keys) -> 'StructuredLogger':
        """Unbind context from logger."""
        self.logger = self.logger.unbind(*keys)
        return self
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **self._enrich_context(kwargs))
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **self._enrich_context(kwargs))
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **self._enrich_context(kwargs))
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error message."""
        if error:
            kwargs["error_type"] = type(error).__name__
            kwargs["error_message"] = str(error)
            kwargs["error_traceback"] = traceback.format_exc()
        self.logger.error(message, **self._enrich_context(kwargs))
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, **self._enrich_context(kwargs))
    
    def api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        client_host: Optional[str] = None,
        **kwargs
    ):
        """Log API request."""
        self.info(
            "API request",
            http_method=method,
            http_path=path,
            http_status=status_code,
            duration_ms=duration_ms,
            client_host=client_host,
            **kwargs
        )
    
    def performance(
        self,
        operation: str,
        duration_ms: float,
        items_processed: Optional[int] = None,
        **kwargs
    ):
        """Log performance metrics."""
        data = {
            "operation": operation,
            "duration_ms": duration_ms,
            "performance_metric": True
        }
        
        if items_processed:
            data["items_processed"] = items_processed
            data["items_per_second"] = (items_processed / duration_ms) * 1000
        
        self.info("Performance metric", **{**data, **kwargs})
    
    def start_timer(self, name: str):
        """Start a named timer."""
        self._timers[name] = time.time()
    
    def stop_timer(self, name: str) -> Optional[float]:
        """Stop a named timer and return duration in milliseconds."""
        if name not in self._timers:
            return None
        
        start_time = self._timers.pop(name)
        duration_ms = (time.time() - start_time) * 1000
        return duration_ms
    
    def timed_operation(self, operation_name: str):
        """Decorator to time operations."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    self.performance(operation_name, duration_ms, success=True)
                    return result
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    self.performance(operation_name, duration_ms, success=False, error=str(e))
                    raise
            
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    self.performance(operation_name, duration_ms, success=True)
                    return result
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    self.performance(operation_name, duration_ms, success=False, error=str(e))
                    raise
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return wrapper
        
        return decorator
    
    def _enrich_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich context with standard fields."""
        enriched = context.copy()
        
        # Add correlation IDs
        if correlation_id := correlation_id_var.get():
            enriched["correlation_id"] = correlation_id
        
        if request_id := request_id_var.get():
            enriched["request_id"] = request_id
        
        if user_id := user_id_var.get():
            enriched["user_id"] = user_id
        
        return enriched


# Structured logging processors
def add_correlation_ids(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add correlation IDs to log events."""
    if correlation_id := correlation_id_var.get():
        event_dict["correlation_id"] = correlation_id
    
    if request_id := request_id_var.get():
        event_dict["request_id"] = request_id
    
    if user_id := user_id_var.get():
        event_dict["user_id"] = user_id
    
    return event_dict


def add_timestamp_iso(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add ISO timestamp."""
    event_dict["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return event_dict


def sanitize_sensitive_data(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Sanitize sensitive data from logs."""
    sensitive_keys = {
        "password", "token", "api_key", "secret", "authorization",
        "credit_card", "ssn", "email", "phone"
    }
    
    def sanitize_dict(d: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = {}
        for key, value in d.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    sanitize_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized
    
    return sanitize_dict(event_dict)


def configure_structured_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    enable_colors: bool = False
) -> None:
    """Configure structured logging for the application."""
    import asyncio
    
    # Configure Python's logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(message)s",
        stream=sys.stdout
    )
    
    # Processors for structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        add_correlation_ids,
        add_timestamp_iso,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        sanitize_sensitive_data,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Add appropriate renderer
    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        if enable_colors and sys.stderr.isatty():
            processors.append(structlog.dev.ConsoleRenderer(colors=True))
        else:
            processors.append(structlog.dev.ConsoleRenderer(colors=False))
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


# Logger cache
_loggers: Dict[str, StructuredLogger] = {}


def get_structured_logger(name: str) -> StructuredLogger:
    """Get or create a structured logger."""
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name)
    return _loggers[name]


# Context managers for correlation IDs
class CorrelationContext:
    """Context manager for correlation IDs."""
    
    def __init__(
        self,
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Initialize correlation context."""
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.request_id = request_id
        self.user_id = user_id
        self._tokens = []
    
    def __enter__(self):
        """Enter context."""
        self._tokens.append(correlation_id_var.set(self.correlation_id))
        
        if self.request_id:
            self._tokens.append(request_id_var.set(self.request_id))
        
        if self.user_id:
            self._tokens.append(user_id_var.set(self.user_id))
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        for token in self._tokens:
            token.var.reset(token)


# Initialize logging on module import
configure_structured_logging()