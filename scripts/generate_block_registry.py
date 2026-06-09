#!/usr/bin/env python3
"""
Automatically generate block_registry entries for existing Cerebrum platform blocks.

Scans app/blocks/ via BLOCK_REGISTRY, extracts metadata, and generates:
  - block_registry/<name>/block.json
  - block_registry/<name>/block.py   (thin adapter)
  - block_registry/<name>/Dockerfile

Run from repository root:
    python scripts/generate_block_registry.py
"""

import os
import sys
import json
import inspect
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.blocks import BLOCK_REGISTRY, get_all_blocks
from app.core.universal_base import UniversalBlock, UniversalContainer


REGISTRY_ROOT = Path("block_registry")
POC_BLOCKS = [
    "chat", "pdf", "ocr", "construction", "web",
    "search", "image", "code", "memory", "auth",
]


def _type_from_ui(ui_type: str) -> str:
    mapping = {
        "text": "string",
        "file": "file",
        "url": "string",
        "json": "json",
        "audio": "file",
        "image": "file",
        "pdf": "file",
        "number": "number",
        "boolean": "boolean",
    }
    return mapping.get(ui_type, "string")


def _widget_from_ui(ui_type: str) -> str:
    mapping = {
        "text": "text",
        "file": "file",
        "url": "text",
        "json": "json",
        "audio": "file",
        "image": "file",
        "pdf": "file",
        "number": "number",
    }
    return mapping.get(ui_type, "text")


def extract_inputs(block_class) -> List[Dict[str, Any]]:
    """Derive inputs from ui_schema and default_config."""
    inputs = []
    ui_schema = getattr(block_class, "ui_schema", {}) or {}
    default_config = getattr(block_class, "default_config", {}) or {}

    # Primary input from ui_schema.input
    ui_input = ui_schema.get("input", {})
    if ui_input:
        input_type = _type_from_ui(ui_input.get("type", "text"))
        inputs.append({
            "name": "input",
            "type": input_type,
            "required": False,
            "description": ui_input.get("placeholder", "Block input"),
        })

    # Params from default_config become configurable inputs
    for key, value in default_config.items():
        param_type = "string"
        if isinstance(value, bool):
            param_type = "boolean"
        elif isinstance(value, int):
            param_type = "number"
        elif isinstance(value, float):
            param_type = "number"
        elif isinstance(value, dict):
            param_type = "json"
        elif isinstance(value, list):
            param_type = "array"

        inputs.append({
            "name": key,
            "type": param_type,
            "required": False,
            "default": value,
            "description": f"Configuration parameter: {key}",
        })

    return inputs


def extract_outputs(block_class) -> List[Dict[str, Any]]:
    """Derive outputs from ui_schema.output.fields."""
    outputs = []
    ui_schema = getattr(block_class, "ui_schema", {}) or {}
    ui_output = ui_schema.get("output", {})
    fields = ui_output.get("fields", [])

    if fields:
        for field in fields:
            outputs.append({
                "name": field.get("name", "result"),
                "type": field.get("type", "json"),
                "description": field.get("label", ""),
            })
    else:
        outputs.append({"name": "result", "type": "json"})

    return outputs


def extract_ui_schema(block_class) -> List[Dict[str, Any]]:
    """Derive ui_schema widgets from inputs."""
    widgets = []
    ui_schema = getattr(block_class, "ui_schema", {}) or {}
    ui_input = ui_schema.get("input", {})
    default_config = getattr(block_class, "default_config", {}) or {}

    # Main input widget
    if ui_input:
        widgets.append({
            "name": "input",
            "widget": _widget_from_ui(ui_input.get("type", "text")),
            "label": ui_input.get("placeholder", "Input"),
        })

    # Config param widgets
    for key, value in default_config.items():
        widget = "text"
        if isinstance(value, bool):
            widget = "toggle"
        elif isinstance(value, int):
            widget = "number"
        elif isinstance(value, float):
            widget = "number"
        elif isinstance(value, dict):
            widget = "json"
        elif isinstance(value, list):
            widget = "json"

        widgets.append({
            "name": key,
            "widget": widget,
            "label": key.replace("_", " ").title(),
        })

    return widgets


