"""Index the MTRAG corpora into the neutral VectorStore with feature-hash embeddings.

Streams JSONL records from the zipped passage_level and document_level corpora
so the full corpus never has to be loaded into memory.  Embeds each batch with
the deterministic hash provider and upserts into the project
``prebuilt_universal_multiturn_core`` under tenant ``cerebrum_prebuilt``.
"""

from __future__ import annotations

import json
import os
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

# Make Cerebrum-Blocks importable when running from block_store/kits/<kit>.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from block_store.kits.universal_kernel.wave2.vector_store import Chunk, VectorStore
from block_store.kits.universal_kernel.wave2.embedding_provider import get_provider
from block_store.kits.universal_kernel.wave2.hybrid_retrieval import hybrid_search

TENANT_ID = "cerebrum_prebuilt"
PROJECT_ID = "prebuilt_universal_multiturn_core"
KIT_FOLDER = "mtrag_benchmark"
PROVIDER_ID = "hash"

# (level_dir, corpus_name, display_domain)
CORPORA: List[Tuple[str, str, str]] = [
    ("passage_level", "clapnq", "wikipedia"),
    ("passage_level", "cloud", "technical_documentation"),
    ("passage_level", "fiqa", "finance"),
    ("passage_level", "govt", "government"),
    ("document_level", "clapnq", "wikipedia"),
    ("document_level", "cloud", "technical_documentation"),
    ("document_level", "fiqa", "finance"),
    ("document_level", "govt", "government"),
]


