"""Value objects for the domain layer."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, ClassVar, Optional, Set, List

from .exceptions import ValidationError, LaTeXValidationError, SecurityError


@dataclass(frozen=True)
class LaTeXExpression:
    """Immutable LaTeX expression value object with comprehensive validation."""
    
    content: str
    _MAX_LENGTH: ClassVar[int] = 10000
    _MAX_NESTING: ClassVar[int] = 20
    
    # Whitelist of allowed LaTeX commands for security
    _ALLOWED_COMMANDS: ClassVar[Set[str]] = {
        # Basic math
        'frac', 'sqrt', 'sin', 'cos', 'tan', 'log', 'ln', 'exp', 'lim', 'sum', 'prod', 'int',
        # Greek letters
        'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 'theta', 'iota', 'kappa',
        'lambda', 'mu', 'nu', 'xi', 'pi', 'rho', 'sigma', 'tau', 'upsilon', 'phi', 'chi', 'psi', 'omega',
        # Uppercase Greek
        'Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon', 'Zeta', 'Eta', 'Theta', 'Iota', 'Kappa',
        'Lambda', 'Mu', 'Nu', 'Xi', 'Pi', 'Rho', 'Sigma', 'Tau', 'Upsilon', 'Phi', 'Chi', 'Psi', 'Omega',
        # Operators
        'cdot', 'times', 'div', 'pm', 'mp', 'leq', 'geq', 'neq', 'approx', 'equiv', 'subset', 'supset',
        'subseteq', 'supseteq', 'cup', 'cap', 'emptyset', 'in', 'notin', 'forall', 'exists',
        # Formatting
        'mathbf', 'mathit', 'mathbb', 'mathcal', 'mathfrak', 'text', 'textbf', 'textit',
        'overline', 'underline', 'hat', 'tilde', 'bar', 'vec', 'dot', 'ddot',
        # Delimiters
        'left', 'right', 'big', 'bigg', 'Big', 'Bigg',
        # Environments (basic)
        'begin', 'end', 'matrix', 'pmatrix', 'bmatrix', 'vmatrix', 'Vmatrix',
        # Calculus
        'partial', 'nabla', 'infty', 'lim', 'sup', 'inf',
        # Other common
        'to', 'rightarrow', 'leftarrow', 'leftrightarrow', 'mapsto'
    }
    
    # Dangerous patterns that should be rejected
    _DANGEROUS_PATTERNS: ClassVar[List[str]] = [
        r'\\input\b',           # File inclusion
        r'\\include\b',         # File inclusion
        r'\\write\b',           # File writing
        r'\\immediate\b',       # Immediate execution
        r'\\expandafter\b',     # Macro expansion
        r'\\csname\b',          # Command name construction
        r'\\def\b',             # Macro definition
        r'\\gdef\b',            # Global macro definition
        r'\\edef\b',            # Expanded definition
        r'\\xdef\b',            # Expanded global definition
        r'\\catcode\b',         # Category code changes
        r'\\uppercase\b',       # Case conversion (can be exploited)
        r'\\lowercase\b',       # Case conversion (can be exploited)
    ]
    
    def __post_init__(self) -> None:
        """Validate expression after initialization."""
        self._validate_basic()
        self._validate_syntax()
        self._validate_nesting()
        self._validate_security()
        self._validate_commands()
    
    def _validate_basic(self) -> None:
        """Validate basic requirements."""
        if not self.content:
            raise ValueError("LaTeX expression cannot be empty")
        
        if not isinstance(self.content, str):
            raise ValueError("LaTeX expression must be a string")
            
        if len(self.content) > self._MAX_LENGTH:
            raise ValueError(
                f"Expression exceeds maximum length of {self._MAX_LENGTH}"
            )
        
        # Check for null bytes and other problematic characters
        if '\x00' in self.content:
            raise ValueError(
                "Null bytes not allowed in LaTeX expressions"
            )
    
    def _validate_syntax(self) -> None:
        """Validate basic LaTeX syntax."""
        # Check balanced braces
        if self.content.count("{") != self.content.count("}"):
            raise LaTeXValidationError("Unbalanced braces in expression", self.content)
            
        # Check balanced brackets
        if self.content.count("[") != self.content.count("]"):
            raise LaTeXValidationError("Unbalanced brackets in expression", self.content)
            
        # Check balanced parentheses
        if self.content.count("(") != self.content.count(")"):
            raise LaTeXValidationError("Unbalanced parentheses in expression", self.content)
        
        # Validate proper nesting of braces
        self._validate_brace_nesting()
    
    def _validate_brace_nesting(self) -> None:
        """Validate proper nesting of braces."""
        stack = []
        for i, char in enumerate(self.content):
            if char == '{':
                stack.append(i)
            elif char == '}':
                if not stack:
                    raise LaTeXValidationError(
                        "Closing brace without matching opening brace",
                        self.content,
                        position=i
                    )
                stack.pop()
        
        if stack:
            raise LaTeXValidationError(
                "Opening brace without matching closing brace",
                self.content,
                position=stack[0]
            )
    
    def _validate_nesting(self) -> None:
        """Validate nesting depth."""
        max_depth = 0
        current_depth = 0
        
        for i, char in enumerate(self.content):
            if char == "{":
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == "}":
                current_depth -= 1
                
        if max_depth > self._MAX_NESTING:
            raise LaTeXValidationError(
                f"Expression too deeply nested (depth: {max_depth}, max: {self._MAX_NESTING})",
                self.content
            )
    
    def _validate_security(self) -> None:
        """Validate against security threats."""
        # Check for dangerous patterns
        for pattern in self._DANGEROUS_PATTERNS:
            if re.search(pattern, self.content, re.IGNORECASE):
                raise SecurityError(
                    f"Potentially dangerous LaTeX command detected: {pattern}",
                    threat_type="dangerous_command",
                    input_content=self.content
                )
        
        # Check for excessive repetition (potential DoS)
        self._check_repetition_attacks()
        
        # Check for excessively long commands
        self._check_command_lengths()
    
    def _check_repetition_attacks(self) -> None:
        """Check for potential repetition-based DoS attacks."""
        # Check for excessive repetition of characters
        for char in ['{', '}', '\\', '$']:
            count = self.content.count(char)
            if count > 1000:  # Reasonable threshold
                raise SecurityError(
                    f"Excessive repetition of character '{char}' ({count} times)",
                    threat_type="repetition_attack",
                    input_content=self.content
                )
    
    def _check_command_lengths(self) -> None:
        """Check for excessively long command names."""
        commands = re.findall(r'\\([a-zA-Z]+)', self.content)
        for cmd in commands:
            if len(cmd) > 50:  # Reasonable threshold
                raise SecurityError(
                    f"Excessively long command name: \\{cmd}",
                    threat_type="long_command",
                    input_content=self.content
                )
    
    def _validate_commands(self) -> None:
        """Validate LaTeX commands against whitelist."""
        commands = re.findall(r'\\([a-zA-Z]+)', self.content)
        
        for cmd in commands:
            if cmd not in self._ALLOWED_COMMANDS:
                raise SecurityError(
                    f"Disallowed LaTeX command: \\{cmd}",
                    threat_type="disallowed_command",
                    input_content=self.content
                )
    
    @property
    def commands(self) -> Set[str]:
        """Extract all LaTeX commands from the expression."""
        return set(re.findall(r'\\([a-zA-Z]+)', self.content))
    
    @property
    def variables(self) -> Set[str]:
        """Extract all single-letter variables."""
        # Find single letters that are not part of commands
        variables = set()
        i = 0
        while i < len(self.content):
            char = self.content[i]
            # Skip LaTeX commands
            if char == '\\':
                # Skip to end of command
                i += 1
                while i < len(self.content) and self.content[i].isalpha():
                    i += 1
                continue
            # Check for single letter variables
            elif char.isalpha():
                # Make sure it's not part of a longer word
                if (i == 0 or not self.content[i-1].isalpha()) and \
                   (i == len(self.content)-1 or not self.content[i+1].isalpha()):
                    variables.add(char)
            i += 1
        return variables
    
    @property
    def complexity_score(self) -> float:
        """Calculate a complexity score for the expression."""
        score = 0.0
        
        # Base score from length
        score += len(self.content) * 0.01
        
        # Command complexity
        score += len(self.commands) * 0.5
        
        # Nesting complexity
        max_depth = 0
        current_depth = 0
        for char in self.content:
            if char == '{':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == '}':
                current_depth -= 1
        score += max_depth * 0.3
        
        # Special function complexity
        special_functions = {'int', 'sum', 'prod', 'lim', 'frac'}
        score += len(self.commands.intersection(special_functions)) * 0.8
        
        return min(score, 10.0)  # Cap at 10
    
    def sanitize(self) -> str:
        """Return a sanitized version of the expression."""
        # Remove comments
        sanitized = re.sub(r'%.*$', '', self.content, flags=re.MULTILINE)
        
        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized
    
    def __str__(self) -> str:
        """String representation."""
        if len(self.content) > 50:
            return f"{self.content[:47]}..."
        return self.content


@dataclass(frozen=True)
class SpeechText:
    """Immutable speech text value object."""
    
    value: str
    ssml: Optional[str] = None
    pronunciation_hints: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate speech text."""
        if not self.value:
            raise ValidationError("Speech text cannot be empty")
    
    def with_ssml(self, ssml: str) -> SpeechText:
        """Create new instance with SSML."""
        return SpeechText(
            value=self.value,
            ssml=ssml,
            pronunciation_hints=self.pronunciation_hints
        )
    
    def with_hint(self, key: str, value: Any) -> SpeechText:
        """Create new instance with additional pronunciation hint."""
        hints = self.pronunciation_hints.copy()
        hints[key] = value
        return SpeechText(
            value=self.value,
            ssml=self.ssml,
            pronunciation_hints=hints
        )


