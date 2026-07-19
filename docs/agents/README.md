# Modular Agent Pack

Platform-agnostic agent infrastructure for Cerebrum and compatible construction-tech platforms.

## Architecture

- **1 core agent** — shared kernel (`core-agent`). Enforces honesty, grounding, tool discipline, memory, handoff syntax, and output conventions.
- **11 domain hats** — specialist agents that extend the core with domain-specific tools, rules, and escalation paths.
- **3 shared utilities** — not hats, but referenced by hats: `external-mcp`, `self-coding`, `smart-orchestrator`.

## The 11 hats

| Hat | Domain | Escalates to |
|---|---|---|
| `project-assistant` | Operator's primary chat surface | construction-pm, contracts-manager, quantity-surveyor, bim-analyst, safety-officer, heavy-reasoning |
| `construction-pm` | Schedule, procurement, risks, costs | contracts-manager, quantity-surveyor, bim-analyst, safety-officer |
| `contracts-manager` | RFP, clauses, change orders, payment, claims | quantity-surveyor, construction-pm, safety-officer |
| `quantity-surveyor` | BOQ takeoff, drawing measurements, variance | contracts-manager, bim-analyst, construction-pm |
| `bim-analyst` | IFC, clash detection, model quantities | quantity-surveyor, construction-pm |
| `document-analyst` | Generic document parsing and Q&A | quantity-surveyor, contracts-manager, bim-analyst |
| `document-ingestion` | File intake and parser routing | heavy-reasoning, quantity-surveyor, document-analyst |
| `safety-officer` | HSE audits, risk register, incidents | contracts-manager, construction-pm |
| `heavy-reasoning` | Variance synthesis, cost/time impact, recommendations | validation, document-ingestion, domain hats |
| `validation` | 5-stage validation and credibility tiers | heavy-reasoning, learning |
| `learning` | User corrections and coefficient tuning | heavy-reasoning, validation |

## Source of truth

| Layer | Path | Role |
|---|---|---|
| **Canonical** | `.agent-core/<id>.md` + `.agent-core/<id>.json` | Vendor-neutral source of truth + machine-readable manifest |
| **Docs** | `docs/agents/` | README + audit |

Each `.agent-core/<id>.json` now includes:

- `description` — frontmatter-style "Use when..." text for host agent stores.
- `examples` — structured user/assistant example exchanges for auto-delegation prompts.
- `activation` — keywords and routing guidance.
- `handoffs` — escalation targets.
- `allowed_paths` / `denied_paths` — filesystem boundaries.
- `verification` / `completion_criteria` — quality gates.

## Porting to a new platform

To adopt this pack in a new platform:

1. Copy `.agent-core/` unchanged.
2. Add a platform wrapper directory (e.g., `.claude/agents/`, `.cursor/agents/`, `.kimi/agents/`) with the host's required frontmatter.
3. Use `description` and `examples` from each JSON to build the host's agent-store listing.
4. Sync the canonical `.md` body into the wrapper, preserving host-specific frontmatter.
5. Map the JSON `handoffs` and `activation` fields to the host's routing/delegation mechanism.
6. Do not commit agent memory or secrets.

## Differences from in-app product agents

These are **coding/development subagents** and runtime routing contracts. They are distinct from:

- `app/agents/configs/*` — in-app product personas
- `app/prompts/construction_expert.txt` — runtime PMC prompt

## Related

- [modular-agent-audit.md](./modular-agent-audit.md) — provenance and design decisions.
