"""
Document Model Module

This module defines database models for uploaded documents (books, PDFs, etc.).
Documents are chunked for RAG (Retrieval Augmented Generation) functionality.

Tables:
    - documents: Uploaded document metadata
    - document_chunks: Text chunks for vector search
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Document(Base):
    """
    Document model for uploaded learning materials.
    
    Stores metadata about uploaded documents (books, PDFs, etc.).
    The actual vector embeddings are stored in ChromaDB, not here.
    
    Attributes:
        id (int): Primary key
        filename (str): Original filename
        title (str): Document title (extracted or user-provided)
        author (str): Document author if available
        file_type (str): File extension (pdf, txt, epub)
        file_path (str): Path to stored file
        total_pages (int): Number of pages/sections
        upload_date (datetime): When document was uploaded
        
    Relationships:
        chunks: Document chunks for RAG retrieval
    """
    __tablename__ = "documents"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # File information
    filename = Column(String(255), nullable=False)
    title = Column(String(255), nullable=True)
    author = Column(String(255), nullable=True)
    file_type = Column(String(20), nullable=False)  # pdf, txt, epub
    file_path = Column(String(500), nullable=False)
    
    # Document metadata
    total_pages = Column(Integer, nullable=True)
    
    # Timestamps
    upload_date = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan"
    )


class DocumentChunk(Base):
    """
    Document Chunk model for RAG text segments.
    
    Documents are split into chunks for efficient retrieval.
    Each chunk stores its location info (page, chapter) so we can
    tell users exactly where to find the information.
    
    Attributes:
        id (int): Primary key
        document_id (int): Foreign key to documents table
        chunk_index (int): Order of chunk in document
        content (str): The actual text content
        page_number (int): Page where chunk is from
        chapter (str): Chapter name/number if available
        section (str): Section name if available
        embedding_id (str): ID in ChromaDB for vector lookup
        
    Relationships:
        document: The parent document
        
    Note:
        The actual vector embedding is stored in ChromaDB, not in SQL.
        We only store the embedding_id to link back to ChromaDB.
    """
    __tablename__ = "document_chunks"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign key to documents
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    
    # Chunk position and content
    chunk_index = Column(Integer, nullable=False)  # Order in document
    content = Column(Text, nullable=False)  # The actual text
    
    # Location information (crucial for guiding users!)
    page_number = Column(Integer, nullable=True)
    chapter = Column(String(255), nullable=True)
    section = Column(String(255), nullable=True)
    
    # Link to vector database
    # This ID is used to find the embedding in ChromaDB
    embedding_id = Column(String(100), unique=True, nullable=True)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
