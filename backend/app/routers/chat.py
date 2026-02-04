"""
Chat Router Module

This module handles chat-related endpoints:
- Send messages and get learning guidance (not direct answers!)
- Manage conversations
- Submit feedback for training

The key feature: Bot provides hints and tells WHERE to find answers,
not the answers themselves.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.chat import Conversation, Message, TrainingQuestion, MessageFeedback
from app.schemas.chat import (
    ChatRequest, ChatResponse,
    ConversationCreate, ConversationResponse, ConversationListResponse,
    MessageResponse, FeedbackRequest, FeedbackResponse, SourceReference
)
from app.services.auth_service import get_current_user
from app.services.llm_service import generate_learning_response
from app.services.rag_service import search_documents

import json

# Create router
router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.post(
    "/send",
    response_model=ChatResponse,
    summary="Send a message and get learning guidance",
    description="Send a question and receive hints about where to find the answer."
)
async def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """
    Send a message and receive learning guidance.
    
    IMPORTANT: This bot doesn't give direct answers!
    Instead, it provides:
    - Brief topic hints
    - References to where the answer can be found (book, page, chapter)
    - Suggested reading materials
    
    Args:
        request (ChatRequest): Chat request containing:
            - message: The user's question
            - conversation_id: Optional existing conversation ID
            - profile_id: Optional chat profile for personalization
            - is_voice: Whether this was a voice input
        current_user (User): Authenticated user
        db (AsyncSession): Database session
    
    Returns:
        ChatResponse: Bot's response with:
            - message: Guiding response text
            - conversation_id: The conversation ID
            - source_references: Where to find the answer
            - topic_hint: Brief description of the topic
            - suggested_reading: What to study
    
    Example:
        POST /api/chat/send
        {
            "message": "What is photosynthesis?",
            "conversation_id": null
        }
        
        Response:
        {
            "message": "Great question about plant biology! This topic 
                       involves how plants convert light into energy...",
            "source_references": [
                {"document_title": "Biology 101", "page_number": 45, 
                 "chapter": "Chapter 3: Plant Cells"}
            ],
            "topic_hint": "Plant energy conversion process",
            "suggested_reading": "Review Chapter 3 of Biology 101"
        }
    """
    # Get or create conversation
    if request.conversation_id:
        # Verify conversation belongs to user
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == request.conversation_id,
                Conversation.user_id == current_user.id
            )
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
    else:
        # Create new conversation
        # Use first few words of message as title (or "Image" if no text)
        if request.message:
            title = request.message[:50] + "..." if len(request.message) > 50 else request.message
        elif request.images:
            title = f"Image conversation ({len(request.images)} image{'s' if len(request.images) > 1 else ''})"
        else:
            title = "New Conversation"
        conversation = Conversation(
            user_id=current_user.id,
            title=title
        )
        db.add(conversation)
        await db.flush()  # Get ID without committing
    
    # Save user's message (content can be empty if only images)
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message or "[Image]",
        is_voice=request.is_voice
    )
    db.add(user_message)
    await db.flush()  # Ensure message is in session for history query
    
    # Get conversation history for context (EXCLUDING the current user message we just added)
    history_result = await db.execute(
        select(Message)
        .where(
            Message.conversation_id == conversation.id,
            Message.id != user_message.id  # Exclude the message we just added
        )
        .order_by(Message.created_at)
    )
    previous_messages = history_result.scalars().all()
    
    # Format history for LLM
    conversation_history = [
        {"role": msg.role, "content": msg.content}
        for msg in previous_messages
    ]
    
    print(f"📜 Retrieved {len(conversation_history)} messages from conversation {conversation.id}")
    if conversation_history:
        print(f"   Last message was: {conversation_history[-1]['role']}: {conversation_history[-1]['content'][:50]}...")
    
    # Extract image data if provided
    images = None
    if request.images:
        images = [{"data": img.data, "type": img.type} for img in request.images]
    
    # Search documents for relevant content (RAG) - only if text message
    search_results = []
    if request.message:
        search_results = await search_documents(
            query=request.message,
            db=db
        )
    
    # Generate learning response using LLM
    # This is where the "don't give answer, give guidance" magic happens
    llm_response = await generate_learning_response(
        question=request.message,
        search_results=search_results,
        profile_id=request.profile_id,
        db=db,
        user_id=current_user.id,
        conversation_history=conversation_history,
        images=images
    )
    
    # Convert search results to source references
    source_references = [
        SourceReference(
            document_title=result.document_title,
            page_number=result.page_number,
            chapter=result.chapter,
            section=result.section,
            relevance_score=result.relevance_score
        )
        for result in search_results
    ]
    
    # Calculate average relevance score for analytics
    avg_relevance = None
    if search_results:
        avg_relevance = sum(r.relevance_score for r in search_results) / len(search_results)
    
    # Save assistant's response with relevance score
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=llm_response["message"],
        source_references=json.dumps([ref.model_dump() for ref in source_references]),
        avg_relevance_score=avg_relevance
    )
    db.add(assistant_message)
    
    # Save anonymized question for training (separate from user data!)
    training_question = TrainingQuestion(
        question_text=request.message,
        topic_category=llm_response.get("topic_hint"),
        difficulty_inferred=None  # Could be enhanced later
    )
    db.add(training_question)
    
    await db.commit()
    
    return ChatResponse(
        message=llm_response["message"],
        conversation_id=conversation.id,
        source_references=source_references,
        topic_hint=llm_response.get("topic_hint"),
        suggested_reading=llm_response.get("suggested_reading")
    )


@router.get(
    "/conversations",
    response_model=List[ConversationListResponse],
    summary="List user's conversations",
    description="Get a list of all conversations for the current user."
)
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[ConversationListResponse]:
    """
    Get all conversations for the current user.
    
    Returns conversation summaries (not full messages) for sidebar/history.
    
    Args:
        current_user (User): Authenticated user
        db (AsyncSession): Database session
    
    Returns:
        List[ConversationListResponse]: List of conversation summaries
    
    Example:
        GET /api/chat/conversations
        Authorization: Bearer <token>
    """
    # Get conversations with message count
    result = await db.execute(
        select(
            Conversation,
            func.count(Message.id).label("message_count")
        )
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .where(Conversation.user_id == current_user.id)
        .group_by(Conversation.id)
        .order_by(Conversation.updated_at.desc())
    )
    
    conversations = []
    for row in result.all():
        conv = row[0]
        count = row[1]
        conversations.append(
            ConversationListResponse(
                id=conv.id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=count
            )
        )
    
    return conversations


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get a specific conversation",
    description="Get a conversation with all its messages."
)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ConversationResponse:
    """
    Get a specific conversation with all messages.
    
    Args:
        conversation_id (int): ID of the conversation to retrieve
        current_user (User): Authenticated user
        db (AsyncSession): Database session
    
    Returns:
        ConversationResponse: Conversation with all messages
    
    Raises:
        HTTPException 404: If conversation not found or doesn't belong to user
    
    Example:
        GET /api/chat/conversations/1
        Authorization: Bearer <token>
    """
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Get messages for this conversation with feedback (eagerly loaded)
    messages_result = await db.execute(
        select(Message)
        .outerjoin(MessageFeedback)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = messages_result.scalars().all()
    
    # Get feedback for all messages in one query
    feedback_result = await db.execute(
        select(MessageFeedback)
        .where(MessageFeedback.message_id.in_([msg.id for msg in messages]))
    )
    feedbacks = {f.message_id: f.is_helpful for f in feedback_result.scalars().all()}
    
    # Parse source references from JSON
    message_responses = []
    for msg in messages:
        refs = None
        if msg.source_references:
            try:
                refs = [SourceReference(**ref) for ref in json.loads(msg.source_references)]
            except (json.JSONDecodeError, TypeError):
                refs = None
        
        message_responses.append(
            MessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                role=msg.role,
                content=msg.content,
                is_voice=msg.is_voice,
                source_references=refs,
                avg_relevance_score=msg.avg_relevance_score,
                feedback=feedbacks.get(msg.id),  # None if no feedback yet
                created_at=msg.created_at
            )
        )
    
    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=message_responses
    )


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation",
    description="Delete a conversation and all its messages."
)
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a conversation and all its messages.
    
    Args:
        conversation_id (int): ID of conversation to delete
        current_user (User): Authenticated user
        db (AsyncSession): Database session
    
    Raises:
        HTTPException 404: If conversation not found
    
    Note:
        Training questions are NOT deleted (they're anonymized and separate).
    """
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    await db.delete(conversation)
    await db.commit()


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Submit feedback on a bot response",
    description="Rate whether a response was helpful (thumbs up/down)."
)
async def submit_feedback(
    feedback: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FeedbackResponse:
    """
    Submit feedback on whether a bot response was helpful.
    
    Creates or updates feedback for a specific message.
    Only works on assistant messages that belong to the current user.
    
    Args:
        feedback (FeedbackRequest): Feedback containing:
            - message_id: ID of the assistant message
            - is_helpful: True = thumbs up, False = thumbs down
        current_user (User): Authenticated user
        db (AsyncSession): Database session
    
    Returns:
        FeedbackResponse: Confirmation with feedback details
    
    Raises:
        HTTPException 404: If message not found or not accessible
        HTTPException 400: If trying to rate a user message
    """
    # Get the message and verify it belongs to user's conversation
    result = await db.execute(
        select(Message)
        .join(Conversation)
        .where(
            Message.id == feedback.message_id,
            Conversation.user_id == current_user.id
        )
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    if message.role != "assistant":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only give feedback on assistant messages"
        )
    
    # Check if feedback already exists
    existing_result = await db.execute(
        select(MessageFeedback).where(MessageFeedback.message_id == message.id)
    )
    existing_feedback = existing_result.scalar_one_or_none()
    
    if existing_feedback:
        # Update existing feedback
        existing_feedback.is_helpful = feedback.is_helpful
        await db.commit()
        await db.refresh(existing_feedback)
        return FeedbackResponse(
            message_id=message.id,
            is_helpful=existing_feedback.is_helpful,
            created_at=existing_feedback.created_at
        )
    else:
        # Create new feedback
        new_feedback = MessageFeedback(
            message_id=message.id,
            is_helpful=feedback.is_helpful
        )
        db.add(new_feedback)
        await db.commit()
        await db.refresh(new_feedback)
        return FeedbackResponse(
            message_id=message.id,
            is_helpful=new_feedback.is_helpful,
            created_at=new_feedback.created_at
        )
