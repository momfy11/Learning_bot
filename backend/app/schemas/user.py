"""
User Schemas Module

Pydantic schemas for user-related API requests and responses.
These schemas handle validation and serialization of user data.

Schemas:
    - UserCreate: For user registration
    - UserLogin: For authentication
    - UserResponse: For returning user data
    - ChatProfileCreate/Response: For chat profiles
    - Token: For JWT token responses
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ====================
# Authentication Schemas
# ====================

class Token(BaseModel):
    """
    JWT Token response schema.
    
    Attributes:
        access_token (str): The JWT token string
        token_type (str): Token type, always "bearer"
    """
    access_token: str = Field(
        ...,
        description="JWT access token for authentication"
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')"
    )


class TokenData(BaseModel):
    """
    Data extracted from JWT token.
    
    Attributes:
        email (str): User's email from token
    """
    email: Optional[str] = Field(
        default=None,
        description="User email extracted from token"
    )


# ====================
# User Schemas
# ====================

class UserCreate(BaseModel):
    """
    Schema for user registration.
    
    Attributes:
        email (str): Valid email address
        username (str): Display name (3-50 chars)
        password (str): Password (min 6 chars)
    """
    email: EmailStr = Field(
        ...,
        description="User's email address for login"
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Display name (3-50 characters)"
    )
    password: str = Field(
        ...,
        min_length=6,
        description="Password (minimum 6 characters)"
    )


class UserLogin(BaseModel):
    """
    Schema for user login.
    
    Attributes:
        email (str): User's email
        password (str): User's password
    """
    email: EmailStr = Field(
        ...,
        description="Email address for login"
    )
    password: str = Field(
        ...,
        description="Account password"
    )


class UserUpdate(BaseModel):
    """
    Schema for updating user profile.
    
    All fields are optional - only provided fields are updated.
    
    Attributes:
        username (str): New display name
        email (str): New email address
    """
    username: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=50,
        description="New display name"
    )
    email: Optional[EmailStr] = Field(
        default=None,
        description="New email address"
    )


class UserResponse(BaseModel):
    """
    Schema for returning user data in API responses.
    
    Note: Never includes password!
    
    Attributes:
        id (int): User ID
        email (str): User's email
        username (str): Display name
        is_active (bool): Account status
        created_at (datetime): Registration date
    """
    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User's email")
    username: str = Field(..., description="Display name")
    is_active: bool = Field(..., description="Account active status")
    created_at: datetime = Field(..., description="Registration timestamp")
    
    class Config:
        """Enable ORM mode for SQLAlchemy model conversion."""
        from_attributes = True


# ====================
# Chat Profile Schemas
# ====================

class ChatProfileCreate(BaseModel):
    """
    Schema for creating a chat profile.
    
    Attributes:
        name (str): Profile name
        description (str): What this profile is for
        learning_style (str): guided/socratic/exploratory
        difficulty_level (str): beginner/intermediate/advanced
        is_default (bool): Set as default profile
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Profile name (e.g., 'Math Study')"
    )
    description: Optional[str] = Field(
        default=None,
        description="Description of what this profile is for"
    )
    learning_style: str = Field(
        default="guided",
        description="Learning approach: guided, socratic, or exploratory"
    )
    difficulty_level: str = Field(
        default="intermediate",
        description="Difficulty: beginner, intermediate, or advanced"
    )
    is_default: bool = Field(
        default=False,
        description="Whether this is the default profile"
    )


class ChatProfileUpdate(BaseModel):
    """
    Schema for updating a chat profile.
    
    All fields optional - only provided fields are updated.
    """
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="New profile name"
    )
    description: Optional[str] = Field(
        default=None,
        description="New description"
    )
    learning_style: Optional[str] = Field(
        default=None,
        description="New learning style"
    )
    difficulty_level: Optional[str] = Field(
        default=None,
        description="New difficulty level"
    )
    is_default: Optional[bool] = Field(
        default=None,
        description="Set as default profile"
    )


class ChatProfileResponse(BaseModel):
    """
    Schema for returning chat profile data.
    
    Attributes:
        id (int): Profile ID
        name (str): Profile name
        description (str): Profile description
        learning_style (str): Learning approach
        difficulty_level (str): Difficulty setting
        is_default (bool): Default status
        created_at (datetime): Creation timestamp
    """
    id: int = Field(..., description="Profile ID")
    name: str = Field(..., description="Profile name")
    description: Optional[str] = Field(None, description="Profile description")
    learning_style: str = Field(..., description="Learning style setting")
    difficulty_level: str = Field(..., description="Difficulty level")
    is_default: bool = Field(..., description="Is default profile")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        """Enable ORM mode for SQLAlchemy model conversion."""
        from_attributes = True
