"""
Helper Functions Module

Utility functions used throughout the application.
"""

import re
import os
from typing import Optional


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to remove potentially dangerous characters.
    
    Removes characters that could be used for path traversal
    or other security issues.
    
    Args:
        filename (str): Original filename
    
    Returns:
        str: Sanitized filename safe for filesystem use
    
    Example:
        safe = sanitize_filename("../../etc/passwd")
        # Returns: "etc_passwd"
    """
    # Remove path separators
    filename = os.path.basename(filename)
    
    # Remove potentially dangerous characters
    # Keep alphanumeric, dots, hyphens, underscores
    filename = re.sub(r'[^\w\-.]', '_', filename)
    
    # Remove leading dots (hidden files)
    filename = filename.lstrip('.')
    
    # Ensure filename isn't empty
    if not filename:
        filename = "unnamed_file"
    
    return filename


def truncate_text(
    text: str,
    max_length: int = 100,
    suffix: str = "..."
) -> str:
    """
    Truncate text to a maximum length with a suffix.
    
    Tries to break at word boundaries for cleaner output.
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum length including suffix
        suffix (str): String to append if truncated
    
    Returns:
        str: Truncated text
    
    Example:
        short = truncate_text("This is a very long text", 15)
        # Returns: "This is a..."
    """
    if len(text) <= max_length:
        return text
    
    # Calculate where to truncate
    truncate_at = max_length - len(suffix)
    
    # Try to break at a space
    space_index = text.rfind(' ', 0, truncate_at)
    if space_index > truncate_at // 2:
        truncate_at = space_index
    
    return text[:truncate_at].rstrip() + suffix


def generate_conversation_title(
    first_message: str,
    max_length: int = 50
) -> str:
    """
    Generate a conversation title from the first message.
    
    Creates a readable title for the conversation sidebar.
    
    Args:
        first_message (str): The first message in the conversation
        max_length (int): Maximum title length
    
    Returns:
        str: Generated title
    
    Example:
        title = generate_conversation_title("What is the process of photosynthesis?")
        # Returns: "What is the process of..."
    """
    # Remove excessive whitespace
    title = ' '.join(first_message.split())
    
    # Remove question marks and periods from end
    title = title.rstrip('?.!')
    
    # Truncate if needed
    return truncate_text(text=title, max_length=max_length)


def estimate_reading_time(
    text: str,
    words_per_minute: int = 200
) -> int:
    """
    Estimate reading time for a piece of text.
    
    Args:
        text (str): The text to estimate
        words_per_minute (int): Average reading speed
    
    Returns:
        int: Estimated minutes to read
    
    Example:
        minutes = estimate_reading_time("Long article text...")
        print(f"{minutes} min read")
    """
    word_count = len(text.split())
    minutes = max(1, round(word_count / words_per_minute))
    return minutes


def extract_keywords(
    text: str,
    max_keywords: int = 5
) -> list[str]:
    """
    Extract potential keywords from text.
    
    Simple keyword extraction by removing common words.
    
    Args:
        text (str): Text to extract keywords from
        max_keywords (int): Maximum number of keywords
    
    Returns:
        list[str]: List of potential keywords
    """
    # Common words to ignore (stopwords)
    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
        'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are',
        'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did',
        'will', 'would', 'could', 'should', 'may', 'might', 'must',
        'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
        'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their',
        'can', 'how', 'why', 'when', 'where'
    }
    
    # Extract words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Filter out stopwords and count occurrences
    word_counts = {}
    for word in words:
        if word not in stopwords:
            word_counts[word] = word_counts.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_words = sorted(
        word_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    return [word for word, count in sorted_words[:max_keywords]]
