"""
Learning Bot - Main Application Entry Point

This is the main FastAPI application that brings everything together.
Run with: uvicorn app.main:app --reload

The Learning Bot is a chatbot that guides users to find answers
rather than giving direct responses. It uses RAG to reference
specific locations in uploaded documents.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables, async_session
from app.routers import (
    auth_router,
    chat_router,
    documents_router,
    voice_router,
    profiles_router
)
from app.services.rag_service import scan_documents_folder


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown tasks:
    - Startup: Create database tables, scan documents folder
    - Shutdown: Clean up resources
    
    Args:
        app (FastAPI): The FastAPI application instance
    
    Yields:
        None: Control is returned to the application
    """
    # Startup
    print("🚀 Starting Learning Bot...")
    try:
        await create_tables()
        print("✅ Database tables created")
    except Exception as e:
        print(f"⚠️ Database setup warning: {e}")
        # Continue anyway - tables might already exist
    
    # Scan documents folder for new files (non-blocking)
    try:
        print("📂 Scanning documents folder...")
        async with async_session() as db:
            result = await scan_documents_folder(db)
            print(f"📚 Documents: {result['new_count']} new, {result['existing_count']} existing")
            if result['errors']:
                print(f"⚠️ Errors: {len(result['errors'])}")
    except Exception as e:
        print(f"⚠️ Document scan warning: {e}")
        # Continue anyway - documents can be uploaded later
    
    print("✅ Learning Bot ready!")
    
    yield  # Application runs here
    
    # Shutdown
    print("👋 Shutting down Learning Bot...")


# Create FastAPI application
app = FastAPI(
    title="Learning Bot API",
    description="""
    ## A chatbot that guides learners to find answers

    This API powers a learning platform where the bot:
    - **Never gives direct answers** to questions
    - Provides hints and guidance instead
    - Points users to specific pages/chapters in uploaded books
    - Supports voice input and output
    - Allows personalized learning profiles

    ### Key Features:
    - 📚 **RAG-powered**: Upload books and documents for reference
    - 🎯 **Guided Learning**: Get hints, not answers
    - 🎤 **Voice Support**: Speak your questions
    - 👤 **User Profiles**: Customize your learning style
    - 📊 **Training Data**: Questions saved (anonymized) for improvement
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",      # Swagger UI
    redoc_url="/api/redoc",    # ReDoc
    openapi_url="/api/openapi.json"
)

# Configure CORS (Cross-Origin Resource Sharing)
# This allows the React frontend to communicate with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,      # React dev server
        "http://localhost:5173",    # Vite default
        "http://localhost:3000",    # CRA default
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include routers
# Each router handles a specific domain of the API
app.include_router(auth_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(voice_router, prefix="/api")
app.include_router(profiles_router, prefix="/api")


@app.get("/", tags=["Root"])
async def root() -> dict:
    """
    Root endpoint - basic health check.
    
    Returns:
        dict: Welcome message and API info
    
    Example:
        GET /
        Returns: {"message": "Welcome to Learning Bot!", ...}
    """
    return {
        "message": "Welcome to Learning Bot! 📚",
        "description": "A chatbot that guides you to find answers",
        "docs": "/api/docs",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """
    Health check endpoint for monitoring.
    
    Returns:
        dict: Health status of the application
    
    Example:
        GET /health
        Returns: {"status": "healthy"}
    """
    return {
        "status": "healthy",
        "service": "learning-bot-api"
    }
