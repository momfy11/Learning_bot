"""
Document Schemas Module

Pydantic schemas for document upload and retrieval functionality.
Used for the RAG (Retrieval Augmented Generation) feature.

Schemas:
    - DocumentCreate/Response: Document metadata
    - DocumentChunkResponse: Text chunk data
    - SearchResult: RAG search results
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ====================
# Document Schemas
# ====================

class DocumentCreate(BaseModel):
    """
    Schema for document upload metadata.
    
    Note: Actual file is uploaded separately via form data.
    
    Attributes:
        title (str): Document title
        author (str): Document author
    """
    title: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Document title (extracted from file if not provided)"
    )
    author: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Document author"
    )


class DocumentResponse(BaseModel):
    """
    Schema for returning document data.
    
    Attributes:
        id (int): Document ID
        filename (str): Original filename
        title (str): Document title
        author (str): Document author
        file_type (str): File extension
        total_pages (int): Page count
        upload_date (datetime): Upload timestamp
        chunk_count (int): Number of indexed chunks
    """
    id: int = Field(..., description="Document ID")
    filename: str = Field(..., description="Original filename")
    title: Optional[str] = Field(None, description="Document title")
    author: Optional[str] = Field(None, description="Document author")
    file_type: str = Field(..., description="File type (pdf, txt, epub)")
    total_pages: Optional[int] = Field(None, description="Total pages")
    upload_date: datetime = Field(..., description="Upload timestamp")
    chunk_count: int = Field(default=0, description="Number of indexed chunks")
    
    class Config:
        """Enable ORM mode for SQLAlchemy model conversion."""
        from_attributes = True


class DocumentListResponse(BaseModel):
    """
    Schema for listing all documents.
    
    Attributes:
        documents (list): List of document summaries
        total_count (int): Total number of documents
    """
    documents: List[DocumentResponse] = Field(
        default=[],
        description="List of uploaded documents"
    )
    total_count: int = Field(default=0, description="Total document count")


# ====================
# Document Chunk Schemas
# ====================

class DocumentChunkResponse(BaseModel):
    """
    Schema for returning document chunk data.
    
    Chunks are used for RAG retrieval. Each chunk knows
    its location in the original document.
    
    Attributes:
        id (int): Chunk ID
        document_id (int): Parent document ID
        content (str): Text content
        page_number (int): Page number in original
        chapter (str): Chapter information
        section (str): Section name
    """
    id: int = Field(..., description="Chunk ID")
    document_id: int = Field(..., description="Parent document ID")
    content: str = Field(..., description="Chunk text content")
    page_number: Optional[int] = Field(None, description="Page number")
    chapter: Optional[str] = Field(None, description="Chapter info")
    section: Optional[str] = Field(None, description="Section name")
    
    class Config:
        """Enable ORM mode for SQLAlchemy model conversion."""
        from_attributes = True


# ====================
# Search Result Schemas
# ====================

class SearchResult(BaseModel):
    """
    Schema for RAG search results.
    
    When a user asks a question, we search the vector database
    and return relevant document chunks with location info.
    
    Attributes:
        chunk_id (int): ID of the matching chunk
        document_id (int): Parent document ID
        document_title (str): Document name
        content_preview (str): Snippet of matching text
        page_number (int): Where to find this in the book
        chapter (str): Chapter information
        section (str): Section name
        relevance_score (float): How relevant (0-1)
    """
    chunk_id: int = Field(..., description="Matching chunk ID")
    document_id: int = Field(..., description="Parent document ID")
    document_title: str = Field(..., description="Document name")
    content_preview: str = Field(..., description="Text snippet (truncated)")
    page_number: Optional[int] = Field(None, description="Page number")
    chapter: Optional[str] = Field(None, description="Chapter info")
    section: Optional[str] = Field(None, description="Section name")
    relevance_score: float = Field(..., description="Relevance score 0-1")
