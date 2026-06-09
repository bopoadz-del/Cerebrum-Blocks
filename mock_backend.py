"""Minimal mock backend for testing the workflow builder frontend.
Serves /blocks and /chain with dummy data so the React UI can be verified."""

import json
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

app = FastAPI(title="Cerebrum Mock Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REGISTRY_DIR = Path(__file__).parent / "block_registry"


def _load_registry_blocks():
    blocks = []
    if not REGISTRY_DIR.exists():
        return blocks
    for subdir in sorted(REGISTRY_DIR.iterdir()):
        if not subdir.is_dir():
            continue
        manifest = subdir / "block.json"
        if not manifest.exists():
            continue
        try:
            with open(manifest, "r", encoding="utf-8") as f:
                m = json.load(f)
            blocks.append({
                "name": m["id"],
                "version": m.get("version", "1.0"),
                "description": m.get("description", ""),
                "layer": m.get("layer", 3),
                "tags": m.get("tags", []),
                "requires": m.get("requires", []),
                "ui_schema": m.get("ui_schema", {}),
                "source": "registry",
            })
        except Exception:
            continue
    return blocks


MOCK_BLOCKS = _load_registry_blocks()


class ChainStep(BaseModel):
    block: str
    params: Dict[str, Any] = {}
    label: Optional[str] = None
    input_mapping: Optional[Dict[str, str]] = None


class ChainRequest(BaseModel):
    steps: List[ChainStep]
    initial_input: Any = None
    fail_fast: bool = True
    continue_on_error: bool = False


@app.get("/health")
def health():
    return {"status": "healthy", "blocks_loaded": len(MOCK_BLOCKS)}


@app.get("/blocks")
def list_blocks():
    return {"blocks": MOCK_BLOCKS, "total": len(MOCK_BLOCKS), "categories": {}}


@app.post("/chain")
def chain_execute(req: ChainRequest):
    results = []
    current_output = req.initial_input or {}
    for i, step in enumerate(req.steps):
        # Mock execution: echo params back as output
        current_output = {
            "step": i,
            "block": step.block,
            "params": step.params,
            "result": f"Mock output from {step.block}",
            "success": True,
            "status": "success",
        }
        results.append(current_output)

    return {
        "success": True,
        "status": "success",
        "steps_executed": len(req.steps),
        "final_output": current_output,
        "results": results,
        "validation_passed": True,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
