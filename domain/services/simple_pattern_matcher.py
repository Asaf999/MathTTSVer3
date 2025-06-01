"""
Simple synchronous pattern matcher for testing.
"""

import re
from typing import List, Optional, Tuple
from src.domain.entities import PatternEntity
from src.domain.value_objects import LaTeXExpression, SpeechText
from src.infrastructure.persistence import MemoryPatternRepository


class PatternMatcher:
    """Simple pattern matching service."""
    
    def __init__(self, repository: MemoryPatternRepository):
        """Initialize with pattern repository."""
        self.repository = repository
        self._compiled_patterns = {}
    
    def process_expression(self, expression: LaTeXExpression) -> SpeechText:
        """
        Process LaTeX expression and convert to speech text.
        
        Args:
            expression: LaTeX expression to process
            
        Returns:
            Speech text result
        """
        # Get all patterns sorted by priority (highest first)
        patterns = sorted(
            self.repository.get_all(),
            key=lambda p: p.priority.value,
            reverse=True
        )
        
        # Start with the original expression
        result = expression.value
        
        # Track which parts have been replaced to avoid overlapping replacements
        replaced_ranges = []
        
        # Apply patterns in priority order
        for pattern in patterns:
            # Compile pattern if not already compiled
            if pattern.id not in self._compiled_patterns:
                try:
                    self._compiled_patterns[pattern.id] = re.compile(pattern.pattern)
                except re.error:
                    # Skip invalid patterns
                    continue
            
            regex = self._compiled_patterns[pattern.id]
            
            # Find all matches
            matches = list(regex.finditer(result))
            
            # Process matches from right to left to preserve positions
            for match in reversed(matches):
                start, end = match.span()
                
                # Check if this range overlaps with any already replaced range
                overlaps = any(
                    not (end <= r_start or start >= r_end)
                    for r_start, r_end in replaced_ranges
                )
                
                if not overlaps:
                    # Apply the replacement
                    replacement = match.expand(pattern.output_template)
                    result = result[:start] + replacement + result[end:]
                    
                    # Update replaced ranges
                    new_end = start + len(replacement)
                    replaced_ranges.append((start, new_end))
                    
                    # Re-sort ranges
                    replaced_ranges.sort()
        
        return SpeechText(result)