@dataclass(frozen=True)
class PatternPriority:
    """Pattern priority value object."""
    
    value: int
    _MIN: ClassVar[int] = 0
    _MAX: ClassVar[int] = 2000
    
    # Priority levels
    CRITICAL: ClassVar[int] = 1500
    HIGH: ClassVar[int] = 1000
    MEDIUM: ClassVar[int] = 500
    LOW: ClassVar[int] = 250
    
    def __post_init__(self) -> None:
        """Validate priority value."""
        if not self._MIN <= self.value <= self._MAX:
            raise ValidationError(
                f"Priority must be between {self._MIN} and {self._MAX}"
            )
    
    def __lt__(self, other: PatternPriority) -> bool:
        """Compare priorities."""
        return self.value < other.value
    
    def __le__(self, other: PatternPriority) -> bool:
        """Compare priorities."""
        return self.value <= other.value
    
    @classmethod
    def critical(cls) -> PatternPriority:
        """Create critical priority."""
        return cls(cls.CRITICAL)
    
    @classmethod
    def high(cls) -> PatternPriority:
        """Create high priority."""
        return cls(cls.HIGH)
    
    @classmethod
    def medium(cls) -> PatternPriority:
        """Create medium priority."""
        return cls(cls.MEDIUM)
    
    @classmethod
    def low(cls) -> PatternPriority:
        """Create low priority."""
        return cls(cls.LOW)