def generate_block_json(block_name: str, block_class) -> Optional[Dict[str, Any]]:
    """Generate block.json manifest from block class metadata."""
    if issubclass(block_class, UniversalContainer):
        return None  # Skip containers

    name = getattr(block_class, "name", block_name)
    version = getattr(block_class, "version", "1.0.0")
    description = getattr(block_class, "description", f"{name} block")
    author = getattr(block_class, "author", "Cerebrum Team")
    tags = getattr(block_class, "tags", [])

    inputs = extract_inputs(block_class)
    outputs = extract_outputs(block_class)
    ui_schema = extract_ui_schema(block_class)

    manifest = {
        "id": name,
        "name": name.replace("_", " ").title(),
        "version": version,
        "author": author,
        "description": description,
        "inputs": inputs,
        "outputs": outputs,
        "execution": {
            "type": "docker",
            "image": f"ghcr.io/cerebrum-blocks/{name}:latest",
        },
        "ui_schema": ui_schema,
        "tags": tags,
    }

    return manifest


def generate_block_adapter(block_name: str, block_class) -> str:
    """Generate block.py adapter that wraps UniversalBlock.process() into run()."""
    cls_name = block_class.__name__
    module_path = block_class.__module__

    code = f'''#!/usr/bin/env python3
"""
Auto-generated adapter for Cerebrum block: {block_name}
Wraps {module_path}.{cls_name}.process() into a synchronous run() function.
"""

import sys
import asyncio

sys.path.insert(0, "/app")

from app.blocks import BLOCK_REGISTRY


def run(**kwargs):
    """
    Execute the {block_name} block.
    Accepts keyword args matching the block's inputs/params.
    Returns the block's raw result dict.
    """
    block_cls = BLOCK_REGISTRY["{block_name}"]
    instance = block_cls()

    # Separate input from params
    input_data = kwargs.get("input", kwargs)
    params = {{k: v for k, v in kwargs.items() if k != "input"}}

    # process() is async — run it in a new event loop
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None:
        # Already inside an async context (e.g. FastAPI) — schedule it
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, instance.process(input_data, params))
            return future.result()
    else:
        return asyncio.run(instance.process(input_data, params))
'''
    return code


def generate_dockerfile(block_name: str) -> str:
    """Generate per-block Dockerfile."""
    return f'''FROM cerebrum-block-base:latest

WORKDIR /app
COPY block.json block.py ./
ENTRYPOINT ["python", "run.py"]
'''


def generate_block(block_name: str, force: bool = False) -> bool:
    """Generate all files for a single block. Returns True if successful."""
    try:
        block_class = BLOCK_REGISTRY[block_name]
    except Exception as e:
        print(f"  [!] SKIP {block_name}: import failed ({e})")
        return False

    if issubclass(block_class, UniversalContainer):
        print(f"  [C] SKIP {block_name}: container block")
        return False

    block_dir = REGISTRY_ROOT / block_name
    block_dir.mkdir(parents=True, exist_ok=True)

    # block.json
    manifest = generate_block_json(block_name, block_class)
    if manifest is None:
        return False

    json_path = block_dir / "block.json"
    if not json_path.exists() or force:
        with open(json_path, "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"  [OK] {block_name}/block.json")
    else:
        print(f"  [SKIP] {block_name}/block.json (exists)")

    # block.py adapter
    adapter_path = block_dir / "block.py"
    if not adapter_path.exists() or force:
        with open(adapter_path, "w") as f:
            f.write(generate_block_adapter(block_name, block_class))
        print(f"  [OK] {block_name}/block.py")
    else:
        print(f"  [SKIP] {block_name}/block.py (exists)")

    # Dockerfile
    dockerfile_path = block_dir / "Dockerfile"
    if not dockerfile_path.exists() or force:
        with open(dockerfile_path, "w") as f:
            f.write(generate_dockerfile(block_name))
        print(f"  [OK] {block_name}/Dockerfile")
    else:
        print(f"  [SKIP] {block_name}/Dockerfile (exists)")

    return True


def main():
    REGISTRY_ROOT.mkdir(exist_ok=True)

    print("=" * 60)
    print("Cerebrum Block Registry Generator")
    print("=" * 60)

    # Determine which blocks to generate
    target_blocks = []
    if len(sys.argv) > 1:
        target_blocks = sys.argv[1:]
    else:
        target_blocks = POC_BLOCKS

    print(f"\nGenerating {len(target_blocks)} blocks:\n")

    generated = 0
    for name in target_blocks:
        print(f"--> {name}")
        if generate_block(name):
            generated += 1

    print(f"\n{'=' * 60}")
    print(f"Generated {generated}/{len(target_blocks)} blocks in {REGISTRY_ROOT}/")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
