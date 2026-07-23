#!/usr/bin/env python3
"""Index the EnterpriseRAG-Bench corpus with feature-hash embeddings.

Streams documents directly from all_documents.zip, embeds them in batches,
upserts them into the neutral VectorStore, and verifies retrieval with a
single hybrid-search query.
"""

from __future__ import annotations

import json
import re
import sys
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

# Ensure the repository root is on sys.path so the universal_kernel imports work
# regardless of where the script is invoked from.
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]  # block_store/kits/<kit>/ -> Cerebrum-Blocks
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from block_store.kits.universal_kernel.wave2 import (
    Chunk,
    VectorStore,
    get_provider,
    hybrid_search,
)


TENANT_ID = "cerebrum_prebuilt"
PROJECT_ID = "prebuilt_enterprise_rag_core"
KIT_FOLDER = "enterpriserag_benchmark"
ZIP_PATH = SCRIPT_DIR / "all_documents.zip"
QUESTIONS_PATH = SCRIPT_DIR / "questions.jsonl"
MANIFEST_PATH = SCRIPT_DIR / "kernel_manifest.json"
INDEXED_PATH = SCRIPT_DIR / f"{KIT_FOLDER}_indexed.json"

BATCH_SIZE = 512
EMBEDDING_PROVIDER = "hash"
EMBEDDING_DIM = 384

_DOC_ID_RE = re.compile(r"dsid_([a-f0-9]+)")


