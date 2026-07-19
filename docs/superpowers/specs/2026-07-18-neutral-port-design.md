# Design: Neutral Port of Fork Construction Blocks + TEKsystems Runtime Patterns into Cerebrum-Blocks

**Date:** 2026-07-18  
**Scope:** Upgrade Cerebrum-Blocks (CB) with capabilities found in The_Fork and TEKsystems, while keeping CB universal, neutral, and free of project-specific data.

---

## 1. Goal

Make Cerebrum-Blocks a stronger, domain-neutral platform by:

1. Back-porting **generic construction-engine capabilities** from The_Fork (scheduling, BOQ/QTO, BIM, validation) with all client/project-specific constants externalized to config.
2. Back-porting **generic runtime patterns** from TEKsystems (action registry, deterministic reasoner, audit, hybrid retrieval, connector contract, agent manifest catalog, verified learning) without any retail-specific business rules.
3. Preserving CB's existing richer blocks (`pdf.py`, `llm_enhancer.py`, etc.) and NOT downgrading them.

---

## 2. Constraints

- **No project-specific data in CB code.** Diriyah Gate, JCB drawing numbers, place names, vendor names, and client headers must live in config files or kit data.
- **No retail-specific rules in platform code.** TEKsystems learners, connectors, and manifests are sources of *pattern*, not content to copy verbatim.
- **No hardcoded repo URLs or secrets.** All source references become neutral.
- **Keep tests green.** Use TDD: write a failing test for each new behavior, then implement.
- **Incremental delivery.** Work in small, reviewable phases. Do not port everything in one pass.

---

## 3. Decomposition

The work is split into four phases. Each phase is independently testable and mergeable.

### Phase 1 — Foundation: file_crypto + universal_base + plan_executor

**Why first:** Subsequent Fork blocks depend on `file_crypto` and the richer `UniversalBlock` base.

- Port `app/core/file_crypto.py` from Fork → neutral encryption-at-rest helper.
- Merge Fork's `UniversalBlock` input-validation additions (`required_input_fields`, `required_input_one_of`, `auto_validate`, `text_output_field`, `input_adapter` prep) into CB `app/core/universal_base.py`.
- Merge Fork's `app/core/plan_executor.py` schedule-workflow step handlers into CB.

**Neutralization:**
- `file_crypto` must use env-driven key only (`DATA_ENCRYPTION_KEY`). No hardcoded keys.
- `plan_executor` step names are generic (`extract_document`, `build_wbs`, `cost_load`, `render_artifact`, `cpm`, `resource`, `gantt`, `compress`, `code_gen`).

### Phase 2 — Construction engine: lib modules + 6 new blocks

**Why second:** These are the real engines behind Fork's construction features.

- Port `app/lib/{pm_computations.py, pm_excel.py, boq_pricing.py, boq_units.py, boq_excel.py, schedule_bridge.py, schedule_feed.py}`.
- Port 6 new blocks: `cpm_engine`, `fasttrack_analyzer`, `manpower_planner`, `schedule_generator`, `schedule_excel_writer`, `scope_extractor`.

**Neutralization:**
- All discipline codes, drawing-number regexes, place names, and project headers move to `app/core/construction_constants.py` or kit config.
- `pm_computations` uses generic calendar/activity/resource names.
- `boq_units` uses standard unit lists, not project-specific abbreviations.

### Phase 3 — Richer shared Fork blocks

Merge selected Fork enhancements into existing CB blocks:

- `drawing_qto`: PDF vector extraction, title-block parsing, multi-drawing merge.
- `boq_processor`: PDF table grouping, memory guard, project filename resolution.
- `validation_pipeline`: full runnable 5-stage numeric validator (replaces the shim).
- `bim_extractor`, `bim`: clash detection, IFC cache, honest format errors.
- `primavera_parser`: real CPM, XER encoding, response caps.
- `smart_orchestrator`: word-boundary router, learned routing, broader keyword coverage.
- `spec_analyzer`: OCR fallback, grade/standard patterns (generic).
- `voice`: audio transcoding.
- `sympy_reasoning`: true symbolic formulas, variance checks.
- `translate`, `google_drive`, `recommendation_template`: small robustness improvements.

**Neutralization:**
- Title-block schemas accept a `title_block_schema` parameter.
- Standard patterns are configurable via `construction_constants`.
- No client-specific adapter paths or default prompt files.

### Phase 4 — TEKsystems platform patterns

Add neutral platform modules under `app/core/`:

- `app/core/action_runtime.py`: `ActionContext`, `ActionSpec`, `ActionResult`, `ActionRegistry`, `execute_action`.
- `app/core/reasoner.py`: deterministic domain-neutral reasoner + execution plan.
- `app/core/graph_orchestrator.py`: LangGraph orchestration consuming action registry.
- `app/core/audit_store.py`: immutable `ActionRun` model + `action_runs` table.
- `app/core/retrieval_hybrid.py`: hybrid RRF retrieval + embedding guard.
- `app/core/verified_learning.py`: `LearningEvent`, `LearningProfile`, pluggable learner modules.
- `app/core/connector_base.py`: generic connector contract + registry.
- `app/core/agent_catalog.py`: JSON manifest schema + base/hat composition.
- Trusted-header middleware for `X-User-Id` / `X-Tenant-Id` / `X-Project-Id`.

**Neutralization:**
- No retail-specific actions, learners, connectors, or manifests in platform code.
- Retail examples become documentation or tests only.

---

## 4. Testing Strategy

- Every new module gets a failing test first (TDD).
- Tests live alongside code: `tests/unit/core/...` and `tests/unit/blocks/...`.
- Integration tests only for cross-module workflows (e.g., `boq_processor` → `file_crypto`).
- Run `pytest` after each module is ported; no phase is "done" while tests are red.

---

## 5. Success Criteria

- [ ] Phase 1 tests pass and no existing CB tests break.
- [ ] Phase 2 adds 6 new construction blocks + 7 lib modules, all neutralized and tested.
- [ ] Phase 3 merges Fork enrichments without losing CB's existing richer blocks.
- [ ] Phase 4 adds 8+ neutral platform modules from TEKsystems patterns, all tested.
- [ ] No hardcoded client names, repo URLs, or secrets anywhere in changed files.
- [ ] Final diff is reviewable and does not include unrelated refactors.

---

## 6. First Action

Start **Phase 1** with `app/core/file_crypto.py`: write a failing test, port a neutral `open_plaintext` context manager, verify it passes.
