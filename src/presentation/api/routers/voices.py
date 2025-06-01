"""
Voice management API endpoints.

This module provides endpoints for listing and managing TTS voices.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query

from src.adapters.tts_providers import TTSProviderAdapter
from src.infrastructure.logging import get_logger
from ..dependencies import get_tts_provider
from ..schemas import VoiceInfo, VoiceListResponse


router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/",
    response_model=VoiceListResponse,
    summary="List available voices",
    description="Get list of all available TTS voices"
)
async def list_voices(
    language: Optional[str] = Query(
        None,
        description="Filter by language code (e.g., 'en-US', 'en')",
        example="en-US"
    ),
    gender: Optional[str] = Query(
        None,
        description="Filter by voice gender (male, female, neutral)",
        example="female"
    ),
    tts_provider: TTSProviderAdapter = Depends(get_tts_provider)
) -> VoiceListResponse:
    """
    List all available voices from the TTS provider.
    
    Supports filtering by language and gender.
    """
    try:
        logger.debug(
            "Listing voices",
            language_filter=language,
            gender_filter=gender
        )
        
        # Get voices from provider
        voices = await tts_provider.list_voices(language=language)
        
        # Convert to API schema and apply gender filter
        voice_infos = []
        for voice in voices:
            # Apply gender filter if specified
            if gender and voice.gender.value.lower() != gender.lower():
                continue
            
            voice_info = VoiceInfo(
                id=voice.id,
                name=voice.name,
                language=voice.language,
                gender=voice.gender.value,
                description=voice.description,
                styles=voice.styles
            )
            voice_infos.append(voice_info)
        
        logger.info(
            "Listed voices",
            total_count=len(voice_infos),
            language_filter=language,
            gender_filter=gender
        )
        
        return VoiceListResponse(
            voices=voice_infos,
            total_count=len(voice_infos)
        )
        
    except Exception as e:
        logger.exception("Failed to list voices")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve voice list"
        )


@router.get(
    "/{voice_id}",
    response_model=VoiceInfo,
    summary="Get voice details",
    description="Get detailed information about a specific voice"
)
async def get_voice(
    voice_id: str,
    tts_provider: TTSProviderAdapter = Depends(get_tts_provider)
) -> VoiceInfo:
    """
    Get detailed information about a specific voice.
    
    - **voice_id**: The voice identifier to look up
    """
    try:
        logger.debug("Getting voice details", voice_id=voice_id)
        
        # Get all voices and find the requested one
        voices = await tts_provider.list_voices()
        
        for voice in voices:
            if voice.id == voice_id:
                return VoiceInfo(
                    id=voice.id,
                    name=voice.name,
                    language=voice.language,
                    gender=voice.gender.value,
                    description=voice.description,
                    styles=voice.styles
                )
        
        # Voice not found
        logger.warning("Voice not found", voice_id=voice_id)
        raise HTTPException(
            status_code=404,
            detail=f"Voice '{voice_id}' not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get voice details", voice_id=voice_id)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve voice details"
        )


@router.get(
    "/languages/",
    response_model=List[str],
    summary="List supported languages",
    description="Get list of all supported language codes"
)
async def list_languages(
    tts_provider: TTSProviderAdapter = Depends(get_tts_provider)
) -> List[str]:
    """
    Get list of all supported language codes.
    
    Returns unique language codes from all available voices.
    """
    try:
        logger.debug("Listing supported languages")
        
        # Get all voices
        voices = await tts_provider.list_voices()
        
        # Extract unique languages
        languages = list(set(voice.language for voice in voices))
        languages.sort()
        
        logger.info("Listed languages", count=len(languages))
        
        return languages
        
    except Exception as e:
        logger.exception("Failed to list languages")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve language list"
        )


@router.get(
    "/test/{voice_id}",
    summary="Test voice",
    description="Test a voice with sample text"
)
async def test_voice(
    voice_id: str,
    text: str = Query(
        "The derivative of sine x is cosine x",
        description="Text to synthesize for testing",
        max_length=200
    ),
    tts_provider: TTSProviderAdapter = Depends(get_tts_provider)
) -> dict:
    """
    Test a voice by synthesizing sample text.
    
    Returns metadata about the synthesis without the actual audio.
    """
    try:
        logger.debug("Testing voice", voice_id=voice_id, text_length=len(text))
        
        # Verify voice exists
        voices = await tts_provider.list_voices()
        voice_exists = any(voice.id == voice_id for voice in voices)
        
        if not voice_exists:
            raise HTTPException(
                status_code=404,
                detail=f"Voice '{voice_id}' not found"
            )
        
        # In a full implementation, we would synthesize the text here
        # For now, just return success
        logger.info("Voice test completed", voice_id=voice_id)
        
        return {
            "voice_id": voice_id,
            "test_text": text,
            "status": "success",
            "message": f"Voice '{voice_id}' is available for synthesis"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Voice test failed", voice_id=voice_id)
        raise HTTPException(
            status_code=500,
            detail="Voice test failed"
        )