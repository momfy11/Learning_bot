"""
Chat Schemas Module

Pydantic schemas for chat-related API requests and responses.
Handles messages, conversations, and training question data.

Schemas:
    - MessageCreate/Response: Individual chat messages
    - ConversationCreate/Response: Chat sessions
    - ChatRequest/Response: Real-time chat interactions
    - TrainingQuestionCreate: Anonymized questions for training
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ====================
# Message Schemas
# ====================

class MessageCreate(BaseModel):
    """
    Schema for creating a new message.
    
    Attributes:
        content (str): The message text
        role (str): 'user' or 'assistant'
        is_voice (bool): Whether sent via voice
    """
    content: str = Field(
        ...,
        min_length=1,
        description="Message content text"
    )
    role: str = Field(
        default="user",
        description="Message sender: 'user' or 'assistant'"
    )
    is_voice: bool = Field(
        default=False,
        description="Was this message sent via voice input"
    )


class SourceReference(BaseModel):
    """
    Schema for document source references.
    
    Used to tell users where they can find information.
    
    Attributes:
        document_title (str): Name of the source document
        page_number (int): Page number
        chapter (str): Chapter name/number
        section (str): Section name
        relevance_score (float): How relevant this source is (0-1)
    """
    document_title: str = Field(..., description="Source document name")
    page_number: Optional[int] = Field(None, description="Page number")
    chapter: Optional[str] = Field(None, description="Chapter information")
    section: Optional[str] = Field(None, description="Section name")
    relevance_score: Optional[float] = Field(None, description="Relevance 0-1")


class MessageResponse(BaseModel):
    """
    Schema for returning message data.
    
    Attributes:
        id (int): Message ID
        conversation_id (int): Parent conversation ID
        role (str): Sender role
        content (str): Message text
        is_voice (bool): Voice input flag
        source_references (list): Document references
        avg_relevance_score (float): Average RAG relevance score
        feedback (bool|None): User feedback if given (True=helpful, False=not helpful)
        created_at (datetime): Timestamp
    """
    id: int = Field(..., description="Message ID")
    conversation_id: int = Field(..., description="Parent conversation ID")
    role: str = Field(..., description="Message sender role")
    content: str = Field(..., description="Message content")
    is_voice: bool = Field(..., description="Was voice input")
    source_references: Optional[List[SourceReference]] = Field(
        default=None,
        description="References to source documents"
    )
    avg_relevance_score: Optional[float] = Field(
        default=None,
        description="Average relevance score from RAG search (0-1)"
    )
    feedback: Optional[bool] = Field(
        default=None,
        description="User feedback: True=helpful, False=not helpful, None=no feedback yet"
    )
    created_at: datetime = Field(..., description="Message timestamp")
    
    class Config:
        """Enable ORM mode for SQLAlchemy model conversion."""
        from_attributes = True


# ====================
# Conversation Schemas
# ====================

class ConversationCreate(BaseModel):
    """
    Schema for creating a new conversation.
    
    Attributes:
        title (str): Conversation title
    """
    title: Optional[str] = Field(
        default="New Conversation",
        max_length=255,
        description="Conversation title"
    )


class ConversationResponse(BaseModel):
    """
    Schema for returning conversation data with messages.
    
    Attributes:
        id (int): Conversation ID
        title (str): Conversation title
        created_at (datetime): Start timestamp
        updated_at (datetime): Last message timestamp
        messages (list): All messages in conversation
    """
    id: int = Field(..., description="Conversation ID")
    title: str = Field(..., description="Conversation title")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    messages: List[MessageResponse] = Field(
        default=[],
        description="Messages in this conversation"
    )
    
    class Config:
        """Enable ORM mode for SQLAlchemy model conversion."""
        from_attributes = True


class ConversationListResponse(BaseModel):
    """
    Schema for listing conversations (without full messages).
    
    Used for sidebar/history view to avoid loading all messages.
    
    Attributes:
        id (int): Conversation ID
        title (str): Conversation title
        created_at (datetime): Start timestamp
        updated_at (datetime): Last activity
        message_count (int): Number of messages
    """
    id: int = Field(..., description="Conversation ID")
    title: str = Field(..., description="Conversation title")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    message_count: int = Field(default=0, description="Number of messages")
    
    class Config:
        """Enable ORM mode for SQLAlchemy model conversion."""
        from_attributes = True


# ====================
# Image Schema
# ====================

class ImageData(BaseModel):
    """
    Schema for image attachment data.
    
    Attributes:
        data (str): Base64 encoded image data URL (data:image/jpeg;base64,...)
        type (str): MIME type of the image
    """
    data: str = Field(..., description="Base64 data URL of the image")
    type: str = Field(..., description="MIME type (image/jpeg, image/png, etc.)")


# ====================
# Chat Request/Response
# ====================

class ChatRequest(BaseModel):
    """
    Schema for sending a chat message and getting a response.
    
    Attributes:
        message (str): User's question/message
        conversation_id (int): Optional existing conversation
        profile_id (int): Optional chat profile to use
        is_voice (bool): Whether input was voice
        images (list): Optional list of image attachments
    """
    message: str = Field(
        default="",
        description="User's question or message"
    )
    conversation_id: Optional[int] = Field(
        default=None,
        description="Existing conversation ID (creates new if not provided)"
    )
    profile_id: Optional[int] = Field(
        default=None,
        description="Chat profile ID for personalized responses"
    )
    is_voice: bool = Field(
        default=False,
        description="Was this a voice input"
    )
    images: Optional[List[ImageData]] = Field(
        default=None,
        description="Optional list of image attachments (max 4)"
    )


class ChatResponse(BaseModel):
    """
    Schema for bot response to a chat message.
    
    The bot provides hints/guidance rather than direct answers.
    
    Attributes:
        message (str): Bot's response (hint, not answer!)
        conversation_id (int): Conversation this belongs to
        source_references (list): Where to find the answer
        topic_hint (str): Brief topic description
        suggested_reading (str): What to read/study
    """
    message: str = Field(
        ...,
        description="Bot's guiding response"
    )
    conversation_id: int = Field(
        ...,
        description="Conversation ID"
    )
    source_references: List[SourceReference] = Field(
        default=[],
        description="Document references for further reading"
    )
    topic_hint: Optional[str] = Field(
        default=None,
        description="Brief hint about the topic"
    )
    suggested_reading: Optional[str] = Field(
        default=None,
        description="Suggested materials to study"
    )


# ====================
# Training Data Schemas
# ====================

class TrainingQuestionCreate(BaseModel):
    """
    Schema for saving anonymized questions for training.
    
    NOTE: This is separated from user data for privacy!
    
    Attributes:
        question_text (str): The question (no user info)
        topic_category (str): Detected topic
        difficulty_inferred (str): Guessed difficulty
    """
    question_text: str = Field(
        ...,
        description="The question text (anonymized)"
    )
    topic_category: Optional[str] = Field(
        default=None,
        description="Auto-detected topic category"
    )
    difficulty_inferred: Optional[str] = Field(
        default=None,
        description="Inferred difficulty level"
    )


class FeedbackRequest(BaseModel):
    """
    Schema for user feedback on a bot response.
    
    Used to track which responses were helpful.
    Linked to specific messages for analytics.
    
    Attributes:
        message_id (int): ID of the assistant message being rated
        is_helpful (bool): True = thumbs up, False = thumbs down
    """
    message_id: int = Field(..., description="Message ID to give feedback on")
    is_helpful: bool = Field(..., description="True = thumbs up, False = thumbs down")


class FeedbackResponse(BaseModel):
    """
    Schema for feedback confirmation response.
    
    Attributes:
        message_id (int): The message that was rated
        is_helpful (bool): The feedback value
        created_at (datetime): When feedback was given
    """
    message_id: int = Field(..., description="Message that was rated")
    is_helpful: bool = Field(..., description="The feedback given")
    created_at: datetime = Field(..., description="Feedback timestamp")
