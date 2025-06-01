"""
Mathematical Expression entity.

This entity represents a processed mathematical expression with metadata
about its structure, complexity, and processing context.
"""

from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
import re
from enum import Enum

from ..value_objects import LaTeXExpression, MathematicalDomain, AudienceLevel, SpeechText


class ExpressionType(str, Enum):
    """Types of mathematical expressions."""
    SIMPLE = "simple"                    # Basic arithmetic: 2+2, x^2
    FRACTION = "fraction"                # Fractions: \frac{a}{b}
    INTEGRAL = "integral"                # Integrals: \int
    DERIVATIVE = "derivative"            # Derivatives: \frac{d}{dx}
    MATRIX = "matrix"                    # Matrices: \begin{matrix}
    EQUATION = "equation"                # Equations: x = y
    INEQUALITY = "inequality"            # Inequalities: x < y
    FUNCTION = "function"                # Functions: f(x), \sin(x)
    LIMIT = "limit"                      # Limits: \lim
    SUMMATION = "summation"              # Summations: \sum
    PRODUCT = "product"                  # Products: \prod
    SERIES = "series"                    # Series expressions
    COMPLEX = "complex"                  # Complex multi-part expressions


class ProcessingContext(str, Enum):
    """Context in which the expression is being processed."""
    INLINE = "inline"                    # Inline math: $x^2$
    DISPLAY = "display"                  # Display math: $$x^2$$
    EQUATION = "equation"                # Numbered equation
    THEOREM = "theorem"                  # In theorem statement
    PROOF = "proof"                      # In proof
    DEFINITION = "definition"            # In definition
    EXAMPLE = "example"                  # In example
    EXERCISE = "exercise"                # In exercise/problem
    AUTO = "auto"                        # Auto-detected context


@dataclass
class ComplexityMetrics:
    """Metrics for expression complexity analysis."""
    nesting_depth: int = 0              # Maximum nesting depth
    command_count: int = 0              # Number of LaTeX commands
    variable_count: int = 0             # Number of variables
    operator_count: int = 0             # Number of operators
    special_function_count: int = 0     # Number of special functions
    length_score: float = 0.0           # Based on string length
    readability_score: float = 0.0      # Estimated readability (0-1)
    
    @property
    def overall_score(self) -> float:
        """Calculate overall complexity score (0-10)."""
        factors = [
            min(self.nesting_depth * 0.5, 2.0),
            min(self.command_count * 0.1, 2.0),
            min(self.variable_count * 0.2, 2.0),
            min(self.operator_count * 0.15, 2.0),
            min(self.special_function_count * 0.3, 2.0),
            min(self.length_score, 1.0)
        ]
        return sum(factors)


@dataclass
class ProcessingMetadata:
    """Metadata about expression processing."""
    processed_at: datetime = field(default_factory=datetime.utcnow)
    processing_time_ms: float = 0.0
    patterns_applied: List[str] = field(default_factory=list)
    transformations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    cache_hit: bool = False
    version: str = "3.0.0"


