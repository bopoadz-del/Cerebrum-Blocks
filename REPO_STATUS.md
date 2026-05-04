# Cerebrum Blocks — Repository Status

> **Date:** 2026-05-04  
> **Branch:** main  
> **Blocks:** 65 registered  
> **Tests:** 187 passed, 79 skipped, 0 failed

---

## Architecture

**MCP-as-Contract + Direct Execution**

| Layer | Component | Purpose |
|-------|-----------|---------|
| **Contract** | `UniversalBlock.mcp_tools()` | Every block declares MCP schema |
| **Discovery** | `MCPRegistry` | Capability discovery for orchestrator |
| **Performance** | Direct `.execute()` | Orchestrator calls blocks directly (~1-5ms) |
| **External API** | `/mcp/sse` + `/mcp/messages/` | Clients use standard MCP over HTTP |

---

## Registered Blocks (65)

### Document Extraction (7)
| Block | Status | Needs |
|-------|--------|-------|
| `pdf` | ✅ Real | File upload |
| `pdf_v2` | ✅ Real | File upload |
| `ocr` | ✅ Real | Image file + Tesseract |
| `ocr_v2` | ✅ Real | Image file + Tesseract |
| `image` | ✅ Real | API key (Stability/Anthropic) |
| `document_engine` | ✅ Real | File upload |
| `capture` | ✅ Real | Image input + Anthropic/OCR |

### AI / Language (7)
| Block | Status | Needs |
|-------|--------|-------|
| `chat` | ✅ Real | DEEPSEEK_API_KEY or ANTHROPIC_API_KEY |
| `translate` | ✅ Real | No key needed |
| `voice` | ✅ Real | No key needed |
| `web` | ✅ Real | No key needed |
| `search` | ✅ Real | DuckDuckGo free (Brave/Serper optional) |
| `llm_enhancer` | ✅ Real | No key needed |
| `code` | ✅ Real | No key needed |

### Construction Intelligence (13)
| Block | Status | Needs |
|-------|--------|-------|
| `construction` | ✅ Real | Text/file input |
| `construction_v2` | ✅ Real | Text/file input |
| `boq_processor` | ✅ Real | BOQ data |
| `bim` | ✅ Real | IFC/JSON input |
| `bim_extractor` | ✅ Real | IFC file |
| `drawing_qto` | ✅ Real | DXF file |
| `primavera_parser` | ✅ Real | XER file |
| `spec_analyzer` | ✅ Real | PDF/text input |
| `formula_executor` | ✅ Real | Formula string |
| `sympy_reasoning` | ✅ Real | Math expression |
| `historical_benchmark` | ✅ Real | Cost data |
| `smart_orchestrator` | ✅ Real | Construction data |
| `recommendation_template` | ✅ Real | Project data |

### File Access (6)
| Block | Status | Needs |
|-------|--------|-------|
| `local_drive` | ✅ Real | Local filesystem |
| `google_drive` | ✅ Real | GOOGLE OAuth credentials |
| `onedrive` | ✅ Real | ONEDRIVE OAuth credentials |
| `android_drive` | ✅ Real | No key needed |
| `storage` | ✅ Real | Local/memory backend |
| `file_hasher` | ✅ Real | File path |

### Search & Memory (4)
| Block | Status | Needs |
|-------|--------|-------|
| `vector_search` | ✅ Real | No key needed |
| `zvec` | ✅ Real | No key needed |
| `cache_manager` | ✅ Real | No key needed |
| `context_broker` | ✅ Real | No key needed |

### Integration (7)
| Block | Status | Needs |
|-------|--------|-------|
| `capture` | ✅ Real | Image + Anthropic/OCR |
| `agent_swarm` | ✅ Real | DeepSeek/Anthropic/Ollama |
| `workflow` | ✅ Real | Workflow definition |
| `knowledge` | ✅ Real | DeepSeek/OpenRouter |
| `orchestrator` | ✅ Real | Chain definition |
| `queue` | ✅ Real | Redis optional (memory fallback) |
| `webhook` | ✅ Real | URL endpoint |

