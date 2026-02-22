"""Vector database service using ChromaDB for embeddings."""

import asyncio
import logging
import chromadb
from openai import AsyncOpenAI
from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB vector store for resume, transcript, and job description embeddings."""

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
        )
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._ensure_collections()

    def _ensure_collections(self):
        """Create collections if they don't exist."""
        self.resumes = self.client.get_or_create_collection("resumes")
        self.transcripts = self.client.get_or_create_collection("transcripts")
        self.job_descriptions = self.client.get_or_create_collection("job_descriptions")

    async def _get_embedding(self, text: str) -> list:
        """Generate embedding for text using OpenAI."""
        response = await self.openai_client.embeddings.create(
            input=text[:8000],
            model="text-embedding-3-small",
        )
        return response.data[0].embedding

    async def store_resume(self, candidate_id: str, text: str):
        """Store resume embedding."""
        embedding = await self._get_embedding(text)
        await asyncio.to_thread(
            self.resumes.upsert,
            ids=[candidate_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{"candidate_id": candidate_id}],
        )

    async def store_transcript(self, candidate_id: str, text: str):
        """Store transcript embedding."""
        embedding = await self._get_embedding(text)
        await asyncio.to_thread(
            self.transcripts.upsert,
            ids=[candidate_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{"candidate_id": candidate_id}],
        )

    async def store_job_description(self, candidate_id: str, text: str):
        """Store job description embedding."""
        embedding = await self._get_embedding(text)
        await asyncio.to_thread(
            self.job_descriptions.upsert,
            ids=[candidate_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{"candidate_id": candidate_id}],
        )

    async def search_similar_candidates(self, query: str, n_results: int = 5):
        """Search for similar candidates by resume content."""
        embedding = await self._get_embedding(query)
        results = await asyncio.to_thread(
            self.resumes.query,
            query_embeddings=[embedding],
            n_results=n_results,
        )
        return results


# Lazy singleton — avoids import-time crash
_vector_store = None

def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        try:
            _vector_store = VectorStore()
        except Exception:
            logger.warning("Failed to initialize VectorStore", exc_info=True)
    return _vector_store
