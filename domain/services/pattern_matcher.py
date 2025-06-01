"""Pattern matching service."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Optional

from src.domain.entities.mathematical_expression import MathematicalExpression
from src.domain.entities.pattern import PatternEntity
from src.domain.exceptions import ProcessingError
from src.domain.interfaces.pattern_repository import PatternRepository
from src.domain.value_objects import SpeechText, MathematicalDomain

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """Result of pattern matching."""
    
    pattern: PatternEntity
    matched: bool
    transformed_text: Optional[str] = None
    match_positions: list[tuple[int, int]] = None
    confidence: float = 1.0
    
    def __post_init__(self) -> None:
        """Initialize match positions."""
        if self.match_positions is None:
            self.match_positions = []


class PatternMatchingService:
    """Service for matching and applying patterns to expressions."""
    
    def __init__(
        self,
        pattern_repository: PatternRepository,
        max_iterations: int = 10,
        timeout_seconds: float = 5.0
    ) -> None:
        """Initialize pattern matching service."""
        self.pattern_repository = pattern_repository
        self.max_iterations = max_iterations
        self.timeout_seconds = timeout_seconds
    
    async def process_expression(
        self,
        expression: MathematicalExpression
    ) -> SpeechText:
        """Process expression using pattern matching.
        
        Args:
            expression: Mathematical expression to process
            
        Returns:
            Speech text result
            
        Raises:
            ProcessingError: If processing fails
        """
        try:
            # Start processing
            expression.add_transformation("pattern_matching_start")
            
            # Get relevant patterns
            patterns = await self._get_relevant_patterns(expression)
            
            if not patterns:
                raise ProcessingError(
                    "No patterns found for expression",
                    expression=expression.latex_expression.content,
                    stage="pattern_selection"
                )
            
            # Apply patterns iteratively
            result = await self._apply_patterns(expression, patterns)
            
            # Create speech text
            speech = SpeechText(value=result)
            
            # Update metadata about patterns applied
            for pattern in patterns:
                if pattern.id not in expression.metadata.patterns_applied:
                    expression.metadata.patterns_applied.append(pattern.id)
            
            return speech
            
        except asyncio.TimeoutError:
            raise ProcessingError(
                f"Pattern matching timed out after {self.timeout_seconds}s",
                expression=expression.latex_expression.content,
                stage="pattern_matching"
            )
        except Exception as e:
            raise ProcessingError(
                f"Pattern matching failed: {e}",
                expression=expression.latex_expression.content,
                stage="pattern_matching"
            )
    
    async def _get_relevant_patterns(
        self,
        expression: MathematicalExpression
    ) -> list[PatternEntity]:
        """Get patterns relevant to the expression."""
        # Get patterns for the detected domain
        domain_patterns = await self.pattern_repository.find_by_domain(
            expression.detected_domain
        )
        
        # Get high-priority general patterns
        general_patterns = await self.pattern_repository.find_by_domain(
            MathematicalDomain("general")
        )
        
        # Combine and sort by priority
        all_patterns = domain_patterns + general_patterns
        
        # Remove duplicates
        seen_ids = set()
        unique_patterns = []
        for pattern in all_patterns:
            if pattern.id not in seen_ids:
                seen_ids.add(pattern.id)
                unique_patterns.append(pattern)
        
        # Sort by priority (highest first)
        unique_patterns.sort(key=lambda p: p.priority.value, reverse=True)
        
        return unique_patterns
    
    async def _apply_patterns(
        self,
        expression: MathematicalExpression,
        patterns: list[PatternEntity]
    ) -> str:
        """Apply patterns to expression text."""
        text = expression.latex_expression.content
        context = self._build_context(expression)
        
        iterations = 0
        applied_patterns = set()
        
        while iterations < self.max_iterations:
            iterations += 1
            text_changed = False
            
            for pattern in patterns:
                # Skip if already applied in this session
                if pattern.id in applied_patterns:
                    continue
                
                # Try to apply pattern
                new_text, was_applied = pattern.apply(text, context)
                
                if was_applied:
                    text = new_text
                    text_changed = True
                    applied_patterns.add(pattern.id)
                    
                    # Track pattern application
                    if pattern.id not in expression.metadata.patterns_applied:
                        expression.metadata.patterns_applied.append(pattern.id)
                    
                    # Add transformation record
                    expression.add_transformation(f"Applied pattern: {pattern.id}")
                    
                    # Update context for next patterns
                    context["current_text"] = text
                    
                    logger.debug(
                        f"Applied pattern '{pattern.id}' to expression",
                        extra={
                            "pattern_id": pattern.id,
                            "expression_id": id(expression),
                            "result": text[:100]
                        }
                    )
            
            # If no patterns were applied, we're done
            if not text_changed:
                break
        
        # Post-process the result
        text = self._post_process(text, expression)
        
        return text
    
    def _build_context(self, expression: MathematicalExpression) -> dict[str, Any]:
        """Build context for pattern matching."""
        return {
            "type": expression.context if expression.context else "inline",
            "domain": expression.detected_domain.value if expression.detected_domain else "general",
            "audience": expression.audience_level.value if expression.audience_level else "undergraduate",
            "full_text": expression.latex_expression.content,
            "current_text": expression.latex_expression.content,
            "variables": list(expression.latex_expression.variables),
            "complexity": expression.complexity_metrics.overall_score if expression.complexity_metrics else 0.0
        }
    
    def _post_process(self, text: str, expression: MathematicalExpression) -> str:
        """Post-process the converted text."""
        # Clean up extra spaces
        text = " ".join(text.split())
        
        # Audience-specific adjustments
        if expression.audience_level and expression.audience_level.is_basic:
            # Simplify language for basic audiences
            replacements = [
                ("with respect to", "by"),
                ("such that", "where"),
                ("implies", "means"),
                ("if and only if", "exactly when"),
            ]
            for old, new in replacements:
                text = text.replace(old, new)
        elif expression.audience_level and expression.audience_level.is_advanced:
            # Use more formal language for advanced audiences
            replacements = [
                (" dot ", " inner product "),
                ("natural log", "natural logarithm"),
            ]
            for old, new in replacements:
                text = text.replace(old, new)
        
        # Ensure proper capitalization
        if text and not text[0].isupper():
            text = text[0].upper() + text[1:]
        
        # Fix punctuation spacing
        text = text.replace(" .", ".")
        text = text.replace(" ,", ",")
        text = text.replace(" ;", ";")
        text = text.replace(" :", ":")
        
        return text.strip()
    
    async def analyze_pattern_coverage(
        self,
        expressions: list[MathematicalExpression]
    ) -> dict[str, Any]:
        """Analyze pattern coverage for a set of expressions."""
        total_expressions = len(expressions)
        matched_expressions = 0
        pattern_usage = {}
        unmatched_samples = []
        
        for expr in expressions:
            patterns = await self._get_relevant_patterns(expr)
            matched = False
            
            for pattern in patterns:
                if pattern.matches(expr.latex.value):
                    matched = True
                    pattern_usage[pattern.id] = pattern_usage.get(pattern.id, 0) + 1
            
            if matched:
                matched_expressions += 1
            else:
                unmatched_samples.append(expr.latex.value)
                if len(unmatched_samples) >= 10:
                    unmatched_samples.append("...")
                    break
        
        return {
            "total_expressions": total_expressions,
            "matched_expressions": matched_expressions,
            "coverage_percentage": (matched_expressions / total_expressions) * 100,
            "pattern_usage": pattern_usage,
            "unmatched_samples": unmatched_samples
        }