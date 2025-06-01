"""
Process expression use case.

This use case handles the processing of LaTeX mathematical expressions
and converting them to natural speech text.
"""

import asyncio
import time
import hashlib
from typing import Optional, List
from datetime import datetime

from ..dtos_v3 import (
    ProcessExpressionRequest,
    ProcessExpressionResponse,
    BatchProcessRequest,
    BatchProcessResponse
)
from src.domain.entities import MathematicalExpression
from src.domain.services import PatternMatchingService
from src.domain.interfaces import PatternRepository
from src.infrastructure.cache import LRUCacheRepository
from src.infrastructure.logging import get_logger
from src.domain.value_objects import LaTeXExpression, SpeechText


logger = get_logger(__name__)


class ProcessExpressionUseCase:
    """Use case for processing mathematical expressions."""
    
    def __init__(
        self,
        pattern_matching_service: PatternMatchingService,
        pattern_repository: PatternRepository,
        cache_repository: Optional[LRUCacheRepository] = None
    ) -> None:
        """
        Initialize the use case.
        
        Args:
            pattern_matching_service: Service for pattern matching
            pattern_repository: Repository for pattern storage
            cache_repository: Optional cache repository
        """
        self.pattern_matching_service = pattern_matching_service
        self.pattern_repository = pattern_repository
        self.cache_repository = cache_repository
    
    async def execute(
        self,
        request: ProcessExpressionRequest
    ) -> ProcessExpressionResponse:
        """
        Execute expression processing.
        
        Args:
            request: Processing request containing expression and options
            
        Returns:
            Processing response with speech text and metadata
        """
        start_time = time.time()
        
        try:
            logger.info(
                "Processing expression",
                expression=request.expression.content[:100],
                audience_level=request.audience_level.value,
                domain=request.domain.value if request.domain else None,
                context=request.context
            )
            
            # Create mathematical expression entity
            math_expr = MathematicalExpression(
                latex_expression=request.expression,
                context=request.context or "auto",
                audience_level=request.audience_level,
                domain_hint=request.domain
            )
            
            # Check cache first
            cache_key = self._generate_cache_key(request)
            cached_result = None
            if self.cache_repository:
                cached_result = await self.cache_repository.get(cache_key)
            
            if cached_result:
                logger.cache_hit(cache_key)
                processing_time_ms = (time.time() - start_time) * 1000
                
                return ProcessExpressionResponse(
                    expression=request.expression,
                    speech_text=cached_result["speech_text"],
                    processing_time_ms=processing_time_ms,
                    cached=True,
                    patterns_applied=cached_result.get("patterns_applied", 0),
                    domain_detected=cached_result.get("domain_detected"),
                    complexity_score=cached_result.get("complexity_score")
                )
            
            logger.cache_miss(cache_key)
            
            # Apply pattern matching
            speech_text = await self.pattern_matching_service.process_expression(
                math_expr
            )
            
            # Set processing results
            patterns_applied_count = len(math_expr.metadata.patterns_applied)
            processing_time_ms = (time.time() - start_time) * 1000
            
            math_expr.set_processing_result(
                speech_text=speech_text,
                patterns_applied=math_expr.metadata.patterns_applied,
                processing_time_ms=processing_time_ms,
                cache_hit=False
            )
            
            # Cache the result
            if self.cache_repository:
                cache_value = {
                    "speech_text": speech_text,
                    "patterns_applied": patterns_applied_count,
                    "domain_detected": math_expr.detected_domain,
                    "complexity_score": math_expr.complexity_metrics.overall_score if math_expr.complexity_metrics else None
                }
                await self.cache_repository.set(cache_key, cache_value)
            
            logger.expression_processed(
                expression=request.expression.content,
                output=speech_text.value,
                duration_ms=processing_time_ms,
                cached=False
            )
            
            return ProcessExpressionResponse(
                expression=request.expression,
                speech_text=speech_text,
                processing_time_ms=processing_time_ms,
                cached=False,
                patterns_applied=patterns_applied_count,
                domain_detected=math_expr.detected_domain,
                complexity_score=math_expr.complexity_metrics.overall_score if math_expr.complexity_metrics else None
            )
            
        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            logger.error(
                "Expression processing failed",
                expression=request.expression.content[:100],
                error=str(e),
                processing_time_ms=processing_time_ms
            )
            
            # Return fallback response
            fallback_speech = SpeechText(
                value=request.expression.content,
                ssml=None,
                pronunciation_hints={}
            )
            
            return ProcessExpressionResponse(
                expression=request.expression,
                speech_text=fallback_speech,
                processing_time_ms=processing_time_ms,
                cached=False,
                patterns_applied=0,
                domain_detected=None,
                complexity_score=None,
                error=str(e)
            )
    
    async def execute_batch(
        self,
        request: BatchProcessRequest
    ) -> BatchProcessResponse:
        """
        Execute batch processing of multiple expressions.
        
        Args:
            request: Batch processing request
            
        Returns:
            Batch processing response with all results
        """
        start_time = time.time()
        
        logger.info(
            "Processing batch",
            expression_count=len(request.requests)
        )
        
        # Process all expressions concurrently
        tasks = [
            self.execute(expr_request)
            for expr_request in request.requests
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Separate successful and failed results
        successful_results = []
        failed_count = 0
        
        for result in results:
            if isinstance(result, Exception):
                logger.error("Batch item failed", error=str(result))
                failed_count += 1
                # Create error response
                error_response = ProcessExpressionResponse(
                    expression=LaTeXExpression("x"),  # We don't have the original here
                    speech_text=SpeechText(value="error", ssml=None, pronunciation_hints={}),
                    processing_time_ms=0,
                    cached=False,
                    patterns_applied=0,
                    error=str(result)
                )
                successful_results.append(error_response)
            else:
                successful_results.append(result)
        
        total_processing_time_ms = (time.time() - start_time) * 1000
        successful_count = len(request.requests) - failed_count
        
        logger.info(
            "Batch processing complete",
            total_expressions=len(request.requests),
            successful=successful_count,
            failed=failed_count,
            total_time_ms=total_processing_time_ms
        )
        
        return BatchProcessResponse(
            results=successful_results,
            total_processing_time_ms=total_processing_time_ms,
            successful_count=successful_count,
            failed_count=failed_count
        )
    
    def _generate_cache_key(self, request: ProcessExpressionRequest) -> str:
        """Generate a cache key for the request."""
        key_components = [
            request.expression.content,
            request.audience_level.value,
            request.domain.value if request.domain else "auto",
            request.context or "auto"
        ]
        
        key_string = "|".join(key_components)
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]