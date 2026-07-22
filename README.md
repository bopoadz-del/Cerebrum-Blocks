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
> **The Store — [Cerebrum-Blocks](https://github.com/bopoadz-del/Cerebrum-Blocks):** 94+ certified AI blocks, 17 industry kits, one universal API. Build a capability once; every sector inherits it.  
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
| Block engine | `app/engine/` | Typed execution, validation, provenance |
| Block registry | `app/block_registry/` | Central registration + discovery of all blocks |
| Store API | `app/store/` | REST API: catalog, search, bundle install, health |
| Kit registry | `app/kits/` | Manifest-driven composition of blocks into domain kits |
| Formula registry | `app/formulas/` | Curated engineering formulas with source references (AISC, ACI, ASHRAE, …) |
| Execution modes | `app/execution/` | Sandboxed (RestrictedPython) → process-pool → container |
| MCP layer | `app/mcp/` | Expose blocks to LLM agents via Model Context Protocol |

## Block categories

| Category | Examples |
|---|---|
| **Reasoning** | llm_query, prompt_chain |
| **Retrieval** | vector_search, hybrid_retrieval, graph_query |
| **Agents** | task_agent, tool_agent, workflow_agent |
| **Formulas** | steel_beam_design, concrete_mix, hvac_load, solar_panel_output |
| **Documents** | pdf_ingest, docx_ingest, chunker, doc_classifier |
| **Integrations** | email, slack, webhook, ifc_parser, dwg_parser |
| **Vision** | image_caption, defect_detection |

## Domain kits

17 domain kits ship today — Construction, Real Estate, Hotel Management,
Oil & Gas, Healthcare, Manufacturing, Legal, Finance, Retail, Education,
Logistics, Agriculture, Energy, Insurance, Telecommunications, Government,
and Transportation. Each kit is a **manifest of block references** — no code
duplication, no vendored copies. Add a kit by writing a JSON manifest that
points at existing blocks.

## Quick start

```bash
git clone https://github.com/bopoadz-del/Cerebrum-Blocks.git
cd Cerebrum-Blocks
pip install -r requirements.txt
python -m pytest tests/integration -q   # verify
uvicorn app.main:app --reload           # serve on :8000
```

## Execution modes

| Mode | Safety | Use |
|---|---|---|
| `sandbox` | RestrictedPython, no imports | untrusted formula code |
| `process` | subprocess pool | default |
| `container` | Docker isolation | production / multi-tenant |

## Security model

- Every block declares its required capabilities (`fs:read`, `net:http`, …)
  and cannot exceed them at runtime.
- Publisher trust tiers (community → reviewed → certified) gate what may be
  installed where.
- Blocks are signed (Ed25519) and verified on install.
- See [SECURITY.md](SECURITY.md) for the full model.

## Docs

- [BLOCK_CONTRACT.md](BLOCK_CONTRACT.md) — the block authoring contract
- [docs/block-store-complete.md](docs/block-store-complete.md) — store architecture
- [docs/MCP_BLOCK_LAYER.md](docs/MCP_BLOCK_LAYER.md) — MCP integration
- [CONTRIBUTING.md](CONTRIBUTING.md) — how to add a block or kit

## License

MIT — see [LICENSE](LICENSE).
