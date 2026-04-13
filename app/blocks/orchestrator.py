"""Orchestrator Block - The Chain Master"""

from typing import Any, Dict, List, Optional
from app.core.universal_base import UniversalBlock


class OrchestratorBlock(UniversalBlock):
    """Execute chains of blocks with automatic context passing and memory persistence."""

    name = "orchestrator"
    version = "1.0.0"
    description = "Chain execution engine for block sequences"
    layer = 2
    tags = ["ai", "core", "orchestrator", "chain"]
    requires = ["memory", "traffic_manager"]

    default_config = {
        "max_steps": 50,
        "persist_steps": True
    }

    ui_schema = {
        "input": {
            "type": "json",
            "accept": None,
            "placeholder": '{"steps": [{"block": "chat", "params": {}}]}',
            "multiline": True
        },
        "output": {
            "type": "json",
            "fields": [
                {"name": "steps_executed", "type": "number", "label": "Steps"},
                {"name": "final_output", "type": "json", "label": "Output"}
            ]
        }
    }

    def __init__(self, hal_block=None, config=None):
        super().__init__(hal_block, config)
        self._registry = {}
        self._instance_cache = {}
        self._create_block_fn = None
        self._memory_fn = None

    def set_platform(self, registry, instance_cache, create_block_fn, memory_fn=None):
        """Wire platform services from main.py"""
        self._registry = registry
        self._instance_cache = instance_cache
        self._create_block_fn = create_block_fn
        self._memory_fn = memory_fn

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        params = params or {}
        steps = params.get("steps", [])
        if not steps and isinstance(input_data, dict):
            steps = input_data.get("steps", [])

        if not steps:
            return {"status": "error", "error": "No steps provided for chain execution"}

        max_steps = params.get("max_steps", self.config.get("max_steps", 50))
        if len(steps) > max_steps:
            return {"status": "error", "error": f"Chain exceeds max_steps ({max_steps})"}

        context = input_data
        results = []

        for i, step in enumerate(steps):
            block_name = step.get("block")
            step_params = step.get("params", {})

            if not block_name:
                return {"status": "error", "error": f"Step {i}: missing block name", "partial_results": results}

            # Check traffic manager if wired
            traffic = self.get_dep("traffic_manager")
            if traffic:
                route_result = await traffic.process(
                    {"source": self.name, "target": block_name, "payload": context},
                    {"operation": "route"}
                )
                if isinstance(route_result, dict) and route_result.get("status") == "queued":
                    return {
                        "status": "queued",
                        "step": i,
                        "block": block_name,
                        "job_id": route_result.get("job_id"),
                        "partial_results": results
                    }
                if isinstance(route_result, dict) and route_result.get("error"):
                    return {
                        "status": "error",
                        "step": i,
                        "block": block_name,
                        "error": route_result["error"],
                        "partial_results": results
                    }

            # Resolve block instance
            block = await self._resolve_block(block_name)
            if not block:
                return {
                    "status": "error",
                    "error": f"Step {i}: Block '{block_name}' not found",
                    "available": list(self._registry.keys()) if self._registry else [],
                    "partial_results": results
                }

            # Skip containers
            if hasattr(block, "name") and block.name.startswith("container_"):
                return {
                    "status": "error",
                    "error": f"Step {i}: Container '{block_name}' cannot be executed in a chain",
                    "partial_results": results
                }
            if block_name.startswith("container_"):
                return {
                    "status": "error",
                    "error": f"Step {i}: Container '{block_name}' cannot be executed in a chain",
                    "partial_results": results
                }

            # Execute block
            result = await block.execute(context, step_params)

            results.append({
                "step": i,
                "block": block_name,
                "success": result.get("status") != "error",
                "result": result
            })

            # Pass output to next step
            context = result.get("result", result)

            # Persist to memory
            if self.config.get("persist_steps", True):
                await self._persist_step(i, block_name, context)

            # Stop on error unless continue_on_error is set
            if result.get("status") == "error" and not params.get("continue_on_error"):
                break

        return {
            "status": "success",
            "steps_executed": len(results),
            "final_output": context,
            "results": results
        }

    async def _resolve_block(self, block_name: str):
        """Get or create block instance."""
        if block_name in self._instance_cache:
            return self._instance_cache[block_name]
        if block_name in self._registry and self._create_block_fn:
            instance = self._create_block_fn(self._registry[block_name])
            self._instance_cache[block_name] = instance
            return instance
        return None

    async def _persist_step(self, step_index: int, block_name: str, context: Any):
        """Persist chain step to memory."""
        memory = self.get_dep("memory")
        if memory:
            try:
                await memory.execute({
                    "action": "set",
                    "key": f"chain:{step_index}:{block_name}",
                    "value": context,
                    "ttl": 3600
                })
            except Exception:
                pass
        elif self._memory_fn:
            try:
                mem = self._memory_fn()
                await mem.execute({
                    "action": "set",
                    "key": f"chain:{step_index}:{block_name}",
                    "value": context,
                    "ttl": 3600
                })
            except Exception:
                pass