@dataclass(frozen=True)
class AudienceLevel:
    """Audience level value object."""
    
    value: str
    _VALID_LEVELS: ClassVar[set[str]] = {
        "elementary",
        "high_school", 
        "undergraduate",
        "graduate",
        "research"
    }
    
    def __post_init__(self) -> None:
        """Validate audience level."""
        if self.value not in self._VALID_LEVELS:
            raise ValidationError(
                f"Invalid audience level: {self.value}. "
                f"Must be one of: {', '.join(self._VALID_LEVELS)}"
            )
    
    @property
    def is_advanced(self) -> bool:
        """Check if audience level is advanced."""
        return self.value in {"graduate", "research"}
    
    @property
    def is_basic(self) -> bool:
        """Check if audience level is basic."""
        return self.value in {"elementary", "high_school"}


@dataclass(frozen=True)
class MathematicalDomain:
    """Mathematical domain value object."""
    
    value: str
    _VALID_DOMAINS: ClassVar[set[str]] = {
        "general",
        "algebra", 
        "calculus",
        "linear_algebra",
        "statistics",
        "set_theory",
        "logic",
        "number_theory",
        "complex_analysis",
        "topology",
        "real_analysis",
        "combinatorics",
        "differential_equations"
    }
    
    def __post_init__(self) -> None:
        """Validate domain."""
        if self.value not in self._VALID_DOMAINS:
            raise ValidationError(
                f"Invalid mathematical domain: {self.value}"
            )
    
    @classmethod
    def general(cls) -> MathematicalDomain:
        """Create general domain."""
        return cls("general")
    
    def is_analysis_related(self) -> bool:
        """Check if domain is analysis-related."""
        return self.value in {
            "calculus", 
            "real_analysis", 
            "complex_analysis",
            "differential_equations"
        }