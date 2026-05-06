"""Local Drive Block - Sandboxed read-only filesystem listing within DATA_DIR.

Previously this block exposed unrestricted read/write to any caller — a
trivial server compromise vector. Now it:
  - resolves every requested path through realpath() and rejects anything
    outside DATA_DIR (default ./data, overridable via DATA_DIR env);
  - exposes only the `list` op (read/write removed);
  - returns the resolved path so the SPA can show users where they are.
"""

import os
from typing import Any, Dict, List
from app.core.universal_base import UniversalBlock


def _data_root() -> str:
    """Realpath of the writable data root, the only directory this block
    is permitted to traverse. Falls back to ./data if env var is unset."""
    return os.path.realpath(os.getenv("DATA_DIR", "./data"))


def _safe_resolve(path: str) -> str:
    """Resolve `path` relative to DATA_DIR and reject paths that escape it.

    Raises PermissionError if the realpath result is outside the data root,
    so symlinks, '..' walks, and absolute paths can't be used to read
    arbitrary files.
    """
    root = _data_root()
    candidate = path if os.path.isabs(path) else os.path.join(root, path)
    resolved = os.path.realpath(candidate)
    if resolved != root and not resolved.startswith(root + os.sep):
        raise PermissionError(f"Path outside permitted data root: {path}")
    return resolved


class LocalDriveBlock(UniversalBlock):
    """Local filesystem listing — sandboxed to DATA_DIR.

    Read and write operations were removed because every API key (including
    the public-tier key shipped in the SPA bundle) reaches this block, and
    unrestricted reads were sufficient to dump arbitrary server files.
    """

    name = "local_drive"
    version = "2.0"
    description = "Sandboxed read-only directory listing within DATA_DIR."
    layer = 4
    tags = ["integration", "storage", "local"]
    requires = []

    ui_schema = {
        "input": {
            "type": "file",
            "accept": ["*/*"],
            "placeholder": "Browse server files...",
            "multiline": False
        },
        "output": {
            "type": "list",
            "fields": [
                {"name": "files", "type": "array", "label": "Files"},
                {"name": "path", "type": "text", "label": "Path"}
            ]
        },
        "quick_actions": [
            {"icon": "📁", "label": "Browse Server", "prompt": "List server files"}
        ]
    }

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """List files within DATA_DIR. Other operations are rejected."""
        params = params or {}
        operation = params.get("operation", "list")

        if operation != "list":
            return {
                "status": "error",
                "error": f"Operation '{operation}' is not supported. Only 'list' is allowed.",
            }

        raw_path = input_data if isinstance(input_data, str) else (
            params.get("folder_path") or params.get("path") or "."
        )

        try:
            resolved = _safe_resolve(raw_path)
        except PermissionError as exc:
            return {"status": "error", "error": str(exc)}

        if not os.path.isdir(resolved):
            return {
                "status": "error",
                "error": f"Path is not a directory: {raw_path}",
            }

        try:
            entries = sorted(os.listdir(resolved))
        except OSError as exc:
            return {"status": "error", "error": f"Cannot read directory: {exc}"}

        files: List[Dict] = []
        for name in entries[:200]:
            full = os.path.join(resolved, name)
            try:
                is_dir = os.path.isdir(full)
                size = os.path.getsize(full) if not is_dir else None
            except OSError:
                continue
            files.append({
                "name": name,
                "type": "directory" if is_dir else "file",
                "path": os.path.relpath(full, _data_root()),
                "size": size,
            })

        return {
            "status": "success",
            "operation": "list",
            "path": os.path.relpath(resolved, _data_root()) or ".",
            "files": files,
            "truncated": len(entries) > 200,
        }
