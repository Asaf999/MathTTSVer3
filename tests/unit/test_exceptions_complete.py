"""
Test all exception classes.
"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.domain.exceptions import *


class TestAllExceptions:
    """Test all exception classes."""
    
    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Invalid value", field="test_field")
        assert str(error) == "Invalid value"
        assert error.field == "test_field"
    
    def test_latex_validation_error(self):
        """Test LaTeXValidationError."""
        error = LaTeXValidationError("Invalid LaTeX", "\\invalid", position=5)
        assert "Invalid LaTeX" in str(error)
        assert error.latex_content == "\\invalid"
        assert error.position == 5
    
    def test_security_error(self):
        """Test SecurityError."""
        error = SecurityError(
            "Security threat",
            threat_type="injection",
            input_content="malicious"
        )
        assert "Security threat" in str(error)
        assert error.threat_type == "injection"
        assert error.input_content == "malicious"
    
    def test_domain_error(self):
        """Test DomainError."""
        error = DomainError("Domain error")
        assert str(error) == "Domain error"
    
    def test_application_error(self):
        """Test ApplicationError."""
        error = ApplicationError("App error", code="APP001")
        assert str(error) == "App error"
        assert error.code == "APP001"
    
    def test_infrastructure_error(self):
        """Test InfrastructureError."""
        error = InfrastructureError("Infra error", details={"service": "database"})
        assert str(error) == "Infra error"
        assert error.details["service"] == "database"
    
    def test_repository_errors(self):
        """Test repository errors."""
        from src.domain.interfaces.pattern_repository import (
            RepositoryError, PatternNotFoundError, DuplicatePatternError
        )
        
        # Base error
        error = RepositoryError("Repo error")
        assert str(error) == "Repo error"
        
        # Not found
        error = PatternNotFoundError("pattern-1")
        assert "pattern-1" in str(error)
        
        # Duplicate
        error = DuplicatePatternError("pattern-1")
        assert "pattern-1" in str(error)
