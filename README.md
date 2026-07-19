# 🧠 Cerebrum Blocks

> **Build AI Like Lego — Snap together blocks. Launch any vertical.**

Cerebrum is a **block store for AI**. Instead of building pipelines from scratch, you snap together pre-built blocks — each one a fully-working AI capability — and chain them into whatever product you need.

---

## 🏪 The Store: 94+ Blocks & 17 Domain Kits

Think of it as an app store, but every "app" is an AI block you can wire into your own system. The repo ships **76 generic platform blocks** and **17 Domain Kits** — pre-packaged vertical solutions that each bundle a container, an extraction block, a knowledge module, and typed schemas. All blocks share the same universal API:

| Category | Blocks |
|----------|--------|
| **🤖 AI Core** | `chat`, `code`, `search`, `translate`, `voice`, `web`, `zvec`, `image`, `ocr`, `pdf`, `vector_search` |
| **👁️ Vision & Media** | `image`, `ocr`, `vector_search` |
| **📄 Documents** | `pdf`, `web`, `ocr` |
| **🔌 Integrations** | `google_drive`, `onedrive`, `local_drive`, `android_drive`, `email`, `webhook`, `voice` |
| **🛡️ Infrastructure** | `memory`, `auth`, `monitoring`, `queue`, `rate_limiter`, `sandbox`, `audit`, `secrets`, `health_check`, `failover`, `event_bus` |
| **🏗️ Domain Kits** | `agriculture`, `automotive`, `aviation`, `construction`, `education`, `finance`, `hotel_management`, `hr`, `insurance`, `legal`, `manufacturing`, `medical`, `oil_gas`, `pharma`, `real_estate`, `retail`, `supply_chain` |

Each block exposes:
- One `execute()` endpoint
- A `ui_schema` so frontends auto-render inputs
- Standardized JSON output you can pass to the next block

**Swap one block. Change the provider. Chain 10 of them. It all just works.**

> Categories overlap for discoverability; totals count unique published blocks and kits.

---

## ⚡ 3-Command Quickstart

```bash
git clone https://github.com/bopoadz-del/Cerebrum-Blocks.git
cd Cerebrum-Blocks
# Optional: enable domain kits at boot
export CEREBRUM_DOMAIN_KITS=1
export CEREBRUM_VIRGIN=false
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000` and you can immediately run any block. Browse available kits at `GET /store/containers`.

---

## 🎮 The Platform: Built From Blocks

The Cerebrum Platform is **itself built from these blocks**. It is a live demo of what happens when you snap them together:

- **Chat UI** → powered by the `chat` block
- **File upload + analysis** → `pdf` → `ocr` → `chat` chain
- **Drive connect** → `local_drive` / `google_drive` / `onedrive` / `android_drive` blocks
- **ZVec indexing** → `zvec` block embeds file lists so search works across drives
- **Domain assistants** → `medical`, `legal`, `finance`, `construction`, … domain kits

### Live Architecture