class MathematicalExpression:
    """
    Entity representing a mathematical expression with processing metadata.
    
    This entity encapsulates all information about a mathematical expression
    including its original form, processed form, complexity analysis, and
    processing history.
    """
    
    def __init__(
        self,
        latex_expression: LaTeXExpression,
        context: ProcessingContext = ProcessingContext.AUTO,
        audience_level: Optional[AudienceLevel] = None,
        domain_hint: Optional[MathematicalDomain] = None
    ):
        """
        Initialize a mathematical expression.
        
        Args:
            latex_expression: The LaTeX expression
            context: Processing context
            audience_level: Target audience level
            domain_hint: Suggested mathematical domain
        """
        self.latex_expression = latex_expression
        self.context = context
        self.audience_level = audience_level or AudienceLevel("high_school")
        self.domain_hint = domain_hint
        
        # Processed results
        self.speech_text: Optional[SpeechText] = None
        self.detected_domain: Optional[MathematicalDomain] = None
        self.expression_type: Optional[ExpressionType] = None
        
        # Analysis results
        self.complexity_metrics: Optional[ComplexityMetrics] = None
        self.variables: Set[str] = set()
        self.functions: Set[str] = set()
        self.operators: Set[str] = set()
        self.commands: Set[str] = set()
        
        # Processing metadata
        self.metadata = ProcessingMetadata()
        
        # Perform initial analysis
        self._analyze_structure()
    
    def _analyze_structure(self) -> None:
        """Analyze the structure of the LaTeX expression."""
        content = self.latex_expression.content
        
        # Extract commands
        self.commands = set(re.findall(r'\\([a-zA-Z]+)', content))
        
        # Extract variables (single letters not in commands)
        self.variables = set(re.findall(r'(?<!\\)\b([a-zA-Z])\b', content))
        
        # Extract common operators
        operator_patterns = [
            r'\+', r'-', r'\*', r'=', r'<', r'>', r'≤', r'≥', r'≠',
            r'∈', r'∉', r'⊂', r'⊆', r'∪', r'∩', r'∧', r'∨'
        ]
        for pattern in operator_patterns:
            if re.search(pattern, content):
                self.operators.add(pattern)
        
        # Extract function names
        function_patterns = [
            r'\\sin', r'\\cos', r'\\tan', r'\\log', r'\\ln', r'\\exp',
            r'\\sqrt', r'\\lim', r'\\int', r'\\sum', r'\\prod'
        ]
        for pattern in function_patterns:
            if re.search(pattern, content):
                self.functions.add(pattern.replace('\\', ''))
        
        # Detect expression type
        self.expression_type = self._detect_expression_type()
        
        # Calculate complexity metrics
        self.complexity_metrics = self._calculate_complexity()
        
        # Detect domain if not provided
        if not self.domain_hint:
            self.detected_domain = self._detect_domain()
    
    def _detect_expression_type(self) -> ExpressionType:
        """Detect the type of mathematical expression."""
        content = self.latex_expression.content.lower()
        
        # Check for specific patterns
        if '\\frac' in content and ('\\int' in content or '\\partial' in content):
            return ExpressionType.DERIVATIVE
        elif '\\int' in content:
            return ExpressionType.INTEGRAL
        elif '\\frac' in content:
            return ExpressionType.FRACTION
        elif '\\lim' in content:
            return ExpressionType.LIMIT
        elif '\\sum' in content:
            return ExpressionType.SUMMATION
        elif '\\prod' in content:
            return ExpressionType.PRODUCT
        elif '\\begin{matrix}' in content or '\\begin{pmatrix}' in content:
            return ExpressionType.MATRIX
        elif any(func in content for func in ['sin', 'cos', 'tan', 'log', 'exp']):
            return ExpressionType.FUNCTION
        elif '=' in content:
            return ExpressionType.EQUATION
        elif any(op in content for op in ['<', '>', '≤', '≥', '\\leq', '\\geq']):
            return ExpressionType.INEQUALITY
        elif len(self.commands) > 3 or len(content) > 50:
            return ExpressionType.COMPLEX
        else:
            return ExpressionType.SIMPLE
    
    def _calculate_complexity(self) -> ComplexityMetrics:
        """Calculate complexity metrics for the expression."""
        content = self.latex_expression.content
        
        # Calculate nesting depth
        nesting_depth = 0
        current_depth = 0
        for char in content:
            if char == '{':
                current_depth += 1
                nesting_depth = max(nesting_depth, current_depth)
            elif char == '}':
                current_depth = max(0, current_depth - 1)
        
        # Count various elements
        command_count = len(self.commands)
        variable_count = len(self.variables)
        operator_count = len(self.operators)
        special_function_count = len(self.functions)
        
        # Length-based score
        length_score = min(len(content) / 100.0, 1.0)
        
        # Readability score (inverse of complexity)
        readability_factors = [
            1.0 - min(nesting_depth / 5.0, 0.8),
            1.0 - min(command_count / 10.0, 0.8),
            1.0 - min(length_score, 0.8)
        ]
        readability_score = sum(readability_factors) / len(readability_factors)
        
        return ComplexityMetrics(
            nesting_depth=nesting_depth,
            command_count=command_count,
            variable_count=variable_count,
            operator_count=operator_count,
            special_function_count=special_function_count,
            length_score=length_score,
            readability_score=readability_score
        )
    
    def _detect_domain(self) -> Optional[MathematicalDomain]:
        """Detect the mathematical domain based on content analysis."""
        content = self.latex_expression.content.lower()
        commands = [cmd.lower() for cmd in self.commands]
        
        # Domain detection patterns
        domain_patterns = {
            MathematicalDomain("calculus"): [
                'int', 'frac{d}', 'partial', 'lim', 'infty', 'derivative'
            ],
            MathematicalDomain("linear_algebra"): [
                'matrix', 'det', 'vec', 'cdot', 'times', 'mathbf'
            ],
            MathematicalDomain("complex_analysis"): [
                'complex', 'real', 'imag', 'arg', 'overline', 'mathbb{c}'
            ],
            MathematicalDomain("topology"): [
                'mathcal', 'subset', 'cup', 'cap', 'emptyset', 'overline'
            ],
            MathematicalDomain("statistics"): [
                'mathbb{p}', 'mathbb{e}', 'text{var}', 'text{cov}', 'sim', 'bar', 'hat', 'tilde', 'chi', 'sigma', 'mu'
            ],
            MathematicalDomain("algebra"): [
                'sqrt', 'frac', 'pm', 'equiv', 'pmod'
            ]
        }
        
        # Score each domain
        domain_scores = {}
        for domain, patterns in domain_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern in content or pattern in commands:
                    score += 1
            if score > 0:
                domain_scores[domain] = score
        
        # Return domain with highest score
        if domain_scores:
            return max(domain_scores.items(), key=lambda x: x[1])[0]
        
        return MathematicalDomain("algebra")  # Default fallback
    
    def set_processing_result(
        self,
        speech_text: SpeechText,
        patterns_applied: List[str],
        processing_time_ms: float,
        cache_hit: bool = False
    ) -> None:
        """Set the processing result for this expression."""
        self.speech_text = speech_text
        self.metadata.patterns_applied = patterns_applied
        self.metadata.processing_time_ms = processing_time_ms
        self.metadata.cache_hit = cache_hit
        self.metadata.processed_at = datetime.utcnow()
    
    def add_transformation(self, transformation: str) -> None:
        """Add a transformation step to the processing history."""
        self.metadata.transformations.append(transformation)
    
    def add_warning(self, warning: str) -> None:
        """Add a warning to the processing metadata."""
        self.metadata.warnings.append(warning)
    
    def get_complexity_level(self) -> str:
        """Get a human-readable complexity level."""
        if not self.complexity_metrics:
            return "unknown"
        
        score = self.complexity_metrics.overall_score
        if score < 2.0:
            return "simple"
        elif score < 4.0:
            return "moderate"
        elif score < 6.0:
            return "complex"
        else:
            return "very complex"
    
    def is_suitable_for_audience(self, audience_level: AudienceLevel) -> bool:
        """Check if expression complexity is suitable for audience level."""
        if not self.complexity_metrics:
            return True
        
        complexity_score = self.complexity_metrics.overall_score
        
        # Define complexity thresholds for each audience level
        thresholds = {
            AudienceLevel("elementary"): 1.5,
            AudienceLevel("high_school"): 5.0,
            AudienceLevel("undergraduate"): 7.0,
            AudienceLevel("graduate"): 8.5,
            AudienceLevel("research"): 10.0
        }
        
        return complexity_score <= thresholds.get(audience_level, 10.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert expression to dictionary representation."""
        return {
            "latex": self.latex_expression.content,
            "context": self.context.value,
            "audience_level": self.audience_level.value,
            "domain_hint": self.domain_hint.value if self.domain_hint else None,
            "detected_domain": self.detected_domain.value if self.detected_domain else None,
            "expression_type": self.expression_type.value if self.expression_type else None,
            "complexity_score": self.complexity_metrics.overall_score if self.complexity_metrics else None,
            "complexity_level": self.get_complexity_level(),
            "variables": list(self.variables),
            "functions": list(self.functions),
            "operators": list(self.operators),
            "commands": list(self.commands),
            "speech_text": self.speech_text.plain_text if self.speech_text else None,
            "processing_time_ms": self.metadata.processing_time_ms,
            "patterns_applied": self.metadata.patterns_applied,
            "cache_hit": self.metadata.cache_hit,
            "processed_at": self.metadata.processed_at.isoformat()
        }
    
    def __repr__(self) -> str:
        """String representation of the expression."""
        return f"MathematicalExpression('{self.latex_expression.content}', {self.expression_type})"
    
    def __eq__(self, other) -> bool:
        """Equality comparison based on LaTeX content."""
        if not isinstance(other, MathematicalExpression):
            return False
        return self.latex_expression == other.latex_expression
    
    def __hash__(self) -> int:
        """Hash based on LaTeX content."""
        return hash(self.latex_expression)