"""
Documents Router Module

This module handles document upload and management:
- Upload PDF, TXT, EPUB files
- List uploaded documents
- Delete documents
- Process documents for RAG (chunking and embedding)

Documents are used for the learning guidance feature.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import os
import uuid

from app.database import get_db
from app.models.user import User
from app.models.document import Document, DocumentChunk
from app.schemas.document import DocumentResponse, DocumentListResponse
from app.services.auth_service import get_current_user
from app.services.rag_service import process_document, delete_document_embeddings
from app.config import settings

# Create router
router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


def validate_file_extension(filename: str) -> str:
    """
    Validate that the file has an allowed extension.
    
    Args:
        filename (str): The original filename
    
    Returns:
        str: The file extension (lowercase, without dot)
    
    Raises:
        HTTPException 400: If extension is not allowed
    """
    # Get extension (handle files with multiple dots)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    
    allowed = settings.get_allowed_extensions_list()
    if ext not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{ext}' not allowed. Allowed types: {', '.join(allowed)}"
        )
    
    return ext


def validate_file_size(file_size: int) -> None:
    """
    Validate that the file size is within limits.
    
    Args:
        file_size (int): File size in bytes
    
    Raises:
        HTTPException 400: If file is too large
    """
    max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB"
        )


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
    description="Upload a PDF, TXT, or EPUB file for RAG processing."
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload"),
    title: Optional[str] = Form(default=None, description="Document title"),
    author: Optional[str] = Form(default=None, description="Document author"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DocumentResponse:
    """
    Upload a document for RAG processing.
    
    The document will be:
    1. Saved to the uploads directory
    2. Chunked into smaller pieces
    3. Embedded and stored in the vector database
    
    Args:
        file (UploadFile): The document file (PDF, TXT, or EPUB)
        title (str): Optional document title
        author (str): Optional document author
        current_user (User): Authenticated user
        db (AsyncSession): Database session
    
    Returns:
        DocumentResponse: Uploaded document metadata
    
    Raises:
        HTTPException 400: If file type not allowed or too large
    
    Example:
        POST /api/documents/upload
        Content-Type: multipart/form-data
        
        file: <binary file data>
        title: "Physics 101"
        author: "Dr. Smith"
    """
    # Validate file
    ext = validate_file_extension(filename=file.filename)
    
    # Read file content to check size
    content = await file.read()
    validate_file_size(file_size=len(content))
    
    # Generate unique filename to avoid collisions
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    # Save file to disk
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Create document record
    document = Document(
        filename=file.filename,
        title=title or file.filename,
        author=author,
        file_type=ext,
        file_path=file_path
    )
    db.add(document)
    await db.flush()  # Get ID
    
    # Process document for RAG (chunking and embedding)
    # This happens asynchronously
    try:
        chunk_count = await process_document(
            document_id=document.id,
            file_path=file_path,
            file_type=ext,
            db=db
        )
        document.total_pages = chunk_count  # Approximate
    except Exception as e:
        # If processing fails, still keep the document but log error
        print(f"Error processing document: {e}")
        chunk_count = 0
    
    await db.commit()
    await db.refresh(document)
    
    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        title=document.title,
        author=document.author,
        file_type=document.file_type,
        total_pages=document.total_pages,
        upload_date=document.upload_date,
        chunk_count=chunk_count
    )


@router.get(
    "/",
    response_model=DocumentListResponse,
    summary="List all documents",
    description="Get a list of all uploaded documents."
)
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DocumentListResponse:
    """
    List all uploaded documents.
    
    Args:
        current_user (User): Authenticated user
        db (AsyncSession): Database session
    
    Returns:
        DocumentListResponse: List of documents with count
    
    Example:
        GET /api/documents/
        Authorization: Bearer <token>
    """
    # Get documents with chunk count
    result = await db.execute(
        select(
            Document,
            func.count(DocumentChunk.id).label("chunk_count")
        )
        .outerjoin(DocumentChunk, DocumentChunk.document_id == Document.id)
        .group_by(Document.id)
        .order_by(Document.upload_date.desc())
    )
    
    documents = []
    for row in result.all():
        doc = row[0]
        chunk_count = row[1]
        documents.append(
            DocumentResponse(
                id=doc.id,
                filename=doc.filename,
                title=doc.title,
                author=doc.author,
                file_type=doc.file_type,
                total_pages=doc.total_pages,
                upload_date=doc.upload_date,
                chunk_count=chunk_count
            )
        )
    
    return DocumentListResponse(
        documents=documents,
        total_count=len(documents)
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document details",
    description="Get details of a specific document."
)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DocumentResponse:
    """
    Get details of a specific document.
    
    Args:
        document_id (int): ID of the document
        current_user (User): Authenticated user
        db (AsyncSession): Database session
    
    Returns:
        DocumentResponse: Document details
    
    Raises:
        HTTPException 404: If document not found
    """
    result = await db.execute(
        select(
            Document,
            func.count(DocumentChunk.id).label("chunk_count")
        )
        .outerjoin(DocumentChunk, DocumentChunk.document_id == Document.id)
        .where(Document.id == document_id)
        .group_by(Document.id)
    )
    
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    doc = row[0]
    chunk_count = row[1]
    
    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        title=doc.title,
        author=doc.author,
        file_type=doc.file_type,
        total_pages=doc.total_pages,
        upload_date=doc.upload_date,
        chunk_count=chunk_count
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document",
    description="Delete a document and its embeddings."
)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a document and all associated data.
    
    This will:
    1. Delete the file from disk
    2. Delete embeddings from vector database
    3. Delete document record and chunks from SQL database
    
    Args:
        document_id (int): ID of the document to delete
        current_user (User): Authenticated user
        db (AsyncSession): Database session
    
    Raises:
        HTTPException 404: If document not found
    """
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete file from disk
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # Delete embeddings from vector database
    await delete_document_embeddings(document_id=document_id)
    
    # Delete from SQL database (cascades to chunks)
    await db.delete(document)
    await db.commit()


@router.get(
    "/{document_id}/file",
    summary="Download/view document file",
    description="Get the actual document file for viewing or download."
)
async def get_document_file(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Serve the actual document file.
    
    Returns the file with appropriate content type for viewing in browser
    (PDFs will open in browser, others will download).
    
    Args:
        document_id (int): ID of the document
        current_user (User): Authenticated user
        db (AsyncSession): Database session
    
    Returns:
        FileResponse: The document file
    
    Raises:
        HTTPException 404: If document or file not found
    """
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if not os.path.exists(document.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found on disk"
        )
    
    # Determine media type
    media_types = {
        "pdf": "application/pdf",
        "txt": "text/plain",
        "epub": "application/epub+zip"
    }
    media_type = media_types.get(document.file_type, "application/octet-stream")
    
    # Return file response
    # For PDFs, inline display; for others, attachment download
    disposition = "inline" if document.file_type == "pdf" else "attachment"
    
    return FileResponse(
        path=document.file_path,
        media_type=media_type,
        filename=document.filename,
        headers={
            "Content-Disposition": f'{disposition}; filename="{document.filename}"'
        }
    )
