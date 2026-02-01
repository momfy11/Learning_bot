"""
Authentication Router Module

This module handles user authentication endpoints:
- User registration
- User login
- Token refresh
- Get current user

All passwords are hashed before storage. JWT tokens are used for auth.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate, UserResponse, UserUpdate, Token
)
from app.services.auth_service import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user
)

# Create router with prefix and tags for API docs
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# OAuth2 scheme for token extraction from headers
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email, username, and password."
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account.
    
    Args:
        user_data (UserCreate): User registration data containing:
            - email: Valid email address (must be unique)
            - username: Display name (must be unique, 3-50 chars)
            - password: Password (min 6 characters)
        db (AsyncSession): Database session (injected by FastAPI)
    
    Returns:
        UserResponse: Created user data (without password)
    
    Raises:
        HTTPException 400: If email or username already exists
    
    Example:
        POST /api/auth/register
        {
            "email": "student@example.com",
            "username": "student123",
            "password": "securepassword"
        }
    """
    # Check if email already exists
    existing_email = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if existing_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if existing_username.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user with hashed password
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(password=user_data.password)
    )
    
    # Save to database
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@router.post(
    "/login",
    response_model=Token,
    summary="Login and get access token",
    description="Authenticate with email and password to receive a JWT token."
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Token:
    """
    Authenticate user and return JWT token.
    
    Args:
        form_data (OAuth2PasswordRequestForm): Login credentials:
            - username: Actually the email (OAuth2 spec uses 'username')
            - password: User's password
        db (AsyncSession): Database session (injected by FastAPI)
    
    Returns:
        Token: JWT access token for subsequent requests
    
    Raises:
        HTTPException 401: If credentials are invalid
    
    Note:
        OAuth2 spec uses 'username' field, but we use email for login.
        The token should be included in subsequent requests as:
        Authorization: Bearer <token>
    
    Example:
        POST /api/auth/login
        Content-Type: application/x-www-form-urlencoded
        
        username=student@example.com&password=securepassword
    """
    # Find user by email (OAuth2 form uses 'username' field)
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    # Verify user exists and password is correct
    if not user or not verify_password(
        plain_password=form_data.password,
        hashed_password=user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled"
        )
    
    # Create and return JWT token
    access_token = create_access_token(
        data={"sub": user.email}
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the currently authenticated user's information."
)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's information.
    
    Args:
        current_user (User): Current user (extracted from JWT token)
    
    Returns:
        UserResponse: User data (without password)
    
    Note:
        Requires valid JWT token in Authorization header.
    
    Example:
        GET /api/auth/me
        Authorization: Bearer <your_jwt_token>
    """
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user",
    description="Update the current user's profile information."
)
async def update_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's profile information.
    
    Args:
        user_update (UserUpdate): Fields to update (all optional):
            - username: New display name
            - email: New email address
        current_user (User): Current user (from JWT)
        db (AsyncSession): Database session
    
    Returns:
        UserResponse: Updated user data
    
    Raises:
        HTTPException 400: If new email/username already exists
    
    Example:
        PUT /api/auth/me
        Authorization: Bearer <token>
        {
            "username": "new_username"
        }
    """
    # Check if new email is already taken (if provided)
    if user_update.email and user_update.email != current_user.email:
        existing = await db.execute(
            select(User).where(User.email == user_update.email)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = user_update.email
    
    # Check if new username is already taken (if provided)
    if user_update.username and user_update.username != current_user.username:
        existing = await db.execute(
            select(User).where(User.username == user_update.username)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        current_user.username = user_update.username
    
    # Update timestamp
    current_user.updated_at = datetime.now(timezone.utc)
    
    # Save changes
    await db.commit()
    await db.refresh(current_user)
    
    return current_user
