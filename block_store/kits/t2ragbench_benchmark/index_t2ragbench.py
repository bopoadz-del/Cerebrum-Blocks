"""Index the T²-RAGBench text metadata corpus for Cerebrum.

Source files used:
  - data/FinQA/{train,dev,test}/metadata.jsonl
  - data/ConvFinQA/turn_0.jsonl
  - data/TAT-DQA/{train,dev,test}/metadata.jsonl

Excluded:
  - PDF/PNG binaries are listed in file_inventory.csv but were not downloaded
    (too large / not needed for text indexing).
  - TAT-DQA raw/ JSON OCR files are not indexed because the extracted context
    text is already present in the metadata jsonl files.

Embeddings are produced with the deterministic feature-hash provider
(provider_id="hash") in batches to keep memory usage low.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

# Make the Cerebrum-Blocks package importable when running from this kit folder.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from block_store.kits.universal_kernel.wave2.vector_store import Chunk, VectorStore
from block_store.kits.universal_kernel.wave2.embedding_provider import get_provider
from block_store.kits.universal_kernel.wave2.hybrid_retrieval import hybrid_search

TENANT_ID = "cerebrum_prebuilt"
PROJECT_ID = "prebuilt_finance_sec_core"
KIT_NAME = "t2ragbench_benchmark"
DEFAULT_PROVIDER = "hash"
BATCH_SIZE = 256

SOURCE_FILES: List[Tuple[str, Path]] = [
    ("FinQA", Path("data/FinQA/train/metadata.jsonl")),
    ("FinQA", Path("data/FinQA/dev/metadata.jsonl")),
    ("FinQA", Path("data/FinQA/test/metadata.jsonl")),
    ("ConvFinQA", Path("data/ConvFinQA/turn_0.jsonl")),
    ("TAT-DQA", Path("data/TAT-DQA/train/metadata.jsonl")),
    ("TAT-DQA", Path("data/TAT-DQA/dev/metadata.jsonl")),
    ("TAT-DQA", Path("data/TAT-DQA/test/metadata.jsonl")),
]


def _metadata_from_record(subset: str, record: Dict[str, Any]) -> Dict[str, Any]:
    """Build neutral chunk metadata from a T²-RAGBench record."""
    meta: Dict[str, Any] = {
        "project_id": PROJECT_ID,
        "domain": "finance",
        "jurisdiction": ["US"],
        "subset": subset,
        "split": record.get("split"),
        "context_id": record.get("context_id"),
        "question": record.get("question"),
        "program_answer": record.get("program_answer"),
        "original_answer": record.get("original_answer"),
        "file_name": record.get("file_name"),
    }
    for key in (
        "company_name",
        "company_symbol",
        "report_year",
        "page_number",
        "company_sector",
        "company_industry",
        "company_headquarters",
        "company_date_added",
        "company_cik",
        "company_founded",
        "table",
    ):
        value = record.get(key)
        if value is not None and value != "":
            meta[key] = value
    return meta


def _chunks_from_kit(kit_path: Path) -> Iterable[Chunk]:
    """Stream Chunk objects from the metadata jsonl files."""
    for subset, rel_path in SOURCE_FILES:
        file_path = kit_path / rel_path
        if not file_path.exists():
            print(f"WARN: source file missing, skipping: {file_path}")
            continue
        with file_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    print(f"WARN: malformed JSONL in {file_path}: {exc}")
                    continue
                record_id = record.get("id")
                if not record_id:
                    continue
                text = record.get("context") or record.get("question", "")
                if not text:
                    continue
                yield Chunk(
                    id=f"t2ragbench:{subset}:{record_id}",
                    text=text,
                    vector=[],
                    metadata=_metadata_from_record(subset, record),
                )


def index_corpus(
    store: VectorStore,
    provider_id: str = DEFAULT_PROVIDER,
    batch_size: int = BATCH_SIZE,
) -> Dict[str, Any]:
    provider = get_provider(provider_id)
    kit_path = Path(__file__).resolve().parent

    indexed = 0
    total = 0
    batch: List[Chunk] = []

    for chunk in _chunks_from_kit(kit_path):
        batch.append(chunk)
        total += 1
        if len(batch) >= batch_size:
            texts = [c.text for c in batch]
            result = provider.embed(texts)
            vectors = result["vectors"]
            for c, vector in zip(batch, vectors):
                c.vector = vector
            indexed += store.upsert(TENANT_ID, PROJECT_ID, batch)
            print(f"  indexed {indexed}/{total} chunks for {PROJECT_ID}")
            batch = []

    if batch:
        texts = [c.text for c in batch]
        result = provider.embed(texts)
        vectors = result["vectors"]
        for c, vector in zip(batch, vectors):
            c.vector = vector
        indexed += store.upsert(TENANT_ID, PROJECT_ID, batch)
        print(f"  indexed {indexed}/{total} chunks for {PROJECT_ID}")

    return {
        "tenant_id": TENANT_ID,
        "project_id": PROJECT_ID,
        "kit": KIT_NAME,
        "provider": provider.model_name,
        "dimensions": provider.dimensions,
        "chunks_indexed": indexed,
        "store_count": store.count(TENANT_ID, PROJECT_ID),
    }


def verify_index(
    store: VectorStore,
    query: str,
    provider_id: str = DEFAULT_PROVIDER,
) -> Dict[str, Any]:
    provider = get_provider(provider_id)
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
    return {
        "query": query,
        "project_id": PROJECT_ID,
        "honesty": result.get("honesty"),
        "top_results": top_results,
    }


def main() -> int:
    store = VectorStore()
    provider_id = os.getenv("EMBEDDING_PROVIDER", DEFAULT_PROVIDER)

    print(f"Indexing {KIT_NAME} with provider={provider_id} ...")
    result = index_corpus(store, provider_id=provider_id)
    print(json.dumps(result, indent=2))

    verification_query = (
        "What was the amount of Income before income taxes for "
        "carpenter-technology-corp in the year ended June 30, 2019?"
    )
    print(f"Verifying {PROJECT_ID} ...")
    verification = verify_index(store, verification_query, provider_id=provider_id)
    print(json.dumps(verification, indent=2))

    indexed_json = {
        "project_id": PROJECT_ID,
        "tenant_id": TENANT_ID,
        "chunks_indexed": result["chunks_indexed"],
        "provider": result["provider"],
        "source_paths": [rel.as_posix() for _subset, rel in SOURCE_FILES],
        "verification_query": verification_query,
        "top_result_id": (
            verification["top_results"][0]["chunk_id"]
            if verification["top_results"]
            else None
        ),
        "verification_succeeded": bool(verification["top_results"]),
        "top_results": verification["top_results"],
    }
    out_path = Path(__file__).resolve().parent / f"{KIT_NAME}_indexed.json"
    out_path.write_text(json.dumps(indexed_json, indent=2), encoding="utf-8")
    print(f"Indexed summary written to {out_path}")

    manifest = {
        "id": "t2ragbench",
        "name": "T²-RAGBench (Finance SEC core)",
        "domain": "finance",
        "project_id": PROJECT_ID,
        "tenant_id": TENANT_ID,
        "chunks_indexed": result["chunks_indexed"],
        "provider": result["provider"],
        "source_files": [rel.as_posix() for _subset, rel in SOURCE_FILES],
        "license": "CC-BY-4.0",
        "description": (
            "Indexed T²-RAGBench text metadata (FinQA, ConvFinQA, TAT-DQA) "
            "using deterministic feature-hash embeddings."
        ),
        "excluded_files": [
            "PDF/PNG binaries were not downloaded (file_inventory.csv lists them as not downloaded).",
            "TAT-DQA raw/ JSON OCR files are not indexed because extracted context text is present in metadata jsonl files.",
        ],
    }
    manifest_path = Path(__file__).resolve().parent / "kernel_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Kernel manifest written to {manifest_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
