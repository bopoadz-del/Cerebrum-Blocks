"""Agent Swarm Block — Multi-agent orchestrator for Cerebrum Blocks.

Lightweight async orchestrator. No heavy frameworks.
- Dependency resolution (topological sort)
- LLM routing: Ollama (local/Orin) ↔ OpenRouter/OpenAI (cloud)
- Vector memory integration
- Standard Cerebrum block contract
"""

import os
import time
import uuid
import asyncio
import json
from typing import Any, Dict, List, Optional
from enum import Enum

from app.core.universal_base import UniversalBlock
from app.core.typed_block import TypedBlock, Schema, ContentType


class LLMProvider(str, Enum):
    OLLAMA = "ollama"
    DEEPSEEK = "deepseek"
    OPENROUTER = "openrouter"


class AgentSwarmBlock(TypedBlock):
    """Universal agent swarm orchestrator."""

    name = "agent_swarm"
    version = "1.0.0"
    description = "Multi-agent task orchestration with dependency resolution and LLM routing"
    layer = 3
    tags = ["agents", "swarm", "orchestration", "ai", "multi-agent"]
    requires = ["vector_search"]

    input_schema = Schema(
        content_type=ContentType.JSON,
        required_fields=[],
        optional_fields=["objective", "project_id", "agents", "tasks", "llm_provider", "verbose", "store_memory"],
        format_hints={}
    )

    output_schema = Schema(
        content_type=ContentType.JSON,
        required_fields=["status", "project_id", "objective", "outputs", "final_output"],
        optional_fields=["total_tokens", "total_time_ms", "swarm_id", "memory_id"],
        format_hints={}
    )

    accepted_input_types = ["JSON", "SwarmRequest"]
    produced_output_types = ["JSON", "SwarmResponse"]

    default_config = {
        "llm_provider": os.getenv("LLM_PROVIDER", "ollama"),
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "ollama_model": os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
        "deepseek_api_key": os.getenv("DEEPSEEK_API_KEY", ""),
        "deepseek_model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY", ""),
        "openrouter_model": os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
        "vector_db_url": os.getenv("VECTOR_DB_URL", "http://localhost:8001"),
        "max_concurrent_agents": int(os.getenv("MAX_CONCURRENT_AGENTS", "5")),
        "default_timeout": int(os.getenv("DEFAULT_TIMEOUT", "120")),
        "store_memory": True,
    }

    ui_schema = {
        "input": {
            "type": "json",
            "placeholder": '{"objective": "Write a FastAPI endpoint", "agents": [...], "tasks": [...]}',
            "multiline": True,
        },
        "output": {
            "type": "json",
            "fields": [
                {"name": "project_id", "type": "text", "label": "Project ID"},
                {"name": "status", "type": "text", "label": "Status"},
                {"name": "final_output", "type": "text", "label": "Final Output"},
                {"name": "outputs", "type": "json", "label": "Agent Outputs"},
                {"name": "total_tokens", "type": "number", "label": "Total Tokens"},
                {"name": "total_time_ms", "type": "number", "label": "Time (ms)"},
            ],
        },
        "quick_actions": [
            {"icon": "🐝", "label": "Run Swarm", "prompt": "Run agent swarm to solve this"},
            {"icon": "📋", "label": "Plan Tasks", "prompt": "Generate a task plan with agents"},
        ],
    }

    async def execute(self, input_data: Any, params: Dict = None) -> Dict:
        params = params or {}
        action = params.get("action") if isinstance(params, dict) else None
        if isinstance(input_data, str):
            if action == "status":
                input_data = {"job_id": input_data}
            else:
                input_data = {"objective": input_data}
        return await super().execute(input_data, params)

    def validate_input(self, data: Any) -> Dict[str, Any]:
        if isinstance(data, dict) and data.get("action") in {"health", "status", "list", "history", "get", "unschedule", "broadcast", "search", "summarize", "structure", "execute_async"}:
            return {"valid": True, "errors": [], "warnings": [], "data": data}
        return super().validate_input(data)

    def __init__(self, hal_block=None, config: Dict = None):
        super().__init__(hal_block, config)
        self.semaphore = asyncio.Semaphore(self.config.get("max_concurrent_agents", 5))
        self.active_swarms: Dict[str, Dict] = {}
        self._job_store: Dict[str, Dict] = {}  # Simple in-memory job store for async

    # ── Public API ─────────────────────────────────────────────────────────────

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Main entry: accepts swarm request dict."""
        params = params or {}
        action = params.get("action", "execute")

        if action == "execute":
            return await self._execute_swarm(input_data, params)
        elif action == "execute_async":
            return await self._execute_swarm_async(input_data, params)
        elif action == "status":
            return self._get_job_status(input_data)
        elif action == "health":
            return await self._health_check()
        else:
            return {"status": "error", "error": f"Unknown action: {action}"}

    # ── Core Execution ─────────────────────────────────────────────────────────

    async def _execute_swarm(self, input_data: Any, params: Dict) -> Dict:
        """Synchronous swarm execution (waits for all tasks)."""
        request = self._normalize_request(input_data)
        project_id = request.get("project_id", "default")
        objective = request.get("objective", "")
        agents = request.get("agents", [])
        tasks = request.get("tasks", [])
        store_memory = request.get("store_memory", self.config.get("store_memory", True))
        llm_provider = request.get("llm_provider", self.config.get("llm_provider", "ollama"))

        if not agents or not tasks:
            # Return a demo/example response so the block works end-to-end
            return {
                "status": "success",
                "mode": "demo",
                "note": "No agents/tasks provided. Below is a demo of swarm output format.",
                "project_id": project_id,
                "objective": objective or "Demo swarm execution",
                "agents_executed": 2,
                "tasks_completed": 3,
                "results": [
                    {"agent": "estimator", "task": "calculate_concrete", "status": "done", "output": "Concrete volume: 125 m³"},
                    {"agent": "scheduler", "task": "check_float", "status": "done", "output": "Total float: 14 days"},
                    {"agent": "qa_engineer", "task": "review_spec", "status": "done", "output": "3 non-compliance items found"},
                ],
                "summary": "Demo swarm completed successfully. Provide agents and tasks for real execution.",
            }

        # Validate agents
        agent_names = {a["name"] for a in agents}
        for task in tasks:
            if task.get("agent") not in agent_names:
                return {
                    "status": "error",
                    "error": f"Task '{task.get('id')}' assigned to unknown agent '{task.get('agent')}'"
                }

        swarm_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        agent_map = {a["name"]: a for a in agents}

        # Topological sort
        task_order = self._resolve_dependencies(tasks)
        completed_tasks: Dict[str, Dict] = {}
        outputs: List[Dict] = []

        try:
            for wave in task_order:
                wave_tasks = [t for t in tasks if t["id"] in wave]
                coros = [
                    self._execute_task(t, agent_map.get(t["agent"]), completed_tasks, llm_provider)
                    for t in wave_tasks
                ]
                results = await asyncio.gather(*coros, return_exceptions=True)

                for task, result in zip(wave_tasks, results):
                    if isinstance(result, Exception):
                        output = {
                            "agent": task["agent"],
                            "task_id": task["id"],
                            "status": "failed",
                            "result": str(result),
                            "tokens_used": 0,
                            "execution_time_ms": 0,
                            "metadata": {"error_type": type(result).__name__},
                        }
                    else:
                        output = result
                        completed_tasks[task["id"]] = output
                    outputs.append(output)

            successful = [o for o in outputs if o["status"] == "completed"]
            final_output = "\n\n---\n\n".join([o["result"] for o in successful])
            total_tokens = sum(o.get("tokens_used", 0) for o in outputs)
            total_time_ms = int((time.time() - start_time) * 1000)
            status = "completed" if all(o["status"] == "completed" for o in outputs) else "partial"

            response = {
                "status": status,
                "project_id": project_id,
                "objective": objective,
                "outputs": outputs,
                "final_output": final_output,
                "total_tokens": total_tokens,
                "total_time_ms": total_time_ms,
                "swarm_id": swarm_id,
            }

            if store_memory:
                memory_id = await self._store_in_vector_db(swarm_id, project_id, objective, outputs, final_output, status)
                response["memory_id"] = memory_id

            return response

        except Exception as e:
            return {"status": "error", "error": str(e), "swarm_id": swarm_id}

    async def _execute_swarm_async(self, input_data: Any, params: Dict) -> Dict:
        """Fire-and-forget: queue swarm and return job ID."""
        job_id = str(uuid.uuid4())[:8]
        self._job_store[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "created_at": time.time(),
            "result": None,
        }

        # Launch in background
        asyncio.create_task(self._run_async_job(job_id, input_data, params))

        return {
            "status": "queued",
            "job_id": job_id,
            "check_url": f"/swarm/status/{job_id}",
        }

    async def _run_async_job(self, job_id: str, input_data: Any, params: Dict):
        self._job_store[job_id]["status"] = "running"
        try:
            result = await self._execute_swarm(input_data, params)
            self._job_store[job_id]["status"] = result.get("status", "completed")
            self._job_store[job_id]["result"] = result
        except Exception as e:
            self._job_store[job_id]["status"] = "failed"
            self._job_store[job_id]["result"] = {"status": "error", "error": str(e)}

    def _get_job_status(self, job_id: str) -> Dict:
        if isinstance(job_id, dict):
            job_id = job_id.get("job_id", "")
        job = self._job_store.get(job_id)
        if not job:
            return {"status": "error", "error": f"Job {job_id} not found"}
        return {
            "status": job["status"],
            "job_id": job_id,
            "result": job.get("result"),
        }

    # ── Task Execution ─────────────────────────────────────────────────────────

    async def _execute_task(
        self,
        task: Dict,
        agent: Optional[Dict],
        completed_tasks: Dict[str, Dict],
        global_provider: str,
    ) -> Dict:
        async with self.semaphore:
            start = time.time()
            task_id = task.get("id", "unknown")
            agent_name = task.get("agent", "unknown")

            if not agent:
                return {
                    "agent": agent_name,
                    "task_id": task_id,
                    "status": "failed",
                    "result": "Agent config not found",
                    "tokens_used": 0,
                    "execution_time_ms": 0,
                    "metadata": {},
                }

            # Build context from dependencies
            context_parts = []
            if task.get("context"):
                context_parts.append(task["context"])
            for dep_id in task.get("dependencies", []):
                if dep_id in completed_tasks:
                    dep = completed_tasks[dep_id]
                    context_parts.append(f"[Task {dep_id} output]:\n{dep['result']}")

            full_context = "\n\n".join(context_parts) if context_parts else ""

            system_prompt = f"""You are {agent.get('name', 'Agent')}, a {agent.get('role', 'custom')} agent.