### Platform / Admin (10)
| Block | Status | Needs |
|-------|--------|-------|
| `auth` | ✅ Real | No key needed |
| `audit` | ✅ Real | No key needed |
| `team` | ✅ Real | No key needed |
| `version` | ✅ Real | No key needed |
| `health_check` | ✅ Real | No key needed |
| `monitoring` | ✅ Real | No key needed |
| `rate_limiter` | ✅ Real | No key needed |
| `validation` | ✅ Real | No key needed |
| `error_tracking` | ✅ Real | No key needed |
| `dashboard` | ✅ Real | No key needed |

### Communication (1)
| Block | Status | Needs |
|-------|--------|-------|
| `webhook` | ✅ Real | URL endpoint |

### Intelligence / Analytics (4)
| Block | Status | Needs |
|-------|--------|-------|
| `analytics` | ✅ Real | No key needed |
| `discovery` | ✅ Real | No key needed |
| `learning_engine` | ✅ Real | No key needed |
| `dashboard` | ✅ Real | No key needed |

### Utilities (7)
| Block | Status | Needs |
|-------|--------|-------|
| `code` | ✅ Real | No key needed |
| `sandbox` | ✅ Real | No key needed |
| `async_processor` | ✅ Real | No key needed |
| `failover` | ✅ Real | No key needed |
| `traffic_manager` | ✅ Real | No key needed |
| `adaptive_router` | ✅ Real | No key needed |
| `jetson_gateway` | ✅ Real | No key needed |

### Marketplace (3)
| Block | Status | Needs |
|-------|--------|-------|
| `review` | ✅ Real | No key needed |
| `payment_split` | ✅ Real | No key needed |
| `documentation` | ✅ Real | No key needed |

---

## Removed Blocks

| Block | Reason |
|-------|--------|
| `notification` | Replaced by MCP server communication |
| `email` | SMTP/SendGrid env dependencies |
| `billing` | Stripe env dependencies |

---

## Environment Variables (Render)

### ✅ Present
| Variable | Used By |
|----------|---------|
| `ANTHROPIC_API_KEY` | chat, capture, image, agent_swarm |
| `DEEPSEEK_API_KEY` | chat, capture, agent_swarm, knowledge |
| `TELEGRAM_BOT_TOKEN` | (unused after notification removal) |
| `GITHUB_TOKEN` | (unused) |
| `CEREBRUM_MASTER_KEY` | auth |
| `ENV` | production mode |
| `DATA_DIR` | file storage |
| `API_BASE_URL` | generated links |

### ❌ Missing (blocks return clear errors)
| Variable | Used By |
|----------|---------|
| `STABILITY_API_KEY` | image generation |
| `GOOGLE_CLIENT_ID/SECRET/REFRESH_TOKEN` | google_drive |
| `ONEDRIVE_CLIENT_ID/SECRET/REFRESH_TOKEN` | onedrive |
| `BRAVE_API_KEY` | search (Brave instead of DuckDuckGo) |
| `OPENROUTER_API_KEY` | agent_swarm, knowledge fallback |

---

## Optional Libraries

| Library | Status | Needed By |
|---------|--------|-----------|
| Tesseract | ✅ Installed | ocr, capture |
| ifcopenshell | ✅ Installed | bim_extractor |
| ezdxf | ✅ Installed | drawing_qto |
| pypdf | ❌ Not installed | pdf, document_engine |
| opencv-python-headless | ❌ Not installed | capture, image, ocr |

---

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /execute` | Execute any block |
| `POST /chain` | Execute block chain |
| `POST /chat` | Chat completions |
| `GET /health` | Health check (68 blocks loaded) |
| `GET /blocks` | List all blocks |
| `/mcp/sse` | MCP SSE transport |
| `/mcp/messages/` | MCP message endpoint |

---

## Known Issues

1. **API keys out of credits** — DeepSeek and Anthropic keys need refill
2. **pypdf not installed** — PDF parsing uses fallback (add to requirements.txt)
3. **opencv not installed** — Image processing uses fallback (add to requirements.txt)

---

## Test Results

```
187 passed, 79 skipped, 0 failed
```

---

## Render Deployment

- **Service:** `cerebrum-platform-api` (srv-d7dd87n7f7vs73es12kg)
- **Status:** Live
- **Build:** `pip install -r requirements.txt`
- **Start:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **MCP Server:** Mounted at `/mcp`
