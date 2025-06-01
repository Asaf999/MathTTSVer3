"""Mathematical expression entity."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from src.domain.exceptions import ProcessingError
from src.domain.value_objects import (
    AudienceLevel,
    LaTeXExpression,
    MathematicalDomain,
    SpeechText,
)


@dataclass
class ProcessingMetadata:
    """Metadata about expression processing."""
    
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    processing_stages: list[str] = field(default_factory=list)
    patterns_applied: list[str] = field(default_factory=list)
    cache_hit: bool = False
    error_occurred: bool = False
    error_message: Optional[str] = None
    
    def add_stage(self, stage: str) -> None:
        """Add processing stage."""
        self.processing_stages.append(f"{stage}:{datetime.utcnow().isoformat()}")
    
    def add_pattern(self, pattern_id: str) -> None:
        """Add applied pattern."""
        self.patterns_applied.append(pattern_id)
    
    def finish(self) -> None:
        """Mark processing as finished."""
        self.end_time = datetime.utcnow()
    
    @property
    def processing_time_ms(self) -> float:
        """Get processing time in milliseconds."""
        if self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() * 1000
        return 0.0


@dataclass
class MathematicalExpression:
    """Mathematical expression entity."""
    
    latex: LaTeXExpression
    audience_level: AudienceLevel = field(default_factory=lambda: AudienceLevel("undergraduate"))
    detected_domain: Optional[MathematicalDomain] = None
    context: dict[str, Any] = field(default_factory=dict)
    metadata: ProcessingMetadata = field(default_factory=ProcessingMetadata)
    
    # Processing results
    speech_text: Optional[SpeechText] = None
    intermediate_results: list[str] = field(default_factory=list)
    confidence_score: float = 1.0
    
    def __post_init__(self) -> None:
        """Initialize expression."""
        if not self.detected_domain:
            self.detected_domain = self._detect_domain()
    
    def _detect_domain(self) -> MathematicalDomain:
        """Detect mathematical domain from expression."""
        expr_lower = self.latex.value.lower()
        
        # Domain detection rules
        domain_indicators = {
            MathematicalDomain("calculus"): [
                r"\\int", r"\\frac\{d", r"\\partial", r"\\lim",
                r"dx", r"dy", r"dt", r"\\nabla"
            ],
            MathematicalDomain("linear_algebra"): [
                r"\\matrix", r"\\pmatrix", r"\\bmatrix", r"\\det",
                r"\\rank", r"\\ker", r"\\dim", r"\\transpose"
            ],
            MathematicalDomain("statistics"): [
                r"\\sum", r"\\prod", r"\\mathbb\{E\}", r"\\text\{Var\}",
                r"\\text\{Cov\}", r"P\(", r"\\mu", r"\\sigma"
            ],
            MathematicalDomain("set_theory"): [
                r"\\cup", r"\\cap", r"\\subset", r"\\supset",
                r"\\in", r"\\notin", r"\\emptyset", r"\\forall"
            ],
            MathematicalDomain("logic"): [
                r"\\land", r"\\lor", r"\\neg", r"\\implies",
                r"\\iff", r"\\exists", r"\\forall"
            ],
            MathematicalDomain("number_theory"): [
                r"\\mod", r"\\gcd", r"\\lcm", r"\\equiv",
                r"\\mid", r"\\nmid", r"\\phi"
            ]
        }
        
        # Count indicators for each domain
        domain_scores: dict[MathematicalDomain, int] = {}
        for domain, indicators in domain_indicators.items():
            score = sum(1 for ind in indicators if ind in expr_lower)
            if score > 0:
                domain_scores[domain] = score
        
        # Return domain with highest score, or general if none found
        if domain_scores:
            return max(domain_scores.items(), key=lambda x: x[1])[0]
        
        return MathematicalDomain.general()
    
    def add_intermediate_result(self, result: str, stage: str) -> None:
        """Add intermediate processing result."""
        self.intermediate_results.append(f"[{stage}] {result}")
        self.metadata.add_stage(stage)
    
    def set_speech_text(self, speech: SpeechText) -> None:
        """Set final speech text."""
        self.speech_text = speech
        self.metadata.finish()
    
    def mark_error(self, error: Exception) -> None:
        """Mark processing as failed."""
        self.metadata.error_occurred = True
        self.metadata.error_message = str(error)
        self.metadata.finish()
    
    def get_complexity_score(self) -> int:
        """Calculate complexity score (0-100)."""
        score = 0
        expr = self.latex.value
        
        # Nesting depth (0-30 points)
        max_depth = self._calculate_max_nesting()
        score += min(max_depth * 3, 30)
        
        # Number of commands (0-20 points)
        commands = self.latex.extract_commands()
        score += min(len(commands) * 2, 20)
        
        # Special symbols (0-20 points)
        special_symbols = [
            r"∫", r"∑", r"∏", r"∂", r"∇", r"∞",
            r"α", r"β", r"γ", r"δ", r"θ", r"φ"
        ]
        symbol_count = sum(expr.count(s) for s in special_symbols)
        score += min(symbol_count * 3, 20)
        
        # Expression length (0-20 points)
        score += min(len(expr) // 50, 20)
        
        # Domain complexity (0-10 points)
        if self.detected_domain and self.detected_domain.is_analysis_related():
            score += 10
        elif self.detected_domain and self.detected_domain.value in {
            "topology", "complex_analysis", "differential_equations"
        }:
            score += 10
        
        return min(score, 100)
    
    def _calculate_max_nesting(self) -> int:
        """Calculate maximum nesting depth."""
        max_depth = 0
        current_depth = 0
        
        for char in self.latex.value:
            if char in "{[(":
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char in "}])":
                current_depth -= 1
                
        return max_depth
    
    def requires_context(self) -> bool:
        """Check if expression requires context for proper processing."""
        # Expressions with pronouns or references need context
        context_indicators = [
            r"\\text\{it\}",
            r"\\text\{this\}",
            r"\\text\{that\}",
            r"\\text\{above\}",
            r"\\text\{below\}",
            r"\\ref\{",
            r"\\eqref\{"
        ]
        
        expr = self.latex.value
        return any(ind in expr for ind in context_indicators)
    
    def extract_variables(self) -> set[str]:
        """Extract variable names from expression."""
        # Simple variable extraction - can be enhanced
        variables = set()
        
        # Single letter variables
        single_vars = re.findall(r"\b([a-zA-Z])\b", self.latex.value)
        variables.update(single_vars)
        
        # Greek letters
        greek_vars = re.findall(r"\\([a-zA-Z]+)(?![a-zA-Z{])", self.latex.value)
        greek_letters = {
            "alpha", "beta", "gamma", "delta", "epsilon",
            "theta", "lambda", "mu", "phi", "psi", "omega"
        }
        variables.update(g for g in greek_vars if g in greek_letters)
        
        return variables
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "latex": self.latex.value,
            "audience_level": self.audience_level.value,
            "detected_domain": self.detected_domain.value if self.detected_domain else None,
            "context": self.context,
            "speech_text": self.speech_text.value if self.speech_text else None,
            "complexity_score": self.get_complexity_score(),
            "requires_context": self.requires_context(),
            "variables": list(self.extract_variables()),
            "processing_metadata": {
                "time_ms": self.metadata.processing_time_ms,
                "stages": self.metadata.processing_stages,
                "patterns_applied": self.metadata.patterns_applied,
                "cache_hit": self.metadata.cache_hit,
                "error": self.metadata.error_message
            }
        }