Backstory: {agent.get('backstory', '')}
Goal: {agent.get('goal', '')}

Your task: {task.get('description', '')}
Expected output: {task.get('expected_output', '')}
{full_context}
"""
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Execute this task and return only the final result.\n\n{task.get('description', '')}"},
            ]

            provider = agent.get("llm_provider") or global_provider
            model = agent.get("model")
            temperature = agent.get("temperature", 0.3)

            try:
                result = await self._llm_chat(
                    messages=messages,
                    provider=provider,
                    model=model,
                    temperature=temperature,
                )
                return {
                    "agent": agent_name,
                    "task_id": task_id,
                    "status": "completed",
                    "result": result["content"],
                    "tokens_used": result.get("tokens", 0),
                    "execution_time_ms": int((time.time() - start) * 1000),
                    "metadata": {
                        "model": result.get("model"),
                        "provider": result.get("provider"),
                    },
                }
            except Exception as e:
                return {
                    "agent": agent_name,
                    "task_id": task_id,
                    "status": "failed",
                    "result": str(e),
                    "tokens_used": 0,
                    "execution_time_ms": int((time.time() - start) * 1000),
                    "metadata": {"error": str(e)},
                }

    # ── Dependency Resolution ──────────────────────────────────────────────────

    def _resolve_dependencies(self, tasks: List[Dict]) -> List[List[str]]:
        """Topological sort — returns waves of task IDs."""
        task_map = {t["id"]: t for t in tasks}
        pending = set(t["id"] for t in tasks)
        waves = []

        while pending:
            ready = [
                tid for tid in pending
                if all(d in task_map and d not in pending for d in task_map[tid].get("dependencies", []))
            ]
            if not ready:
                ready = list(pending)  # Circular — force break
            waves.append(ready)
            for tid in ready:
                pending.remove(tid)

        return waves

    # ── LLM Routing ────────────────────────────────────────────────────────────

    async def _llm_chat(
        self,
        messages: List[Dict],
        provider: str,
        model: Optional[str] = None,
        temperature: float = 0.3,
    ) -> Dict:
        import httpx

        if provider == LLMProvider.OLLAMA:
            return await self._ollama_chat(messages, model, temperature)
        elif provider == "deepseek" or provider == LLMProvider.DEEPSEEK:
            api_key = self.config.get("deepseek_api_key") or os.getenv("DEEPSEEK_API_KEY", "")
            if not api_key:
                raise ValueError("DeepSeek API key not configured")
            model = model or self.config.get("deepseek_model", "deepseek-chat")
            url = "https://api.deepseek.com/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return {
                    "content": data["choices"][0]["message"]["content"],
                    "model": model,
                    "provider": "deepseek",
                    "tokens": data.get("usage", {}).get("total_tokens", 0),
                }

        elif provider == LLMProvider.OPENROUTER:
            return await self._openrouter_chat(messages, model, temperature)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _ollama_chat(self, messages, model, temperature):
        import httpx
        model = model or self.config.get("ollama_model", "llama3.2:3b")
        url = f"{self.config.get('ollama_base_url')}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        async with httpx.AsyncClient(timeout=self.config.get("default_timeout", 120)) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return {
                "content": data["message"]["content"],
                "model": model,
                "provider": "ollama",
                "tokens": data.get("eval_count", 0) + data.get("prompt_eval_count", 0),
            }

    async def _openrouter_chat(self, messages, model, temperature):
        import httpx
        api_key = self.config.get("openrouter_api_key") or os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            raise ValueError("OpenRouter API key not configured")
        model = model or self.config.get("openrouter_model", "anthropic/claude-3.5-sonnet")
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return {
                "content": data["choices"][0]["message"]["content"],
                "model": model,
                "provider": "openrouter",
                "tokens": data.get("usage", {}).get("total_tokens", 0),
            }

    # ── Vector Memory ──────────────────────────────────────────────────────────

    async def _store_in_vector_db(
        self,
        swarm_id: str,
        project_id: str,
        objective: str,
        outputs: List[Dict],
        final_output: str,
        status: str,
    ) -> Optional[str]:
        vector_block = self.get_dep("vector_search")
        collection = "cerebrum_swarm"
        content = f"Objective: {objective}\n\n{final_output}"
        metadata = {
            "swarm_id": swarm_id,
            "project_id": project_id,
            "objective": objective,
            "agents": json.dumps(list({o["agent"] for o in outputs})),
            "tasks": json.dumps([o["task_id"] for o in outputs]),
            "status": status,
        }

        if vector_block:
            try:
                result = await vector_block.process(
                    {"documents": [content], "metadatas": [metadata], "ids": [swarm_id]},
                    {"operation": "add", "collection": collection},
                )
                if result.get("status") == "success":
                    return swarm_id
            except Exception:
                pass

        # Fallback HTTP
        return await self._store_chroma_http(swarm_id, content, metadata, collection)

    async def _store_chroma_http(self, doc_id: str, document: str, metadata: Dict, collection: str) -> Optional[str]:
        import httpx
        db_url = self.config.get("vector_db_url", "")
        if not db_url:
            return None
        try:
            payload = {
                "collection": collection,
                "documents": [document],
                "metadatas": [metadata],
                "ids": [doc_id],
            }
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(f"{db_url}/api/v1/collections/add", json=payload)
                if resp.status_code == 200:
                    return doc_id
        except Exception:
            pass
        return None

    # ─- Health ─────────────────────────────────────────────────────────────────

    async def _health_check(self) -> Dict:
        llm_ready = await self._check_llm_health()
        return {
            "status": "healthy" if llm_ready else "degraded",
            "block_id": self.name,
            "version": self.version,
            "llm_provider": self.config.get("llm_provider", "ollama"),
            "llm_ready": llm_ready,
        }

    async def _check_llm_health(self) -> bool:
        import httpx
        provider = self.config.get("llm_provider", "ollama")
        try:
            if provider == LLMProvider.OLLAMA:
                url = f"{self.config.get('ollama_base_url')}/api/tags"
                async with httpx.AsyncClient(timeout=5) as client:
                    resp = await client.get(url)
                    return resp.status_code == 200
            elif provider == "deepseek" or provider == LLMProvider.DEEPSEEK:
                return bool(self.config.get("deepseek_api_key"))
            elif provider == LLMProvider.OPENROUTER:
                return bool(self.config.get("openrouter_api_key"))
        except Exception:
            return False
        return False

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _normalize_request(self, input_data: Any) -> Dict:
        """Ensure input is a valid swarm request dict."""
        if isinstance(input_data, dict):
            req = input_data
        elif isinstance(input_data, str):
            try:
                req = json.loads(input_data)
            except json.JSONDecodeError:
                req = {"objective": input_data, "agents": [], "tasks": []}
        else:
            req = {"objective": str(input_data), "agents": [], "tasks": []}
        
        # Auto-assign IDs to tasks that don't have them
        for i, task in enumerate(req.get("tasks", [])):
            if isinstance(task, dict) and "id" not in task:
                task["id"] = f"task_{i}"
        
        return req
