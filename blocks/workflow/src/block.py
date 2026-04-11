from blocks.base import LegoBlock
from typing import Dict, Any, List
import time

class WorkflowBlock(LegoBlock):
    """Workflow Automation - n8n/Temporal style chains"""
    name = "workflow"
    version = "1.0.0"
    requires = ["config", "queue"]
    
    def __init__(self, hal_block, config: Dict[str, Any]):
        super().__init__(hal_block, config)
        self.workflows = {}
        self.executions = {}
        self.queue_block = None
        
    async def execute(self, input_data: Dict) -> Dict:
        action = input_data.get("action")
        if action == "create":
            return await self._create_workflow(input_data)
        elif action == "trigger":
            return await self._trigger_workflow(input_data)
        elif action == "get_status":
            return await self._get_execution_status(input_data)
        elif action == "list":
            return await self._list_workflows()
        return {"error": "Unknown action"}
    
    async def _create_workflow(self, data: Dict) -> Dict:
        workflow_id = data.get("workflow_id") or f"wf_{int(time.time())}"
        steps = data.get("steps", [])
        
        self.workflows[workflow_id] = {
            "id": workflow_id,
            "name": data.get("name", "Untitled"),
            "steps": steps,
            "created": time.time(),
            "trigger": data.get("trigger", "manual")
        }
        
        return {
            "workflow_id": workflow_id,
            "steps": len(steps),
            "created": True
        }
    
    async def _trigger_workflow(self, data: Dict) -> Dict:
        workflow_id = data.get("workflow_id")
        payload = data.get("payload", {})
        
        if workflow_id not in self.workflows:
            return {"error": "Workflow not found"}
        
        workflow = self.workflows[workflow_id]
        execution_id = f"exec_{workflow_id}_{int(time.time())}"
        
        if self.queue_block:
            await self.queue_block.execute({
                "action": "enqueue",
                "job_type": "workflow",
                "payload": {
                    "execution_id": execution_id,
                    "workflow": workflow,
                    "input": payload
                }
            })
        
        self.executions[execution_id] = {
            "status": "queued",
            "workflow_id": workflow_id,
            "started": time.time()
        }
        
        return {
            "execution_id": execution_id,
            "status": "queued",
            "workflow_id": workflow_id
        }
    
    async def _get_execution_status(self, data: Dict) -> Dict:
        execution_id = data.get("execution_id")
        return self.executions.get(execution_id, {"error": "Execution not found"})
    
    async def _list_workflows(self) -> Dict:
        return {
            "workflows": [
                {"id": w["id"], "name": w["name"], "steps": len(w["steps"])}
                for w in self.workflows.values()
            ],
            "count": len(self.workflows)
        }
    
    def health(self) -> Dict:
        h = super().health()
        h["workflows"] = len(self.workflows)
        h["executions"] = len(self.executions)
        return h
