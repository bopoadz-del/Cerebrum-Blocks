"""Tests for the Indexed RAG Collections shelf loader/validator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.indexed_rag_collections import (
    IndexedRagCollectionsError,
    get_collection,
    list_collections,
    list_project_ids,
    load_shelf,
    validate_shelf,
)

_EXPECTED_PROJECT_IDS = [
    "prebuilt_danish_public_sector_core",
    "prebuilt_document_parsing_core",
    "prebuilt_enterprise_rag_core",
    "prebuilt_finance_sec_core",
    "prebuilt_legal_adgm_core",
    "prebuilt_multi_domain_qa_core",
    "prebuilt_pharma_core",
    "prebuilt_universal_multiturn_core",
]

_EXPECTED_KITS = {
    "prebuilt_pharma_core": "confusable_pharma_benchmark",
    "prebuilt_danish_public_sector_core": "danragbench_benchmark",
    "prebuilt_legal_adgm_core": "obliqa_mp_benchmark",
    "prebuilt_document_parsing_core": "parsebench_benchmark",
    "prebuilt_multi_domain_qa_core": "recor_benchmark",
    "prebuilt_finance_sec_core": "t2ragbench_benchmark",
    "prebuilt_enterprise_rag_core": "enterpriserag_benchmark",
    "prebuilt_universal_multiturn_core": "mtrag_benchmark",
}


def test_load_shelf_returns_expected_shape():
    data = load_shelf()
    assert data["shelf_id"] == "indexed_rag_collections"
    assert "schema_version" in data
    assert "collections" in data
    assert len(data["collections"]) == 8


def test_list_project_ids_covers_all_8_collections():
    assert list_project_ids() == _EXPECTED_PROJECT_IDS


def test_each_collection_has_required_fields():
    for collection in list_collections():
        assert collection.project_id
        assert collection.tenant_id
        assert collection.kit
        assert collection.domain
        assert collection.status == "indexed"
        assert collection.provider
        assert collection.dimensions == 384
        assert collection.chunks_indexed >= 0
        assert collection.store_count >= 0
        assert collection.vector_store_path
        assert collection.indexed_at
        assert isinstance(collection.files_present, dict)
        assert collection.files_present["kernel_manifest"] is True
        assert collection.files_present["indexed_json"] is True
        assert collection.files_present["verification_json"] is True
        assert collection.files_present["vector_store_pkl"] is True


def test_store_count_matches_or_is_less_than_chunks_indexed():
    for collection in list_collections():
        assert collection.store_count <= collection.chunks_indexed


def test_project_id_to_kit_mapping():
    for collection in list_collections():
        assert _EXPECTED_KITS[collection.project_id] == collection.kit


def test_get_collection_by_project_id():
    collection = get_collection("prebuilt_pharma_core")
    assert collection.kit == "confusable_pharma_benchmark"
    assert collection.domain == "pharma"


def test_get_collection_missing_raises():
    with pytest.raises(IndexedRagCollectionsError):
        get_collection("not_a_project")


def test_validate_shelf_reports_no_errors():
    errors = validate_shelf()
    assert errors == []


def test_validate_shelf_detects_wrong_shelf_id(tmp_path: Path):
    bad_shelf = tmp_path / "bad_shelf.json"
    bad_shelf.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "shelf_id": "wrong",
                "name": "Wrong Shelf",
                "description": "test",
                "collections": [],
            }
        ),
        encoding="utf-8",
    )
    errors = validate_shelf(bad_shelf)
    assert any("shelf_id" in e for e in errors)


def test_validate_shelf_detects_missing_required_key(tmp_path: Path):
    bad_shelf = tmp_path / "bad_shelf.json"
    bad_shelf.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "shelf_id": "indexed_rag_collections",
                "name": "Bad Shelf",
                "description": "test",
                "collections": [
                    {
                        "project_id": "prebuilt_bad_core",
                        "tenant_id": "cerebrum_prebuilt",
                        "kit": "bad_benchmark",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    errors = validate_shelf(bad_shelf)
    assert any("missing keys" in e for e in errors)


def test_validate_shelf_detects_duplicate_project_id(tmp_path: Path):
    bad_shelf = tmp_path / "bad_shelf.json"
    bad_shelf.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "shelf_id": "indexed_rag_collections",
                "name": "Bad Shelf",
                "description": "test",
                "collections": [
                    _make_bad_collection(),
                    _make_bad_collection(),
                ],
            }
        ),
        encoding="utf-8",
    )
    errors = validate_shelf(bad_shelf)
    assert any("duplicate project_id" in e for e in errors)


def test_validate_shelf_detects_store_count_greater_than_indexed(tmp_path: Path):
    bad_shelf = tmp_path / "bad_shelf.json"
    collection = _make_bad_collection()
    collection["store_count"] = 9999
    bad_shelf.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "shelf_id": "indexed_rag_collections",
                "name": "Bad Shelf",
                "description": "test",
                "collections": [collection],
            }
        ),
        encoding="utf-8",
    )
    errors = validate_shelf(bad_shelf)
    assert any("store_count cannot exceed chunks_indexed" in e for e in errors)


def test_validate_shelf_detects_missing_artifact(tmp_path: Path):
    bad_shelf = tmp_path / "bad_shelf.json"
    collection = _make_bad_collection()
    collection["files_present"]["vector_store_pkl"] = False
    bad_shelf.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "shelf_id": "indexed_rag_collections",
                "name": "Bad Shelf",
                "description": "test",
                "collections": [collection],
            }
        ),
        encoding="utf-8",
    )
    errors = validate_shelf(bad_shelf)
    assert any("vector_store_pkl" in e for e in errors)


def _make_bad_collection():
    return {
        "project_id": "prebuilt_bad_core",
        "tenant_id": "cerebrum_prebuilt",
        "kit": "bad_benchmark",
        "domain": "bad",
        "status": "indexed",
        "provider": "hash",
        "dimensions": 384,
        "chunks_indexed": 1,
        "store_count": 1,
        "vector_store_path": "block_store/kits/bad_benchmark/vector_store.pkl",
        "indexed_at": "2026-07-23T00:00:00+00:00",
        "notes": None,
        "files_present": {
            "kernel_manifest": True,
            "indexed_json": True,
            "verification_json": True,
            "vector_store_pkl": True,
        },
    }
