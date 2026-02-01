"""API Schemas Package"""

from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, UserUpdate,
    ChatProfileCreate, ChatProfileResponse, ChatProfileUpdate,
    Token, TokenData
)
from app.schemas.chat import (
    MessageCreate, MessageResponse,
    ConversationCreate, ConversationResponse, ConversationListResponse,
    ChatRequest, ChatResponse,
    TrainingQuestionCreate, FeedbackRequest
)
from app.schemas.document import (
    DocumentCreate, DocumentResponse, DocumentListResponse,
    DocumentChunkResponse, SearchResult
)

__all__ = [
    # User schemas
    "UserCreate", "UserLogin", "UserResponse", "UserUpdate",
    "ChatProfileCreate", "ChatProfileResponse", "ChatProfileUpdate",
    "Token", "TokenData",
    # Chat schemas
    "MessageCreate", "MessageResponse",
    "ConversationCreate", "ConversationResponse", "ConversationListResponse",
    "ChatRequest", "ChatResponse",
    "TrainingQuestionCreate", "FeedbackRequest",
    # Document schemas
    "DocumentCreate", "DocumentResponse", "DocumentListResponse",
    "DocumentChunkResponse", "SearchResult",
]
