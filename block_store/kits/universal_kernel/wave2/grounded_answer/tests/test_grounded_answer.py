"""Tests for the neutral grounded answerer sub-kit."""

from block_store.kits.universal_kernel.wave2.embedding_provider import HashEmbeddingProvider
from block_store.kits.universal_kernel.wave2.grounded_answer import GroundedAnswerer
from block_store.kits.universal_kernel.wave2.llm_provider import get_provider
from block_store.kits.universal_kernel.wave2.vector_store import Chunk, VectorStore


def _make_store():
    store = VectorStore()
    embedder = HashEmbeddingProvider()
    chunks = [
        Chunk(id="c1", text="The capital of France is Paris.", vector=embedder.embed(["France capital"])["vectors"][0]),
        Chunk(id="c2", text="Berlin is the capital of Germany.", vector=embedder.embed(["Germany capital"])["vectors"][0]),
    ]
    store.upsert("tenant-1", "project-1", chunks)
    return store


def test_answer_returns_grounded_response():
    store = _make_store()
    embedder = HashEmbeddingProvider()
    llm = get_provider("stub")
    answerer = GroundedAnswerer(store, llm, embed_fn=lambda text: embedder.embed([text])["vectors"][0])
    result = answerer.answer("tenant-1", "project-1", "What is the capital of France?")
    assert "Stub answer" in result["answer"]
    assert result["honesty"] == "grounded"
    assert len(result["citations"]) > 0
    assert result["citations"][0]["chunk_id"] == "c1"


def test_insufficient_sources():
    store = VectorStore()
    embedder = HashEmbeddingProvider()
    llm = get_provider("stub")
    answerer = GroundedAnswerer(store, llm, embed_fn=lambda text: embedder.embed([text])["vectors"][0])
    result = answerer.answer("tenant-1", "project-1", "What is the capital of Mars?")
    assert result["answer"] == "Insufficient sources."
    assert result["honesty"] == "insufficient_sources"
    assert result["citations"] == []


def test_no_cross_tenant_borrowing():
    store = _make_store()
    embedder = HashEmbeddingProvider()
    llm = get_provider("stub")
    answerer = GroundedAnswerer(store, llm, embed_fn=lambda text: embedder.embed([text])["vectors"][0])
    result = answerer.answer("tenant-2", "project-1", "What is the capital of France?")
    assert result["honesty"] == "insufficient_sources"
