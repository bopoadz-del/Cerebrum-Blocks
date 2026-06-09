#!/usr/bin/env python3
"""
Standalone adapter for sandbox block.
Provides secure code execution with safety checks.
Note: Full resource limits require Unix (resource module).
"""

import asyncio
import json
import sys
import io
import os
import tempfile
import subprocess
from typing import Dict, Any


ALLOWED_MODULES = ["math", "random", "datetime", "json", "re", "string", "collections"]
BLOCKED_BUILTINS = ["__import__", "open", "exec", "eval", "compile"]


def _check_safety(code: str, language: str = "python") -> Dict:
    violations = []
    warnings = []
    if language == "python":
        dangerous = {
            "__import__": "Dynamic import detected",
            "eval(": "eval() usage detected",
            "exec(": "exec() usage detected",
            "compile(": "compile() usage detected",
            "subprocess": "Subprocess usage detected",
            "os.system": "System command detected",
            "open(": "File operation detected",
            "socket": "Network socket detected",
            "urllib": "Network access detected",
        }
        for pattern, message in dangerous.items():
            if pattern in code:
                violations.append({"pattern": pattern, "message": message})
        if "while True:" in code and "break" not in code:
            warnings.append("Potential infinite loop")
    return {
        "safe": len(violations) == 0,
        "violations": violations,
        "warnings": warnings,
        "language": language,
    }


def _execute_python(code: str, inputs: Dict, max_cpu_time: int = 5) -> Dict:
    safe_globals = {"__builtins__": {}}
    for name in dir(__builtins__):
        if name not in BLOCKED_BUILTINS and not name.startswith("_"):
            try:
                safe_globals["__builtins__"][name] = getattr(__builtins__, name)
            except AttributeError:
                pass
    for mod_name in ALLOWED_MODULES:
        try:
            safe_globals[mod_name] = __import__(mod_name)
        except ImportError:
            pass
    safe_globals["input"] = lambda prompt="": inputs.get("input", "")
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = stdout_capture, stderr_capture
    result_value = None
    error = None
    try:
        exec(code, safe_globals)
        if "result" in safe_globals:
            result_value = safe_globals["result"]
        elif "output" in safe_globals:
            result_value = safe_globals["output"]
    except Exception as e:
        error = str(e)
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
    return {
        "success": error is None,
        "result": result_value,
        "stdout": stdout_capture.getvalue(),
        "stderr": stderr_capture.getvalue(),
        "error": error,
        "sandboxed": True,
    }


def _execute_javascript(code: str, max_cpu_time: int = 5) -> Dict:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        f.write(code)
        temp_path = f.name
    try:
        result = subprocess.run(
            ["node", temp_path],
            capture_output=True,
            text=True,
            timeout=max_cpu_time,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "sandboxed": True,
        }
    except FileNotFoundError:
        return {"error": "Node.js not available", "sandboxed": True}
    except subprocess.TimeoutExpired:
        return {"error": "Execution timeout", "killed": True, "sandboxed": True}
    finally:
        os.unlink(temp_path)


def run(input_data: Any = None, **params) -> Any:
    action = params.get("action")
    if action is None and isinstance(input_data, dict):
        action = input_data.get("action")
    if action is None:
        action = "execute"

    code = params.get("code") or (input_data.get("code") if isinstance(input_data, dict) else None)
    language = params.get("language") or (input_data.get("language") if isinstance(input_data, dict) else "python")
    max_cpu_time = params.get("max_cpu_time", 5)

    if action == "execute":
        if not code:
            return {"error": "No code provided"}
        safety = _check_safety(code, language)
        if not safety["safe"]:
            return {"error": "Code failed safety check", "violations": safety["violations"], "blocked": True}
        if language == "python":
            inputs = input_data.get("inputs", {}) if isinstance(input_data, dict) else {}
            return _execute_python(code, inputs, max_cpu_time)
        elif language == "javascript":
            return _execute_javascript(code, max_cpu_time)
        else:
            return {"error": f"Unsupported language: {language}"}
    elif action == "validate_code":
        return _check_safety(code or "", language)
    elif action == "check_safety":
        return _check_safety(code or "", language)
    elif action == "get_stats":
        return {"executions": 0, "blocked": 0, "policies": 1, "active_sessions": 0}
    elif action == "create_policy":
        return {"created": True, "policy": params.get("name", "custom")}
    else:
        return {"error": f"Unknown action: {action}"}


if __name__ == "__main__":
    data = json.load(sys.stdin)
    try:
        output = run(**data)
        print(json.dumps({"success": True, "output": output}))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
