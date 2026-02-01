"""
Configuration Module for Learning Bot

This module handles all application settings using Pydantic Settings.
It loads environment variables from .env file and provides type-safe access.

Usage:
    from app.config import settings
    print(settings.DATABASE_URL)
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Attributes:
        DATABASE_URL (str): Database connection string
        SECRET_KEY (str): Secret key for JWT token signing
        ALGORITHM (str): Algorithm for JWT encoding
        ACCESS_TOKEN_EXPIRE_MINUTES (int): Token expiration time
        MISTRAL_API_KEY (str): API key for Mistral LLM
        MISTRAL_MODEL (str): Which Mistral model to use
        EMBEDDING_MODEL (str): Model for text embeddings
        MAX_CONTEXT_TOKENS (int): Max tokens for RAG context
        TOP_K_RESULTS (int): Number of document chunks to retrieve
        FRONTEND_URL (str): Frontend URL for CORS
        MAX_UPLOAD_SIZE_MB (int): Maximum file upload size
        ALLOWED_EXTENSIONS (str): Comma-separated allowed file types
        UPLOAD_DIR (str): Directory for uploaded files
    """
    
    # Database
    DATABASE_URL: str = "sqlite:///./learning_bot.db"
    
    # Authentication
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # LLM Settings
    MISTRAL_API_KEY: str = ""
    MISTRAL_MODEL: str = "mistral-small-2506"  # Vision-capable model (or use mistral-large-2512 for better quality)
    
    # RAG Settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    MAX_CONTEXT_TOKENS: int = 2000
    TOP_K_RESULTS: int = 3
    
    # CORS
    FRONTEND_URL: str = "http://localhost:5173"
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: str = "pdf,txt,epub"
    UPLOAD_DIR: str = "uploads"
    
    class Config:
        """Pydantic config to load from .env file."""
        env_file = "../.env"  # Load from project root
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra env variables
    
    def get_allowed_extensions_list(self) -> list[str]:
        """
        Get allowed file extensions as a list.
        
        Returns:
            list[str]: List of allowed file extensions
        """
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]


# Create a global settings instance
# This is imported throughout the application
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
