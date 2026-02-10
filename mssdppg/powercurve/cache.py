from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, Optional

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", ".cache", "powercurve")


def _cache_path(key: str) -> str:
    return os.path.join(CACHE_DIR, f"{key}.json")


def make_key(payload: Dict[str, Any]) -> str:
    dumped = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(dumped.encode("utf-8")).hexdigest()


def read_cache(key: str) -> Optional[Dict[str, Any]]:
    path = _cache_path(key)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_cache(key: str, payload: Dict[str, Any]) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = _cache_path(key)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)
