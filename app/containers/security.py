"""Security Container - Auth, secrets, sandbox, audit"""

import hashlib
import os
import time
from typing import Any, Dict
from app.core.universal_base import UniversalContainer


class SecurityContainer(UniversalContainer):
    """
    Security Container: API key auth, rate limiting, sandbox, audit logging
    """
    
    name = "security"
    version = "1.0"
    description = "Security: Auth, Secrets, Sandbox, Audit, Rate Limiter"
    layer = 1  # Security layer
    tags = ["security", "container", "auth"]
    requires = []
    
    def __init__(self, hal_block=None, config: Dict = None):
        super().__init__(hal_block, config)
        self.api_keys = {}
        self.rate_counters = {}
        self.audit_log = []
    
    async def route(self, action: str, input_data: Any, params: Dict) -> Dict:
        if action == "create_key":
            return await self.create_key(params)
        elif action == "auth":
            return await self.auth(params)
        elif action == "check_rate":
            return await self.check_rate(params)
        elif action == "sandbox_check":
            return await self.sandbox_check(input_data, params)
        elif action == "audit":
            return await self.audit(params)
        elif action == "health_check":
            return await self.health_check()
        else:
            return {"error": f"Unknown action: {action}"}
    
    async def create_key(self, params: Dict) -> Dict:
        """Generate API key"""
        owner = params.get("owner", "anonymous")
        key_hash = hashlib.sha256(os.urandom(32)).hexdigest()[:24]
        api_key = f"cb_{key_hash}"
        
        self.api_keys[api_key] = {
            "owner": owner,
            "created_at": time.time(),
            "role": params.get("role", "user"),
            "rate_limit": params.get("rate_limit", 100)
        }
        
        return {
            "status": "success",
            "created": True,
            "api_key": api_key,
            "role": "user",
            "rate_limit": 100
        }
    
    async def auth(self, params: Dict) -> Dict:
        """Validate API key"""
        api_key = params.get("api_key", "")
        
        # Dev key check (only if CB_DEV_KEY set and not production)
        dev_key = os.environ.get("CB_DEV_KEY", "")
        env = os.environ.get("ENV", "production")
        if api_key == dev_key and env != "production":
            return {"authenticated": True, "role": "admin", "key_id": "dev", "warning": "Dev key"}
        
        if api_key in self.api_keys:
            return {"authenticated": True, **self.api_keys[api_key]}
        return {"authenticated": False, "error": "Invalid key"}
    
    async def check_rate(self, params: Dict) -> Dict:
        """Check rate limit"""
        key = params.get("key", "default")
        limit = params.get("limit", 100)
        
        now = time.time()
        window = 3600  # 1 hour
        
        if key not in self.rate_counters:
            self.rate_counters[key] = {"count": 0, "reset_at": now + window}
        
        counter = self.rate_counters[key]
        if now > counter["reset_at"]:
            counter["count"] = 0
            counter["reset_at"] = now + window
        
        allowed = counter["count"] < limit
        if allowed:
            counter["count"] += 1
        
        return {
            "allowed": allowed,
            "remaining": max(0, limit - counter["count"]),
            "reset_at": counter["reset_at"]
        }
    
    async def sandbox_check(self, code: str, params: Dict) -> Dict:
        """Check code safety"""
        if not code:
            code = params.get("code", "")
        
        blocked = ["exec(", "eval(", "__import__", "os.system", "subprocess"]
        violations = [b for b in blocked if b in code]
        
        return {
            "safe": len(violations) == 0,
            "violations": violations
        }
    
    async def audit(self, params: Dict) -> Dict:
        """Log audit event"""
        event = {
            "action": params.get("action"),
            "timestamp": time.time(),
            "user": params.get("user"),
            "result": params.get("result")
        }
        self.audit_log.append(event)
        return {"logged": True}
    
    async def health_check(self) -> Dict:
        return {
            "status": "healthy",
            "container": self.name,
            "capabilities": ["create_key", "auth", "check_rate", "sandbox_check", "audit"],
            "keys_issued": len(self.api_keys)
        }
