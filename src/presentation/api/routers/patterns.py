"""
Pattern management API endpoints.

This module provides endpoints for listing, testing, and managing
LaTeX-to-speech conversion patterns.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query

from src.infrastructure.persistence import MemoryPatternRepository
from src.domain.services import PatternMatchingService
from src.domain.value_objects import LaTeXExpression, MathematicalDomain
from src.infrastructure.logging import get_logger
from ..dependencies import get_pattern_repository, get_pattern_matching_service, PaginationParams
from ..schemas import (
    PatternInfo,
    PatternListResponse,
    PatternTestRequest,
    PatternTestResponse,
    MathematicalDomainEnum
)


router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/",
    response_model=PatternListResponse,
    summary="List patterns",
    description="Get list of all available LaTeX-to-speech patterns"
)
async def list_patterns(
    domain: Optional[MathematicalDomainEnum] = Query(
        None,
        description="Filter by mathematical domain"
    ),
    context: Optional[str] = Query(
        None,
        description="Filter by context (inline, display, equation, etc.)"
    ),
    pagination: PaginationParams = Depends(PaginationParams),
    pattern_repo: MemoryPatternRepository = Depends(get_pattern_repository)
) -> PatternListResponse:
    """
    List all available patterns with optional filtering.
    
    Supports filtering by mathematical domain and context.
    """
    try:
        logger.debug(
            "Listing patterns",
            domain_filter=domain.value if domain else None,
            context_filter=context,
            offset=pagination.offset,
            limit=pagination.limit
        )
        
        # Build filters
        filters = {}
        if domain:
            filters["domain"] = MathematicalDomain(domain.value)
        if context:
            filters["contexts"] = [context]
        
        # Get patterns from repository
        patterns = await pattern_repo.find_by_filters(filters)
        
        # Apply pagination
        total_count = len(patterns)
        paginated_patterns = patterns[pagination.offset:pagination.offset + pagination.limit]
        
        # Convert to API schema
        pattern_infos = []
        for pattern in paginated_patterns:
            pattern_info = PatternInfo(
                id=pattern.id,
                pattern=pattern.pattern,
                output_template=pattern.output_template,
                priority=pattern.priority.value,
                domain=pattern.domain.value,
                contexts=pattern.contexts,
                description=pattern.description
            )
            pattern_infos.append(pattern_info)
        
        # Get all unique domains
        all_patterns = await pattern_repo.get_all()
        domains = list(set(p.domain.value for p in all_patterns))
        domains.sort()
        
        logger.info(
            "Listed patterns",
            total_count=total_count,
            returned_count=len(pattern_infos),
            domain_filter=domain.value if domain else None
        )
        
        return PatternListResponse(
            patterns=pattern_infos,
            total_count=total_count,
            domains=domains
        )
        
    except Exception as e:
        logger.exception("Failed to list patterns")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve pattern list"
        )


@router.get(
    "/{pattern_id}",
    response_model=PatternInfo,
    summary="Get pattern details",
    description="Get detailed information about a specific pattern"
)
async def get_pattern(
    pattern_id: str,
    pattern_repo: MemoryPatternRepository = Depends(get_pattern_repository)
) -> PatternInfo:
    """
    Get detailed information about a specific pattern.
    
    - **pattern_id**: The pattern identifier to look up
    """
    try:
        logger.debug("Getting pattern details", pattern_id=pattern_id)
        
        # Get pattern from repository
        pattern = await pattern_repo.get_by_id(pattern_id)
        
        if not pattern:
            logger.warning("Pattern not found", pattern_id=pattern_id)
            raise HTTPException(
                status_code=404,
                detail=f"Pattern '{pattern_id}' not found"
            )
        
        return PatternInfo(
            id=pattern.id,
            pattern=pattern.pattern,
            output_template=pattern.output_template,
            priority=pattern.priority.value,
            domain=pattern.domain.value,
            contexts=pattern.contexts,
            description=pattern.description
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get pattern details", pattern_id=pattern_id)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve pattern details"
        )


@router.post(
    "/test",
    response_model=PatternTestResponse,
    summary="Test pattern matching",
    description="Test if a pattern matches against a LaTeX expression"
)
async def test_pattern(
    request: PatternTestRequest,
    pattern_service: PatternMatchingService = Depends(get_pattern_matching_service)
) -> PatternTestResponse:
    """
    Test pattern matching against a LaTeX expression.
    
    Useful for debugging and validating patterns during development.
    """
    try:
        logger.debug(
            "Testing pattern",
            pattern=request.pattern[:50] + "..." if len(request.pattern) > 50 else request.pattern,
            expression=request.test_expression
        )
        
        # Create a temporary expression
        latex_expr = LaTeXExpression(request.test_expression)
        
        # Test the pattern (this is a simplified version)
        # In a full implementation, we would need to create a temporary pattern entity
        # and test it against the expression
        
        # For now, return a basic response
        # TODO: Implement actual pattern testing
        
        return PatternTestResponse(
            matched=False,
            output=None,
            match_groups=None
        )
        
    except ValueError as e:
        logger.warning("Invalid test request", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Pattern test failed")
        raise HTTPException(
            status_code=500,
            detail="Pattern test failed"
        )


@router.get(
    "/domains/",
    response_model=List[str],
    summary="List mathematical domains",
    description="Get list of all mathematical domains used in patterns"
)
async def list_domains(
    pattern_repo: MemoryPatternRepository = Depends(get_pattern_repository)
) -> List[str]:
    """
    Get list of all mathematical domains used in patterns.
    
    Returns unique domain names from all available patterns.
    """
    try:
        logger.debug("Listing pattern domains")
        
        # Get all patterns
        patterns = await pattern_repo.get_all()
        
        # Extract unique domains
        domains = list(set(pattern.domain.value for pattern in patterns))
        domains.sort()
        
        logger.info("Listed domains", count=len(domains))
        
        return domains
        
    except Exception as e:
        logger.exception("Failed to list domains")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve domain list"
        )


@router.get(
    "/contexts/",
    response_model=List[str],
    summary="List pattern contexts",
    description="Get list of all contexts used in patterns"
)
async def list_contexts(
    pattern_repo: MemoryPatternRepository = Depends(get_pattern_repository)
) -> List[str]:
    """
    Get list of all contexts used in patterns.
    
    Returns unique context names from all available patterns.
    """
    try:
        logger.debug("Listing pattern contexts")
        
        # Get all patterns
        patterns = await pattern_repo.get_all()
        
        # Extract unique contexts
        contexts = set()
        for pattern in patterns:
            contexts.update(pattern.contexts)
        
        context_list = list(contexts)
        context_list.sort()
        
        logger.info("Listed contexts", count=len(context_list))
        
        return context_list
        
    except Exception as e:
        logger.exception("Failed to list contexts")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve context list"
        )


@router.get(
    "/stats",
    summary="Pattern statistics",
    description="Get statistics about the pattern library"
)
async def get_pattern_stats(
    pattern_repo: MemoryPatternRepository = Depends(get_pattern_repository)
) -> dict:
    """
    Get statistics about the pattern library.
    
    Returns counts by domain, context, priority, etc.
    """
    try:
        logger.debug("Getting pattern statistics")
        
        # Get all patterns
        patterns = await pattern_repo.get_all()
        
        # Calculate statistics
        stats = {
            "total_patterns": len(patterns),
            "domains": {},
            "contexts": {},
            "priorities": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }
        
        # Count by domain
        for pattern in patterns:
            domain = pattern.domain.value
            stats["domains"][domain] = stats["domains"].get(domain, 0) + 1
        
        # Count by context
        for pattern in patterns:
            for context in pattern.contexts:
                stats["contexts"][context] = stats["contexts"].get(context, 0) + 1
        
        # Count by priority
        for pattern in patterns:
            priority_val = pattern.priority.value
            if priority_val >= 1500:
                stats["priorities"]["critical"] += 1
            elif priority_val >= 1000:
                stats["priorities"]["high"] += 1
            elif priority_val >= 500:
                stats["priorities"]["medium"] += 1
            else:
                stats["priorities"]["low"] += 1
        
        logger.info("Generated pattern statistics")
        
        return stats
        
    except Exception as e:
        logger.exception("Failed to get pattern statistics")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve pattern statistics"
        )