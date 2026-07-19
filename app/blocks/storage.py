"""Storage Block - File storage with multiple backends.

Supports local disk, in-memory, and cloud (S3/R2) backends. Adds secure
multipart-style upload validation (extension allowlist, path-traversal guard)
and archive helpers for object-store backends.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.universal_base import UniversalBlock


# Lazy import: aiofiles may not be installed in all environments.
aiofiles = None


def _load_aiofiles():
    global aiofiles
    if aiofiles is None:
        try:
            import aiofiles as _aiofiles

            aiofiles = _aiofiles
        except ImportError:
            aiofiles = False
    return aiofiles


def _safe_filename(filename: str) -> str:
    """Return the basename with path separators stripped; blocks traversal."""
    normalized = filename.replace("\\", "/")
    # Reject parent-directory traversal and absolute paths
    if ".." in normalized or normalized.startswith(("/", "\\")):
        return ""
    # Normalize and strip any path components
    cleaned = os.path.basename(normalized)
    # Remove any dangerous chars except extension dot, dash, underscore
    cleaned = re.sub(r"[^\w\-\. ]", "", cleaned)
    if not cleaned or cleaned in {".", ".."}:
        return ""
    return cleaned


class StorageBlock(UniversalBlock):
    """Storage Block - Unified file storage with upload validation."""

    name = "storage"
    version = "1.1.0"
    updated_at = "2026-07-19"
    requires = ["config"]
    layer = 2  # Core layer
    tags = ["storage", "files", "core"]
    default_config = {
        "backend": "local",
        "data_dir": "./data/storage",
        "allowed_extensions": [],  # empty = allow all
        "max_size_bytes": 100 * 1024 * 1024,  # 100 MB
    }

    ui_schema = {
        "input": {
            "type": "json",
            "accept": None,
            "placeholder": 'JSON payload for the selected action',
            "multiline": True,
        },
        "output": {"type": "json", "fields": [{"name": "result", "type": "json", "label": "Result"}]},
        "params": [
            {
                "name": "action",
                "type": "select",
                "label": "Action",
                "options": ["store", "retrieve", "delete", "exists", "list", "upload", "archive"],
                "default": "store",
            }
        ],
        "quick_actions": [],
    }

    def __init__(self, hal_block=None, config: Dict[str, Any] = None):
        super().__init__(hal_block, config)
        self.backend = (config or {}).get("backend", "local")
        self.data_dir = (config or {}).get("data_dir", "./data/storage")
        self.memory_block = None
        os.makedirs(self.data_dir, exist_ok=True)

    async def _legacy_initialize(self):
        print(f"💾 Storage Block initialized")
        print(f"   Backend: {self.backend}")
        print(f"   Data dir: {self.data_dir}")
        return True

    async def process(self, input_data: Dict, params: Dict = None) -> Dict:
        """Storage operations."""
        if isinstance(input_data, str):
            input_data = {"text": input_data}
        input_data = input_data or {}
        action = (params or {}).get("action") or input_data.get("action")

        if action == "store":
            return await self._store(input_data)
        elif action == "retrieve":
            return await self._retrieve(input_data.get("file_id"))
        elif action == "delete":
            return await self._delete(input_data.get("file_id"))
        elif action == "exists":
            return await self._exists(input_data.get("file_id"))
        elif action == "list":
            return await self._list(input_data.get("prefix", ""))
        elif action == "upload":
            return await self._upload(input_data)
        elif action == "archive":
            return await self._archive(input_data)

        return await self._list("")

    async def _store(self, data: Dict) -> Dict:
        """Store a file."""
        content = data.get("content")  # bytes or str
        filename = data.get("filename", "unnamed")
        metadata = data.get("metadata", {})

        if content is None:
            return {"status": "error", "error": "content is required"}

        file_hash = hashlib.sha256(
            content if isinstance(content, bytes) else content.encode()
        ).hexdigest()[:16]
        file_id = f"file_{file_hash}"

        if self.backend == "local":
            file_path = os.path.join(self.data_dir, file_id)
            await self._write_file(file_path, content)

            meta_path = os.path.join(self.data_dir, f"{file_id}.meta")
            await self._write_file(
                meta_path,
                json.dumps({
                    "filename": filename,
                    "metadata": metadata,
                    "stored_at": time.time(),
                }).encode(),
            )

        elif self.backend == "memory" and self.memory_block:
            await self.memory_block.process({
                "action": "set",
                "key": f"storage:{file_id}",
                "value": {
                    "content": content,
                    "filename": filename,
                    "metadata": metadata,
                },
                "ttl": 3600,
            })

        return {"status": "success", "stored": True, "file_id": file_id, "backend": self.backend}

    async def _upload(self, data: Dict) -> Dict:
        """Secure upload: validate extension, size, and path; then store."""
        filename = data.get("filename", "")
        content = data.get("content")
        allowed = data.get("allowed_extensions") or self.config.get("allowed_extensions", [])
        max_size = data.get("max_size_bytes") or self.config.get("max_size_bytes", 100 * 1024 * 1024)

        if not filename:
            return {"status": "error", "error": "filename is required"}
        if content is None:
            return {"status": "error", "error": "content is required"}

        content_bytes = content if isinstance(content, bytes) else content.encode()
        if len(content_bytes) > max_size:
            return {"status": "error", "error": "file exceeds max_size_bytes"}

        safe_name = _safe_filename(filename)
        if not safe_name:
            return {"status": "error", "error": "invalid filename or path traversal detected"}

        if allowed:
            ext = Path(safe_name).suffix.lower()
            if ext not in [a.lower() for a in allowed]:
                return {"status": "error", "error": f"extension '{ext}' not allowed"}

        store_result = await self._store({
            "content": content_bytes,
            "filename": safe_name,
            "metadata": data.get("metadata", {}),
        })
        if store_result.get("status") == "error":
            return store_result

        stored_path = ""
        if self.backend == "local":
            stored_path = os.path.join(self.data_dir, store_result["file_id"])

        return {
            "status": "success",
            "file_id": store_result["file_id"],
            "filename": safe_name,
            "stored_path": stored_path,
            "backend": self.backend,
        }

    async def _archive(self, data: Dict) -> Dict:
        """Archive a local file to S3/R2-compatible object store.

        This is a thin wrapper: it expects either AWS/boto3 or a compatible
        client to be configured via environment variables. The block remains
        neutral about the specific provider.
        """
        file_id = data.get("file_id")
        bucket = data.get("bucket") or os.getenv("STORAGE_ARCHIVE_BUCKET")
        endpoint = data.get("endpoint") or os.getenv("STORAGE_ARCHIVE_ENDPOINT")
        access_key = data.get("access_key") or os.getenv("STORAGE_ARCHIVE_ACCESS_KEY")
        secret_key = data.get("secret_key") or os.getenv("STORAGE_ARCHIVE_SECRET_KEY")

        if not file_id:
            return {"status": "error", "error": "file_id is required"}
        if not bucket:
            return {"status": "error", "error": "archive bucket is required"}

        try:
            import boto3
        except ImportError:
            return {"status": "error", "error": "boto3 is required for archive backend"}

        retrieve_result = await self._retrieve(file_id)
        if retrieve_result.get("status") == "error" or "content" not in retrieve_result:
            return {"status": "error", "error": "source file not found"}

        session_kwargs = {}
        if endpoint:
            session_kwargs["endpoint_url"] = endpoint
        if access_key and secret_key:
            session_kwargs["aws_access_key_id"] = access_key
            session_kwargs["aws_secret_access_key"] = secret_key

        try:
            s3 = boto3.client("s3", **session_kwargs)
            key = data.get("key") or file_id
            s3.put_object(Bucket=bucket, Key=key, Body=retrieve_result["content"])
            return {
                "status": "success",
                "file_id": file_id,
                "bucket": bucket,
                "key": key,
            }
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "error": f"archive failed: {exc}"}

    async def _retrieve(self, file_id: str) -> Dict:
        """Retrieve a file."""
        if not file_id:
            return {"status": "error", "error": "file_id is required"}

        if self.backend == "local":
            file_path = os.path.join(self.data_dir, file_id)
            if not os.path.exists(file_path):
                return {"status": "error", "error": "file_not_found"}

            content = await self._read_file(file_path)

            metadata = {}
            meta_path = os.path.join(self.data_dir, f"{file_id}.meta")
            if os.path.exists(meta_path):
                meta_bytes = await self._read_file(meta_path)
                metadata = json.loads(meta_bytes.decode())

            return {
                "status": "success",
                "file_id": file_id,
                "content": content,
                "filename": metadata.get("filename", "unknown"),
                "metadata": metadata.get("metadata", {}),
            }

        elif self.backend == "memory" and self.memory_block:
            result = await self.memory_block.process({
                "action": "get",
                "key": f"storage:{file_id}",
            })

            if not result.get("hit"):
                return {"status": "error", "error": "file_not_found"}

            data = result.get("value", {})
            return {
                "status": "success",
                "file_id": file_id,
                "content": data.get("content"),
                "filename": data.get("filename"),
                "metadata": data.get("metadata", {}),
            }

        return {"status": "error", "error": "backend_not_supported"}

    async def _delete(self, file_id: str) -> Dict:
        """Delete a file."""
        if not file_id:
            return {"status": "error", "error": "file_id is required"}

        if self.backend == "local":
            file_path = os.path.join(self.data_dir, file_id)
            meta_path = os.path.join(self.data_dir, f"{file_id}.meta")

            deleted = False
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted = True
            if os.path.exists(meta_path):
                os.remove(meta_path)

            return {"status": "success", "deleted": deleted}

        elif self.backend == "memory" and self.memory_block:
            await self.memory_block.process({
                "action": "delete",
                "key": f"storage:{file_id}",
            })
            return {"status": "success", "deleted": True}

        return {"status": "error", "error": "backend_not_supported"}

    async def _exists(self, file_id: str) -> Dict:
        """Check if file exists."""
        if not file_id:
            return {"status": "error", "error": "file_id is required"}

        if self.backend == "local":
            file_path = os.path.join(self.data_dir, file_id)
            return {"status": "success", "exists": os.path.exists(file_path)}

        elif self.backend == "memory" and self.memory_block:
            result = await self.memory_block.process({
                "action": "exists",
                "key": f"storage:{file_id}",
            })
            return {"status": "success", "exists": result.get("exists", False)}

        return {"status": "error", "error": "backend_not_supported"}

    async def _list(self, prefix: str = "") -> Dict:
        """List files."""
        if self.backend == "local":
            files = []
            for f in os.listdir(self.data_dir):
                if not f.endswith(".meta") and f.startswith(prefix):
                    files.append(f)
            return {"status": "success", "files": files, "count": len(files)}

        return {"status": "success", "files": [], "count": 0}

    async def _read_file(self, path: str) -> bytes:
        af = _load_aiofiles()
        if af:
            async with af.open(path, "rb") as f:
                return await f.read()
        # Fallback to synchronous I/O
        with open(path, "rb") as f:
            return f.read()

    async def _write_file(self, path: str, content: bytes) -> None:
        af = _load_aiofiles()
        if af:
            async with af.open(path, "wb") as f:
                await f.write(content)
        else:
            with open(path, "wb") as f:
                f.write(content)

    def health(self) -> Dict[str, Any]:
        """Health check."""
        h = {"name": self.name, "version": self.version}
        h["backend"] = self.backend
        h["data_dir"] = self.data_dir
        return h
