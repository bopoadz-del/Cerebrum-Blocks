"""Tests for the Prebuilt Domain RAG Pack shelf loader/validator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.rag_pack_loader import (
    RagPackLoaderError,
    get_pack,
    list_domain_ids,
    list_packs,
    load_shelf,
    validate_shelf,
)


_EXPECTED_DOMAINS = [
    "agriculture",
    "automotive",
    "aviation",
    "construction",
    "education",
    "finance",
    "hotel_management",
    "hr",
    "insurance",
    "legal",
    "manufacturing",
    "medical",
    "oil_gas",
    "pharma",
    "real_estate",
    "retail",
    "supply_chain",
]


def test_load_shelf_returns_expected_shape():
    data = load_shelf()
    assert data["shelf_id"] == "rag_packs"
    assert "schema_version" in data
    assert "packs" in data
    assert len(data["packs"]) == 17


def test_list_domain_ids_covers_all_17_domains():
    domains = list_domain_ids()
    assert domains == _EXPECTED_DOMAINS


def test_each_pack_has_required_fields():
    for pack in list_packs():
        assert pack.id
        assert pack.domain
        assert pack.name
        assert pack.status
        assert pack.description
        assert pack.collection_id
        assert pack.visibility
        assert pack.data_class
        assert isinstance(pack.enterprise_specific, bool)
        assert pack.requires_blocks
        assert pack.recommended_with_blocks
        assert pack.source_types
        assert isinstance(pack.expected_queries, list)
        assert isinstance(pack.expected_outputs, list)
        assert pack.fetch_mode
        assert pack.ingestion_status
        assert isinstance(pack.notes, list)


def test_each_pack_requires_knowledge_and_vector_search():
    for pack in list_packs():
        requires = set(pack.requires_blocks)
        assert "knowledge" in requires, f"{pack.id} missing knowledge"
        assert "vector_search" in requires, f"{pack.id} missing vector_search"


def test_each_pack_recommends_domain_v2_and_formula_executor():
    for pack in list_packs():
        recommended = set(pack.recommended_with_blocks)
        expected_domain_v2 = f"{pack.domain}_v2"
        assert expected_domain_v2 in recommended, f"{pack.id} missing {expected_domain_v2}"
        assert "formula_executor_v2" in recommended, f"{pack.id} missing formula_executor_v2"


def test_each_pack_is_metadata_only_and_not_ingested():
    for pack in list_packs():
        assert pack.fetch_mode == "metadata_only", f"{pack.id} fetch_mode mismatch"
        assert pack.ingestion_status == "not_ingested", f"{pack.id} ingestion_status mismatch"
        assert pack.enterprise_specific is False, f"{pack.id} enterprise_specific must be false"


def test_pack_collection_ids_are_unique():
    collection_ids = [pack.collection_id for pack in list_packs()]
    assert len(collection_ids) == len(set(collection_ids))


def test_get_pack_for_legal_returns_legal_core_rag():
    pack = get_pack("legal")
    assert pack.id == "legal_core_rag"
    assert pack.domain == "legal"


def test_get_pack_missing_raises():
    with pytest.raises(RagPackLoaderError):
        get_pack("not_a_domain")


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
                "packs": [],
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
                "shelf_id": "rag_packs",
                "name": "Bad Shelf",
                "description": "test",
                "packs": [
                    {
                        "id": "bad_core_rag",
                        "domain": "bad",
                        "name": "Bad",
                        "description": "test",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    errors = validate_shelf(bad_shelf)
    assert any("missing keys" in e for e in errors)


def test_validate_shelf_detects_missing_knowledge_block(tmp_path: Path):
    bad_shelf = tmp_path / "bad_shelf.json"
    bad_shelf.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "shelf_id": "rag_packs",
                "name": "Bad Shelf",
                "description": "test",
                "packs": [
                    {
                        "id": "bad_core_rag",
                        "domain": "bad",
                        "name": "Bad",
                        "description": "test",
                        "status": "metadata_only",
                        "collection_id": "prebuilt_bad_core",
                        "visibility": "platform_prebuilt",
                        "data_class": "public_or_licensed_reference",
                        "enterprise_specific": False,
                        "requires_blocks": ["vector_search"],
                        "recommended_with_blocks": ["bad_v2", "formula_executor_v2"],
                        "source_types": ["guidance"],
                        "expected_queries": [],
                        "expected_outputs": [],
                        "fetch_mode": "metadata_only",
                        "ingestion_status": "not_ingested",
                        "notes": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    errors = validate_shelf(bad_shelf)
    assert any("'knowledge' and 'vector_search'" in e for e in errors)


def test_validate_shelf_detects_enterprise_specific_true(tmp_path: Path):
    bad_shelf = tmp_path / "bad_shelf.json"
    bad_shelf.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "shelf_id": "rag_packs",
                "name": "Bad Shelf",
                "description": "test",
                "packs": [
                    {
                        "id": "bad_core_rag",
                        "domain": "bad",
                        "name": "Bad",
                        "description": "test",
                        "status": "metadata_only",
                        "collection_id": "prebuilt_bad_core",
                        "visibility": "platform_prebuilt",
                        "data_class": "public_or_licensed_reference",
                        "enterprise_specific": True,
                        "requires_blocks": ["knowledge", "vector_search"],
                        "recommended_with_blocks": ["bad_v2", "formula_executor_v2"],
                        "source_types": ["guidance"],
                        "expected_queries": [],
                        "expected_outputs": [],
                        "fetch_mode": "metadata_only",
                        "ingestion_status": "not_ingested",
                        "notes": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    errors = validate_shelf(bad_shelf)
    assert any("enterprise_specific" in e for e in errors)


def test_validate_shelf_detects_ingested_status(tmp_path: Path):
    bad_shelf = tmp_path / "bad_shelf.json"
    bad_shelf.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "shelf_id": "rag_packs",
                "name": "Bad Shelf",
                "description": "test",
                "packs": [
                    {
                        "id": "bad_core_rag",
                        "domain": "bad",
                        "name": "Bad",
                        "description": "test",
                        "status": "metadata_only",
                        "collection_id": "prebuilt_bad_core",
                        "visibility": "platform_prebuilt",
                        "data_class": "public_or_licensed_reference",
                        "enterprise_specific": False,
                        "requires_blocks": ["knowledge", "vector_search"],
                        "recommended_with_blocks": ["bad_v2", "formula_executor_v2"],
                        "source_types": ["guidance"],
                        "expected_queries": [],
                        "expected_outputs": [],
                        "fetch_mode": "metadata_only",
                        "ingestion_status": "ingested",
                        "notes": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    errors = validate_shelf(bad_shelf)
    assert any("ingestion_status" in e for e in errors)
