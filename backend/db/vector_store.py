"""ChromaDB vector store for code embeddings and security patterns."""

from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from config import settings


_chroma_client: Optional[chromadb.ClientAPI] = None


def get_chroma() -> chromadb.ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _chroma_client


def get_or_create_collection(name: str) -> chromadb.Collection:
    client = get_chroma()
    return client.get_or_create_collection(name=name)


async def store_code_embeddings(
    project_id: str,
    documents: List[str],
    metadatas: List[Dict[str, Any]],
    ids: List[str],
) -> None:
    collection = get_or_create_collection(f"project_{project_id}")
    collection.add(documents=documents, metadatas=metadatas, ids=ids)


async def query_similar_code(
    project_id: str, query_text: str, n_results: int = 5
) -> List[Dict[str, Any]]:
    collection = get_or_create_collection(f"project_{project_id}")
    results = collection.query(query_texts=[query_text], n_results=n_results)
    items = []
    if results and results["documents"]:
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            distance = results["distances"][0][i] if results["distances"] else 0
            items.append({"document": doc, "metadata": meta, "distance": distance})
    return items


async def store_security_patterns(patterns: List[Dict[str, Any]]) -> None:
    collection = get_or_create_collection("security_patterns")
    docs = [p["description"] for p in patterns]
    metas = [{"type": p["type"], "severity": p.get("severity", "Medium")} for p in patterns]
    ids = [f"pattern_{i}" for i in range(len(patterns))]
    collection.upsert(documents=docs, metadatas=metas, ids=ids)


async def query_security_patterns(query: str, n_results: int = 5) -> List[Dict[str, Any]]:
    collection = get_or_create_collection("security_patterns")
    try:
        results = collection.query(query_texts=[query], n_results=n_results)
        items = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                items.append({"description": doc, **meta})
        return items
    except Exception:
        return []
