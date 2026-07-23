"""Index ParseBench rules into the neutral VectorStore using feature-hash embeddings.

Streams the approved JSONL rule files in the kit folder, embeds batches with the
"hash" provider, and upserts chunks into the project `prebuilt_document_parsing_core`.
Produces `kernel_manifest.json` and `parsebench_indexed.json` in the kit folder.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

# Make Cerebrum-Blocks importable when running from inside the kit folder.
KIT_PATH = Path(__file__).resolve().parent
PROJECT_ROOT = KIT_PATH.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from block_store.kits.universal_kernel.wave2.vector_store import Chunk, VectorStore
from block_store.kits.universal_kernel.wave2.embedding_provider import get_provider
from block_store.kits.universal_kernel.wave2.hybrid_retrieval import hybrid_search

TENANT_ID = "cerebrum_prebuilt"
PROJECT_ID = "prebuilt_document_parsing_core"
KIT_NAME = "parsebench_benchmark"
PROVIDER_ID = "hash"
BATCH_SIZE = 512

RULE_FILES = [
    "chart.jsonl",
    "table.jsonl",
    "text_content.jsonl",
    "text_formatting.jsonl",
    "layout.jsonl",
]

VERIFICATION_QUERY = "table missing sentence"


def _rule_text(record: Dict[str, Any]) -> str:
    """Convert the rule field into a searchable text representation."""
    rule = record.get("rule", "")
    if isinstance(rule, (dict, list)):
        return json.dumps(rule, ensure_ascii=False)
    return str(rule)


def _build_chunk_text(record: Dict[str, Any]) -> str:
    """Build chunk text from category, type, pdf and rule for lexical + vector search."""
    parts = [
        record.get("category", ""),
        record.get("type", ""),
        record.get("pdf", ""),
    ]
    tags = record.get("tags") or []
    if tags:
        parts.extend(str(t) for t in tags)
    parts.append(_rule_text(record))
    return " ".join(p for p in parts if p)


def _parse_record(record: Dict[str, Any]) -> Chunk:
    rec_id = record.get("id", "")
    return Chunk(
        id=f"parsebench:{rec_id}",
        text=_build_chunk_text(record),
        vector=[],
        metadata={
            "project_id": PROJECT_ID,
            "tenant_id": TENANT_ID,
            "kit": KIT_NAME,
            "domain": "document_parsing",
            "authority": "ParseBench",
            "authority_type": "parsing_benchmark",
            "category": record.get("category", ""),
            "type": record.get("type", ""),
            "pdf": record.get("pdf", ""),
            "page": record.get("page"),
            "tags": record.get("tags", []),
        },
    )


def _iter_records(kit_path: Path) -> Iterable[Dict[str, Any]]:
    """Stream records from all rule JSONL files."""
    for fname in RULE_FILES:
        fpath = kit_path / fname
        if not fpath.exists():
            print(f"  skipping missing source file: {fname}")
            continue
        with fpath.open("r", encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    print(f"  WARN malformed JSONL in {fname}:{line_no}: {exc}")


def _iter_unique_chunks(kit_path: Path) -> Iterable[Chunk]:
    """Yield chunks, deduplicating by record id across all rule files."""
    seen_ids: Set[str] = set()
    for record in _iter_records(kit_path):
        rec_id = record.get("id", "")
        if not rec_id:
            continue
        if rec_id in seen_ids:
            continue
        seen_ids.add(rec_id)
        yield _parse_record(record)


def index_parsebench(store: VectorStore, batch_size: int = BATCH_SIZE) -> Dict[str, Any]:
    provider = get_provider(PROVIDER_ID)
    indexed = 0
    total = 0
    batch: List[Chunk] = []

    print(f"Indexing {KIT_NAME} -> {PROJECT_ID} (provider={provider.model_name}, dim={provider.dimensions})")

    for chunk in _iter_unique_chunks(KIT_PATH):
        batch.append(chunk)
        total += 1
        if len(batch) >= batch_size:
            texts = [c.text for c in batch]
            result = provider.embed(texts)
            for c, vector in zip(batch, result["vectors"]):
                c.vector = vector
            indexed += store.upsert(TENANT_ID, PROJECT_ID, batch)
            print(f"  indexed {indexed}/{total} chunks ...")
            batch = []

    if batch:
        texts = [c.text for c in batch]
        result = provider.embed(texts)
        for c, vector in zip(batch, result["vectors"]):
            c.vector = vector
        indexed += store.upsert(TENANT_ID, PROJECT_ID, batch)
        print(f"  indexed {indexed}/{total} chunks ...")

    store_count = store.count(TENANT_ID, PROJECT_ID)
    return {
        "tenant_id": TENANT_ID,
        "project_id": PROJECT_ID,
        "kit": KIT_NAME,
        "provider": provider.model_name,
        "dimensions": provider.dimensions,
        "chunks_indexed": indexed,
        "store_count": store_count,
    }


def verify_index(store: VectorStore) -> Dict[str, Any]:
    provider = get_provider(PROVIDER_ID)
    query_vector = provider.embed([VERIFICATION_QUERY])["vectors"][0]
    result = hybrid_search(store, TENANT_ID, PROJECT_ID, VERIFICATION_QUERY, query_vector, top_k=3)

    top_results = []
    top_result_id = None
    for r in result.get("results", []):
        top_results.append({
            "chunk_id": r.chunk.id,
            "score": r.score,
            "text_snippet": r.source_citation.get("text_snippet", ""),
        })
        if top_result_id is None:
            top_result_id = r.chunk.id

    print(f"Verification query: {VERIFICATION_QUERY!r}")
    for rank, tr in enumerate(top_results, start=1):
        print(f"  #{rank} {tr['chunk_id']} score={tr['score']}")

    return {
        "query": VERIFICATION_QUERY,
        "project_id": PROJECT_ID,
        "honesty": result.get("honesty"),
        "top_result_id": top_result_id,
        "top_results": top_results,
    }


def _source_files() -> Dict[str, Any]:
    """Return metadata about the indexed source files."""
    sources = []
    for fname in RULE_FILES:
        fpath = KIT_PATH / fname
        info = {"path": fname, "indexed": fpath.exists()}
        if fpath.exists():
            info["sha256"] = hashlib.sha256(fpath.read_bytes()).hexdigest()
            info["bytes"] = fpath.stat().st_size
        sources.append(info)
    return sources


def main() -> int:
    start = time.time()
    store = VectorStore()

    result = index_parsebench(store)
    verification = verify_index(store)

    # Kernel manifest describing the indexed collection.
    kernel_manifest = {
        "id": PROJECT_ID,
        "name": "ParseBench Document Parsing Rules",
        "domain": "document_parsing",
        "project_id": PROJECT_ID,
        "tenant_id": TENANT_ID,
        "chunks_indexed": result["chunks_indexed"],
        "provider": result["provider"],
        "dimensions": result["dimensions"],
        "source_files": _source_files(),
        "excluded_files": [
            {
                "path": "docs/",
                "reason": "Large binary PDF source pages skipped; only JSONL rule metadata is indexed.",
            },
            {
                "path": "thumbnails/",
                "reason": "Binary thumbnail images skipped; not required for rule indexing.",
            },
        ],
        "licence": "Apache-2.0",
        "description": "Indexed ParseBench rules for chart, table, text content, text formatting and layout parsing evaluation.",
    }
    manifest_path = KIT_PATH / "kernel_manifest.json"
    manifest_path.write_text(json.dumps(kernel_manifest, indent=2), encoding="utf-8")
    print(f"Wrote kernel manifest: {manifest_path}")

    # Index manifest required by the task.
    index_manifest = {
        "project_id": PROJECT_ID,
        "tenant_id": TENANT_ID,
        "chunks_indexed": result["chunks_indexed"],
        "provider": result["provider"],
        "source_paths": [s["path"] for s in _source_files() if s["indexed"]],
        "verification_query": verification["query"],
        "top_result_id": verification["top_result_id"],
    }
    index_path = KIT_PATH / f"{KIT_NAME}_indexed.json"
    index_path.write_text(json.dumps(index_manifest, indent=2), encoding="utf-8")
    print(f"Wrote index manifest: {index_path}")

    elapsed = time.time() - start
    print(f"Done in {elapsed:.1f}s: indexed {result['chunks_indexed']} chunks, store_count={result['store_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