def iter_zip_text_files(zip_path: Path) -> Iterable[Tuple[str, str, str, int]]:
    """Yield (archive_name, doc_id, text, size) for every .txt file in the zip."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = info.filename
            if not name.endswith(".txt"):
                continue
            # Derive doc_id from filename segment like dsid_<uuid>__<title>.txt
            match = _DOC_ID_RE.search(name)
            if not match:
                continue
            doc_id = match.group(0)
            with zf.open(info) as fh:
                raw = fh.read()
            text = raw.decode("utf-8", errors="replace")
            yield name, doc_id, text, info.file_size


def build_metadata(archive_name: str, size: int) -> Dict[str, Any]:
    """Extract source_type and path metadata from the archive entry name."""
    parts = archive_name.split("/")
    source_type = parts[0] if parts else "unknown"
    return {
        "source_type": source_type,
        "archive_path": archive_name,
        "size": size,
    }


def load_verification_query(questions_path: Path) -> Tuple[str, List[str]]:
    """Return the first question text and its expected doc ids."""
    with questions_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            return obj["question"], obj.get("expected_doc_ids", [])
    return "Redwood Inference enterprise RAG", []


def flush_batch(
    store: VectorStore,
    provider: Any,
    doc_ids: List[str],
    texts: List[str],
    metas: List[Dict[str, Any]],
    batch_num: int,
    batch_start: float,
) -> int:
    """Embed and upsert one batch; return number of chunks indexed."""
    result = provider.embed(texts)
    vectors = result["vectors"]

    chunks: List[Chunk] = []
    for doc_id, text, meta, vec in zip(doc_ids, texts, metas, vectors):
        chunks.append(
            Chunk(
                id=doc_id,
                text=text,
                vector=vec,
                metadata=meta,
            )
        )

    store.upsert(TENANT_ID, PROJECT_ID, chunks)
    elapsed = time.time() - batch_start
    print(
        f"  Batch {batch_num}: upserted {len(chunks)} chunks "
        f"({len(vectors[0])}-d) in {elapsed:.2f}s"
    )
    return len(chunks)


def index_corpus() -> Dict[str, Any]:
    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"Corpus zip not found: {ZIP_PATH}")

    provider = get_provider(EMBEDDING_PROVIDER)
    store = VectorStore()

    print(f"Indexing corpus from {ZIP_PATH}")
    print(f"Tenant: {TENANT_ID}, Project: {PROJECT_ID}, Provider: {EMBEDDING_PROVIDER}")
    start_time = time.time()

    total_indexed = 0
    total_bytes = 0
    excluded: List[str] = []
    batch_num = 0

    doc_ids: List[str] = []
    texts: List[str] = []
    metas: List[Dict[str, Any]] = []
    batch_start = time.time()

    for archive_name, doc_id, text, size in iter_zip_text_files(ZIP_PATH):
        # Skip empty or tiny files that produce no signal.
        if len(text.strip()) < 3:
            excluded.append(archive_name)
            continue

        doc_ids.append(doc_id)
        texts.append(text)
        metas.append(build_metadata(archive_name, size))
        total_bytes += size

        if len(texts) >= BATCH_SIZE:
            batch_num += 1
            total_indexed += flush_batch(
                store, provider, doc_ids, texts, metas, batch_num, batch_start
            )
            doc_ids, texts, metas = [], [], []
            batch_start = time.time()

    # Flush the final partial batch.
    if texts:
        batch_num += 1
        total_indexed += flush_batch(
            store, provider, doc_ids, texts, metas, batch_num, batch_start
        )

    index_elapsed = time.time() - start_time
    print(
        f"Indexed {total_indexed} chunks ({total_bytes / 1e9:.2f} GB) "
        f"in {index_elapsed:.2f}s"
    )

    # Verification query.
    query, expected_doc_ids = load_verification_query(QUESTIONS_PATH)
    print(f"\nVerification query: {query[:120]}...")
    query_vector = provider.embed([query])["vectors"][0]
    search_result = hybrid_search(store, TENANT_ID, PROJECT_ID, query, query_vector, top_k=3)

    top_results = search_result.get("results", [])
    top_result_id = top_results[0].chunk.id if top_results else None
    verification_succeeded = bool(top_results)
    expected_in_top3 = any(
        r.chunk.id in expected_doc_ids for r in top_results
    ) if expected_doc_ids else verification_succeeded

    print(f"Top-3 result ids: {[r.chunk.id for r in top_results]}")
    print(f"Expected doc ids: {expected_doc_ids}")
    print(f"Expected in top-3: {expected_in_top3}")

    # Source file inventory for the manifest.
    source_paths = [str(ZIP_PATH.relative_to(REPO_ROOT))]
    if QUESTIONS_PATH.exists():
        source_paths.append(str(QUESTIONS_PATH.relative_to(REPO_ROOT)))

    # Write kernel_manifest.json.
    manifest = {
        "id": PROJECT_ID,
        "name": "EnterpriseRAG-Bench indexed corpus",
        "domain": "enterprise_rag",
        "project_id": PROJECT_ID,
        "tenant_id": TENANT_ID,
        "chunks_indexed": total_indexed,
        "provider": EMBEDDING_PROVIDER,
        "embedding_dimensions": EMBEDDING_DIM,
        "source_files": source_paths,
        "licence": "MIT",
        "description": (
            "Indexed collection of the EnterpriseRAG-Bench corpus "
            "(all_documents.zip) using deterministic feature-hash embeddings."
        ),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nWrote manifest: {MANIFEST_PATH}")

    # Write enterpriserag_indexed.json.
    indexed = {
        "project_id": PROJECT_ID,
        "tenant_id": TENANT_ID,
        "chunks_indexed": total_indexed,
        "provider": EMBEDDING_PROVIDER,
        "source_paths": source_paths,
        "verification_query": query,
        "top_result_id": top_result_id,
        "expected_doc_ids": expected_doc_ids,
        "expected_in_top3": expected_in_top3,
    }
    INDEXED_PATH.write_text(json.dumps(indexed, indent=2), encoding="utf-8")
    print(f"Wrote indexed summary: {INDEXED_PATH}")

    return {
        "project_id": PROJECT_ID,
        "tenant_id": TENANT_ID,
        "chunks_indexed": total_indexed,
        "verification_succeeded": verification_succeeded,
        "expected_in_top3": expected_in_top3,
        "top_result_id": top_result_id,
        "excluded_count": len(excluded),
        "excluded_sample": excluded[:10],
    }


if __name__ == "__main__":
    result = index_corpus()
    print("\nSummary:")
    print(json.dumps(result, indent=2))
