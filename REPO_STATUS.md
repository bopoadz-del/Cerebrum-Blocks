# Cerebrum Blocks — Repository Status

> **Date:** 2026-07-22  
> **Branch:** main  
> **Python files in `app/blocks/`:** 121  
> **Registered blocks (`block_registry/`):** 105  
> **Tests collected:** 660 (8 deselected, 4 collection errors)

---

## Summary

Recent merges brought in:
- **FinanceOps foundation blocks** (PR #41): 7 new finance transformation blocks plus container and kit bundle.
- **Generic action-contract runtime** (PR #40): domain-neutral action discovery, registry, and execution engine under `app/blocks/core/action_contract/`.
- **Store registry update** (PR #42): registered `action_contract` in `block_registry/`.

Earlier hygiene pass moved root-level scripts/tests into `scripts/`, `tests/`, and `dev/`; cleaned duplicate PDF dependencies; and wired `tests/test_all_blocks.py` and `tests/test_regression_security.py` into CI.

---

## Block Inventory

| Location | Count |
|----------|-------|
| `app/blocks/*.py` (top-level) | 121 |
| `block_registry/` entries | 105 |
| Containers under `app/containers/` | 2 directories (`construction/`, plus container modules) |
| Core modules under `app/core/` | 40+ |

### Recently added / upgraded blocks

| Block | Purpose | Source | Tier |
|-------|---------|--------|------|
| `universal_kernel` | Product-neutral 24-capability kernel kit (trust, intelligence, operations, frontier) | Mixed (Fork + Factory + new) | **premium** |
| `action_contract` | Generic action-contract runtime (models, registry, execution, schema validation) | Cerebrum-Steward | standard |
| `finance_canonical_model` | Canonical chart-of-accounts and financial data model | FinanceOps kit |
| `finance_coa_governance` | COA governance rules and validation | FinanceOps kit |
| `finance_data_quality` | Financial data quality checks | FinanceOps kit |
| `finance_import` | General ledger and sub-ledger import transforms | FinanceOps kit |
| `finance_reconciliation` | Account reconciliation engine | FinanceOps kit |
| `finance_saas_metrics` | SaaS / subscription KPI calculations | FinanceOps kit |
| `finance_v2` | Composite FinanceOps reasoning block | FinanceOps kit |
| `finance_ops` | FinanceOps domain container | FinanceOps kit |
| `agency_commission_engine` | Commission calculation and chargebacks | InsureOps kit |
| `agency_hierarchy` | Agency/producer hierarchy management | InsureOps kit |
| `attrition_scorer` | Churn / attrition scoring | InsureOps kit |
| `bordereaux_ingest` | Insurance statement feed ingest | InsureOps kit |
| `channel_router` | Explainable case channel routing | InsureOps kit |
| `distribution_analytics` | Distribution performance analytics | InsureOps kit |
| `hkia_gn16_rules` | HK insurance regulatory rule evaluation | InsureOps kit |
| `incentive_targeting` | Incentive eligibility and recommendations | InsureOps kit |
| `producer_record` | Producer / agent record management | InsureOps kit |

---

## Test Inventory

Collected via `pytest --collect-only`:

```
660/668 tests collected (8 deselected), 4 errors in 9.02s
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
├── app/blocks/          # 121 .py files (blocks + helpers)
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
