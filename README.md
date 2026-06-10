# 🧠 Cerebrum Blocks

> **Build AI Like Lego — Snap together blocks. Launch any vertical.**

Cerebrum is a **block store for AI**. Instead of building pipelines from scratch, you snap together pre-built blocks — each one a fully-working AI capability — and chain them into whatever product you need.

---

## 🏪 The Store: 28+ Plug & Play Blocks

Think of it as an app store, but every "app" is an AI block you can wire into your own system. We ship **50+ blocks** across 6 categories, all with the same universal API:

| Category | Blocks |
|----------|--------|
| **🤖 AI Core** | `chat`, `code`, `search`, `translate`, `voice`, `web`, `zvec` |
| **👁️ Vision & Media** | `image`, `ocr`, `vector_search` |
| **📄 Documents** | `pdf`, `web`, `ocr` |
| **🔌 Integrations** | `google_drive`, `onedrive`, `local_drive`, `android_drive`, `email`, `webhook`, `voice` |
| **🛡️ Infrastructure** | `memory`, `auth`, `monitoring`, `queue`, `rate_limiter`, `sandbox`, `audit`, `secrets`, `health_check`, `failover`, `event_bus` |
| **🏗️ Domain Containers** | `construction`, `medical`, `legal`, `finance`, `security`, `ai_core`, `store` |

Each block exposes:
- One `execute()` endpoint
- A `ui_schema` so frontends auto-render inputs
- Standardized JSON output you can pass to the next block

**Swap one block. Change the provider. Chain 10 of them. It all just works.**

---

## ⚡ 3-Command Quickstart

```bash
git clone https://github.com/bopoadz-del/Cerebrum-Blocks.git
cd Cerebrum-Blocks
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000` and you can immediately run any block.

---

## 🎮 The Platform: Built From Blocks

The Cerebrum Platform is **itself built from these blocks**. It is a live demo of what happens when you snap them together:

- **Chat UI** → powered by the `chat` block
- **File upload + analysis** → `pdf` → `ocr` → `chat` chain
- **Drive connect** → `local_drive` / `google_drive` / `onedrive` / `android_drive` blocks
- **ZVec indexing** → `zvec` block embeds file lists so search works across drives
- **Domain assistants** → `construction`, `medical`, `legal`, `finance` containers

### Live Architecture

| Product | What it is | Live URL |
|---------|-----------|----------|
| **Platform API** | FastAPI backend executing 28+ blocks | [cerebrum-platform-api.onrender.com](https://cerebrum-platform-api.onrender.com) |
| **Platform UI** | Chat interface, drive connect, chain builder | [cerebrum-platform.onrender.com](https://cerebrum-platform.onrender.com) |
| **Store API** | Catalog of all blocks | [cerebrum-store-api.onrender.com](https://cerebrum-store-api.onrender.com) |
| **Store UI** | Browse and discover blocks | [cerebrum-store.onrender.com](https://cerebrum-store.onrender.com) |

---

## 🔗 Chaining Blocks: The Killer Feature

Blocks are designed to be chained. The output of one block becomes the input of the next.

```bash
curl -X POST https://cerebrum-platform-api.onrender.com/v1/chain \
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
curl -X POST https://cerebrum-platform-api.onrender.com/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"block": "legal", "params": {"action": "process_contract"}}'
```

Or search across your connected drives with ZVec:

```bash
curl -X POST https://cerebrum-platform-api.onrender.com/v1/execute \
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

### Domain Containers (7)
- `construction` — BIM, QA, progress tracking, material extraction
- `medical` — DICOM, HIPAA validation, clinical entities
- `legal` — Contract analysis, precedent matching
- `finance` — Risk analysis, compliance reporting
- `security` — Auth, rate limits, sandbox, audit
- `ai_core` — Adaptive routing & provider leaderboard
- `store` — Catalog & discovery logic

**Total: 50+ blocks, all with the same universal API.**

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
│construction│     │  medical  │  ← Domain Containers
└───────────┘     └───────────┘
```

Each block inherits from `UniversalBlock` and implements:
- `process(input_data, params)` — the actual logic
- `execute(input_data, params)` — standardized wrapper with timing, error handling, and `source_id`

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
| `CEREBRUM_VIRGIN` | `1` = skip auto-loading domain kits at boot |
| `DATABASE_URL` | Postgres for `historical_benchmark` block |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | LLM providers for chat block |
| `SENTRY_DSN` | Error tracking |

The frontend is a **separate static site** on Render (build `npm run build` in `frontend/`, set `VITE_API_BASE` to the API URL). Local dev: `python mock_backend.py` on `:8000` + `npm run dev` in `frontend/` on `:5173`.

| Service | URL |
|---------|-----|
| Platform API | https://cerebrum-platform-api.onrender.com |
| Platform UI | https://cerebrum-platform.onrender.com |
| Store API | https://cerebrum-store-api.onrender.com |
| Store UI | https://cerebrum-store.onrender.com |

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

- **Platform:** https://cerebrum-platform.onrender.com
- **Store:** https://cerebrum-store.onrender.com
- **GitHub:** https://github.com/bopoadz-del/Cerebrum-Blocks
- **Docker Hub:** https://hub.docker.com/r/bopoadz-del/cerebrum-blocks

---

**Version:** 2.0.0 — Domain Adapter Protocol  
**Blocks:** 50+ plug & play modules  
**Status:** ✅ **Production Ready**

---

*One block at a time. Build anything.*
