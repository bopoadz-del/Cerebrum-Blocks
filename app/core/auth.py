"""API Key authentication and usage tracking for Cerebrum Blocks."""

import hmac
import logging
import os
import sqlite3
import sys
import threading
import time
from typing import Optional, Dict, Any

from fastapi import HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


logger = logging.getLogger(__name__)


class _UsageStore:
    """Hour-bucketed usage counter shared across processes.

    Backed by SQLite in WAL mode at $DATA_DIR/rate_limits.db when DATA_DIR
    is writable; falls back to a process-local dict otherwise. The
    previous in-memory-only implementation reset on every worker restart
    and let multi-worker deployments multiply the limit by `n` (each
    worker had an independent counter). With SQLite WAL the upsert is
    atomic across processes on the same host.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._mem: Dict[str, Dict[int, int]] = {}
        self._db_path: Optional[str] = None
        self._setup_db()

    def _setup_db(self) -> None:
        data_dir = os.getenv("DATA_DIR", "./data")
        try:
            os.makedirs(data_dir, exist_ok=True)
            path = os.path.join(data_dir, "rate_limits.db")
            with sqlite3.connect(path, timeout=2.0) as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS usage("
                    "  key TEXT NOT NULL, "
                    "  hour_bucket INTEGER NOT NULL, "
                    "  count INTEGER NOT NULL DEFAULT 0, "
                    "  PRIMARY KEY (key, hour_bucket))"
                )
            self._db_path = path
        except (OSError, sqlite3.Error) as exc:
            logger.warning(
                "rate_limit: SQLite backend unavailable (%s) — falling back "
                "to in-memory counter; multi-worker bypass possible.", exc,
            )
            self._db_path = None

    def increment(self, key: str, hour_bucket: int) -> int:
        if self._db_path:
            try:
                with sqlite3.connect(self._db_path, timeout=2.0) as conn:
                    conn.execute(
                        "INSERT INTO usage(key, hour_bucket, count) VALUES(?, ?, 1) "
                        "ON CONFLICT(key, hour_bucket) DO UPDATE SET count = count + 1",
                        (key, hour_bucket),
                    )
                    row = conn.execute(
                        "SELECT count FROM usage WHERE key=? AND hour_bucket=?",
                        (key, hour_bucket),
                    ).fetchone()
                    return int(row[0]) if row else 0
            except sqlite3.Error as exc:
                logger.warning("rate_limit: SQLite write failed (%s)", exc)
                # fall through to memory backup
        with self._lock:
            self._mem.setdefault(key, {})
            self._mem[key][hour_bucket] = self._mem[key].get(hour_bucket, 0) + 1
            return self._mem[key][hour_bucket]

    def get(self, key: str, hour_bucket: int) -> int:
        if self._db_path:
            try:
                with sqlite3.connect(self._db_path, timeout=2.0) as conn:
                    row = conn.execute(
                        "SELECT count FROM usage WHERE key=? AND hour_bucket=?",
                        (key, hour_bucket),
                    ).fetchone()
                    return int(row[0]) if row else 0
            except sqlite3.Error:
                pass
        with self._lock:
            return self._mem.get(key, {}).get(hour_bucket, 0)

    def prune_older_than(self, hour_bucket: int) -> None:
        """Drop counters strictly older than `hour_bucket`. Cheap to call
        once per request — SQLite does the work without scanning."""
        if self._db_path:
            try:
                with sqlite3.connect(self._db_path, timeout=2.0) as conn:
                    conn.execute("DELETE FROM usage WHERE hour_bucket < ?", (hour_bucket,))
            except sqlite3.Error:
                pass
        with self._lock:
            for k in list(self._mem):
                self._mem[k] = {h: c for h, c in self._mem[k].items() if h >= hour_bucket}
                if not self._mem[k]:
                    del self._mem[k]


class APIKeyAuth:
    """API key authentication with usage tracking and periodic env reload."""

    def __init__(self):
        self.security = HTTPBearer(auto_error=False)
        self._keys: Dict[str, Dict] = {}
        self._keys_loaded_at: float = 0.0
        self._reload_ttl = float(os.getenv("API_KEYS_RELOAD_TTL", "60"))
        self._usage = _UsageStore()
        self._reload_keys()

    @staticmethod
    def _is_dev_environment() -> bool:
        # Single source of truth: ENV / ENVIRONMENT env vars. The previous
        # version also returned True if `pytest` was anywhere in sys.modules,
        # which incorrectly triggers when a worker has pytest preloaded for
        # any reason — silently activating the cb_dev_key in production.
        env = os.getenv("ENV", os.getenv("ENVIRONMENT", "production")).strip().lower()
        return env in {"dev", "development", "local", "test", "testing"}

    def _load_keys(self) -> Dict[str, Dict]:
        keys: Dict[str, Dict] = {}

        if self._is_dev_environment():
            keys["cb_dev_key"] = {
                "user": "dev",
                "tier": "unlimited",
                "role": "admin",
                "rate_limit": float('inf'),
                "created_at": time.time(),
            }

        master = os.getenv("CEREBRUM_MASTER_KEY")
        if master:
            keys[master] = {
                "user": "master",
                "tier": "unlimited",
                "role": "admin",
                "rate_limit": float('inf'),
                "created_at": time.time(),
            }

        for k, v in os.environ.items():
            if k.startswith("CEREBRUM_API_KEY_") and v:
                keys[v] = {
                    "user": k.replace("CEREBRUM_API_KEY_", "").lower(),
                    "tier": "standard",
                    "role": "user",
                    "rate_limit": 1000,
                    "created_at": time.time(),
                }

        return keys

    def _reload_keys(self) -> None:
        self._keys = self._load_keys()
        self._keys_loaded_at = time.time()
        logger.info("auth: loaded %d API key(s)", len(self._keys))

    def _maybe_reload(self) -> None:
        if self._reload_ttl > 0 and time.time() - self._keys_loaded_at > self._reload_ttl:
            self._reload_keys()

    def reload(self) -> None:
        """Force an immediate key reload from environment."""
        self._reload_keys()

    def validate_key(self, credentials: Optional[HTTPAuthorizationCredentials]) -> Dict[str, Any]:
        if not credentials:
            raise HTTPException(status_code=401, detail="API key required.")

        self._maybe_reload()

        key = credentials.credentials

        # Constant-time match against every loaded key. dict-membership
        # leaks timing on long shared prefixes; hmac.compare_digest does
        # not. Cost is O(N keys × len(longest)) per request — fine for
        # the small key set this service runs (single-digit count).
        matched = None
        for known in self._keys:
            if hmac.compare_digest(key, known):
                matched = known
                break
        if matched is None:
            raise HTTPException(status_code=401, detail="Invalid API key")

        key_data = self._keys[matched].copy()
        key_data["valid"] = True
        # Default role for legacy entries — unlimited keys without a role
        # are treated as admin (master keys), standard keys as user.
        if "role" not in key_data:
            key_data["role"] = "admin" if key_data.get("tier") == "unlimited" else "user"

        current_count = self._track_usage(matched)

        if self._is_rate_limited(matched, key_data.get("rate_limit", 100), current_count):
            raise HTTPException(status_code=429, detail="Rate limit exceeded.")

        return key_data

    def _track_usage(self, key: str) -> int:
        """Increment and return usage count for the current hour bucket."""
        hour_bucket = int(time.time() / 3600)
        # Opportunistic prune: keeps the table size bounded with no extra
        # background job. Older-than-current-hour rows are not consulted
        # by the limiter.
        self._usage.prune_older_than(hour_bucket)
        return self._usage.increment(key, hour_bucket)

    def _is_rate_limited(self, key: str, limit: float, current_count: Optional[int] = None) -> bool:
        """Check if key is rate limited."""
        if limit == float('inf'):
            return False
        if current_count is None:
            current_count = self._usage.get(key, int(time.time() / 3600))
        return current_count > limit

    def get_usage(self, key: str) -> Dict[str, Any]:
        """Get usage stats for a key."""
        hour_bucket = int(time.time() / 3600)
        return {
            "requests_this_hour": self._usage.get(key, hour_bucket),
            "rate_limit": self._keys.get(key, {}).get("rate_limit", 100),
            "tier": self._keys.get(key, {}).get("tier", "free"),
        }


# Global auth instance
auth = APIKeyAuth()
