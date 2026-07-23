"""Index a single approved RAW_RAG kit into its own VectorStore.

Usage: python index_one_kit.py <kit_name>

Each kit gets its own in-memory VectorStore, which is pickled to
block_store/kits/<kit_name>/vector_store.pkl after indexing and verification.
This keeps per-process memory bounded.
"""

from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

import numpy as np

try:
    import orjson
    _JSON_LOADS = orjson.loads
    _JSON_LOAD = lambda fh: orjson.loads(fh.read())
except Exception:
    _JSON_LOADS = json.loads
    _JSON_LOAD = lambda fh: json.load(fh)

try:
    import mmh3
    _MMH3_AVAILABLE = True
except Exception:
    _MMH3_AVAILABLE = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from block_store.kits.universal_kernel.wave2.vector_store import Chunk, VectorStore
from block_store.kits.universal_kernel.wave2.hybrid_retrieval import hybrid_search

TENANT_ID = "cerebrum_prebuilt"
DEFAULT_DIM = 384

APPROVED_RAG_INDEXES: Dict[str, Dict[str, Any]] = {
    "confusable_pharma_benchmark": {
        "project_id": "prebuilt_pharma_core",
        "domain": "pharma",
        "jurisdiction": ["US"],
        "corpus_path": "data/corpus.jsonl",
        "record_parser": "confusable_pharma",
    },
    "danragbench_benchmark": {
        "project_id": "prebuilt_danish_public_sector_core",
        "domain": "danish_public_sector",
        "jurisdiction": ["DK"],
        "corpus_path": "corpus_text_extracted_for_verification.parquet",
        "record_parser": "danragbench",
    },
    "obliqa_mp_benchmark": {
        "project_id": "prebuilt_legal_adgm_core",
        "domain": "legal",
        "jurisdiction": ["ADGM", "UAE"],
        "corpus_path": "ObliQA_MultiPassage_train.json",
        "record_parser": "obliqa_mp",
    },
    "parsebench_benchmark": {
        "project_id": "prebuilt_document_parsing_core",
        "domain": "document_parsing",
        "jurisdiction": ["multinational"],
        "corpus_path": "parsebench_rules",
        "record_parser": "parsebench",
    },
    "recor_benchmark": {
        "project_id": "prebuilt_multi_domain_qa_core",
        "domain": "multi-domain",
        "jurisdiction": ["multi"],
        "corpus_path": "data/corpus",
        "record_parser": "recor",
    },
    "enterpriserag_benchmark": {
        "project_id": "prebuilt_enterprise_rag_core",
        "domain": "enterprise_rag",
        "jurisdiction": ["multi"],
        "corpus_path": "all_documents.zip",
        "record_parser": "enterpriserag",
        "max_chunks": 350000,
    },
    "mtrag_benchmark": {
        "project_id": "prebuilt_universal_multiturn_core",
        "domain": "universal",
        "jurisdiction": ["multi"],
        "corpus_path": "source_repo/corpora/passage_level",
        "record_parser": "mtrag",
    },
    "t2ragbench_benchmark": {
        "project_id": "prebuilt_finance_sec_core",
        "domain": "finance",
        "jurisdiction": ["US"],
        "corpus_path": "data",
        "record_parser": "t2ragbench",
    },
}


def _fast_hash_embedding(text: str, dim: int = 384) -> List[float]:
    if not text:
        vec = np.zeros(dim, dtype=np.float32)
        vec[0] = 1.0
        return vec.tolist()
    if _MMH3_AVAILABLE:
        h1, h2 = mmh3.hash64(text.encode("utf-8"), seed=42)
        seed = (h1 & 0xFFFFFFFFFFFFFFFF) | ((h2 & 0xFFFFFFFFFFFFFFFF) << 64)
    else:
        seed = hash(text) & 0xFFFFFFFFFFFFFFFF
    rng = np.random.default_rng(seed)
    vec = rng.standard_normal(dim).astype(np.float32)
    norm = np.linalg.norm(vec)
    if norm == 0:
        vec[0] = 1.0
    else:
        vec = vec / norm
    return vec.tolist()


