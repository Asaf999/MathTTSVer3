"""
Domain exceptions for MathTTS v3.

This module defines all domain-specific exceptions that can occur
during mathematical expression processing.
"""

from typing import Any, Optional, Dict


class DomainException(Exception):
    """Base domain exception."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ) -> None:
        """Initialize domain exception."""
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.error_code = error_code or self.__class__.__name__
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary representation."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class ValidationError(DomainException):
    """Validation error."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None) -> None:
        """Initialize validation error."""
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        super().__init__(message, details)


class LaTeXValidationError(ValidationError):
    """LaTeX expression validation error."""
    
    def __init__(
        self,
        message: str,
        expression: Optional[str] = None,
        position: Optional[int] = None
    ) -> None:
        """Initialize LaTeX validation error."""
        details = {}
        if expression:
            details["expression"] = expression[:100]  # Truncate for security
        if position is not None:
            details["position"] = position
        super().__init__(message, details=details)


class PatternError(DomainException):
    """Pattern-related error."""
    
    def __init__(self, message: str, pattern_id: Optional[str] = None) -> None:
        """Initialize pattern error."""
        details = {}
        if pattern_id:
            details["pattern_id"] = pattern_id
        super().__init__(message, details)


class PatternValidationError(PatternError):
    """Pattern validation error."""
    
    def __init__(
        self,
        message: str,
        pattern_id: Optional[str] = None,
        pattern: Optional[str] = None
    ) -> None:
        """Initialize pattern validation error."""
        details = {}
        if pattern_id:
            details["pattern_id"] = pattern_id
        if pattern:
            details["pattern"] = pattern[:100]  # Truncate for security
        super().__init__(message, details)


class ProcessingError(DomainException):
    """Expression processing error."""
    
    def __init__(
        self, 
        message: str, 
        expression: Optional[str] = None,
        stage: Optional[str] = None
    ) -> None:
        """Initialize processing error."""
        details = {}
        if expression:
            details["expression"] = expression[:100]  # Truncate for security
        if stage:
            details["stage"] = stage
        super().__init__(message, details)


class ComplexityError(ProcessingError):
    """Expression complexity error."""
    
    def __init__(
        self,
        message: str,
        expression: Optional[str] = None,
        complexity_score: Optional[float] = None,
        max_allowed: Optional[float] = None
    ) -> None:
        """Initialize complexity error."""
        details = {}
        if expression:
            details["expression"] = expression[:100]
        if complexity_score is not None:
            details["complexity_score"] = complexity_score
        if max_allowed is not None:
            details["max_allowed"] = max_allowed
        super().__init__(message, details)


class TimeoutError(ProcessingError):
    """Processing timeout error."""
    
    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        elapsed_seconds: Optional[float] = None
    ) -> None:
        """Initialize timeout error."""
        details = {}
        if timeout_seconds is not None:
            details["timeout_seconds"] = timeout_seconds
        if elapsed_seconds is not None:
            details["elapsed_seconds"] = elapsed_seconds
        super().__init__(message, details)


class ConfigurationError(DomainException):
    """Configuration error."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None
    ) -> None:
        """Initialize configuration error."""
        details = {}
        if config_key:
            details["config_key"] = config_key
        if config_value is not None:
            details["config_value"] = str(config_value)
        super().__init__(message, details)


class ResourceNotFoundError(DomainException):
    """Resource not found error."""
    
    def __init__(self, resource_type: str, resource_id: str) -> None:
        """Initialize resource not found error."""
        message = f"{resource_type} not found: {resource_id}"
        super().__init__(message, {"type": resource_type, "id": resource_id})


class SecurityError(DomainException):
    """Security-related error."""
    
    def __init__(
        self,
        message: str,
        threat_type: Optional[str] = None,
        input_content: Optional[str] = None
    ) -> None:
        """Initialize security error."""
        details = {}
        if threat_type:
            details["threat_type"] = threat_type
        if input_content:
            details["input_length"] = len(input_content)
            # Don't store the actual content for security
        super().__init__(message, details)


class RateLimitError(SecurityError):
    """Rate limiting error."""
    
    def __init__(
        self,
        message: str,
        limit: Optional[int] = None,
        window_seconds: Optional[int] = None,
        retry_after: Optional[int] = None
    ) -> None:
        """Initialize rate limit error."""
        details = {}
        if limit is not None:
            details["limit"] = limit
        if window_seconds is not None:
            details["window_seconds"] = window_seconds
        if retry_after is not None:
            details["retry_after"] = retry_after
        super().__init__(message, details)


class ExternalServiceError(DomainException):
    """External service error."""
    pass


class TTSProviderError(ExternalServiceError):
    """TTS provider error."""
    
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        status_code: Optional[int] = None
    ) -> None:
        """Initialize TTS provider error."""
        details = {}
        if provider:
            details["provider"] = provider
        if status_code is not None:
            details["status_code"] = status_code
        super().__init__(message, details)


class CacheError(ExternalServiceError):
    """Cache operation error."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        key: Optional[str] = None
    ) -> None:
        """Initialize cache error."""
        details = {}
        if operation:
            details["operation"] = operation
        if key:
            details["key"] = key[:50]  # Truncate for logs
        super().__init__(message, details)


def handle_exception(
    exception: Exception,
    context: Optional[str] = None,
    fallback_message: str = "An unexpected error occurred"
) -> DomainException:
    """
    Convert any exception to a DomainException.
    
    Args:
        exception: The original exception
        context: Context where the exception occurred
        fallback_message: Fallback message if exception has no message
        
    Returns:
        DomainException instance
    """
    if isinstance(exception, DomainException):
        return exception
    
    message = str(exception) or fallback_message
    if context:
        message = f"{context}: {message}"
    
    details = {
        "original_exception": exception.__class__.__name__,
        "original_message": str(exception)
    }
    
    if context:
        details["context"] = context
    
    return DomainException(message, details=details)


def is_recoverable_error(exception: Exception) -> bool:
    """
    Determine if an exception is recoverable.
    
    Args:
        exception: Exception to check
        
    Returns:
        True if the error is recoverable, False otherwise
    """
    # Non-recoverable errors
    non_recoverable = (
        ValidationError,
        ConfigurationError,
        SecurityError
    )
    
    if isinstance(exception, non_recoverable):
        return False
    
    # Potentially recoverable errors
    recoverable = (
        TTSProviderError,
        CacheError,
        TimeoutError
    )
    
    return isinstance(exception, recoverable)