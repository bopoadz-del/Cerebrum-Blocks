# Store Inventory — verified enumeration

**Verified on 2026-09-19** by a programmatic scan of the Cerebrum-Blocks
checkout (`block_registry/`, `block_store/`, `block_store/kits/`),
`scripts/census_registry.py`, a manifest/signature sweep, and an author
sweep. Every claim below is from the files themselves, not from memory.

## Trust summary

- **115 registry blocks**, every one with a `block.json` manifest
  (115/115) and a signature (115/115). Census: **0 missing (115
  advertised)**. Author sweep: **107 declared `Cerebrum Team`**, 8 declare
  no author.
- **Zero stub-like blocks in the Store registry.** The echo-stub pattern
  (`run()` returning `{"status": "ok", "result": <input>}` unconditionally)
  appears nowhere in `block_registry/` (pattern sweep ships in CI). The
  universal_kernel security wave (audit_evidence, provenance_verification)
  contains real SHA-256 chain verification with tamper tests.
- **The five estate blocks are real and registered in the Store**
  (`estate_registry`, `estate_maintenance`, `evidence_verifier`,
  `readiness_engine`, `portfolio_rollup`). The always-ok stubs they
  replaced are gone — Store `main` `9b8d781f`. There is no factory vendor
  mirror of store blocks; the factory consumes this inventory like any
  other client.

## Vertical readiness

### Ready — build and test these five

| Vertical | Kit | Domain blocks (beyond the generic core) |
|---|---|---|
| hotels | hotel_management | hotel_v2 |
| insurance | insurance | insurance_v2, agency_hierarchy, producer_record, agency_commission_engine, channel_router, attrition_scorer, incentive_targeting, hkia_gn16_rules, bordereaux_ingest, distribution_analytics |
| construction | construction | construction_v2, boq_processor, spec_analyzer, sympy_reasoning, drawing_qto, primavera_parser, smart_orchestrator, jetson_gateway, bim_extractor, bim, learning_engine, recommendation_template, project_reasoner |
| finance | finance, finance_ops | finance_v2, finance_canonical_model, finance_import, finance_data_quality, finance_reconciliation, finance_coa_governance, finance_saas_metrics |
| retail | retail | retail_v2 |

The generic core shared by domain kits: `pdf, ocr, chat, image,
formula_executor, formula_executor_v2`. A capability that resolves only to
these (or to cross-cutting plumbing) is flagged as a domain gap at plan
time (2b).

### Excluded — no testing (declared)

medical, legal, veterinary, pharma. Drafts for these verticals carry the
honest note: no authoritative domain content; domain logic would be
fabricated.

### Unverified — kit exists, not on the ready list

agriculture, automotive, aviation, education, hr, manufacturing,
mep_coordination, oil_gas, real_estate, supply_chain. Their kits exist in
the Store; depth is not guaranteed until each is declared ready.

## Full kit list (21)

_template (empty) · agriculture · automotive · aviation · construction ·
education · finance · finance_ops · hotel_management · hr · insurance ·
legal · manufacturing · medical · mep_coordination (geometry_engine,
clearance_rules, clash_triage, clash_resolver, bcf_export, version_diff,
model_clone) · oil_gas · pharma · real_estate · retail · supply_chain ·
universal_kernel (identity, authorization_policy, scope_guard,
rate_limit_guard, audit_evidence, provenance_verification,
secure_ingestion, document_parsing, durable_jobs, embedding_provider,
vector_store, hybrid_retrieval, llm_provider, grounded_answer, xlsx_export,
pdf_export, json_audit_export, health, monitoring, structured_outcomes,
billing_entitlement, notification_mailer, approval_action, block_runner)

19 domain kits + `universal_kernel` + `_template`. The previously listed
`universal_business` kit does not exist in `block_store/kits/` and is
removed from this inventory.

## Registry blocks (115) — categories

- **Registered `*_v2` domain blocks (8)**: construction_v2, finance_v2,
  formula_executor_v2, insurance_v2, legal_v2, ocr_v2, pdf_v2, retail_v2.
- **Unregistered `*_v2` modules (12)** — real code, no registry entry yet
  (COLLECTOR rung 2, by design): agriculture_v2, automotive_v2,
  aviation_v2, education_v2, hotel_v2, hr_v2, manufacturing_v2,
  medical_v2, oil_gas_v2, pharma_v2, real_estate_v2, supply_chain_v2.
- **Generic core**: pdf, ocr, chat, image, formula_executor(_v2).
- **Cross-cutting plumbing**: database, storage, queue, workflow,
  notification, team, validation, audit, dashboard, analytics, event_bus,
  file_hasher, document_engine, capture, knowledge, memory, search, web,
  email, auth, rate_limiter, cache_manager, monitoring, secrets, skills,
  review, sandbox, orchestration/smart_orchestrator.
- **Governance & security** (universal_kernel): identity,
  authorization_policy, scope_guard, rate_limit_guard, audit_evidence
  (SHA-256 chain — REAL), provenance_verification (digest/root-hash — REAL).
- **Capture/parsing**: drawing_qto, bim_extractor, bordereaux_ingest,
  primavera_parser, spec_analyzer, ocr(_v2), pdf(_v2), image,
  video_metadata_ingest, hkia_gn16_rules.
- **Estate (real)**: estate_registry, estate_maintenance,
  evidence_verifier, readiness_engine, portfolio_rollup.
- **Specialist**: jetson_gateway, sympy_reasoning, learning_engine,
  recommendation_template, project_reasoner, attrition_scorer,
  incentive_targeting, distribution_analytics, agency_commission_engine,
  producer_record, channel_router, finance_canonical_model and the
  finance_ops quality set, mep_coordination clash stack.

## Known defects (tracked, not hidden)

1. `block_store/admin_block.py::_preflight` — the database check reports
   `not_configured` when no database block is bound (honest), but reports
   `ok` without an actual probe when one is injected (PARTIAL — Store
   side, one-line fix queued).

## Consumers of this file

- The factory inventory declaration (`app.factory.inventory`) — ready
  verticals and kit domain sets are mirrored there and enforced at draft
  and plan time.
- Build/test planning: only the five ready verticals are tested until more
  kits are declared ready.