def _iter_records(zip_path: Path) -> Iterable[Dict[str, Any]]:
    """Yield JSONL records from a zipped JSONL file, streaming one line at a time."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        members = [n for n in zf.namelist() if n.endswith(".jsonl")]
        if not members:
            raise FileNotFoundError(f"no .jsonl member in {zip_path}")
        with zf.open(members[0], "r") as raw:
            for line in raw:
                line = line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    print(f"WARN: malformed JSONL in {zip_path}: {exc}")
                    continue


def _to_chunk(level: str, corpus: str, record: Dict[str, Any]) -> Chunk:
    doc_id = record.get("_id") or record.get("id") or ""
    text = record.get("text", "")
    title = record.get("title", "")
    url = record.get("url", "")
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    return Chunk(
        id=f"mtrag:{level}:{corpus}:{doc_id}",
        text=text,
        vector=[],
        metadata={
            "project_id": PROJECT_ID,
            "tenant_id": TENANT_ID,
            "kit": KIT_FOLDER,
            "corpus": corpus,
            "level": level,
            "domain": {
                "clapnq": "wikipedia",
                "cloud": "technical_documentation",
                "fiqa": "finance",
                "govt": "government",
            }[corpus],
            "title": title,
            "url": url,
            **metadata,
        },
    )


def index_mtrag(
    kit_path: Path,
    store: VectorStore,
    batch_size: int = 1024,
) -> Dict[str, Any]:
    provider = get_provider(PROVIDER_ID)
    indexed_total = 0
    source_paths: List[str] = []
    corpus_counts: Dict[str, int] = {}

    for level, corpus, _domain in CORPORA:
        zip_path = kit_path / "source_repo" / "corpora" / level / f"{corpus}.jsonl.zip"
        if not zip_path.exists():
            print(f"WARN: missing source file {zip_path}; skipping")
            continue
        source_paths.append(str(zip_path.relative_to(kit_path)))
        key = f"{level}/{corpus}"
        corpus_counts[key] = 0

        batch: List[Chunk] = []
        for record in _iter_records(zip_path):
            chunk = _to_chunk(level, corpus, record)
            if not chunk.text or not chunk.text.strip():
                continue
            batch.append(chunk)
            if len(batch) >= batch_size:
                _upsert_batch(store, provider, batch)
                indexed_total += len(batch)
                corpus_counts[key] += len(batch)
                batch = []
                if corpus_counts[key] % (batch_size * 4) == 0:
                    print(f"  {key}: {corpus_counts[key]} chunks indexed")
        if batch:
            _upsert_batch(store, provider, batch)
            indexed_total += len(batch)
            corpus_counts[key] += len(batch)
        print(f"  {key}: finished with {corpus_counts[key]} chunks")

    store_count = store.count(TENANT_ID, PROJECT_ID)
    return {
        "tenant_id": TENANT_ID,
        "project_id": PROJECT_ID,
        "kit": KIT_FOLDER,
        "provider": provider.model_name,
        "dimensions": provider.dimensions,
        "chunks_indexed": indexed_total,
        "store_count": store_count,
        "source_paths": source_paths,
        "corpus_counts": corpus_counts,
    }


def _upsert_batch(store: VectorStore, provider: Any, batch: List[Chunk]) -> None:
    texts = [c.text for c in batch]
    result = provider.embed(texts)
    vectors = result["vectors"]
    for chunk, vector in zip(batch, vectors):
        chunk.vector = vector
    store.upsert(TENANT_ID, PROJECT_ID, batch)


def verify_index(store: VectorStore, query: str) -> Dict[str, Any]:
    provider = get_provider(PROVIDER_ID)
    query_vector = provider.embed([query])["vectors"][0]
    result = hybrid_search(store, TENANT_ID, PROJECT_ID, query, query_vector, top_k=3)
    top_result_id = None
    top_results = []
    for r in result.get("results", []):
        entry = {
            "chunk_id": r.chunk.id,
            "score": r.score,
            "text_snippet": r.source_citation.get("text_snippet", ""),
        }
        top_results.append(entry)
        if top_result_id is None:
            top_result_id = r.chunk.id
    return {
        "query": query,
        "project_id": PROJECT_ID,
        "honesty": result.get("honesty"),
        "top_result_id": top_result_id,
        "top_results": top_results,
    }


def main() -> int:
    kit_path = Path(__file__).resolve().parent
    store = VectorStore()

    print(f"Indexing {KIT_FOLDER} into {PROJECT_ID} ...")
    result = index_mtrag(kit_path, store)
    print(json.dumps(result, indent=2))

    verification_query = "What caused the French Revolution?"
    print(f"Verifying with query: {verification_query!r}")
    verification = verify_index(store, verification_query)
    print(json.dumps(verification, indent=2))

    # kernel_manifest.json
    manifest = {
        "id": KIT_FOLDER,
        "name": "MTRAG Multi-Turn RAG Benchmark Corpora",
        "domain": "universal",
        "subdomains": ["wikipedia", "technical_documentation", "finance", "government"],
        "project_id": PROJECT_ID,
        "tenant_id": TENANT_ID,
        "chunks_indexed": result["chunks_indexed"],
        "provider": result["provider"],
        "dimensions": result["dimensions"],
        "source_files": result["source_paths"],
        "licence": "Apache-2.0 (repository); upstream corpora are CC-BY-SA (ClapNQ, FiQA) and mixed/vendor (Cloud, Govt) — verify redistribution rights before redistribution",
        "excluded_files": [
            "Banking/Telco corpora — not released by upstream",
        ],
        "large_binary_handling": "Source corpora are compressed JSONL archives; text is streamed directly from zip without extracting binary contents to disk.",
    }
    manifest_path = kit_path / "kernel_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote kernel_manifest.json to {manifest_path}")

    # mtrag_indexed.json
    indexed_path = kit_path / f"{KIT_FOLDER}_indexed.json"
    indexed_record = {
        "project_id": PROJECT_ID,
        "tenant_id": TENANT_ID,
        "chunks_indexed": result["chunks_indexed"],
        "provider": result["provider"],
        "source_paths": result["source_paths"],
        "verification_query": verification["query"],
        "top_result_id": verification["top_result_id"],
        "verification_honesty": verification["honesty"],
    }
    indexed_path.write_text(json.dumps(indexed_record, indent=2), encoding="utf-8")
    print(f"Wrote {indexed_path.name} to {indexed_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
