"""
User Model Module

This module defines the User and ChatProfile database models.
Users can have multiple chat profiles for different learning contexts.

Tables:
    - users: Core user information (login details)
    - chat_profiles: User's chat preferences/personas
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class User(Base):
    """
    User model for authentication and account management.
    
    This table stores core user information like login credentials.
    Sensitive data (password) is stored as a hash, never plain text.
    
    Attributes:
        id (int): Primary key, auto-incrementing
        email (str): User's email, used for login (unique)
        username (str): Display name (unique)
        hashed_password (str): Bcrypt hashed password
        is_active (bool): Whether account is active
        created_at (datetime): Account creation timestamp
        updated_at (datetime): Last update timestamp
        
    Relationships:
        chat_profiles: User's saved chat profiles
        conversations: User's chat conversations
    """
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Login credentials
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Account status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    # One user can have many chat profiles
    chat_profiles = relationship(
        "ChatProfile",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # One user can have many conversations
    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class ChatProfile(Base):
    """
    Chat Profile model for personalized chat experiences.
    
    Similar to ChatGPT's custom instructions, users can create
    profiles that affect how the bot responds to them.
    
    Attributes:
        id (int): Primary key
        user_id (int): Foreign key to users table
        name (str): Profile name (e.g., "Math Study", "History Research")
        description (str): What this profile is for
        learning_style (str): Preferred learning approach
        difficulty_level (str): beginner/intermediate/advanced
        is_default (bool): Whether this is the user's default profile
        created_at (datetime): Creation timestamp
        
    Relationships:
        user: The user who owns this profile
    """
    __tablename__ = "chat_profiles"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign key to users
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Profile details
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Learning preferences
    # Defines how the bot should guide the user
    learning_style = Column(
        String(50),
        default="guided"  # Options: guided, socratic, exploratory
    )
    
    # Difficulty affects how much detail is given in hints
    difficulty_level = Column(
        String(20),
        default="intermediate"  # Options: beginner, intermediate, advanced
    )
    
    # Only one profile can be default per user
    is_default = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    user = relationship("User", back_populates="chat_profiles")