| Product | What it is | Live URL |
|---------|-----------|----------|
| **Cerebrum Blocks API** | FastAPI backend + block store | [cerebrum-blocks.onrender.com](https://cerebrum-blocks.onrender.com) |

---

## 🔗 Chaining Blocks: The Killer Feature

Blocks are designed to be chained. The output of one block becomes the input of the next.

```
Input → [pdf] → text → [construction] → measurements → [chat] → answer
```

```bash
curl -X POST https://cerebrum-blocks.onrender.com/v1/chain \
  -H "Content-Type: application/json" \
  -d '{
    "steps": [
      {"block": "pdf",   "params": {"extract_text": true}},
      {"block": "construction", "params": {"action": "extract_measurements"}},
      {"block": "chat",  "params": {}}
    ],
    "initial_input": {"url": "floorplan.pdf"}
  }'
```

Another example — analyze a contract:

```bash
curl -X POST https://cerebrum-blocks.onrender.com/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"block": "legal", "params": {"action": "process_contract"}}'
```

Or search across your connected drives with ZVec:

```bash
curl -X POST https://cerebrum-blocks.onrender.com/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"block": "zvec", "input": "budget report", "params": {"operation": "search"}}'
```

---

## 📦 Full Block Catalog

### Core AI (11)
- `chat` — Multi-provider LLM chat (DeepSeek, Groq, OpenAI)
- `code` — Code execution & analysis
- `search` — Web search
- `translate` — Language translation
- `voice` — Text-to-speech & speech-to-text
- `web` — Web scraping & HTML parsing
- `zvec` — Zero-shot vector ops (embed, classify, similarity, search)
- `image` — Image analysis
- `ocr` — Text extraction from images
- `pdf` — PDF text & table extraction
- `vector_search` — Semantic search

### Drive & Storage (4)
- `google_drive` — Google Drive integration
- `onedrive` — Microsoft OneDrive integration
- `local_drive` — Local filesystem access
- `android_drive` — Android storage integration

### Infrastructure & Security (12)
- `memory` — High-speed cache with TTL
- `auth` — API key validation, RBAC
- `monitoring` — Provider leaderboard & failover prediction
- `queue` — Background job queue
- `rate_limiter` — Request throttling
- `sandbox` — Code safety validation
- `audit` — Audit event logging
- `secrets` — Secret management
- `health_check` — System health probes
- `failover` — Automatic provider switching
- `event_bus` — Cross-block messaging
- `database` — Data persistence layer

### Workflow & Communication (8)
- `email` — Email sending
- `webhook` — Webhook dispatch
- `notification` — Push / SMS alerts
- `team` — Multi-user workspaces
- `workflow` — Workflow orchestration
- `review` — Approval flows
- `documentation` — Auto-doc generation
- `version` — Block versioning

### Analytics & Discovery (7)
- `analytics` — Usage analytics
- `discovery` — Block discovery engine
- `dashboard` — Metrics dashboard
- `error_tracking` — Error aggregation
- `migration` — Schema / block migration
- `billing` — Usage tracking
- `payment_split` — Revenue sharing logic

### Domain Kits (17)
- `agriculture` — Crop health, yield, and supply-chain extraction
- `automotive` — Vehicle diagnostics, recall, and compliance analysis
- `aviation` — Maintenance logs, safety, and regulatory extraction
- `construction` — BIM, QA, progress tracking, material extraction
- `education` — Curriculum, assessment, and student-record extraction
- `finance` — Risk analysis, compliance reporting
- `hotel_management` — Booking, occupancy, and guest-service extraction
- `hr` — Resume, compliance, and workforce analytics
- `insurance` — Claims, policy, and risk extraction
- `legal` — Contract analysis, precedent matching
- `manufacturing` — Quality, production, and defect extraction
- `medical` — DICOM, HIPAA validation, clinical entities
- `oil_gas` — Well logs, safety, and regulatory extraction
- `pharma` — Trial, batch, and regulatory extraction
- `real_estate` — Property, lease, and valuation extraction
- `retail` — Inventory, pricing, and sales extraction
- `supply_chain` — Shipment, vendor, and logistics extraction

**Total: 94+ blocks across 17 verticals, all with the same universal API.**

---

## 🏗️ How It Works

```
┌─────────────────────────────────────────┐
│         Your Product / UI               │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│      Cerebrum Platform API              │
│  (FastAPI router for all blocks)        │
└─────────────┬───────────────────────────┘
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
┌───────┐ ┌───────┐ ┌───────┐
│  pdf  │ │  ocr  │ │  chat │  ← Core Blocks
└───┬───┘ └───┬───┘ └───┬───┘
    │         │         │
    └─────────┴─────────┘
              │
    ┌─────────┴─────────┐
    ▼                   ▼
┌───────────┐     ┌───────────┐
│construction│     │  medical  │  ← Domain Kits
└───────────┘     └───────────┘
```

Each block inherits from `UniversalBlock` (or `TypedBlock`/`DomainBlockV2` for schema-aware domain blocks) and implements:
- `process(input_data, params)` — the actual logic
- `execute(input_data, params)` — standardized wrapper with timing, error handling, and `source_id`

---

## 🤖 Modular Agent Pack

This repo includes a platform-agnostic agent layer under `.agent-core/`:

- **1 core agent** — shared kernel with honesty, grounding, tool-discipline, and handoff rules.
- **11 domain hats** — specialist agents that extend the core for construction-domain work.

| Agent | Role |
|---|---|
| `project-assistant` | Operator's primary chat surface |
| `construction-pm` | Schedule, procurement, risks, costs |
| `contracts-manager` | RFP, clauses, change orders, claims |
| `quantity-surveyor` | BOQ takeoff, drawing measurements, variance |
| `bim-analyst` | IFC, clash detection, model quantities |
| `document-analyst` | Generic document parsing and Q&A |
| `document-ingestion` | File intake and parser routing |
| `safety-officer` | HSE audits, risk register, incidents |
| `heavy-reasoning` | Variance synthesis and recommendations |
| `validation` | 5-stage validation and credibility tiers |
| `learning` | User corrections and coefficient tuning |

Each agent has a canonical `.md` body plus a machine-readable `.json` manifest with `description`, `examples`, `activation`, `handoffs`, and `allowed_paths`. See [`docs/agents/README.md`](docs/agents/README.md) for porting instructions.

## 🏢 Built on by CerebrumDev.ai

Cerebrum Blocks is the open-core engine behind **[CerebrumDev.ai](https://cerebrumdev.ai)** — the enterprise builder for vertical AI products. The block store is open source; CerebrumDev.ai adds hosted infrastructure, team collaboration, managed deployments, and premium enterprise kits on top.

If you are building a product on Cerebrum Blocks, you are using the same primitives that power CerebrumDev.ai.

---

## 🛠️ Store Helpers

| Script | Purpose |
|--------|---------|
| `scripts/publish_kit.py --domain <name>` | Bundle a Domain Kit (container + extraction block + knowledge module + types + shared core files) into `block_store/kits/<name>/` |
| `scripts/audit_store.py` | Inventory `app/blocks/` against published kits and flag stale files |

Publish a new domain kit:

```bash
python scripts/publish_kit.py --domain healthcare
```

---

## 🚀 Deployment

### Deploy on Render

Production uses **`app/main.py`** (not `mock_backend.py`). The repo ships a blueprint at [`render.yaml`](render.yaml) and a [`Procfile`](Procfile).

| Setting | Value |
|---------|-------|
| **Build** | `./render-build.sh` (or `pip install -r requirements.txt`) |
| **Start** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Health check** | `GET /health` |

**Required env vars** (set in Render dashboard — never commit secrets):

| Variable | Purpose |
|----------|---------|
| `ENV` | `production` |
| `CEREBRUM_MASTER_KEY` | Admin API key |
| `CEREBRUM_API_KEY_<USER>` | Per-user API keys (e.g. `CEREBRUM_API_KEY_ALICE`) |
| `CORS_ORIGINS` | SPA origin(s), comma-separated |
| `DATA_DIR` | Persistent disk mount (e.g. `/app/data`) |

**Optional env vars:**

| Variable | Purpose |
|----------|---------|
| `CEREBRUM_DOMAIN_KITS` | `1` = enable the domain-kit store |
| `CEREBRUM_VIRGIN` | `false` = auto-load domain kits at boot |
| `DATABASE_URL` | Postgres backend for the `historical_benchmark` test fixture |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | LLM providers for chat block |
| `SENTRY_DSN` | Error tracking |

The frontend is a **separate static site** on Render (build `npm run build` in `frontend/`, set `VITE_API_BASE` to the API URL). Local dev: `python mock_backend.py` on `:8000` + `npm run dev` in `frontend/` on `:5173`.

| Service | URL |
|---------|-----|
| Cerebrum Blocks API | https://cerebrum-blocks.onrender.com |

### Docker
```bash
docker compose up --build
```
Then open http://localhost:8000.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[API.md](API.md)** | Full API reference |
| **[RENDER_DEPLOY.md](RENDER_DEPLOY.md)** | Deployment guide |

---

## 🌐 Links

- **Live API:** https://cerebrum-blocks.onrender.com
- **GitHub:** https://github.com/bopoadz-del/Cerebrum-Blocks
- **Docker Hub:** https://hub.docker.com/r/bopoadz-del/cerebrum-blocks

---

**Version:** 2.1.0 — Domain Kit Store  
**Blocks:** 94+ plug & play modules  
**Domain Kits:** 17 verticals  
**Status:** 🟢 **Live, deployable, and actively hardening**

---

*One block at a time. Build anything.*
