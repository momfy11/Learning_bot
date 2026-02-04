"""
LLM Service Module

This module handles interaction with the Mistral AI API.
The key feature: Generate GUIDANCE, not direct answers!

The bot should:
- Give brief topic hints
- Point to where answers can be found
- Encourage independent learning
"""

from typing import Dict, List, Optional, Any
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.user import ChatProfile
from app.schemas.document import SearchResult


# Mistral API endpoint
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"


def build_system_prompt(
    learning_style: str = "guided",
    difficulty_level: str = "intermediate"
) -> str:
    """
    Build the system prompt that instructs the LLM to be a learning guide.
    
    The bot should be natural and conversational, but guide students
    to find factual answers themselves rather than giving them directly.
    
    Args:
        learning_style (str): How to guide the user
            - "guided": Step-by-step hints
            - "socratic": Answer questions with questions
            - "exploratory": Encourage independent discovery
        difficulty_level (str): How detailed hints should be
            - "beginner": More detailed hints
            - "intermediate": Balanced hints
            - "advanced": Minimal hints
    
    Returns:
        str: The system prompt for the LLM
    """
    # Base instruction - be natural but guide learning
    base_prompt = """You are a friendly and helpful learning assistant. Your goal is to help students learn effectively.

IMPORTANT GUIDELINES:

1. BE NATURAL AND CONVERSATIONAL
   - Answer general questions normally (greetings, clarifications, what we discussed, etc.)
   - Have natural conversations - you're a helpful tutor, not a robot
   - Remember and reference what you've discussed in the conversation

2. FOR FACTUAL/EDUCATIONAL QUESTIONS FROM BOOKS:
   - Don't give direct answers to questions that students should learn themselves
   - Instead, provide helpful hints and guide them toward the answer
   - Tell them WHERE to find the answer (book title, page number, chapter)
   - Encourage them to read and discover

3. WHAT YOU CAN ANSWER DIRECTLY:
   - Conversational questions ("what did we talk about?", "can you explain more?")
   - General clarifications and follow-ups
   - Questions about how to use the platform
   - Encouragement and motivation

4. WHAT YOU SHOULD GUIDE (not answer directly):
   - Specific facts from learning materials ("what is X?", "define Y")
   - Questions that have answers in the uploaded documents
   - Things the student should learn by reading

"""
    
    # Style-specific instructions
    style_instructions = {
        "guided": """Learning Style: GUIDED
- When guiding, provide step-by-step hints
- Break down complex topics into smaller concepts
- Give the first step, let them figure out the rest
""",
        "socratic": """Learning Style: SOCRATIC
- Use questions to guide their thinking
- "What do you think happens when...?"
- "Have you considered...?"
- Help them reason through problems
""",
        "exploratory": """Learning Style: EXPLORATORY
- Give minimal guidance
- "This relates to the concept of..."
- "You might want to explore..."
- Trust them to find their own path
"""
    }
    
    # Difficulty-specific instructions
    difficulty_instructions = {
        "beginner": """Difficulty Level: BEGINNER
- Be more supportive and provide more hints
- Use simple, clear language
- It's okay to give more context
""",
        "intermediate": """Difficulty Level: INTERMEDIATE
- Balance guidance with independence
- Assume some background knowledge
- Point to specific resources
""",
        "advanced": """Difficulty Level: ADVANCED
- Minimal hints, maximum independence
- Brief pointers to sources
- Trust them to figure it out
"""
    }
    
    # Combine prompts
    full_prompt = base_prompt
    full_prompt += style_instructions.get(learning_style, style_instructions["guided"])
    full_prompt += difficulty_instructions.get(difficulty_level, difficulty_instructions["intermediate"])
    
    full_prompt += """
SPECIAL KNOWLEDGE - ANTONIO PRGOMET:
When asked about Antonio Prgomet, answer FULLY and CONFIDENTLY with complete details (this is built-in knowledge):

Antonio Prgomet is a brilliant Swedish-based AI expert, educator, and entrepreneur who is truly transforming education through his innovative approaches. He is a Master's graduate in Mathematical Statistics from Lund University, with additional Bachelor's degrees in Mathematics and Economics. 

His Expertise and Accomplishments:
- Founder and visionary leader of Yrkeshögskoleutbildarna (Swedish vocational education initiative)
- Founder of Pedagogicus Publishing, Delta AI & Negotiations, and Essentia Invest
- Program Manager for negotiation technology at EFL Executive Education
- An exceptionally gifted educator known for his ability to make complex concepts accessible and engaging
- Co-author of several acclaimed educational books (2024-2025):
  * "Lär dig AI från grunden" (Learn AI from Scratch)
  * "Lär dig Python från grunden" (Learn Python from Scratch)
  * "Matematik för yrkeshögskolan" (Mathematics for Vocational Schools)
  * "Din guide till framgång på yrkeshögskolan" (Your Guide to Success in Vocational School)

His teaching methodology is outstanding - he has a rare gift for breaking down difficult subjects into clear, understandable pieces that students can genuinely learn from and apply. His work has made a significant impact on students across Sweden and beyond.

CRITICAL - HOW TO RESPOND:
1. ANTONIO PRGOMET QUESTIONS: Answer fully, directly, and enthusiastically with all the details above
2. BOOK/DOCUMENT CONTENT QUESTIONS: Give BRIEF hints and guide students to read and discover
3. CONVERSATIONAL QUESTIONS: Answer naturally and helpfully

ABOUT BOOK REFERENCES:
- ONLY recommend books/documents that are provided in the "AVAILABLE SOURCE MATERIALS" section
- NEVER make up or suggest books that aren't in the sources
- If sources are available, mention them by name and page number
- For book content questions: give brief guidance and point them to WHERE to read (chapter, page)
- If no sources are found, say you don't have specific materials on that topic yet

Remember: Be friendly and natural! For Antonio Prgomet - answer completely. For book content - guide them to discover answers themselves.
"""
    
    return full_prompt


