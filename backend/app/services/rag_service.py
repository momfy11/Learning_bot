"""
RAG Service Module

RAG = Retrieval Augmented Generation

This module handles:
- Document processing (chunking, embedding)
- Vector storage in ChromaDB
- Semantic search for relevant content

When a user asks a question, we search the documents and
return relevant chunks with their location (page, chapter).
"""

from typing import List, Optional
import os
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.document import Document, DocumentChunk
from app.schemas.document import SearchResult

# ChromaDB for vector storage
import chromadb
from chromadb.config import Settings as ChromaSettings

# Sentence transformers for embeddings
# This creates vector representations of text
from sentence_transformers import SentenceTransformer


# Initialize ChromaDB client
# persist_directory stores the vectors on disk
chroma_client = chromadb.Client(ChromaSettings(
    anonymized_telemetry=False,  # Disable telemetry
    is_persistent=True,
    persist_directory="./chroma_data"
))

# Get or create the collection for document chunks
# A collection is like a table in a traditional database
try:
    collection = chroma_client.get_or_create_collection(
        name="document_chunks",
        metadata={"description": "Learning materials for RAG"}
    )
except Exception:
    collection = chroma_client.create_collection(
        name="document_chunks",
        metadata={"description": "Learning materials for RAG"}
    )

# Initialize the embedding model
# This model converts text to vectors
# all-MiniLM-L6-v2 is fast and good for semantic search
_embedding_model = None


def get_embedding_model() -> SentenceTransformer:
    """
    Get the sentence transformer model (lazy loading).
    
    Lazy loading prevents slow startup and allows for
    model caching between requests.
    
    Returns:
        SentenceTransformer: The embedding model
    """
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _embedding_model


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> List[dict]:
    """
    Split text into overlapping chunks.
    
    Chunks should be:
    - Small enough for embedding (typically 500-1000 chars)
    - Large enough to contain meaningful content
    - Overlapping to avoid losing context at boundaries
    
    Args:
        text (str): The full document text
        chunk_size (int): Maximum characters per chunk
        overlap (int): Characters to overlap between chunks
    
    Returns:
        List[dict]: List of chunks with index and content
    
    Example:
        chunks = chunk_text("Long document text...", chunk_size=500)
        # Returns: [{"index": 0, "content": "..."}, ...]
    """
    chunks = []
    start = 0
    chunk_index = 0
    
    while start < len(text):
        # Find the end of this chunk
        end = start + chunk_size
        
        # Try to break at a sentence or paragraph
        if end < len(text):
            # Look for paragraph break
            paragraph_break = text.rfind("\n\n", start, end)
            if paragraph_break > start + chunk_size // 2:
                end = paragraph_break
            else:
                # Look for sentence break
                sentence_break = text.rfind(". ", start, end)
                if sentence_break > start + chunk_size // 2:
                    end = sentence_break + 1
        
        chunk_content = text[start:end].strip()
        
        if chunk_content:  # Skip empty chunks
            chunks.append({
                "index": chunk_index,
                "content": chunk_content
            })
            chunk_index += 1
        
        # Move start for next chunk (with overlap)
        start = end - overlap if end < len(text) else end
    
    return chunks


def extract_text_from_pdf(file_path: str) -> tuple[List[dict], int]:
    """
    Extract text from a PDF file, page by page.
    
    Args:
        file_path (str): Path to the PDF file
    
    Returns:
        tuple: (list of {page_number, text} dicts, page_count)
    """
    from pypdf import PdfReader
    
    reader = PdfReader(file_path)
    pages_data = []
    
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text and page_text.strip():
            pages_data.append({
                "page_number": i + 1,  # 1-indexed
                "text": page_text
            })
    
    return pages_data, len(reader.pages)


