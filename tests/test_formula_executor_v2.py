"""Tests for the shared, domain-agnostic formula_executor_v2 block."""

from __future__ import annotations

import pytest

from app.core.sandbox import run_sandboxed, SandboxResult
from app.prompts.codegen_system import build_codegen_prompt
from app.blocks.formula_executor_v2 import FormulaExecutorV2Block


# ---------------------------------------------------------------------------
# Prompt policy tests
# ---------------------------------------------------------------------------


def test_prompt_allows_numpy():
    prompt = build_codegen_prompt("sum an array", {})
    assert "numpy" in prompt


def test_prompt_allows_sympy():
    prompt = build_codegen_prompt("solve symbolically", {})
    assert "sympy" in prompt


def test_prompt_allows_pint():
    prompt = build_codegen_prompt("convert units", {})
    assert "pint" in prompt


def test_prompt_blocks_scipy():
    prompt = build_codegen_prompt("interpolate", {})
    assert "scipy" in prompt.lower()
    assert "not allowed" in prompt.lower() or "not allowed" in prompt


def test_prompt_is_domain_agnostic():
    prompt = build_codegen_prompt("calculate", {})
    assert "construction-project intelligence" not in prompt.lower()
    assert "domain intelligence platform" in prompt.lower()


def test_prompt_states_auditable_calculations_only():
    prompt = build_codegen_prompt("calculate", {})
    assert "deterministic, auditable calculations" in prompt
    assert "network access" in prompt
    assert "file access" in prompt


# ---------------------------------------------------------------------------
# Sandbox import tests
# ---------------------------------------------------------------------------


def test_sandbox_accepts_numpy():
    out = run_sandboxed("import numpy as np\nresult = int(np.array([1, 2, 3]).sum())")
    assert out.success is True
    assert out.result == 6


def test_sandbox_accepts_sympy():
    out = run_sandboxed(
        'import sympy as sp\nx = sp.Symbol("x")\nresult = str(sp.expand((x + 1) ** 2))'
    )
    assert out.success is True
    assert "x**2" in out.result


def test_sandbox_accepts_pint():
    out = run_sandboxed(
        "import pint\n"
        "ureg = pint.UnitRegistry()\n"
        "q = 3 * ureg.meter + 200 * ureg.centimeter\n"
        "result = str(q.to(ureg.meter))"
    )
    assert out.success is True
    assert "5" in out.result
    assert "meter" in out.result


def test_sandbox_rejects_scipy():
    out = run_sandboxed("import scipy\nresult = 1")
    assert out.success is False
    assert "blocked" in out.error.lower() or "not allowed" in out.error.lower()


# ---------------------------------------------------------------------------
# FormulaExecutorV2Block process tests with mocked LLM
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
def _mock_llm(code: str):
    async def _inner(prompt: str) -> str:
        return _fence(code)
    return _inner


@pytest.mark.asyncio
async def test_block_runs_numpy_code():
    block = FormulaExecutorV2Block()
    block._call_llm = _mock_llm("import numpy as np\nresult = int(np.array([1, 2, 3]).sum())")
    out = await block.process({"task": "sum array"})
    assert out["status"] == "success"
    assert out["result"] == 6


@pytest.mark.asyncio
async def test_block_runs_sympy_code():
    block = FormulaExecutorV2Block()
    block._call_llm = _mock_llm('import sympy as sp\nx = sp.Symbol("x")\nresult = str(sp.expand((x + 1) ** 2))')
    out = await block.process({"task": "expand binomial"})
    assert out["status"] == "success"
    assert "x**2" in out["result"]


@pytest.mark.asyncio
async def test_block_runs_pint_code():
    block = FormulaExecutorV2Block()
    block._call_llm = _mock_llm(
        "import pint\n"
        "ureg = pint.UnitRegistry()\n"
        "q = 3 * ureg.meter + 200 * ureg.centimeter\n"
        "result = str(q.to(ureg.meter))"
    )
    out = await block.process({"task": "convert units"})
    assert out["status"] == "success"
    assert "meter" in out["result"]


@pytest.mark.asyncio
async def test_block_retries_then_fails_on_scipy():
    block = FormulaExecutorV2Block()
    block._call_llm = _mock_llm("import scipy\nresult = 1")
    out = await block.process({"task": "use scipy"})
    assert out["status"] == "error"
    assert out["attempts"] >= 1


def _fence(code: str) -> str:
    return f"```python\n{code}\n```"
