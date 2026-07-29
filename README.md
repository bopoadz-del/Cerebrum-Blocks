# The Store - Cerebrum Blocks 

**Independent.** Cerebrum Blocks is **not** Cerebrum — it is a separate
project with its own repo, its own API, and its own kits. The block store is
open source; CerebrumDev is a separate proprietary product that *consumes*
blocks and kits through the public API, exactly like any other client.

[![CI](https://github.com/bopoadz-del/Cerebrum-Blocks/actions/workflows/ci.yml/badge.svg)](https://github.com/bopoadz-del/Cerebrum-Blocks/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

> ### Part of the CEREBRUM ecosystem — industrialized AI delivery
>
> **The Store — [Cerebrum-Blocks](https://github.com/bopoadz-del/Cerebrum-Blocks):** 129 typed blocks (108 registry entries), 19 domain kits + universal kernel, one API. Build a capability once; every sector inherits it.  
> **The Factory — [CerebrumDev.ai](https://github.com/bopoadz-del/CerebrumDev.ai):** the client-facing interface that assembles blocks into governed, deployable vertical platforms — evaluation gates in CI, release certification, honest closure reporting.  
> **The Products — [The Fork](https://github.com/bopoadz-del/The_Fork)** (construction AI — enterprise client pilot) **· [RetailOps](https://github.com/bopoadz-del/TEKsystems_GlobalRetailMNC)** (retail operations — assembled, CI-gated and deployed in under three days).  
> **The Edge:** sovereign deployment proven — zero-egress on-premise profile, executed air-gap acceptance test, signed sovereignty report.
>
> **You are here: THE STORE** — the certified capability inventory every product is assembled from.

---

## Why this exists

AI product teams keep rebuilding the same capabilities from scratch —
retrieval, agents, document processing, formula engines, vision — and then
rebuilding them again inside every vertical product. Cerebrum Blocks
turns those capabilities into **typed, reusable execution blocks** with a
uniform contract, so they are built once, certified once, and reused across
products, clients, and domain kits.

## What it is

| Component | Path | Purpose |
|---|---|---|
| Blocks | `app/blocks/` | 129 typed execution blocks (chat, RAG, documents, domain analysis, workbench, …) |
| Block runtime | `app/core/` | TypedBlock base with fail-closed I/O validation, trust-scope enforcement, grounding stage, capability model |
| Execute API | `app/routers/execute.py` | `/v1/execute` — auth, tier boundary, trust scope, grounding, capability dispatch |
| Block registry | `block_registry/` | 108 manifest + adapter entries for discovery and subprocess execution |
| Store | `app/routers/store.py` + `block_store/` | Kit catalog, provenance-verified install, 19 domain kits + the universal kernel |
| Sandbox runner | `sandbox-runner/` | Out-of-process execution service for blocks with elevated capabilities |
| Containers | `app/containers/` | Domain containers assembling blocks per vertical |

## Block categories

| Category | Examples (real block names) |
|---|---|
| **Reasoning / chat** | chat, agent_swarm, smart_orchestrator, adaptive_router |
| **Retrieval** | vector_search, knowledge, zvec |
| **Formulas** | formula_executor, formula_executor_v2, construction_advisor (cited construction KB) |
| **Documents** | pdf, ocr, xlsx_schedule, spec_analyzer, bim_extractor |
| **Domain analysis** | construction_v2, aviation_v2, finance_v2, medical_v2, … (19 verticals) |
| **Workbench** | workbench (bounded Kimi CLI editing with diff + safety gates) |

## Domain kits

19 domain kits ship under `block_store/kits/` (construction, aviation,
finance, medical, legal, retail, insurance, education, agriculture,
manufacturing, oil & gas, pharma, real estate, hotel management, HR,
supply chain, automotive, finance ops, and more), plus the
`universal_kernel` capability kits. A kit is a manifest plus a bundle;
installs are provenance-verified (see Security model).

## Quick start

```bash
git clone https://github.com/bopoadz-del/Cerebrum-Blocks.git
cd Cerebrum-Blocks
pip install -r requirements.txt
python -m pytest tests/integration -q   # verify
uvicorn app.main:app --reload           # serve on :8000
```

## Execution modes

| Mode | When | Mechanism |
|---|---|---|
| in-process | blocks whose declared capabilities are safe | direct call inside the API worker |
| registry subprocess | registry-only blocks with safe capabilities | `block_registry/<id>/block.py` via subprocess |
| sandbox runner | blocks declaring network / filesystem / privileged imports | out-of-process `sandbox-runner/` service |

## Security model

- Every block declares capabilities (network, filesystem, privileged
  imports) in its registry manifest; elevated blocks are dispatched to the
  out-of-process sandbox runner, and revoked publishers cannot execute.
- `/v1/execute` enforces the tier block-access boundary, strips
  caller-supplied trust scope (tenant/permission keys are
  server-controlled), and routes answer-producing blocks through a
  mandatory grounding stage (blocked answers are null, verdicts audited).
- Kit installs verify a `provenance.json` (sha256 digests + root hash)
  when present; kits without one are labeled `absent — unverified` in the
  install response. Ed25519 block signing exists (`scripts/sign_block.py`,
  `app/core/block_validation.py`) but is **not yet operating**: no
  publisher private key is present and kit signature fields are empty —
  see `PARKED_BLOCKERS.md`. Do not describe blocks as signed today.

## Docs

- [API.md](API.md) — the HTTP API surface
- [REPO_STATUS.md](REPO_STATUS.md) — current inventory and status
- [SKILLS_BLOCK_LOGIC.md](SKILLS_BLOCK_LOGIC.md) — block logic notes
- [docs/decisions/phase1-dead-controls.md](docs/decisions/phase1-dead-controls.md) — control dispositions (wired vs deleted)
- [PARKED_BLOCKERS.md](PARKED_BLOCKERS.md) — honestly parked work (e.g. block signing)

## License

MIT — see [LICENSE](LICENSE).
