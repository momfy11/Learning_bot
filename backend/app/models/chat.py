"""
Chat Model Module

This module defines database models for chat functionality.
Questions are stored separately from user details for training purposes.

Tables:
    - conversations: Chat sessions between user and bot
    - messages: Individual messages within conversations
    - training_questions: Anonymized questions for future training
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Conversation(Base):
    """
    Conversation model representing a chat session.
    
    Each conversation contains multiple messages and belongs to a user.
    Conversations can be named for easy reference.
    
    Attributes:
        id (int): Primary key
        user_id (int): Foreign key to users table
        title (str): Conversation title (auto-generated or user-set)
        created_at (datetime): When conversation started
        updated_at (datetime): Last message timestamp
        
    Relationships:
        user: The user who owns this conversation
        messages: All messages in this conversation
    """
    __tablename__ = "conversations"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign key to users
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Conversation metadata
    title = Column(String(255), default="New Conversation")
    
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
    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )


class Message(Base):
    """
    Message model for individual chat messages.
    
    Stores both user questions and bot responses.
    The role field distinguishes between user and assistant messages.
    
    Attributes:
        id (int): Primary key
        conversation_id (int): Foreign key to conversations table
        role (str): 'user' or 'assistant'
        content (str): The message text
        is_voice (bool): Whether message was sent via voice
        source_references (str): JSON string of document references
        avg_relevance_score (float): Average relevance score from RAG search
        created_at (datetime): Message timestamp
        
    Relationships:
        conversation: The conversation this message belongs to
        feedback: User feedback on this message (if assistant)
    """
    __tablename__ = "messages"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign key to conversations
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id"),
        nullable=False
    )
    
    # Message content
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    
    # Voice indicator
    is_voice = Column(Boolean, default=False)
    
    # Document references (stored as JSON string)
    # Example: '[{"document": "Physics 101", "page": 42, "chapter": "Forces"}]'
    source_references = Column(Text, nullable=True)
    
    # Average relevance score from RAG search (0.0 - 1.0)
    # Helps track how well the bot found relevant content
    avg_relevance_score = Column(Float, nullable=True)
    
    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    feedback = relationship(
        "MessageFeedback",
        back_populates="message",
        uselist=False,  # One-to-one relationship
        cascade="all, delete-orphan"
    )


class MessageFeedback(Base):
    """
    Feedback model for tracking user ratings on bot responses.
    
    Stores thumbs up/down feedback linked to specific messages.
    Used for analytics and improving bot responses.
    
    Attributes:
        id (int): Primary key
        message_id (int): Foreign key to the message being rated
        is_helpful (bool): True = thumbs up, False = thumbs down
        created_at (datetime): When feedback was given
        
    Relationships:
        message: The message this feedback is for
    """
    __tablename__ = "message_feedback"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign key to messages (one-to-one)
    message_id = Column(
        Integer,
        ForeignKey("messages.id"),
        nullable=False,
        unique=True  # Each message can only have one feedback
    )
    
    # Feedback value
    is_helpful = Column(Boolean, nullable=False)  # True = thumbs up, False = thumbs down
    
    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    message = relationship("Message", back_populates="feedback")


class TrainingQuestion(Base):
    """
    Training Question model for storing anonymized questions.
    
    IMPORTANT: This table stores questions SEPARATELY from user details.
    This allows us to use question data for training without exposing
    personal information. Questions are anonymized - no user_id is stored.
    
    Attributes:
        id (int): Primary key
        question_text (str): The question asked (anonymized)
        topic_category (str): Auto-detected topic category
        difficulty_inferred (str): Inferred difficulty level
        was_helpful (bool): Whether user found the response helpful
        created_at (datetime): When question was asked
        
    Note:
        No foreign key to users - this is intentional for privacy!
    """
    __tablename__ = "training_questions"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Question content (NO user_id - intentionally anonymized)
    question_text = Column(Text, nullable=False)
    
    # Metadata for training categorization
    topic_category = Column(String(100), nullable=True)
    difficulty_inferred = Column(String(20), nullable=True)
    
    # Feedback (optional, user can rate if response was helpful)
    was_helpful = Column(Boolean, nullable=True)
    
    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