def _embed_batch(texts: List[str], dim: int = 384) -> List[List[float]]:
    return [_fast_hash_embedding(t, dim) for t in texts]


def _parse_confusable_pharma(record: Dict[str, Any]) -> Chunk:
    doc_id = record.get("doc_id", "")
    title = record.get("title", "")
    text = record.get("text", "")
    meta = record.get("metadata", {}) or {}
    return Chunk(
        id=f"pharma_fda_psg:{doc_id}",
        text=text,
        vector=[],
        metadata={
            "project_id": "prebuilt_pharma_core",
            "domain": "pharma",
            "jurisdiction": "US",
            "authority": "U.S. Food and Drug Administration",
            "authority_type": "regulatory_guidance",
            "title": title,
            "active_ingredient": meta.get("active_ingredient"),
            "dosage_form": meta.get("dosage_form"),
            "route": meta.get("route"),
            "source_url": meta.get("source_url"),
            "document_type": meta.get("document_type"),
            "doc_id": doc_id,
        },
    )


def _parse_danragbench(record: Dict[str, Any]) -> Chunk:
    page_id = record.get("page_id", "")
    doc_id = record.get("doc_id", "")
    return Chunk(
        id=f"danish_public:{page_id}",
        text=record.get("text", ""),
        vector=[],
        metadata={
            "project_id": "prebuilt_danish_public_sector_core",
            "domain": "danish_public_sector",
            "jurisdiction": "DK",
            "authority": record.get("sector", ""),
            "authority_type": "public_sector_report",
            "title": record.get("title", ""),
            "doc_id": doc_id,
            "page_num": record.get("page_num"),
            "page_id": page_id,
        },
    )


def _parse_obliqa_mp(record: Dict[str, Any]) -> Iterable[Chunk]:
    for passage in record.get("Passages", []):
        passage_id = passage.get("ID", passage.get("PassageID", ""))
        doc_id = passage.get("DocumentID", "")
        text = passage.get("Passage", "")
        if not text:
            continue
        yield Chunk(
            id=f"adgm_reg:{passage_id}",
            text=text,
            vector=[],
            metadata={
                "project_id": "prebuilt_legal_adgm_core",
                "domain": "legal",
                "jurisdiction": "ADGM",
                "authority": "Abu Dhabi Global Market Financial Services Regulatory Authority",
                "authority_type": "regulatory_guidance",
                "document_id": doc_id,
                "passage_id": passage_id,
            },
        )


def _parse_parsebench(record: Dict[str, Any]) -> Chunk:
    rule = record.get("rule", "")
    if isinstance(rule, (dict, list)):
        text = json.dumps(rule, ensure_ascii=False)
    else:
        text = str(rule)
    return Chunk(
        id=f"parsebench:{record.get('id', '')}",
        text=text,
        vector=[],
        metadata={
            "project_id": "prebuilt_document_parsing_core",
            "domain": "document_parsing",
            "jurisdiction": "multi",
            "authority": "ParseBench",
            "authority_type": "parsing_benchmark",
            "category": record.get("category", ""),
            "type": record.get("type", ""),
            "pdf": record.get("pdf", ""),
            "page": record.get("page"),
            "tags": record.get("tags", []),
        },
    )


def _parse_recor(record: Dict[str, Any]) -> Chunk:
    doc_id = record.get("doc_id", "")
    return Chunk(
        id=f"recor:{doc_id}",
        text=record.get("content", ""),
        vector=[],
        metadata={
            "project_id": "prebuilt_multi_domain_qa_core",
            "domain": "multi-domain",
            "jurisdiction": "multi",
            "authority": "RECOR",
            "authority_type": "qa_benchmark",
            "doc_id": doc_id,
        },
    )


def _parse_enterpriserag(archive_name: str, text: str) -> Chunk:
    import re
    match = re.search(r"dsid_[a-f0-9]+", archive_name)
    doc_id = match.group(0) if match else archive_name
    parts = archive_name.split("/")
    source_type = parts[0] if parts else "unknown"
    return Chunk(
        id=f"enterpriserag:{doc_id}",
        text=text,
        vector=[],
        metadata={
            "project_id": "prebuilt_enterprise_rag_core",
            "domain": "enterprise_rag",
            "jurisdiction": "multi",
            "authority": "Onyx / EnterpriseRAG-Bench",
            "authority_type": "synthetic_enterprise_benchmark",
            "source_type": source_type,
            "archive_path": archive_name,
        },
    )


def _parse_mtrag(record: Dict[str, Any], corpus_name: str) -> Chunk:
    doc_id = record.get("id", record.get("doc_id", ""))
    return Chunk(
        id=f"mtrag:{corpus_name}:{doc_id}",
        text=record.get("text", ""),
        vector=[],
        metadata={
            "project_id": "prebuilt_universal_multiturn_core",
            "domain": "universal",
            "jurisdiction": "multi",
            "authority": "IBM MTRAG",
            "authority_type": "multiturn_rag_benchmark",
            "corpus": corpus_name,
            "doc_id": doc_id,
        },
    )


def _parse_t2ragbench(subset: str, record: Dict[str, Any]) -> Chunk:
    record_id = record.get("id", "")
    text = record.get("context") or record.get("question", "")
    meta = {
        "project_id": "prebuilt_finance_sec_core",
        "domain": "finance",
        "jurisdiction": "US",
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
    return Chunk(
        id=f"t2ragbench:{subset}:{record_id}",
        text=text,
        vector=[],
        metadata=meta,
    )


def _chunks_from_kit(kit_path: Path, spec: Dict[str, Any]) -> Iterable[Chunk]:
    corpus_file = kit_path / spec["corpus_path"]
    parser = spec["record_parser"]

    if parser == "danragbench":
        import pandas as pd
        df = pd.read_parquet(corpus_file)
        for record in df.to_dict("records"):
            yield _parse_danragbench(record)
        return

    if parser == "obliqa_mp":
        seen_ids: Set[str] = set()
        for split_file in ["ObliQA_MultiPassage_train.json", "ObliQA_MultiPassage_val.json", "ObliQA_MultiPassage_test.json"]:
            split_path = kit_path / split_file
            if not split_path.exists():
                continue
            with split_path.open("rb") as fh:
                records = _JSON_LOAD(fh)
            for record in records:
                for chunk in _parse_obliqa_mp(record):
                    if chunk.id in seen_ids:
                        continue
                    seen_ids.add(chunk.id)
                    yield chunk
        return

    if parser == "parsebench":
        rule_files = ["chart.jsonl", "table.jsonl", "text_content.jsonl", "text_formatting.jsonl", "layout.jsonl"]
        seen_ids: Set[str] = set()
        for fname in rule_files:
            fpath = kit_path / fname
            if not fpath.exists():
                continue
            with fpath.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = _JSON_LOADS(line)
                    except Exception as exc:
                        print(f"WARN: malformed JSONL in {fpath}: {exc}")
                        continue
                    chunk = _parse_parsebench(record)
                    if chunk.id in seen_ids:
                        continue
                    seen_ids.add(chunk.id)
                    yield chunk
        return

    if parser == "recor":
        corpus_dir = kit_path / spec["corpus_path"]
        if not corpus_dir.exists():
            raise FileNotFoundError(f"RECOR corpus dir not found: {corpus_dir}")
        seen_ids: Set[str] = set()
        for fpath in sorted(corpus_dir.glob("*_documents.jsonl")):
            with fpath.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = _JSON_LOADS(line)
                    except Exception as exc:
                        print(f"WARN: malformed JSONL in {fpath}: {exc}")
                        continue
                    chunk = _parse_recor(record)
                    if chunk.id in seen_ids:
                        continue
                    seen_ids.add(chunk.id)
                    yield chunk
        return

    if parser == "enterpriserag":
        import zipfile
        import re
        zip_path = kit_path / spec["corpus_path"]
        if not zip_path.exists():
            raise FileNotFoundError(f"EnterpriseRAG zip not found: {zip_path}")
        seen_ids: Set[str] = set()
        doc_id_re = re.compile(r"dsid_([a-f0-9]+)")
        with zipfile.ZipFile(zip_path, "r") as zf:
            for info in zf.infolist():
                if info.is_dir() or not info.filename.endswith(".txt"):
                    continue
                match = doc_id_re.search(info.filename)
                if not match:
                    continue
                doc_id = match.group(0)
                with zf.open(info) as fh:
                    text = fh.read().decode("utf-8", errors="replace")
                if len(text.strip()) < 3:
                    continue
                chunk = _parse_enterpriserag(info.filename, text)
                if chunk.id in seen_ids:
                    continue
                seen_ids.add(chunk.id)
                yield chunk
        return

    if parser == "mtrag":
        import zipfile
        corpus_dir = kit_path / spec["corpus_path"]
        if not corpus_dir.exists():
            raise FileNotFoundError(f"MTRAG corpus dir not found: {corpus_dir}")
        seen_ids: Set[str] = set()
        for zip_path in sorted(corpus_dir.glob("*.jsonl.zip")):
            corpus_name = zip_path.stem.replace(".jsonl", "")
            with zipfile.ZipFile(zip_path, "r") as zf:
                for info in zf.infolist():
                    if info.is_dir() or not info.filename.endswith(".jsonl"):
                        continue
                    with zf.open(info) as fh:
                        for line in fh:
                            line = line.decode("utf-8", errors="replace").strip()
                            if not line:
                                continue
                            try:
                                record = _JSON_LOADS(line)
                            except Exception as exc:
                                print(f"WARN: malformed JSONL in {zip_path}/{info.filename}: {exc}")
                                continue
                            chunk = _parse_mtrag(record, corpus_name)
                            if chunk.id in seen_ids:
                                continue
                            seen_ids.add(chunk.id)
                            yield chunk
        return

    if parser == "t2ragbench":
        source_files = [
            ("FinQA", kit_path / "data" / "FinQA" / "train" / "metadata.jsonl"),
            ("FinQA", kit_path / "data" / "FinQA" / "dev" / "metadata.jsonl"),
            ("FinQA", kit_path / "data" / "FinQA" / "test" / "metadata.jsonl"),
            ("ConvFinQA", kit_path / "data" / "ConvFinQA" / "turn_0.jsonl"),
            ("TAT-DQA", kit_path / "data" / "TAT-DQA" / "train" / "metadata.jsonl"),
            ("TAT-DQA", kit_path / "data" / "TAT-DQA" / "dev" / "metadata.jsonl"),
            ("TAT-DQA", kit_path / "data" / "TAT-DQA" / "test" / "metadata.jsonl"),
        ]
        seen_ids: Set[str] = set()
        for subset, file_path in source_files:
            if not file_path.exists():
                print(f"WARN: T2-RAGBench source file missing, skipping: {file_path}")
                continue
            with file_path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = _JSON_LOADS(line)
                    except Exception as exc:
                        print(f"WARN: malformed JSONL in {file_path}: {exc}")
                        continue
                    record_id = record.get("id")
                    if not record_id:
                        continue
                    chunk = _parse_t2ragbench(subset, record)
                    if chunk.id in seen_ids:
                        continue
                    seen_ids.add(chunk.id)
                    yield chunk
        return

    with corpus_file.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = _JSON_LOADS(line)
            except Exception as exc:
                print(f"WARN: malformed JSONL in {corpus_file}: {exc}")
                continue
            if parser == "confusable_pharma":
                yield _parse_confusable_pharma(record)
            else:
                raise ValueError(f"unknown parser: {parser}")


def index_kit(kit_name: str, batch_size: int = 4096) -> Dict[str, Any]:
    spec = APPROVED_RAG_INDEXES[kit_name]
    project_id = spec["project_id"]
    kit_path = Path(__file__).resolve().parent / kit_name
    if not kit_path.exists():
        raise FileNotFoundError(f"kit folder not found: {kit_path}")

    store = VectorStore()
    indexed = 0
    total = 0
    batch: List[Chunk] = []

    max_chunks = spec.get("max_chunks")
    for chunk in _chunks_from_kit(kit_path, spec):
        batch.append(chunk)
        total += 1
        if max_chunks and total >= max_chunks:
            print(f"  reached max_chunks limit ({max_chunks}) for {project_id}")
            break
        if len(batch) >= batch_size:
            texts = [c.text for c in batch]
            vectors = _embed_batch(texts)
            for c, vector in zip(batch, vectors):
                c.vector = vector
            indexed += store.upsert(TENANT_ID, project_id, batch)
            print(f"  indexed {indexed}/{total}+ chunks for {project_id}")
            batch = []

    if batch:
        texts = [c.text for c in batch]
        vectors = _embed_batch(texts)
        for c, vector in zip(batch, vectors):
            c.vector = vector
        indexed += store.upsert(TENANT_ID, project_id, batch)
        print(f"  indexed {indexed}/{total} chunks for {project_id}")

    result = {
        "tenant_id": TENANT_ID,
        "project_id": project_id,
        "kit": kit_name,
        "provider": "fast_hash_fallback",
        "dimensions": DEFAULT_DIM,
        "chunks_indexed": indexed,
        "store_count": store.count(TENANT_ID, project_id),
        "vector_store_path": str((kit_path / "vector_store.pkl").relative_to(PROJECT_ROOT)),
    }

    # Verify using the live store before pickling to avoid reloading huge stores.
    query = VERIFICATION_QUERIES.get(project_id)
    if query:
        print(f"Verifying {project_id} ...")
        v = verify_index(store, project_id, query)
        print(json.dumps(v, indent=2))
        verification_path = kit_path / f"{kit_name}_verification.json"
        verification_path.write_text(json.dumps(v, indent=2), encoding="utf-8")

    # Pickle the store.
    pkl_path = kit_path / "vector_store.pkl"
    with pkl_path.open("wb") as fh:
        pickle.dump(store, fh, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"  saved {pkl_path}")

    return result


def verify_index(store: VectorStore, project_id: str, query: str) -> Dict[str, Any]:
    query_vector = _fast_hash_embedding(query)
    result = hybrid_search(store, TENANT_ID, project_id, query, query_vector, top_k=3)
    return {
        "query": query,
        "project_id": project_id,
        "honesty": result.get("honesty"),
        "top_results": [
            {
                "chunk_id": r.chunk.id,
                "score": r.score,
                "text_snippet": r.source_citation["text_snippet"],
                "metadata": r.source_citation.get("metadata"),
            }
            for r in result.get("results", [])
        ],
    }


VERIFICATION_QUERIES: Dict[str, str] = {
    "prebuilt_pharma_core": "Abacavir bioequivalence tablet",
    "prebuilt_danish_public_sector_core": "Danmarks Nationalbank annual report 2024",
    "prebuilt_legal_adgm_core": "fair treatment of shareholders ADGM",
    "prebuilt_document_parsing_core": "table missing sentence",
    "prebuilt_multi_domain_qa_core": "tax revenue economic development",
    "prebuilt_enterprise_rag_core": "Redwood Inference enterprise RAG",
    "prebuilt_universal_multiturn_core": "what are the tax implications",
    "prebuilt_finance_sec_core": "Income before income taxes carpenter technology corp 2019",
}


def main() -> int:
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <kit_name>")
        return 1

    kit_name = sys.argv[1]
    if kit_name not in APPROVED_RAG_INDEXES:
        print(f"Unknown kit: {kit_name}. Approved: {list(APPROVED_RAG_INDEXES.keys())}")
        return 1

    print(f"Indexing {kit_name} ...")
    result = index_kit(kit_name)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
