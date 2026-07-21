# Cerebrum Blocks — Repository Status

> **Date:** 2026-07-19  
> **Branch:** main  
> **Python files in `app/blocks/`:** 106  
> **Registered blocks (`BLOCK_REGISTRY`):** 42  
> **Tests collected:** 608 (8 deselected, 4 collection errors)

---

## Summary

Repository hygiene pass completed. Root-level scripts and test files were moved
to `scripts/`, `tests/`, and `dev/`. CI now runs `tests/test_all_blocks.py` and
`tests/test_regression_security.py`. Duplicate PDF dependencies were removed
from `requirements.txt` (`PyPDF2` dropped, `pypdf` kept; `pdfplumber` and
`pymupdf`/`PyMuPDF` deduplicated).

---

## Block Inventory

| Location | Count |
|----------|-------|
| `app/blocks/*.py` (top-level) | 106 |
| Registered in `BLOCK_REGISTRY` | 42 |
| Containers under `app/containers/` | 2+ |
| Core modules under `app/core/` | 40+ |

### New / upgraded platform blocks (this pass)

| Block | Purpose |
|-------|---------|
| `tenant` | Tenant/project provisioning and header context resolution |
| `auth` | API keys + tenant/project scoping |
| `audit` | Immutable hash-chain log + structured `ActionRun` records |
| `graph_orchestrator` | Universal directed-graph execution engine |
| `agent_catalog` | Declarative agent manifests, hats, handoffs |
| `connector_registry` | Connector lifecycle registry and run tracking |
| `storage` | Secure upload validation + S3/R2 archive support |
| `admin` | Preflight checks, stats, bulk cleanup |

---

## Test Inventory

Collected via `pytest --collect-only`:

```
608/616 tests collected (8 deselected), 4 errors in 8.07s
```

### Collection errors (pre-existing)

| File | Cause |
|------|-------|
| `tests/blocks/test_vector_search.py` | Missing optional dependency / import issue |
| `tests/blocks/test_web.py` | Missing optional dependency / import issue |
| `tests/blocks/test_zvec.py` | `sklearn` not installed |
| `tests/test_formula_executor_v2.py` | `RestrictedPython` not installed |

### CI coverage

`.github/workflows/ci.yml` now runs:

- `tests/integration/`
- `tests/test_typed_block.py`
- `tests/test_all_blocks.py`
- `tests/test_regression_security.py`

---

## Repository Layout

```
├── app/blocks/          # 106 .py files (blocks + helpers)
├── app/containers/      # Domain containers
├── app/core/            # Runtime core
├── app/lib/             # Shared domain libraries
├── dev/                 # Local dev tools (excluded from Docker)
│   └── mock_backend.py
├── scripts/             # Maintenance scripts
│   ├── assemble.py
│   ├── audit_all_blocks.py
│   └── migrate_to_universal.py
├── tests/               # All pytest tests
└── block_store/         # Packaged block archive
```

---

## Known Issues

1. **4 test collection errors** due to missing optional deps (`sklearn`,
   `RestrictedPython`). CI does not fail on these because the files are not yet
   included in the CI run.
2. **API keys out of credits** — DeepSeek and Anthropic keys need refill.
3. **Optional libraries** — `opencv-python-headless` and some heavy ML packages
   remain optional; blocks degrade gracefully when absent.

---

## Render Deployment

- **Build:** `pip install -r requirements.txt`
- **Start:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **MCP Server:** Mounted at `/mcp`
