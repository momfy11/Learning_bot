"""
Chat Profiles Router Module

This module handles chat profile management:
- Create custom learning profiles
- Update profile settings
- Delete profiles

Similar to ChatGPT's custom instructions feature.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.user import User, ChatProfile
from app.schemas.user import (
    ChatProfileCreate, ChatProfileUpdate, ChatProfileResponse
)
from app.services.auth_service import get_current_user

# Create router
router = APIRouter(
    prefix="/profiles",
    tags=["Chat Profiles"]
)


@router.post(
    "/",
    response_model=ChatProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a chat profile",
    description="Create a new chat profile for personalized learning."
)
async def create_profile(
    profile_data: ChatProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ChatProfileResponse:
    """
    Create a new chat profile.
    
    Profiles allow users to customize how the bot responds:
    - Learning style: guided, socratic, exploratory
    - Difficulty: beginner, intermediate, advanced
    
    Args:
        profile_data (ChatProfileCreate): Profile settings:
            - name: Profile name (e.g., "Math Study")
            - description: What this profile is for
            - learning_style: How the bot should guide
            - difficulty_level: How detailed hints should be
            - is_default: Set as default profile
        current_user (User): Authenticated user
        db (AsyncSession): Database session
    
    Returns:
        ChatProfileResponse: Created profile data
    
    Example:
        POST /api/profiles/
        {
            "name": "Math Study",
            "description": "For studying calculus",
            "learning_style": "socratic",
            "difficulty_level": "intermediate"
        }
    """
    # If setting as default, unset other defaults
    if profile_data.is_default:
        result = await db.execute(
            select(ChatProfile).where(
                ChatProfile.user_id == current_user.id,
                ChatProfile.is_default == True
            )
        )
        for profile in result.scalars():
            profile.is_default = False
    
    # Create new profile
    new_profile = ChatProfile(
        user_id=current_user.id,
        name=profile_data.name,
        description=profile_data.description,
        learning_style=profile_data.learning_style,
        difficulty_level=profile_data.difficulty_level,
        is_default=profile_data.is_default
    )
    
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)
    
    return new_profile


@router.get(
    "/",
    response_model=List[ChatProfileResponse],
    summary="List chat profiles",
    description="Get all chat profiles for the current user."
)
async def list_profiles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[ChatProfileResponse]:
    """
    List all chat profiles for the current user.
    
    Args:
        current_user (User): Authenticated user
        db (AsyncSession): Database session
    
    Returns:
        List[ChatProfileResponse]: User's chat profiles
    """
    result = await db.execute(
        select(ChatProfile)
        .where(ChatProfile.user_id == current_user.id)
        .order_by(ChatProfile.created_at.desc())
    )
    
    return result.scalars().all()


@router.get(
    "/{profile_id}",
    response_model=ChatProfileResponse,
    summary="Get a profile",
    description="Get details of a specific chat profile."
)
async def get_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ChatProfileResponse:
    """
    Get a specific chat profile.
    
    Args:
        profile_id (int): ID of the profile
        current_user (User): Authenticated user
        db (AsyncSession): Database session
    
    Returns:
        ChatProfileResponse: Profile details
    
    Raises:
        HTTPException 404: If profile not found
    """
    result = await db.execute(
        select(ChatProfile).where(
            ChatProfile.id == profile_id,
            ChatProfile.user_id == current_user.id
        )
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return profile


@router.put(
    "/{profile_id}",
    response_model=ChatProfileResponse,
    summary="Update a profile",
    description="Update a chat profile's settings."
)
async def update_profile(
    profile_id: int,
    profile_update: ChatProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ChatProfileResponse:
    """
    Update a chat profile.
    
    Args:
        profile_id (int): ID of the profile to update
        profile_update (ChatProfileUpdate): Fields to update
        current_user (User): Authenticated user
        db (AsyncSession): Database session
    
    Returns:
        ChatProfileResponse: Updated profile
    
    Raises:
        HTTPException 404: If profile not found
    """
    result = await db.execute(
        select(ChatProfile).where(
            ChatProfile.id == profile_id,
            ChatProfile.user_id == current_user.id
        )
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    # If setting as default, unset others
    if profile_update.is_default:
        other_result = await db.execute(
            select(ChatProfile).where(
                ChatProfile.user_id == current_user.id,
                ChatProfile.is_default == True,
                ChatProfile.id != profile_id
            )
        )
        for other_profile in other_result.scalars():
            other_profile.is_default = False
    
    # Update fields that were provided
    update_data = profile_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    await db.commit()
    await db.refresh(profile)
    
    return profile


@router.delete(
    "/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a profile",
    description="Delete a chat profile."
)
async def delete_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a chat profile.
    
    Args:
        profile_id (int): ID of the profile to delete
        current_user (User): Authenticated user
        db (AsyncSession): Database session
    
    Raises:
        HTTPException 404: If profile not found
    """
    result = await db.execute(
        select(ChatProfile).where(
            ChatProfile.id == profile_id,
            ChatProfile.user_id == current_user.id
        )
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    await db.delete(profile)
    await db.commit()
