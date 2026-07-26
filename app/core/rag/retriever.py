"""RAG retriever backed by the pgvector vector store."""

from __future__ import annotations

from dataclasses import dataclass

from app.core import vector_store


@dataclass
class RetrievedChunk:
    doc_id: str
    chunk_index: int
    text: str
    score: float
    metadata: dict


async def retrieve(query: str, project_id: str, k: int = 5) -> list[RetrievedChunk]:
    """Retrieve the top ``k`` chunks for ``query`` from ``project_id``."""
    results = await vector_store.search_vectors(
        project_id, query, top_k=k, threshold=0.3
    )
    chunks: list[RetrievedChunk] = []
    for idx, row in enumerate(results):
        metadata = row.get("metadata", {}) or {}
        chunks.append(
            RetrievedChunk(
                doc_id=str(row.get("document_id", "")),
                chunk_index=int(metadata.get("chunk_index", idx)),
                text=row.get("content", ""),
                score=float(row.get("score", 0.0)),
                metadata=metadata,
            )
        )
    return chunks