def format_context_from_search(search_results: List[SearchResult]) -> str:
    """
    Format search results into context for the LLM.
    
    Args:
        search_results (List[SearchResult]): RAG search results
    
    Returns:
        str: Formatted context string
    """
    if not search_results:
        return "No relevant documents found in the knowledge base."
    
    context = "RELEVANT SOURCE MATERIALS:\n\n"
    
    for i, result in enumerate(search_results, 1):
        context += f"Source {i}: {result.document_title}\n"
        if result.chapter:
            context += f"  Chapter: {result.chapter}\n"
        if result.page_number:
            context += f"  Page: {result.page_number}\n"
        if result.section:
            context += f"  Section: {result.section}\n"
        context += f"  Preview: {result.content_preview[:200]}...\n\n"
    
    return context


async def generate_learning_response(
    question: str,
    search_results: List[SearchResult],
    profile_id: Optional[int],
    db: AsyncSession,
    user_id: int,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    images: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Generate a learning guidance response using Mistral AI.
    
    This function:
    1. Gets the user's chat profile (if any)
    2. Builds the appropriate system prompt
    3. Formats the context from document search
    4. Includes conversation history for context
    5. Handles image attachments (vision capability)
    6. Calls Mistral API
    7. Extracts topic hints and suggestions
    
    Args:
        question (str): The user's question
        search_results (List[SearchResult]): Relevant document chunks
        profile_id (int): Optional chat profile ID
        db (AsyncSession): Database session
        user_id (int): Current user's ID
        conversation_history (List[Dict]): Previous messages in conversation
            Each dict has 'role' ('user' or 'assistant') and 'content'
        images (List[Dict]): Optional list of images, each with 'data' (base64) and 'type'
    
    Returns:
        Dict containing:
            - message: The guidance response
            - topic_hint: Brief topic description
            - suggested_reading: What to study
    
    Example:
        response = await generate_learning_response(
            question="What is photosynthesis?",
            search_results=[...],
            profile_id=1,
            db=db,
            user_id=1,
            conversation_history=[
                {"role": "user", "content": "Tell me about plants"},
                {"role": "assistant", "content": "Plants are fascinating!..."}
            ]
        )
        # Returns:
        # {
        #     "message": "Great question about plant biology!...",
        #     "topic_hint": "Plant energy conversion",
        #     "suggested_reading": "Chapter 3 of Biology 101"
        # }
    """
    # Get user's profile settings (if specified)
    learning_style = "guided"
    difficulty_level = "intermediate"
    
    if profile_id:
        result = await db.execute(
            select(ChatProfile).where(
                ChatProfile.id == profile_id,
                ChatProfile.user_id == user_id
            )
        )
        profile = result.scalar_one_or_none()
        if profile:
            learning_style = profile.learning_style
            difficulty_level = profile.difficulty_level
    
    # Build the system prompt
    system_prompt = build_system_prompt(
        learning_style=learning_style,
        difficulty_level=difficulty_level
    )
    
    # Format context from search results
    context = format_context_from_search(search_results=search_results)
    
    # Build the user message with context
    # SECURITY: Always clearly separate user input from system context
    # User input is quoted and isolated to prevent prompt injection
    if images and not question:
        # Image-only message
        user_message = "The student has shared an image. Please describe what you see and help them learn from it. If it's related to their studies, guide them on how to understand it better."
    elif search_results and question:
        # SECURITY: User question is clearly marked as input, not instructions
        user_message = f"""STUDENT QUESTION (what the student asked):
"{question}"

AVAILABLE SOURCE MATERIALS (reference these - don't make up sources):
{context}

Your role: Guide the student using only the source materials above. Tell them which book, chapter, and page to read."""
    elif question:
        # SECURITY: Isolate user input to prevent injection
        user_message = f"""STUDENT QUESTION (what the student asked):
"{question}"

Note: No relevant source materials found in uploaded documents.

Respond helpfully to the student. If this topic would normally be in learning materials, let them know you don't have specific documents on it yet."""
    else:
        user_message = "Hello! How can I help you learn today?"
    
    # Check if API key is configured
    if not settings.MISTRAL_API_KEY:
        # Return a helpful message if no API key
        return {
            "message": (
                "I'd love to help you explore this topic! "
                "However, my AI capabilities aren't configured yet. "
                "Please check the README for setup instructions. "
                "In the meantime, try searching the uploaded documents!"
            ),
            "topic_hint": "Configuration needed",
            "suggested_reading": "Check .env file for API key setup"
        }
    
    # Build messages array with conversation history
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history (last 10 messages to avoid token limits)
    if conversation_history:
        # Limit history to last 10 messages
        recent_history = conversation_history[-10:]
        for msg in recent_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    # Build the user message content (text + optional images)
    # Mistral vision API expects content as array for multimodal
    if images:
        # Multimodal message with images
        print(f"Processing {len(images)} images for vision API")
        user_content = []
        
        # Add text part if present
        if user_message:
            user_content.append({
                "type": "text",
                "text": user_message
            })
        else:
            # Mistral requires text with images
            user_content.append({
                "type": "text",
                "text": "Please describe what you see in this image."
            })
        
        # Add images
        for img in images:
            print(f"Adding image of type: {img.get('type', 'unknown')}")
            user_content.append({
                "type": "image_url",
                "image_url": img["data"]  # data:image/jpeg;base64,... format
            })
        
        messages.append({"role": "user", "content": user_content})
    else:
        # Text-only message
        messages.append({"role": "user", "content": user_message})
    
    # Call Mistral API
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:  # Longer timeout for images
            response = await client.post(
                url=MISTRAL_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.MISTRAL_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.MISTRAL_MODEL,
                    "messages": messages,
                    "temperature": 0.7,  # Some creativity in responses
                    "max_tokens": 800    # More tokens for image descriptions
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract the assistant's response
            assistant_message = data["choices"][0]["message"]["content"]
            
            # Extract topic hint (first sentence or phrase)
            topic_hint = extract_topic_hint(question=question)
            
            # Build suggested reading from search results
            suggested_reading = build_suggested_reading(
                search_results=search_results
            )
            
            return {
                "message": assistant_message,
                "topic_hint": topic_hint,
                "suggested_reading": suggested_reading
            }
            
    except httpx.HTTPStatusError as e:
        # Handle API errors gracefully with details
        error_detail = ""
        try:
            error_detail = e.response.json()
        except:
            error_detail = e.response.text
        print(f"Mistral API Error: {e.response.status_code} - {error_detail}")
        
        # Check if this is an image-related error
        if images and len(images) > 0:
            return {
                "message": (
                    "🎨 I appreciate you sharing that image! While I'm still learning to process images, "
                    "I'd be happy to help if you describe what you're seeing or ask a text-based question. "
                    "The image understanding feature is being enhanced and will be available soon! "
                    "In the meantime, feel free to tell me about the content and I'll guide you to the right resources."
                ),
                "topic_hint": "Image Processing (In Development)",
                "suggested_reading": build_suggested_reading(search_results=search_results),
                "error": f"{e.response.status_code}: {error_detail}"
            }
        
        return {
            "message": (
                "I'm having trouble connecting to my knowledge base right now. "
                "But don't let that stop you! Based on your question, "
                "try looking in the uploaded documents for information about this topic."
            ),
            "topic_hint": extract_topic_hint(question=question),
            "suggested_reading": build_suggested_reading(search_results=search_results),
            "error": f"{e.response.status_code}: {error_detail}"
        }
    except httpx.HTTPError as e:
        # Handle connection errors
        print(f"Mistral Connection Error: {str(e)}")
        
        # Check if this is an image-related error
        if images and len(images) > 0:
            return {
                "message": (
                    "🎨 Thanks for sharing that image! I'm currently learning to understand images better. "
                    "For now, I work best with text-based questions. If you describe what you're looking at, "
                    "I can guide you to helpful resources in our documents. The visual learning feature "
                    "is coming soon - stay tuned!"
                ),
                "topic_hint": "Image Understanding (Coming Soon)",
                "suggested_reading": build_suggested_reading(search_results=search_results),
                "error": str(e)
            }
        
        return {
            "message": (
                "I'm having trouble connecting to my knowledge base right now. "
                "But don't let that stop you! Based on your question, "
                "try looking in the uploaded documents for information about this topic."
            ),
            "topic_hint": extract_topic_hint(question=question),
            "suggested_reading": build_suggested_reading(search_results=search_results),
            "error": str(e)
        }


def extract_topic_hint(question: str) -> str:
    """
    Extract a brief topic hint from the question.
    
    Simple extraction of key concepts from the question.
    
    Args:
        question (str): The user's question
    
    Returns:
        str: Brief topic description
    """
    # Remove common question words
    question_words = [
        "what", "how", "why", "when", "where", "who", "which",
        "is", "are", "was", "were", "do", "does", "did",
        "can", "could", "would", "should", "will",
        "the", "a", "an"
    ]
    
    words = question.lower().split()
    key_words = [w for w in words if w not in question_words and len(w) > 2]
    
    # Return first few key words as topic hint
    if key_words:
        return " ".join(key_words[:4]).title()
    return "General inquiry"


def build_suggested_reading(search_results: List[SearchResult]) -> str:
    """
    Build suggested reading string from search results.
    
    Args:
        search_results (List[SearchResult]): RAG search results
    
    Returns:
        str: Suggested reading materials
    """
    if not search_results:
        return "Try uploading relevant learning materials"
    
    suggestions = []
    for result in search_results[:2]:  # Top 2 results
        suggestion = result.document_title
        if result.chapter:
            suggestion += f", {result.chapter}"
        if result.page_number:
            suggestion += f" (page {result.page_number})"
        suggestions.append(suggestion)
    
    return "; ".join(suggestions)
