"""Tenant Block - Project/tenant isolation for multi-tenant deployments.

Provides universal tenant and project management. Storage backend defaults to
an in-memory block for local/dev use; a database block can be wired for
persistence.
"""

import time
import uuid
from typing import Any, Dict, List, Optional

from app.core.universal_base import UniversalBlock


class TenantBlock(UniversalBlock):
    """Tenant and project provisioning with header-based context resolution."""

    name = "tenant"
    version = "1.0.0"
    updated_at = "2026-07-19"
    description = (
        "Provision tenants, projects, and users; resolve request context from "
        "headers for multi-tenant isolation."
    )
    layer = 1  # Security layer
    tags = ["security", "tenant", "multi-tenant", "core"]
    requires = ["memory"]

    default_config = {
        "tenant_key_prefix": "tenant:tenants",
        "project_key_prefix": "tenant:projects",
        "user_key_prefix": "tenant:users",
    }

    ui_schema = {
        "input": {
            "type": "json",
            "accept": None,
            "placeholder": '{"action": "create_tenant", "name": "Acme"}',
            "multiline": False,
        },
        "output": {"type": "json", "fields": [{"name": "result", "type": "json"}]},
        "params": [
            {
                "name": "action",
                "type": "select",
                "label": "Action",
                "options": [
                    "create_tenant",
                    "get_tenant",
                    "list_tenants",
                    "create_project",
                    "get_project",
                    "list_projects",
                    "resolve_context",
                ],
                "default": "create_tenant",
            }
        ],
        "quick_actions": [],
    }

    def __init__(self, hal_block=None, config: Dict = None):
        super().__init__(hal_block, config)
        self.memory_block = None  # Wired by assembler or tests
        self.database_block = None  # Optional persistence backend

    async def _legacy_initialize(self) -> bool:
        """Initialize tenant storage."""
        return True

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Route to tenant action."""
        data = input_data if isinstance(input_data, dict) else {}
        params = params or {}
        action = params.get("action") or data.get("action")

        handlers = {
            "create_tenant": self._create_tenant,
            "get_tenant": self._get_tenant,
            "list_tenants": self._list_tenants,
            "create_project": self._create_project,
            "get_project": self._get_project,
            "list_projects": self._list_projects,
            "resolve_context": self._resolve_context,
        }

        handler = handlers.get(action)
        if not handler:
            return {"status": "error", "error": f"Unknown action: {action}"}
        return await handler(data, params)

    def _generate_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:12]}"

    async def _store(self, key: str, value: Dict) -> None:
        if self.memory_block:
            await self.memory_block.process(
                {"action": "set", "key": key, "value": value, "ttl": 0}
            )

    async def _fetch(self, key: str) -> Optional[Dict]:
        if not self.memory_block:
            return None
        result = await self.memory_block.process({"action": "get", "key": key})
        if result.get("hit"):
            return result.get("value")
        return None

    async def _keys(self, prefix: str) -> List[str]:
        if not self.memory_block:
            return []
        result = await self.memory_block.process({"action": "keys"})
        return [k for k in result.get("keys", []) if k.startswith(prefix)]

    async def _create_tenant(self, data: Dict, params: Dict) -> Dict:
        name = data.get("name") or params.get("name")
        if not name:
            return {"status": "error", "error": "name is required"}

        tenant_id = self._generate_id("tnt")
        tenant = {
            "tenant_id": tenant_id,
            "name": name,
            "created_at": time.time(),
            "metadata": data.get("metadata", {}),
        }
        prefix = self.config.get("tenant_key_prefix", "tenant:tenants")
        await self._store(f"{prefix}:{tenant_id}", tenant)
        return {"status": "success", "tenant": tenant}

    async def _get_tenant(self, data: Dict, params: Dict) -> Dict:
        tenant_id = data.get("tenant_id") or params.get("tenant_id")
        if not tenant_id:
            return {"status": "error", "error": "tenant_id is required"}

        prefix = self.config.get("tenant_key_prefix", "tenant:tenants")
        tenant = await self._fetch(f"{prefix}:{tenant_id}")
        if not tenant:
            return {"status": "error", "error": "tenant not found"}
        return {"status": "success", "tenant": tenant}

    async def _list_tenants(self, data: Dict, params: Dict) -> Dict:
        prefix = self.config.get("tenant_key_prefix", "tenant:tenants")
        keys = await self._keys(f"{prefix}:")
        tenants = []
        for key in keys:
            value = await self._fetch(key)
            if value:
                tenants.append(value)
        return {"status": "success", "tenants": tenants}

    async def _create_project(self, data: Dict, params: Dict) -> Dict:
        tenant_id = data.get("tenant_id") or params.get("tenant_id")
        name = data.get("name") or params.get("name")
        if not tenant_id or not name:
            return {"status": "error", "error": "tenant_id and name are required"}

        # Verify tenant exists
        tenant_prefix = self.config.get("tenant_key_prefix", "tenant:tenants")
        tenant = await self._fetch(f"{tenant_prefix}:{tenant_id}")
        if not tenant:
            return {"status": "error", "error": "tenant not found"}

        project_id = self._generate_id("prj")
        project = {
            "project_id": project_id,
            "tenant_id": tenant_id,
            "name": name,
            "created_at": time.time(),
            "metadata": data.get("metadata", {}),
        }
        prefix = self.config.get("project_key_prefix", "tenant:projects")
        await self._store(f"{prefix}:{project_id}", project)
        return {"status": "success", "project": project}

    async def _get_project(self, data: Dict, params: Dict) -> Dict:
        project_id = data.get("project_id") or params.get("project_id")
        if not project_id:
            return {"status": "error", "error": "project_id is required"}

        prefix = self.config.get("project_key_prefix", "tenant:projects")
        project = await self._fetch(f"{prefix}:{project_id}")
        if not project:
            return {"status": "error", "error": "project not found"}
        return {"status": "success", "project": project}

    async def _list_projects(self, data: Dict, params: Dict) -> Dict:
        tenant_id = data.get("tenant_id") or params.get("tenant_id")
        prefix = self.config.get("project_key_prefix", "tenant:projects")
        keys = await self._keys(f"{prefix}:")
        projects = []
        for key in keys:
            value = await self._fetch(key)
            if value and (not tenant_id or value.get("tenant_id") == tenant_id):
                projects.append(value)
        return {"status": "success", "projects": projects}

    async def _resolve_context(self, data: Dict, params: Dict) -> Dict:
        headers = data.get("headers") or params.get("headers") or {}
        tenant_id = headers.get("X-Tenant-Id") or headers.get("x-tenant-id")
        project_id = headers.get("X-Project-Id") or headers.get("x-project-id")
        user_id = headers.get("X-User-Id") or headers.get("x-user-id")

        # Validate ids if provided
        tenant_prefix = self.config.get("tenant_key_prefix", "tenant:tenants")
        project_prefix = self.config.get("project_key_prefix", "tenant:projects")

        if tenant_id and not await self._fetch(f"{tenant_prefix}:{tenant_id}"):
            return {"status": "error", "error": "tenant not found"}

        if project_id:
            project = await self._fetch(f"{project_prefix}:{project_id}")
            if not project:
                return {"status": "error", "error": "project not found"}
            if tenant_id and project.get("tenant_id") != tenant_id:
                return {
                    "status": "error",
                    "error": "project does not belong to tenant",
                }

        return {
            "status": "success",
            "context": {
                "tenant_id": tenant_id,
                "project_id": project_id,
                "user_id": user_id,
            },
        }
