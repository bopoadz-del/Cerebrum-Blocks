"""Index the RECOR multi-domain QA corpus using feature-hash embeddings.

Streams all ``data/corpus/*_documents.jsonl`` files in batches so the raw
records are never all held in memory at once. Writes a ``kernel_manifest.json``
and ``recor_indexed.json`` summary in the kit folder.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

# Make the Cerebrum-Blocks package importable when running from block_store/kits/{kit}.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from block_store.kits.universal_kernel.wave2.vector_store import Chunk, VectorStore
from block_store.kits.universal_kernel.wave2.embedding_provider import get_provider
from block_store.kits.universal_kernel.wave2.hybrid_retrieval import hybrid_search

TENANT_ID = "cerebrum_prebuilt"
PROJECT_ID = "prebuilt_multi_domain_qa_core"
KIT_FOLDER = "recor_benchmark"
PROVIDER_ID = "hash"
BATCH_SIZE = 50000

CORPUS_DIR = Path(__file__).resolve().parent / "data" / "corpus"


def _domain_from_filename(path: Path) -> str:
    """Extract domain name from ``{domain}_documents.jsonl``."""
    name = path.stem
    if name.endswith("_documents"):
        return name[: -len("_documents")]
    return name


def _stream_records() -> Iterable[Tuple[str, Dict[str, Any]]]:
    """Yield (domain, record) tuples from all corpus JSONL files."""
    if not CORPUS_DIR.exists():
        raise FileNotFoundError(f"RECOR corpus directory not found: {CORPUS_DIR}")

    files = sorted(CORPUS_DIR.glob("*_documents.jsonl"))
    if not files:
        raise FileNotFoundError(f"No *_documents.jsonl files found in {CORPUS_DIR}")

    for fpath in files:
        domain = _domain_from_filename(fpath)
        with fpath.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    print(f"WARN: malformed JSONL in {fpath}: {exc}", file=sys.stderr)
                    continue
                yield domain, record


def _record_to_chunk(domain: str, record: Dict[str, Any]) -> Chunk:
    doc_id = record.get("doc_id", "")
    content = record.get("content", "")
    return Chunk(
        id=f"recor:{domain}:{doc_id}",
        text=content,
        vector=[],  # filled before upsert
        metadata={
            "project_id": PROJECT_ID,
            "tenant_id": TENANT_ID,
            "domain": domain,
            "collection": "recor_corpus",
            "doc_id": doc_id,
            "source_file": f"data/corpus/{domain}_documents.jsonl",
        },
    )


def index_corpus(store: VectorStore, batch_size: int = BATCH_SIZE) -> Dict[str, Any]:
    provider = get_provider(PROVIDER_ID)
    indexed = 0
    total_seen = 0
    batch: List[Chunk] = []
    source_files: List[str] = []
    domain_counts: Dict[str, int] = {}
    start_time = time.time()

    for domain, record in _stream_records():
        chunk = _record_to_chunk(domain, record)
        batch.append(chunk)
        total_seen += 1
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

        if len(batch) >= batch_size:
            _embed_and_upsert(store, batch, provider)
            indexed += len(batch)
            if indexed % 10_000 == 0:
                elapsed = time.time() - start_time
                print(f"  indexed {indexed:,} chunks ({elapsed:.1f}s)")
            batch = []

    if batch:
        _embed_and_upsert(store, batch, provider)
        indexed += len(batch)

    elapsed = time.time() - start_time
    print(f"Finished indexing {indexed:,} chunks in {elapsed:.1f}s")

    source_files = sorted(
        {f"data/corpus/{domain}_documents.jsonl" for domain in domain_counts}
    )

    return {
        "tenant_id": TENANT_ID,
        "project_id": PROJECT_ID,
        "kit": KIT_FOLDER,
        "provider": provider.model_name,
        "dimensions": provider.dimensions,
        "chunks_indexed": indexed,
        "chunks_seen": total_seen,
        "store_count": store.count(TENANT_ID, PROJECT_ID),
        "domain_counts": domain_counts,
        "source_files": source_files,
        "elapsed_seconds": round(elapsed, 2),
    }


def _embed_and_upsert(store: VectorStore, batch: List[Chunk], provider) -> None:
    texts = [c.text for c in batch]
    result = provider.embed(texts)
    vectors = result["vectors"]
    for chunk, vector in zip(batch, vectors):
        chunk.vector = vector
    store.upsert(TENANT_ID, PROJECT_ID, batch)


def verify_index(store: VectorStore) -> Dict[str, Any]:
    query = "tax revenue economic development"
    provider = get_provider(PROVIDER_ID)
    query_vector = provider.embed([query])["vectors"][0]
    result = hybrid_search(store, TENANT_ID, PROJECT_ID, query, query_vector, top_k=3)

    top_results = [
        {
            "chunk_id": r.chunk.id,
            "score": r.score,
            "text_snippet": r.source_citation["text_snippet"],
            "metadata": r.source_citation.get("metadata"),
        }
        for r in result.get("results", [])
    ]

    top_result_id = top_results[0]["chunk_id"] if top_results else None
    return {
        "query": query,
        "project_id": PROJECT_ID,
        "tenant_id": TENANT_ID,
        "honesty": result.get("honesty"),
        "top_results": top_results,
        "top_result_id": top_result_id,
    }


def write_kernel_manifest(index_result: Dict[str, Any], verification: Dict[str, Any]) -> None:
    manifest = {
        "id": PROJECT_ID,
        "name": "RECOR Multi-Domain QA Corpus",
        "version": "1.0.0",
        "domain": "multi-domain",
        "project_id": PROJECT_ID,
        "tenant_id": TENANT_ID,
        "provider": PROVIDER_ID,
        "dimensions": index_result["dimensions"],
        "chunks_indexed": index_result["chunks_indexed"],
        "source_files": index_result["source_files"],
        "domains": sorted(index_result["domain_counts"].keys()),
        "domain_counts": index_result["domain_counts"],
        "license": "MIT",
        "description": (
            "Indexed RECOR benchmark corpus covering 11 domains: biology, "
            "earth_science, economics, psychology, robotics, sustainable_living, "
            "Drones, hardware, law, medicalsciences, and politics."
        ),
        "verification_query": verification["query"],
        "verification_top_result_id": verification["top_result_id"],
    }
    manifest_path = Path(__file__).resolve().parent / "kernel_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote kernel_manifest.json to {manifest_path}")


def write_indexed_json(index_result: Dict[str, Any], verification: Dict[str, Any]) -> None:
    indexed = {
        "project_id": PROJECT_ID,
        "tenant_id": TENANT_ID,
        "chunks_indexed": index_result["chunks_indexed"],
        "provider": PROVIDER_ID,
        "source_paths": index_result["source_files"],
        "verification_query": verification["query"],
        "top_result_id": verification["top_result_id"],
        "verification_honesty": verification["honesty"],
        "elapsed_seconds": index_result["elapsed_seconds"],
    }
    out_path = Path(__file__).resolve().parent / f"{KIT_FOLDER}_indexed.json"
    out_path.write_text(json.dumps(indexed, indent=2), encoding="utf-8")
    print(f"Wrote {out_path.name} to {out_path}")


def main() -> int:
    store = VectorStore()
    print(f"Indexing RECOR corpus into {TENANT_ID}:{PROJECT_ID} using {PROVIDER_ID} embeddings ...")
    index_result = index_corpus(store)
    print(json.dumps(index_result, indent=2))

    print("Verifying index with hybrid search ...")
    verification = verify_index(store)
    print(json.dumps(verification, indent=2))

    write_kernel_manifest(index_result, verification)
    write_indexed_json(index_result, verification)

    if verification["top_result_id"] is None:
        print("ERROR: verification returned no results", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
