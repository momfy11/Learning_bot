"""API Routers Package"""

from app.routers.auth import router as auth_router
from app.routers.chat import router as chat_router
from app.routers.documents import router as documents_router
from app.routers.voice import router as voice_router
from app.routers.profiles import router as profiles_router

__all__ = [
    "auth_router",
    "chat_router",
    "documents_router",
    "voice_router",
    "profiles_router",
]
