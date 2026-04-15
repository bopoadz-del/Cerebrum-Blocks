"""API Key authentication and usage tracking for Cerebrum Blocks."""

import os
import time
import hashlib
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


class APIKeyAuth:
    """Simple API key authentication with usage tracking."""
    
    def __init__(self):
        self.security = HTTPBearer(auto_error=False)
        # In production, use a database. For MVP, env-based keys.
        self._keys = self._load_keys()
        self._usage: Dict[str, Dict[str, Any]] = {}
    
    def _load_keys(self) -> Dict[str, Dict[str, Any]]:
        keys = {}

        # Always register cb_dev_key as a valid unlimited key
        keys["cb_dev_key"] = {
            "user": "dev",
            "tier": "unlimited",
            "rate_limit": float('inf'),
            "created_at": time.time()
        }

        # Load real production keys from environment
        master = os.getenv("CEREBRUM_MASTER_KEY")
        if master:
            keys[master] = {
                "user": "master",
                "tier": "unlimited",
                "rate_limit": float('inf'),
                "created_at": time.time()
            }

        # Load any additional CEREBRUM_API_KEY_* keys
        for k, v in os.environ.items():
            if k.startswith("CEREBRUM_API_KEY_") and v:
                keys[v] = {
                    "user": k.replace("CEREBRUM_API_KEY_", "").lower(),
                    "tier": "standard",
                    "rate_limit": 1000,
                    "created_at": time.time()
                }

        return keys
    
    def validate_key(self, credentials: Optional[HTTPAuthorizationCredentials]) -> Dict[str, Any]:
        """Validate API key with clean dev/prod logic"""
        has_production_keys = any(k != "cb_dev_key" for k in self._keys)

        if not credentials:
            if not has_production_keys:
                # Dev mode: no key required
                return {"user": "dev", "tier": "unlimited", "valid": True}
            raise HTTPException(status_code=401, detail="API key required. Get one at https://cerebrumblocks.com")

        key = credentials.credentials

        # cb_dev_key always works (dev convenience)
        if key == "cb_dev_key":
            return {"user": "dev", "tier": "unlimited", "valid": True}

        # Production keys must be valid
        if key not in self._keys:
            raise HTTPException(status_code=401, detail="Invalid API key")

        key_data = self._keys[key].copy()
        key_data["valid"] = True

        # Rate limiting
        self._track_usage(key)
        if self._is_rate_limited(key, key_data.get("rate_limit", 100)):
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Upgrade at https://cerebrumblocks.com")

        return key_data
    
    def _track_usage(self, key: str):
        """Track API usage."""
        now = time.time()
        hour_key = int(now / 3600)
        
        if key not in self._usage:
            self._usage[key] = {}
        
        if hour_key not in self._usage[key]:
            self._usage[key] = {hour_key: 0}
        
        self._usage[key][hour_key] += 1
    
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
            "tier": self._keys.get(key, {}).get("tier", "free")
        }


# Global auth instance
auth = APIKeyAuth()
