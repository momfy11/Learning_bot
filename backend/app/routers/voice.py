"""
Voice Router Module

This module handles voice-related endpoints.

Note: Main voice processing happens on the frontend using Web Speech API.
The backend provides endpoints for:
- Converting voice transcript to chat response
- Text-to-speech settings (if needed in future)

This keeps it simple - no heavy audio processing on backend.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.auth_service import get_current_user
from app.routers.chat import send_message

# Create router
router = APIRouter(
    prefix="/voice",
    tags=["Voice"]
)


@router.post(
    "/transcript",
    response_model=ChatResponse,
    summary="Process voice transcript",
    description="Process a voice transcript and get a learning response."
)
async def process_voice_transcript(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """
    Process a voice transcript and return a learning response.
    
    This endpoint is essentially the same as /chat/send but explicitly
    marks the message as coming from voice input.
    
    The actual speech-to-text conversion happens on the frontend using
    the browser's Web Speech API. This keeps the backend simple.
    
    Args:
        request (ChatRequest): Chat request with voice transcript:
            - message: The transcribed text from voice input
            - conversation_id: Optional existing conversation
            - profile_id: Optional chat profile
            - is_voice: Should be True for voice inputs
        current_user (User): Authenticated user
        db (AsyncSession): Database session
    
    Returns:
        ChatResponse: Bot's learning guidance response
    
    Example:
        POST /api/voice/transcript
        {
            "message": "What is photosynthesis",
            "is_voice": true
        }
    
    Note:
        The response can be read aloud on the frontend using
        the Web Speech API's SpeechSynthesis feature.
    """
    # Ensure voice flag is set
    request.is_voice = True
    
    # Use the same logic as regular chat
    return await send_message(
        request=request,
        current_user=current_user,
        db=db
    )


@router.get(
    "/settings",
    summary="Get voice settings",
    description="Get voice-related settings for the user."
)
async def get_voice_settings(
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Get voice settings for the frontend.
    
    Returns configuration for the Web Speech API on the frontend.
    This could be expanded to store per-user voice preferences.
    
    Args:
        current_user (User): Authenticated user
    
    Returns:
        dict: Voice configuration settings
    
    Example response:
        {
            "speech_recognition": {
                "language": "en-US",
                "continuous": false,
                "interim_results": true
            },
            "speech_synthesis": {
                "language": "en-US",
                "rate": 1.0,
                "pitch": 1.0
            }
        }
    """
    # Default voice settings
    # Could be stored per-user in database for customization
    return {
        "speech_recognition": {
            "language": "en-US",      # Recognition language
            "continuous": False,       # Stop after one phrase
            "interim_results": True    # Show partial results
        },
        "speech_synthesis": {
            "language": "en-US",      # Voice language
            "rate": 1.0,              # Speech rate (0.1-10)
            "pitch": 1.0,             # Voice pitch (0-2)
            "volume": 1.0             # Volume (0-1)
        },
        "features": {
            "auto_read_response": True,  # Auto-read bot responses
            "push_to_talk": False        # Hold button to record
        }
    }
