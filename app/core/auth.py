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
        """Load API keys from environment."""
        keys = {}
        # Format: CEREBRUM_API_KEY_user1=sk-xxx
        for key, value in os.environ.items():
            if key.startswith("CEREBRUM_API_KEY_"):
                user = key.replace("CEREBRUM_API_KEY_", "").lower()
                keys[value] = {
                    "user": user,
                    "tier": "free",
                    "rate_limit": 100,  # requests per hour
                    "created_at": time.time()
                }
        
        # Also support a master key for admin
        master_key = os.getenv("CEREBRUM_MASTER_KEY")
        if master_key:
            keys[master_key] = {
                "user": "admin",
                "tier": "unlimited",
                "rate_limit": float('inf'),
                "created_at": time.time()
            }
        
        # Dev key fallback — matches AuthBlock behavior and frontend default
        keys["cb_dev_key"] = {
            "user": "dev",
            "tier": "unlimited",
            "rate_limit": float('inf'),
            "created_at": time.time()
        }
        
        return keys
    
    def validate_key(self, credentials: Optional[HTTPAuthorizationCredentials]) -> Dict[str, Any]:
        """Validate an API key."""
        # Determine if we're in production mode (real keys configured)
        has_production_keys = any(k != "cb_dev_key" for k in self._keys)

        # If no production keys configured, allow all (development mode)
        if not has_production_keys:
            return {"user": "dev", "tier": "unlimited", "valid": True}

        if not credentials:
            raise HTTPException(status_code=401, detail="API key required. Get one at https://cerebrumblocks.com")

        key = credentials.credentials
        if key not in self._keys:
            raise HTTPException(status_code=401, detail="Invalid API key")

        key_data = self._keys[key].copy()
        key_data["valid"] = True

        # Check rate limit
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


async def require_api_key(request: Request) -> Dict[str, Any]:
    """Dependency to require API key on endpoints."""
    credentials = await auth.security(request)
    return auth.validate_key(credentials)
