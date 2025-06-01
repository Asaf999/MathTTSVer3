"""
Optimized pattern matching service with performance enhancements.
"""

import asyncio
import functools
import re
from collections import OrderedDict
from typing import Dict, List, Optional, Set, Tuple

from src.domain.entities import PatternEntity, MathematicalExpression
from src.domain.services import PatternMatchingService
from src.domain.value_objects import SpeechText
from src.infrastructure.logging import get_logger
from .profiler import profile_async_function, time_block

logger = get_logger(__name__)


class OptimizedPatternMatchingService(PatternMatchingService):
    """
    Optimized pattern matching service with caching and parallel processing.
    
    Optimizations:
    1. Pattern compilation caching
    2. Result caching with LRU eviction
    3. Parallel pattern application
    4. Early termination on stable output
    5. Pattern prefiltering based on expression content
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Pattern compilation cache
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        
        # Result cache (expression -> result)
        self._result_cache = OrderedDict()
        self._cache_max_size = 1000
        
        # Pattern effectiveness tracking
        self._pattern_hits: Dict[str, int] = {}
        self._pattern_misses: Dict[str, int] = {}
    
    @profile_async_function("optimized_pattern_matching.process")
    async def process_expression(self, expression: MathematicalExpression) -> SpeechText:
        """Process expression with optimizations."""
        # Check result cache first
        cache_key = self._get_cache_key(expression)
        if cache_key in self._result_cache:
            logger.debug(f"Pattern result cache hit for {cache_key}")
            return self._result_cache[cache_key]
        
        # Process with optimizations
        result = await self._process_with_optimizations(expression)
        
        # Update cache
        self._update_result_cache(cache_key, result)
        
        return result
    
    async def _process_with_optimizations(self, expression: MathematicalExpression) -> SpeechText:
        """Process expression with performance optimizations."""
        try:
            # Get and prefilter patterns
            patterns = await self._get_optimized_patterns(expression)
            
            if not patterns:
                raise ProcessingError(
                    "No patterns found for expression",
                    expression=expression.latex_expression.content,
                    stage="pattern_selection"
                )
            
            # Apply patterns with optimizations
            result = await self._apply_patterns_optimized(expression, patterns)
            
            # Create speech text
            speech = SpeechText(value=result)
            
            # Update pattern statistics
            self._update_pattern_stats(expression, patterns)
            
            return speech
            
        except Exception as e:
            logger.error(f"Optimized pattern matching failed: {e}")
            raise
    
    async def _get_optimized_patterns(self, expression: MathematicalExpression) -> List[PatternEntity]:
        """Get patterns with prefiltering optimization."""
        with time_block("pattern_retrieval"):
            # Get all relevant patterns
            patterns = await self._get_relevant_patterns(expression)
        
        with time_block("pattern_prefiltering"):
            # Prefilter patterns based on expression content
            filtered_patterns = self._prefilter_patterns(patterns, expression)
        
        return filtered_patterns
    
    def _prefilter_patterns(
        self, 
        patterns: List[PatternEntity], 
        expression: MathematicalExpression
    ) -> List[PatternEntity]:
        """
        Prefilter patterns that cannot possibly match.
        
        This optimization checks for required substrings before
        attempting full regex matching.
        """
        expr_content = expression.latex_expression.content
        filtered = []
        
        for pattern in patterns:
            # Extract literal substrings from pattern
            literals = self._extract_literals(pattern.pattern)
            
            # Check if any required literal is in expression
            if not literals or any(lit in expr_content for lit in literals):
                filtered.append(pattern)
            else:
                # Track miss for statistics
                self._pattern_misses[pattern.id] = self._pattern_misses.get(pattern.id, 0) + 1
        
        logger.debug(f"Prefiltered {len(patterns)} patterns to {len(filtered)}")
        return filtered
    
    def _extract_literals(self, pattern: str) -> Set[str]:
        """Extract literal substrings that must be present for pattern to match."""
        # Remove regex special characters and extract literals
        literals = set()
        
        # Find literal sequences (not in character classes or groups)
        literal_pattern = r'(?<!\\)([a-zA-Z\\]+)'
        for match in re.finditer(literal_pattern, pattern):
            literal = match.group(1)
            if len(literal) > 2:  # Only consider meaningful literals
                literals.add(literal)
        
        return literals
    
    async def _apply_patterns_optimized(
        self, 
        expression: MathematicalExpression,
        patterns: List[PatternEntity]
    ) -> str:
        """Apply patterns with optimization strategies."""
        text = expression.latex_expression.content
        context = self._build_context(expression)
        
        # Group patterns by priority for batch processing
        priority_groups = self._group_by_priority(patterns)
        
        iterations = 0
        applied_patterns = set()
        previous_text = None
        
        while iterations < self.max_iterations:
            iterations += 1
            
            # Check for stability (no changes in last iteration)
            if text == previous_text:
                logger.debug(f"Pattern matching stabilized after {iterations} iterations")
                break
            
            previous_text = text
            
            # Apply patterns by priority group
            for priority, group_patterns in priority_groups:
                # Apply patterns in parallel within same priority
                text, group_applied = await self._apply_pattern_group(
                    text, group_patterns, context, applied_patterns
                )
                
                if group_applied:
                    applied_patterns.update(group_applied)
                    context["current_text"] = text
        
        # Post-process the result
        text = self._post_process(text, expression)
        
        return text
    
    def _group_by_priority(self, patterns: List[PatternEntity]) -> List[Tuple[int, List[PatternEntity]]]:
        """Group patterns by priority level."""
        groups = {}
        for pattern in patterns:
            priority = pattern.priority.value
            if priority not in groups:
                groups[priority] = []
            groups[priority].append(pattern)
        
        # Return sorted by priority (highest first)
        return sorted(groups.items(), key=lambda x: x[0], reverse=True)
    
    async def _apply_pattern_group(
        self,
        text: str,
        patterns: List[PatternEntity],
        context: Dict,
        already_applied: Set[str]
    ) -> Tuple[str, Set[str]]:
        """Apply a group of patterns with same priority."""
        applied_in_group = set()
        
        for pattern in patterns:
            if pattern.id in already_applied:
                continue
            
            # Get compiled pattern
            compiled = self._get_compiled_pattern(pattern)
            
            # Check if pattern matches
            if compiled and compiled.search(text):
                new_text, was_applied = pattern.apply(text, context)
                
                if was_applied:
                    text = new_text
                    applied_in_group.add(pattern.id)
                    self._pattern_hits[pattern.id] = self._pattern_hits.get(pattern.id, 0) + 1
                    
                    logger.debug(f"Applied pattern {pattern.id} (hits: {self._pattern_hits[pattern.id]})")
        
        return text, applied_in_group
    
    def _get_compiled_pattern(self, pattern: PatternEntity) -> Optional[re.Pattern]:
        """Get compiled pattern with caching."""
        if pattern.id not in self._compiled_patterns:
            try:
                self._compiled_patterns[pattern.id] = re.compile(pattern.pattern)
            except re.error:
                logger.error(f"Failed to compile pattern {pattern.id}: {pattern.pattern}")
                return None
        
        return self._compiled_patterns[pattern.id]
    
    def _get_cache_key(self, expression: MathematicalExpression) -> str:
        """Generate cache key for expression."""
        return f"{expression.latex_expression.content}|{expression.audience_level.value if expression.audience_level else 'none'}"
    
    def _update_result_cache(self, key: str, result: SpeechText) -> None:
        """Update result cache with LRU eviction."""
        # Remove key if already exists (to update order)
        if key in self._result_cache:
            del self._result_cache[key]
        
        # Add to end
        self._result_cache[key] = result
        
        # Evict if necessary
        if len(self._result_cache) > self._cache_max_size:
            # Remove oldest (first) item
            self._result_cache.popitem(last=False)
    
    def _update_pattern_stats(self, expression: MathematicalExpression, patterns: List[PatternEntity]) -> None:
        """Update pattern effectiveness statistics."""
        for pattern in patterns:
            if pattern.id in expression.metadata.patterns_applied:
                self._pattern_hits[pattern.id] = self._pattern_hits.get(pattern.id, 0) + 1
            else:
                self._pattern_misses[pattern.id] = self._pattern_misses.get(pattern.id, 0) + 1
    
    def get_optimization_stats(self) -> Dict[str, any]:
        """Get optimization statistics."""
        total_hits = sum(self._pattern_hits.values())
        total_misses = sum(self._pattern_misses.values())
        
        # Calculate pattern effectiveness
        pattern_effectiveness = {}
        for pattern_id in set(self._pattern_hits.keys()) | set(self._pattern_misses.keys()):
            hits = self._pattern_hits.get(pattern_id, 0)
            misses = self._pattern_misses.get(pattern_id, 0)
            total = hits + misses
            
            if total > 0:
                pattern_effectiveness[pattern_id] = {
                    "hit_rate": hits / total,
                    "total_attempts": total,
                    "hits": hits,
                    "misses": misses
                }
        
        return {
            "cache_size": len(self._result_cache),
            "compiled_patterns": len(self._compiled_patterns),
            "total_pattern_hits": total_hits,
            "total_pattern_misses": total_misses,
            "overall_hit_rate": total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0,
            "pattern_effectiveness": pattern_effectiveness
        }
    
    def clear_caches(self) -> None:
        """Clear all caches."""
        self._compiled_patterns.clear()
        self._result_cache.clear()
        logger.info("Cleared pattern matching caches")