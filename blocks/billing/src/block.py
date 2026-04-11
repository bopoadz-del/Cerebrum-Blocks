from blocks.base import LegoBlock
from typing import Dict, Any
from datetime import datetime

class BillingBlock(LegoBlock):
    """Stripe Billing - Usage metering, subscriptions"""
    name = "billing"
    version = "1.0.0"
    requires = ["config", "auth", "memory"]
    
    PLANS = {
        "free": {"price": 0, "requests": 1000, "blocks": ["chat", "vector"]},
        "pro": {"price": 2900, "requests": 50000, "blocks": ["*"]},
        "enterprise": {"price": None, "requests": float('inf'), "blocks": ["*"], "custom": True}
    }
    
    def __init__(self, hal_block, config: Dict[str, Any]):
        super().__init__(hal_block, config)
        self.stripe_key = config.get("stripe_secret_key")
        self.stripe = None
        if self.stripe_key:
            try:
                import stripe
                self.stripe = stripe.StripeClient(self.stripe_key)
            except ImportError:
                pass
        self.auth_block = None
        self.memory_block = None
        
    async def execute(self, input_data: Dict) -> Dict:
        action = input_data.get("action")
        if action == "record_usage":
            return await self._record_usage(input_data)
        elif action == "check_quota":
            return await self._check_quota(input_data)
        elif action == "create_subscription":
            return await self._create_subscription(input_data)
        elif action == "get_invoice":
            return await self._get_invoice(input_data)
        elif action == "upgrade":
            return await self._upgrade_plan(input_data)
        return {"error": "Unknown action"}
    
    async def _record_usage(self, data: Dict) -> Dict:
        api_key = data.get("api_key")
        block_used = data.get("block")
        tokens = data.get("tokens", 0)
        cost_cents = self._calculate_cost(block_used, tokens)
        
        if self.memory_block:
            today = datetime.now().strftime("%Y-%m-%d")
            key = f"billing:usage:{api_key}:{today}"
            
            current = await self.memory_block.execute({
                "action": "get",
                "key": key
            })
            
            usage = current.get("value", {"requests": 0, "cost": 0}) if current.get("hit") else {"requests": 0, "cost": 0}
            usage["requests"] += 1
            usage["cost"] += cost_cents
            
            await self.memory_block.execute({
                "action": "set",
                "key": key,
                "value": usage,
                "ttl": 86400 * 35
            })
        
        return {"recorded": True, "cost_cents": cost_cents}
    
    async def _check_quota(self, data: Dict) -> Dict:
        api_key = data.get("api_key")
        plan = "free"
        
        if self.auth_block:
            user = await self.auth_block.execute({
                "action": "validate",
                "api_key": api_key
            })
            plan = user.get("role", "free")
        
        plan_config = self.PLANS.get(plan, self.PLANS["free"])
        limit = plan_config["requests"]
        
        today = datetime.now().strftime("%Y-%m-%d")
        used = 0
        if self.memory_block:
            usage_data = await self.memory_block.execute({
                "action": "get",
                "key": f"billing:usage:{api_key}:{today}"
            })
            used = usage_data.get("value", {}).get("requests", 0) if usage_data.get("hit") else 0
        
        remaining = max(0, limit - used)
        percent_used = (used / limit * 100) if limit > 0 else 0
        
        return {
            "plan": plan,
            "limit": limit,
            "used": used,
            "remaining": remaining,
            "percent_used": round(percent_used, 2),
            "exceeded": remaining == 0
        }
    
    async def _create_subscription(self, data: Dict) -> Dict:
        if not self.stripe:
            return {"error": "Stripe not configured"}
        return {"subscription_id": "mock_sub", "status": "active"}
    
    async def _get_invoice(self, data: Dict) -> Dict:
        return {"invoices": []}
    
    async def _upgrade_plan(self, data: Dict) -> Dict:
        return {"upgraded": True, "plan": data.get("plan")}
    
    def _calculate_cost(self, block: str, tokens: int) -> int:
        rates = {"chat": 0.002, "image": 2.0, "vector": 0.001, "default": 0.001}
        rate = rates.get(block, rates["default"])
        return int(tokens * rate)
    
    def health(self) -> Dict:
        h = super().health()
        h["stripe_connected"] = self.stripe is not None
        h["plans"] = list(self.PLANS.keys())
        return h