def extract_text_from_txt(file_path: str) -> tuple[List[dict], int]:
    """
    Extract text from a plain text file.
    
    Args:
        file_path (str): Path to the text file
    
    Returns:
        tuple: (list with single page dict, None)
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    return [{"page_number": None, "text": text}], None


def extract_text_from_epub(file_path: str) -> tuple[List[dict], int]:
    """
    Extract text from an EPUB file.
    
    Args:
        file_path (str): Path to the EPUB file
    
    Returns:
        tuple: (list of chapter dicts, chapter_count)
    """
    import ebooklib
    from ebooklib import epub
    from html.parser import HTMLParser
    
    class HTMLStripper(HTMLParser):
        def __init__(self):
            super().__init__()
            self.text = []
        def handle_data(self, data):
            self.text.append(data)
        def get_text(self):
            return ' '.join(self.text)
    
    book = epub.read_epub(file_path)
    pages_data = []
    chapter_count = 0
    
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            chapter_count += 1
            stripper = HTMLStripper()
            stripper.feed(item.get_content().decode("utf-8", errors="ignore"))
            text = stripper.get_text()
            if text.strip():
                pages_data.append({
                    "page_number": chapter_count,  # Use chapter as "page"
                    "text": text
                })
    
    return pages_data, chapter_count


def clean_text(text: str) -> str:
    """
    Clean text for embedding.
    
    Removes problematic characters that can cause encoding errors.
    
    Args:
        text (str): Raw text to clean
    
    Returns:
        str: Cleaned text safe for embedding
    """
    if not text:
        return ""
    
    # Replace null bytes and other problematic characters
    text = text.replace('\x00', '')
    
    # Remove surrogate characters that cause encoding issues
    text = text.encode('utf-8', errors='ignore').decode('utf-8')
    
    # Replace multiple whitespace with single space
    import re
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


async def process_document(
    document_id: int,
    file_path: str,
    file_type: str,
    db: AsyncSession
) -> int:
    """
    Process an uploaded document for RAG.
    
    This function:
    1. Extracts text from the file (page by page for PDFs)
    2. Splits text into chunks while preserving page numbers
    3. Creates embeddings for each chunk
    4. Stores chunks in vector database
    5. Saves chunk metadata to SQL database
    
    Args:
        document_id (int): Database ID of the document
        file_path (str): Path to the uploaded file
        file_type (str): File extension (pdf, txt, epub)
        db (AsyncSession): Database session
    
    Returns:
        int: Number of chunks created
    """
    # Extract text based on file type
    extractors = {
        "pdf": extract_text_from_pdf,
        "txt": extract_text_from_txt,
        "epub": extract_text_from_epub
    }
    
    extractor = extractors.get(file_type)
    if not extractor:
        raise ValueError(f"Unsupported file type: {file_type}")
    
    # Extract returns list of {page_number, text} dicts
    pages_data, page_count = extractor(file_path)
    
    if not pages_data:
        return 0
    
    # Get embedding model
    model = get_embedding_model()
    
    # Get document for title
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one()
    
    # Process each page and create chunks with actual page numbers
    all_chunks = []
    for page_info in pages_data:
        page_num = page_info["page_number"]
        page_text = clean_text(page_info["text"])
        
        if not page_text or len(page_text) < 10:
            continue
        
        # Chunk this page's text
        page_chunks = chunk_text(text=page_text, chunk_size=500, overlap=50)
        
        for chunk in page_chunks:
            cleaned_content = clean_text(chunk["content"])
            if cleaned_content and len(cleaned_content) > 10:
                all_chunks.append({
                    "content": cleaned_content,
                    "page_number": page_num  # Actual page number!
                })
    
    if not all_chunks:
        return 0
    
    chunk_contents = [c["content"] for c in all_chunks]
    chunk_ids = []
    chunk_metadatas = []
    
    for i, chunk in enumerate(all_chunks):
        embedding_id = f"doc_{document_id}_chunk_{i}_{uuid.uuid4().hex[:8]}"
        chunk_ids.append(embedding_id)
        
        chunk_metadatas.append({
            "document_id": document_id,
            "document_title": document.title or document.filename,
            "chunk_index": i,
            "page_number": chunk["page_number"] or 0,
            "file_type": file_type
        })
        
        # Create database record
        db_chunk = DocumentChunk(
            document_id=document_id,
            chunk_index=i,
            content=chunk["content"],
            page_number=chunk["page_number"],  # Actual page number
            embedding_id=embedding_id
        )
        db.add(db_chunk)
    
    # Create embeddings in batch (more efficient)
    embeddings = model.encode(chunk_contents).tolist()
    
    # Add to ChromaDB
    collection.add(
        ids=chunk_ids,
        embeddings=embeddings,
        documents=chunk_contents,
        metadatas=chunk_metadatas
    )
    
    await db.flush()
    
    return len(all_chunks)


async def search_documents(
    query: str,
    db: AsyncSession,
    top_k: int = None,
    min_relevance: float = 0.35
) -> List[SearchResult]:
    """
    Search documents for relevant content.
    
    Uses semantic search to find chunks similar to the query.
    Returns results with location information (page, chapter).
    Only returns results above the minimum relevance threshold.
    
    Args:
        query (str): The search query (user's question)
        db (AsyncSession): Database session
        top_k (int): Number of results to return
        min_relevance (float): Minimum relevance score (0-1) to include results
    
    Returns:
        List[SearchResult]: Relevant chunks with metadata
    
    Example:
        results = await search_documents(
            query="What is photosynthesis?",
            db=db
        )
        for result in results:
            print(f"Found in {result.document_title}, page {result.page_number}")
    """
    top_k = top_k or settings.TOP_K_RESULTS
    
    # Get embedding for query
    model = get_embedding_model()
    query_embedding = model.encode([query]).tolist()
    
    # Search ChromaDB
    try:
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
    except Exception:
        # Collection might be empty
        return []
    
    # Convert to SearchResult objects
    search_results = []
    
    if results and results["ids"] and results["ids"][0]:
        for i, embedding_id in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i] if results["distances"] else 0
            content = results["documents"][0][i] if results["documents"] else ""
            
            # Convert distance to similarity (ChromaDB returns L2 distance)
            # Lower distance = higher similarity
            relevance_score = max(0, 1 - (distance / 2))
            
            # Skip results below minimum relevance threshold
            if relevance_score < min_relevance:
                continue
            
            search_results.append(SearchResult(
                chunk_id=i,
                document_id=metadata.get("document_id", 0),
                document_title=metadata.get("document_title", "Unknown"),
                content_preview=content[:300] if content else "",
                page_number=metadata.get("page_number"),
                chapter=metadata.get("chapter"),
                section=metadata.get("section"),
                relevance_score=round(relevance_score, 3)
            ))
    
    return search_results


async def delete_document_embeddings(document_id: int) -> None:
    """
    Delete all embeddings for a document from ChromaDB.
    
    Called when a document is deleted.
    
    Args:
        document_id (int): ID of the document to remove
    """
    try:
        # Get all embedding IDs for this document
        results = collection.get(
            where={"document_id": document_id},
            include=[]
        )
        
        if results and results["ids"]:
            collection.delete(ids=results["ids"])
    except Exception:
        # Silently handle if embeddings don't exist
        pass


# =============================================================================
# FOLDER-BASED DOCUMENT LOADING
# =============================================================================
# Place documents in the "documents" folder and they'll be automatically
# processed on server startup. No need for user uploads!

DOCUMENTS_FOLDER = "documents"


async def scan_documents_folder(db: AsyncSession) -> dict:
    """
    Scan the documents folder and process any new files.
    
    This function:
    1. Checks the 'documents' folder for PDF, TXT, EPUB files
    2. Compares against already processed documents in database
    3. Processes any new documents for RAG
    
    Call this on application startup to auto-load documents.
    
    Args:
        db (AsyncSession): Database session
    
    Returns:
        dict: Summary of processed documents
            - new_count: Number of new documents processed
            - existing_count: Number of already processed documents
            - errors: List of any errors encountered
    
    Example:
        result = await scan_documents_folder(db)
        print(f"Processed {result['new_count']} new documents")
    """
    # Ensure folder exists
    os.makedirs(DOCUMENTS_FOLDER, exist_ok=True)
    
    allowed_extensions = settings.get_allowed_extensions_list()
    
    new_count = 0
    existing_count = 0
    errors = []
    
    # Get all files in documents folder
    try:
        files = os.listdir(DOCUMENTS_FOLDER)
    except Exception as e:
        return {"new_count": 0, "existing_count": 0, "errors": [str(e)]}
    
    for filename in files:
        # Skip hidden files and directories
        if filename.startswith("."):
            continue
        
        file_path = os.path.join(DOCUMENTS_FOLDER, filename)
        
        # Skip directories
        if os.path.isdir(file_path):
            continue
        
        # Check extension
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in allowed_extensions:
            continue
        
        # Check if already processed (by filename)
        existing = await db.execute(
            select(Document).where(Document.filename == filename)
        )
        if existing.scalar_one_or_none():
            existing_count += 1
            continue
        
        # Process new document
        try:
            print(f"📄 Processing: {filename}")
            
            # Create document record (system document - no user)
            new_doc = Document(
                filename=filename,
                file_type=ext,
                file_path=file_path,
                title=filename.rsplit(".", 1)[0],  # Use filename as title
            )
            db.add(new_doc)
            await db.flush()  # Get the ID
            
            # Process for RAG
            chunk_count = await process_document(
                document_id=new_doc.id,
                file_path=file_path,
                file_type=ext,
                db=db
            )
            
            new_doc.total_pages = chunk_count  # Store chunk count as pages
            
            await db.commit()
            
            print(f"✅ Processed: {filename} ({chunk_count} chunks)")
            new_count += 1
            
        except Exception as e:
            await db.rollback()
            error_msg = f"Error processing {filename}: {str(e)}"
            print(f"❌ {error_msg}")
            errors.append(error_msg)
    
    return {
        "new_count": new_count,
        "existing_count": existing_count,
        "errors": errors
    }
