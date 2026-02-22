"""Utility functions for text processing and PDF extraction."""

from PyPDF2 import PdfReader
import io
import re

from utils.auth import verify_jwt_token, verify_api_key

__all__ = [
    "extract_text_from_pdf",
    "clean_text",
    "truncate_text",
    "chunk_text",
    "verify_jwt_token",
    "verify_api_key",
]


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text content from a PDF file."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()


def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep punctuation
    text = re.sub(r'[^\w\s.,;:!?\'\"()\-/]', '', text)
    return text.strip()


def truncate_text(text: str, max_tokens: int = 4000) -> str:
    """Truncate text to approximate token limit (rough estimate: 1 token ≈ 4 chars)."""
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
    """Split text into overlapping chunks for embedding."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks
