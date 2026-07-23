"""Build/update kit manifests for every indexed RAG collection.

Reads index_approved_rags_summary.json and creates:
  - block_store/kits/<kit>/kernel_manifest.json
  - block_store/kits/<kit>/<kit>_indexed.json
  - block_store/shelves/indexed_rag_collections.json

The metadata-only domain RAG pack shelf (block_store/shelves/rag_packs.json)
is intentionally NOT modified here; it remains a catalogue of available
domains and must stay in the "not_ingested" state per store standards.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

KITS_DIR = Path(__file__).resolve().parent
SHELVES_DIR = KITS_DIR.parent / "shelves"
SUMMARY_PATH = KITS_DIR / "index_approved_rags_summary.json"
INDEXED_COLLECTIONS_PATH = SHELVES_DIR / "indexed_rag_collections.json"

DOMAIN_NAME_MAP: Dict[str, str] = {
    "prebuilt_pharma_core": "Pharma Core RAG Pack",
    "prebuilt_danish_public_sector_core": "Danish Public Sector Core RAG Pack",
    "prebuilt_legal_adgm_core": "ADGM Financial Regulations Core RAG Pack",
    "prebuilt_document_parsing_core": "Document Parsing Core RAG Pack",
    "prebuilt_multi_domain_qa_core": "Multi-Domain QA Core RAG Pack",
    "prebuilt_enterprise_rag_core": "Enterprise RAG Core RAG Pack",
    "prebuilt_finance_sec_core": "Finance SEC Filings Core RAG Pack",
    "prebuilt_universal_multiturn_core": "Universal Multi-Turn RAG Core Pack",
}

DOMAIN_MAP: Dict[str, str] = {
    "prebuilt_pharma_core": "pharma",
    "prebuilt_danish_public_sector_core": "danish_public_sector",
    "prebuilt_legal_adgm_core": "legal",
    "prebuilt_document_parsing_core": "document_parsing",
    "prebuilt_multi_domain_qa_core": "multi-domain",
    "prebuilt_enterprise_rag_core": "enterprise_rag",
    "prebuilt_finance_sec_core": "finance",
    "prebuilt_universal_multiturn_core": "universal",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_kernel_manifest(index: Dict[str, Any]) -> Dict[str, Any]:
    project_id = index["project_id"]
    kit = index["kit"]
    return {
        "schema_version": "1.0.0",
        "id": project_id,
        "name": DOMAIN_NAME_MAP.get(project_id, project_id),
        "domain": DOMAIN_MAP.get(project_id, "general"),
        "project_id": project_id,
        "tenant_id": index.get("tenant_id", "cerebrum_prebuilt"),
        "kit_folder": kit,
        "status": "indexed",
        "description": f"Indexed RAG collection from {kit}.",
        "embedding": {
            "provider": index.get("provider", "unknown"),
            "dimensions": index.get("dimensions", 384),
        },
        "ingestion_status": {
            "state": "indexed",
            "documents_total": index["chunks_indexed"],
            "documents_indexed": index["chunks_indexed"],
            "chunks_total": index["chunks_indexed"],
            "chunks_indexed": index["chunks_indexed"],
            "last_ingested_at": _now(),
            "last_error": None,
        },
        "source_policy": {
            "allowed_source_classes": [
                "public_domain",
                "open_license",
                "official_statute_or_regulation",
                "official_guidance",
                "platform_curated_template",
            ],
            "precluded_source_classes": [
                "private_enterprise_data",
                "confidential_client_data",
                "copyrighted_commercial_content_without_license",
                "user_uploaded_project_records",
                "unknown_license",
            ],
            "requires_source_record": True,
            "requires_license_review": True,
            "requires_authority_rating": True,
        },
    }


def update_indexed_collections(summary: Dict[str, Any]) -> None:
    """Write/update the operational inventory of indexed RAG collections."""
    collections: Dict[str, Dict[str, Any]] = {}
    if INDEXED_COLLECTIONS_PATH.exists():
        with INDEXED_COLLECTIONS_PATH.open("r", encoding="utf-8") as fh:
            existing = json.load(fh)
        for col in existing.get("collections", []):
            collections[col["project_id"]] = col

    for index in summary.get("indexes", []):
        project_id = index["project_id"]
        kit = index["kit"]
        kit_path = KITS_DIR / kit
        collections[project_id] = {
            "project_id": project_id,
            "tenant_id": index.get("tenant_id", "cerebrum_prebuilt"),
            "kit": kit,
            "domain": DOMAIN_MAP.get(project_id),
            "status": "indexed",
            "provider": index.get("provider", "unknown"),
            "dimensions": index.get("dimensions", 384),
            "chunks_indexed": index["chunks_indexed"],
            "store_count": index.get("store_count", index["chunks_indexed"]),
            "vector_store_path": index.get(
                "vector_store_path", f"block_store/kits/{kit}/vector_store.pkl"
            ),
            "indexed_at": _now(),
            "notes": index.get("notes"),
            "files_present": {
                "kernel_manifest": (kit_path / "kernel_manifest.json").is_file(),
                "indexed_json": (kit_path / f"{kit}_indexed.json").is_file(),
                "verification_json": (kit_path / f"{kit}_verification.json").is_file(),
                "vector_store_pkl": (kit_path / "vector_store.pkl").is_file(),
            },
        }

    data = {
        "schema_version": "1.0.0",
        "shelf_id": "indexed_rag_collections",
        "name": "Indexed RAG Collections Inventory",
        "description": "Operational inventory of successfully indexed prebuilt RAG collections and their store artifacts.",
        "generated_at": _now(),
        "collections": sorted(collections.values(), key=lambda c: c["project_id"]),
    }

    INDEXED_COLLECTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with INDEXED_COLLECTIONS_PATH.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def main() -> int:
    if not SUMMARY_PATH.exists():
        print(f"Summary not found: {SUMMARY_PATH}")
        return 1

    with SUMMARY_PATH.open("r", encoding="utf-8") as fh:
        summary = json.load(fh)

    for index in summary.get("indexes", []):
        kit = index["kit"]
        kit_path = KITS_DIR / kit
        if not kit_path.exists():
            print(f"WARN: kit folder missing: {kit_path}")
            continue

        manifest = build_kernel_manifest(index)
        manifest_path = kit_path / "kernel_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"Wrote {manifest_path}")

        indexed_path = kit_path / f"{kit}_indexed.json"
        indexed_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
        print(f"Wrote {indexed_path}")

    update_indexed_collections(summary)
    print(f"Updated {INDEXED_COLLECTIONS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
