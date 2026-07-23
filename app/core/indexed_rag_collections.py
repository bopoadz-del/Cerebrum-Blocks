"""Loader and validator for the Indexed RAG Collections inventory shelf.

This shelf is the operational inventory of prebuilt RAG collections that have
been indexed into VectorStore pickles. It is separate from the metadata-only
``rag_packs.json`` shelf and may contain ``status: indexed`` records.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.virgin_shelf import PROJECT_ROOT

_SHELF_REL_PATH = Path("block_store") / "shelves" / "indexed_rag_collections.json"

_REQUIRED_COLLECTION_KEYS = {
    "project_id",
    "tenant_id",
    "kit",
    "domain",
    "status",
    "provider",
    "dimensions",
    "chunks_indexed",
    "store_count",
    "vector_store_path",
    "indexed_at",
    "files_present",
}

_REQUIRED_FILE_KEYS = {
    "kernel_manifest",
    "indexed_json",
    "verification_json",
    "vector_store_pkl",
}


class IndexedRagCollectionsError(Exception):
    """Raised when the indexed collections shelf cannot be located or parsed."""


class IndexedRagCollection:
    """Lightweight wrapper around a single indexed RAG collection."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @property
    def project_id(self) -> str:
        return self._data["project_id"]

    @property
    def tenant_id(self) -> str:
        return self._data["tenant_id"]

    @property
    def kit(self) -> str:
        return self._data["kit"]

    @property
    def domain(self) -> str | None:
        return self._data.get("domain")

    @property
    def status(self) -> str:
        return self._data["status"]

    @property
    def provider(self) -> str:
        return self._data["provider"]

    @property
    def dimensions(self) -> int:
        return int(self._data["dimensions"])

    @property
    def chunks_indexed(self) -> int:
        return int(self._data["chunks_indexed"])

    @property
    def store_count(self) -> int:
        return int(self._data["store_count"])

    @property
    def vector_store_path(self) -> str:
        return self._data["vector_store_path"]

    @property
    def indexed_at(self) -> str:
        return self._data["indexed_at"]

    @property
    def files_present(self) -> dict[str, bool]:
        return dict(self._data.get("files_present", {}))

    @property
    def notes(self) -> str | None:
        return self._data.get("notes")

    def to_dict(self) -> dict[str, Any]:
        return dict(self._data)


def _shelf_path(path: Path | str | None = None) -> Path:
    """Return the absolute path to the indexed collections shelf file."""
    if path:
        return Path(path)
    return PROJECT_ROOT / _SHELF_REL_PATH


def load_shelf(path: Path | str | None = None) -> dict[str, Any]:
    """Load the raw indexed collections shelf JSON."""
    target = Path(path) if path else _shelf_path()
    if not target.exists():
        raise IndexedRagCollectionsError(f"Indexed collections shelf not found: {target}")

    try:
        with open(target, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        raise IndexedRagCollectionsError(f"invalid JSON in indexed collections shelf {target}: {exc}")
    except OSError as exc:
        raise IndexedRagCollectionsError(f"cannot read indexed collections shelf {target}: {exc}")


def list_collections(path: Path | str | None = None) -> list[IndexedRagCollection]:
    """Return all indexed RAG collections from the shelf."""
    data = load_shelf(path)
    if "collections" not in data:
        raise IndexedRagCollectionsError("indexed collections shelf missing top-level 'collections' key")
    return [IndexedRagCollection(c) for c in data["collections"]]


def list_project_ids(path: Path | str | None = None) -> list[str]:
    """Return sorted project IDs for all indexed collections."""
    return sorted(c.project_id for c in list_collections(path))


def get_collection(project_id: str, path: Path | str | None = None) -> IndexedRagCollection:
    """Fetch a single indexed collection by project_id."""
    for collection in list_collections(path):
        if collection.project_id == project_id:
            return collection
    raise IndexedRagCollectionsError(f"Indexed collection not found for project_id: {project_id}")


def validate_shelf(path: Path | str | None = None) -> list[str]:
    """Validate the indexed collections shelf and return human-readable errors."""
    errors: list[str] = []
    try:
        data = load_shelf(path)
    except IndexedRagCollectionsError as exc:
        return [str(exc)]

    if data.get("shelf_id") != "indexed_rag_collections":
        errors.append("shelf_id must be 'indexed_rag_collections'")

    for key in ("schema_version", "shelf_id", "name", "description", "collections"):
        if key not in data:
            errors.append(f"shelf missing top-level key: {key}")

    if "collections" not in data:
        return errors

    seen_project_ids: set[str] = set()
    seen_kits: set[str] = set()

    for idx, collection in enumerate(data["collections"]):
        prefix = f"collection[{idx}]"
        missing = _REQUIRED_COLLECTION_KEYS - set(collection.keys())
        if missing:
            errors.append(f"{prefix} missing keys: {sorted(missing)}")
            continue

        project_id = collection["project_id"]
        if project_id in seen_project_ids:
            errors.append(f"duplicate project_id: {project_id}")
        seen_project_ids.add(project_id)

        kit = collection["kit"]
        if kit in seen_kits:
            errors.append(f"duplicate kit: {kit}")
        seen_kits.add(kit)

        if collection.get("status") != "indexed":
            errors.append(f"{prefix} status must be 'indexed'")

        for num_key in ("dimensions", "chunks_indexed", "store_count"):
            value = collection.get(num_key)
            if not isinstance(value, int) or value < 0:
                errors.append(f"{prefix} '{num_key}' must be a non-negative integer")

        if collection.get("store_count", 0) > collection.get("chunks_indexed", 0):
            errors.append(f"{prefix} store_count cannot exceed chunks_indexed")

        files_present = collection.get("files_present")
        if not isinstance(files_present, dict):
            errors.append(f"{prefix} 'files_present' must be an object")
        else:
            missing_files = _REQUIRED_FILE_KEYS - set(files_present.keys())
            if missing_files:
                errors.append(f"{prefix} 'files_present' missing keys: {sorted(missing_files)}")
            for file_key, present in files_present.items():
                if file_key in _REQUIRED_FILE_KEYS and present is not True:
                    errors.append(f"{prefix} required artifact '{file_key}' is not present")

    return errors
