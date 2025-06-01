"""Simple logger implementation for testing without external dependencies."""

import logging
import sys
from typing import Any, Dict, Optional


class SimpleLogger:
    """Simple logger that doesn't require structlog."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Add console handler if not already present
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        extra_info = " - " + str(kwargs) if kwargs else ""
        self.logger.info(f"{message}{extra_info}")
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        extra_info = " - " + str(kwargs) if kwargs else ""
        self.logger.warning(f"{message}{extra_info}")
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        extra_info = " - " + str(kwargs) if kwargs else ""
        self.logger.error(f"{message}{extra_info}")
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        extra_info = " - " + str(kwargs) if kwargs else ""
        self.logger.debug(f"{message}{extra_info}")
    
    def cache_hit(self, key: str) -> None:
        """Log cache hit."""
        self.info(f"Cache hit for key: {key}")
    
    def cache_miss(self, key: str) -> None:
        """Log cache miss."""
        self.info(f"Cache miss for key: {key}")
    
    def expression_processed(self, expression: str, output: str, 
                           duration_ms: float, cached: bool) -> None:
        """Log expression processing."""
        self.info(
            "Expression processed",
            expression=expression[:50] + "..." if len(expression) > 50 else expression,
            output=output[:50] + "..." if len(output) > 50 else output,
            duration_ms=f"{duration_ms:.2f}",
            cached=cached
        )


def get_logger(name: str) -> SimpleLogger:
    """Get a logger instance."""
    return SimpleLogger(name)