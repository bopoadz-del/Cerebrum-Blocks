"""Graph Orchestrator Block — universal directed-graph execution engine.

Executes a declarative graph of nodes (block calls or pure transforms) with
conditional edges. Keeps no domain logic: nodes delegate to other blocks or to
built-in transforms. Inspired by LangGraph-style orchestrators, but neutral and
block-store friendly.
"""

from __future__ import annotations

import copy
import time
import uuid
from typing import Any, Dict, List, Optional

from app.core.universal_base import UniversalBlock


class GraphOrchestratorBlock(UniversalBlock):
    """Run a directed graph of block calls with shared mutable state."""

    name = "graph_orchestrator"
    version = "1.0.0"
    updated_at = "2026-07-19"
    description = (
        "Universal directed-graph orchestrator: declare nodes, edges, and "
        "conditions; execute block chains with auditable trace."
    )
    layer = 2
    tags = ["orchestrator", "workflow", "graph", "core"]
    requires = []

    default_config = {
        "max_steps": 100,
        "timeout_seconds": 300,
    }

    ui_schema = {
        "input": {
            "type": "json",
            "placeholder": '{"graph": {"nodes": {...}, "edges": [...], "entry": "start"}, "state": {}}',
            "multiline": True,
        },
        "output": {"type": "json", "fields": [{"name": "result", "type": "json"}]},
        "params": [
            {
                "name": "action",
                "type": "select",
                "label": "Action",
                "options": ["execute", "validate"],
                "default": "execute",
            }
        ],
        "quick_actions": [],
    }

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        params = params or {}
        data = input_data if isinstance(input_data, dict) else {}
        action = params.get("action") or data.get("action", "execute")

        if action == "execute":
            return await self._execute_graph(data)
        if action == "validate":
            return self._validate_graph(data.get("graph"))
        return {"status": "error", "error": f"Unknown action: {action}"}

    def _validate_graph(self, graph: Optional[Dict]) -> Dict:
        if not isinstance(graph, dict):
            return {"status": "error", "error": "graph must be a dict"}
        nodes = graph.get("nodes", {})
        edges = graph.get("edges", [])
        entry = graph.get("entry")
        errors = []
        if not nodes:
            errors.append("graph has no nodes")
        if entry and entry not in nodes:
            errors.append(f"entry node '{entry}' not in nodes")
        for edge in edges:
            src = edge.get("from")
            dst = edge.get("to")
            if src not in nodes:
                errors.append(f"edge references unknown source node '{src}'")
            if dst not in nodes:
                errors.append(f"edge references unknown target node '{dst}'")
        if errors:
            return {"status": "error", "error": "; ".join(errors)}
        return {"status": "success", "valid": True, "node_count": len(nodes), "edge_count": len(edges)}

    async def _execute_graph(self, data: Dict) -> Dict:
        graph = data.get("graph")
        validation = self._validate_graph(graph)
        if validation.get("status") == "error":
            return validation

        state = copy.deepcopy(data.get("state", {}))
        nodes = graph["nodes"]
        edges = graph["edges"]
        entry = graph.get("entry")
        if not entry:
            return {"status": "error", "error": "graph.entry is required"}

        trace: List[Dict] = []
        visited: set = set()
        current = entry
        steps = 0
        max_steps = self.config.get("max_steps", 100)

        while current and steps < max_steps:
            if current in visited:
                return {"status": "error", "error": f"cycle detected at node '{current}'"}
            visited.add(current)

            node_def = nodes.get(current, {})
            started_at = time.time()
            try:
                state = await self._run_node(current, node_def, state)
                trace.append({
                    "node": current,
                    "status": "success",
                    "duration_ms": round((time.time() - started_at) * 1000, 2),
                })
            except Exception as exc:  # noqa: BLE001
                trace.append({
                    "node": current,
                    "status": "error",
                    "error": str(exc),
                    "duration_ms": round((time.time() - started_at) * 1000, 2),
                })
                return {
                    "status": "error",
                    "error": f"node '{current}' failed: {exc}",
                    "state": state,
                    "trace": trace,
                }

            # Determine next node(s)
            next_nodes = self._pick_next(current, edges, state)
            if not next_nodes:
                break
            if len(next_nodes) > 1:
                # Fan-out: run branches in parallel and merge state
                branches = []
                for n in next_nodes:
                    branch_state = copy.deepcopy(state)
                    branch_result = await self._execute_subgraph(n, nodes, edges, branch_state, visited)
                    branches.append(branch_result)
                # Merge successful branch states (last-write-wins for shared keys)
                for branch in branches:
                    if branch.get("status") == "success":
                        state.update(branch.get("state", {}))
                        trace.extend(branch.get("trace", []))
                return {"status": "success", "state": state, "trace": trace}

            current = next_nodes[0]
            steps += 1

        if steps >= max_steps:
            return {"status": "error", "error": "max_steps exceeded", "state": state, "trace": trace}

        return {"status": "success", "state": state, "trace": trace}

    async def _execute_subgraph(
        self,
        entry: str,
        nodes: Dict,
        edges: List[Dict],
        state: Dict,
        visited: set,
    ) -> Dict:
        """Run a subgraph from entry until leaf; used for parallel fan-out."""
        trace: List[Dict] = []
        current = entry
        steps = 0
        max_steps = self.config.get("max_steps", 100)
        while current and steps < max_steps:
            if current in visited:
                break
            visited.add(current)
            node_def = nodes.get(current, {})
            try:
                state = await self._run_node(current, node_def, state)
                trace.append({"node": current, "status": "success"})
            except Exception as exc:  # noqa: BLE001
                trace.append({"node": current, "status": "error", "error": str(exc)})
                return {"status": "error", "error": str(exc), "state": state, "trace": trace}
            next_nodes = self._pick_next(current, edges, state)
            if not next_nodes:
                break
            current = next_nodes[0]
            steps += 1
        return {"status": "success", "state": state, "trace": trace}

    async def _run_node(self, node_name: str, node_def: Dict, state: Dict) -> Dict:
        block_name = node_def.get("block", "_identity")
        node_config = node_def.get("config", {})

        if block_name == "_identity":
            return self._apply_identity_transform(state, node_config)

        # Delegate to another block via the block registry
        from app.blocks import BLOCK_REGISTRY

        if block_name not in BLOCK_REGISTRY:
            raise ValueError(f"block '{block_name}' not found in registry")
        block_class = BLOCK_REGISTRY[block_name]
        block = block_class()
        input_data = node_def.get("input") or state
        params = node_def.get("params") or {}
        result = await block.process(input_data, params)
        if isinstance(result, dict):
            # Merge result into state; namespace under block name if requested
            if node_config.get("merge_into_state", True):
                state = copy.deepcopy(state)
                if node_config.get("output_key"):
                    state[node_config["output_key"]] = result
                else:
                    state.update(result)
        return state

    def _apply_identity_transform(self, state: Dict, config: Dict) -> Dict:
        state = copy.deepcopy(state)
        if "add" in config and isinstance(state.get("value"), (int, float)):
            state["value"] += config["add"]
        if "set_flag" in config:
            state["flag"] = config["set_flag"]
        if "set" in config:
            for key, value in config["set"].items():
                state[key] = value
        return state

    def _pick_next(self, current: str, edges: List[Dict], state: Dict) -> List[str]:
        matches = []
        for edge in edges:
            if edge.get("from") != current:
                continue
            condition = edge.get("condition")
            if condition is None or self._evaluate_condition(condition, state):
                matches.append(edge["to"])
        return matches

    def _evaluate_condition(self, condition: str, state: Dict) -> bool:
        if condition == "state.flag":
            return bool(state.get("flag"))
        if condition == "not state.flag":
            return not bool(state.get("flag"))
        if condition.startswith("state."):
            key = condition.split("state.", 1)[1]
            return bool(state.get(key))
        return bool(condition)
