"""
Expression processing API endpoints.

This module contains endpoints for processing LaTeX expressions
and converting them to speech.
"""

from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
import io

from src.application.use_cases import ProcessExpressionUseCase
from src.application.dtos import (
    ProcessExpressionRequest,
    ProcessExpressionResponse,
    BatchProcessRequest,
    BatchProcessResponse
)
from src.domain.value_objects import LaTeXExpression, AudienceLevel, MathematicalDomain
from src.adapters.tts_providers import TTSProviderAdapter, TTSOptions, AudioFormat
from src.infrastructure.logging import get_logger
from ..dependencies import (
    get_process_expression_use_case,
    get_tts_provider,
    PaginationParams
)
from src.infrastructure.auth.dependencies import CurrentUser, ValidAPIKey
from ..schemas import (
    ExpressionProcessRequest,
    ExpressionProcessResponse,
    BatchExpressionRequest,
    BatchExpressionResponse,
    TTSRequest,
    TTSResponse
)


router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/process",
    response_model=ExpressionProcessResponse,
    summary="Process LaTeX expression",
    description="Convert a LaTeX mathematical expression to natural speech text"
)
async def process_expression(
    request: ExpressionProcessRequest,
    use_case: ProcessExpressionUseCase = Depends(get_process_expression_use_case)
) -> ExpressionProcessResponse:
    """
    Process a LaTeX expression and convert it to natural speech.
    
    - **expression**: LaTeX mathematical expression
    - **audience_level**: Target audience complexity level
    - **domain**: Mathematical domain hint (optional)
    - **context**: Expression context (inline, display, etc.)
    """
    try:
        # Create domain objects
        latex_expr = LaTeXExpression(request.expression)
        
        # Create use case request
        use_case_request = ProcessExpressionRequest(
            expression=latex_expr,
            audience_level=request.audience_level,
            domain=request.domain,
            context=request.context or "auto"
        )
        
        # Process expression
        result = await use_case.execute(use_case_request)
        
        # Return response
        return ExpressionProcessResponse(
            expression=request.expression,
            speech_text=result.speech_text.plain_text,
            ssml=result.speech_text.ssml if result.speech_text.ssml else None,
            processing_time_ms=result.processing_time_ms,
            cached=result.cached,
            patterns_applied=result.patterns_applied,
            domain_detected=result.domain_detected.value if result.domain_detected else None,
            complexity_score=result.complexity_score
        )
        
    except ValueError as e:
        logger.warning("Invalid expression", expression=request.expression, error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Expression processing failed")
        raise HTTPException(status_code=500, detail="Processing failed")


@router.post(
    "/batch",
    response_model=BatchExpressionResponse,
    summary="Process multiple expressions",
    description="Process multiple LaTeX expressions in a single request"
)
async def process_batch(
    request: BatchExpressionRequest,
    use_case: ProcessExpressionUseCase = Depends(get_process_expression_use_case)
) -> BatchExpressionResponse:
    """
    Process multiple LaTeX expressions in batch.
    
    More efficient than individual requests for multiple expressions.
    """
    if len(request.expressions) > 50:  # Limit batch size
        raise HTTPException(
            status_code=400,
            detail="Batch size exceeds maximum of 50 expressions"
        )
    
    try:
        # Create use case requests
        use_case_requests = []
        for expr_req in request.expressions:
            latex_expr = LaTeXExpression(expr_req.expression)
            use_case_req = ProcessExpressionRequest(
                expression=latex_expr,
                audience_level=expr_req.audience_level,
                domain=expr_req.domain,
                context=expr_req.context or "auto"
            )
            use_case_requests.append(use_case_req)
        
        # Create batch request
        batch_request = BatchProcessRequest(requests=use_case_requests)
        
        # Process batch
        batch_result = await use_case.execute_batch(batch_request)
        
        # Convert results
        results = []
        for i, result in enumerate(batch_result.results):
            expr_response = ExpressionProcessResponse(
                expression=request.expressions[i].expression,
                speech_text=result.speech_text.plain_text,
                ssml=result.speech_text.ssml if result.speech_text.ssml else None,
                processing_time_ms=result.processing_time_ms,
                cached=result.cached,
                patterns_applied=result.patterns_applied,
                domain_detected=result.domain_detected.value if result.domain_detected else None,
                complexity_score=result.complexity_score
            )
            results.append(expr_response)
        
        return BatchExpressionResponse(
            results=results,
            total_processing_time_ms=batch_result.total_processing_time_ms,
            successful_count=batch_result.successful_count,
            failed_count=batch_result.failed_count
        )
        
    except ValueError as e:
        logger.warning("Invalid batch request", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Batch processing failed")
        raise HTTPException(status_code=500, detail="Batch processing failed")


@router.post(
    "/synthesize",
    response_model=TTSResponse,
    summary="Synthesize speech audio",
    description="Convert LaTeX expression to speech audio file"
)
async def synthesize_speech(
    request: TTSRequest,
    use_case: ProcessExpressionUseCase = Depends(get_process_expression_use_case),
    tts_provider: TTSProviderAdapter = Depends(get_tts_provider)
) -> TTSResponse:
    """
    Process LaTeX expression and synthesize speech audio.
    
    Returns audio file download URL and metadata.
    """
    try:
        # First process the expression
        latex_expr = LaTeXExpression(request.expression)
        use_case_request = ProcessExpressionRequest(
            expression=latex_expr,
            audience_level=request.audience_level,
            domain=request.domain,
            context=request.context or "auto"
        )
        
        process_result = await use_case.execute(use_case_request)
        
        # Create TTS options
        tts_options = TTSOptions(
            voice_id=request.voice_id,
            rate=request.rate,
            pitch=request.pitch,
            volume=request.volume,
            format=request.format,
            sample_rate=request.sample_rate
        )
        
        # Synthesize speech
        audio_data = await tts_provider.synthesize(
            process_result.speech_text,
            tts_options
        )
        
        # For now, return metadata (in production, upload to storage and return URL)
        return TTSResponse(
            expression=request.expression,
            speech_text=process_result.speech_text.plain_text,
            audio_size_bytes=audio_data.size_bytes,
            audio_format=audio_data.format.value,
            duration_seconds=audio_data.duration_seconds,
            voice_id=request.voice_id,
            processing_time_ms=process_result.processing_time_ms,
            # download_url would be populated in production
        )
        
    except ValueError as e:
        logger.warning("Invalid synthesis request", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Speech synthesis failed")
        raise HTTPException(status_code=500, detail="Synthesis failed")


@router.post(
    "/synthesize/stream",
    summary="Stream synthesized speech",
    description="Stream speech audio directly as response"
)
async def stream_synthesized_speech(
    request: TTSRequest,
    use_case: ProcessExpressionUseCase = Depends(get_process_expression_use_case),
    tts_provider: TTSProviderAdapter = Depends(get_tts_provider)
) -> StreamingResponse:
    """
    Process expression and stream synthesized speech audio.
    
    Returns audio data as streaming response.
    """
    try:
        # Process expression
        latex_expr = LaTeXExpression(request.expression)
        use_case_request = ProcessExpressionRequest(
            expression=latex_expr,
            audience_level=request.audience_level,
            domain=request.domain,
            context=request.context or "auto"
        )
        
        process_result = await use_case.execute(use_case_request)
        
        # Create TTS options
        tts_options = TTSOptions(
            voice_id=request.voice_id,
            rate=request.rate,
            pitch=request.pitch,
            volume=request.volume,
            format=request.format,
            sample_rate=request.sample_rate
        )
        
        # Synthesize speech
        audio_data = await tts_provider.synthesize(
            process_result.speech_text,
            tts_options
        )
        
        # Stream audio data
        audio_stream = io.BytesIO(audio_data.data)
        
        # Determine media type
        media_type = f"audio/{audio_data.format.value}"
        
        return StreamingResponse(
            audio_stream,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename=expression.{audio_data.format.value}",
                "X-Audio-Duration": str(audio_data.duration_seconds),
                "X-Processing-Time": str(process_result.processing_time_ms)
            }
        )
        
    except ValueError as e:
        logger.warning("Invalid stream request", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Stream synthesis failed")
        raise HTTPException(status_code=500, detail="Stream synthesis failed")


@router.get(
    "/history",
    summary="Get processing history",
    description="Get recent expression processing history (if caching is enabled)"
)
async def get_processing_history(
    pagination: PaginationParams = Depends(PaginationParams),
) -> List[dict]:
    """
    Get recent expression processing history.
    
    This would typically query a database or cache for recent expressions.
    Currently returns empty list as it's not implemented.
    """
    # TODO: Implement history tracking
    return []