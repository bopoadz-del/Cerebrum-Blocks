"""API Key authentication and usage tracking for Cerebrum Blocks."""

import logging
import os
import sys
import time
from typing import Optional, Dict, Any

from fastapi import HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


logger = logging.getLogger(__name__)


class APIKeyAuth:
    """API key authentication with usage tracking and periodic env reload."""

    def __init__(self):
        self.security = HTTPBearer(auto_error=False)
        self._keys: Dict[str, Dict] = {}
        self._keys_loaded_at: float = 0.0
        self._reload_ttl = float(os.getenv("API_KEYS_RELOAD_TTL", "60"))
        self._usage: Dict[str, Dict[str, Any]] = {}
        self._reload_keys()

    @staticmethod
    def _is_dev_environment() -> bool:
        env = os.getenv("ENV", os.getenv("ENVIRONMENT", "production")).strip().lower()
        if env in {"dev", "development", "local", "test", "testing"}:
            return True
        if "pytest" in sys.modules:
            return True
        return False

    def _load_keys(self) -> Dict[str, Dict]:
        keys: Dict[str, Dict] = {}

        if self._is_dev_environment():
            keys["cb_dev_key"] = {
                "user": "dev",
                "tier": "unlimited",
                "rate_limit": float('inf'),
                "created_at": time.time(),
            }

        master = os.getenv("CEREBRUM_MASTER_KEY")
        if master:
            keys[master] = {
                "user": "master",
                "tier": "unlimited",
                "rate_limit": float('inf'),
                "created_at": time.time(),
            }

        for k, v in os.environ.items():
            if k.startswith("CEREBRUM_API_KEY_") and v:
                keys[v] = {
                    "user": k.replace("CEREBRUM_API_KEY_", "").lower(),
                    "tier": "standard",
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

        if key not in self._keys:
            raise HTTPException(status_code=401, detail="Invalid API key")

        key_data = self._keys[key].copy()
        key_data["valid"] = True
        self._track_usage(key)

        if self._is_rate_limited(key, key_data.get("rate_limit", 100)):
            raise HTTPException(status_code=429, detail="Rate limit exceeded.")

        return key_data

    def _track_usage(self, key: str):
        """Track API usage."""
        now = time.time()
        hour_key = int(now / 3600)

        if key not in self._usage:
            self._usage[key] = {}

        self._usage[key][hour_key] = self._usage[key].get(hour_key, 0) + 1

    def _is_rate_limited(self, key: str, limit: int) -> bool:
        """Check if key is rate limited."""
        if limit == float('inf'):
            return False

        now = time.time()
        hour_key = int(now / 3600)

        usage = self._usage.get(key, {})
        current_hour_usage = usage.get(hour_key, 0)

        return current_hour_usage > limit

    def get_usage(self, key: str) -> Dict[str, Any]:
        """Get usage stats for a key."""
        now = time.time()
        hour_key = int(now / 3600)

        usage = self._usage.get(key, {})
        current_hour = usage.get(hour_key, 0)

        return {
            "requests_this_hour": current_hour,
            "rate_limit": self._keys.get(key, {}).get("rate_limit", 100),
            "tier": self._keys.get(key, {}).get("tier", "free"),
        }


# Global auth instance
auth = APIKeyAuth()
