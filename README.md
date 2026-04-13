# 🧠 Cerebrum Blocks

> **The Domain Adapter Protocol (DAP) — An AI Operating System for Every Industry**

**One platform. Seven verticals. Infinite possibilities.**

[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-bopoadz--del%2Fcerebrum--blocks-blue?logo=docker)](https://hub.docker.com/r/bopoadz-del/cerebrum-blocks)
[![API Status](https://img.shields.io/badge/api-up-success)](https://cerebrum-platform-api.onrender.com/health)
[![Domain Containers](https://img.shields.io/badge/Domain%20Containers-7-blueviolet)]()
[![Lego Tax](https://img.shields.io/badge/Lego%20Tax-20%25-gold)]()

---

## 🏛️ Architecture: Two Products, One Ecosystem

Cerebrum Blocks is split into **2 backends + 2 frontends**:

| Product | Type | URL | Purpose |
|---------|------|-----|---------|
| **Cerebrum Platform API** | Python/FastAPI | [cerebrum-platform-api.onrender.com](https://cerebrum-platform-api.onrender.com) | Execute 22 AI blocks & domain containers |
| **Cerebrum Platform** | Static HTML | [cerebrum-platform.onrender.com](https://cerebrum-platform.onrender.com) | Chat UI, file upload, drive connect, chain builder |
| **Cerebrum Store API** | Python/FastAPI | [cerebrum-store-api.onrender.com](https://cerebrum-store-api.onrender.com) | Block catalog, marketplace, reviews |
| **Cerebrum Store** | Static HTML | [cerebrum-store.onrender.com](https://cerebrum-store.onrender.com) | Browse & purchase domain containers |

> **Platform** = Where you *run* blocks.  
> **Store** = Where you *buy* new domain containers.

---

## 🎯 What We Built

**Not a product. A protocol.**

```
Layer 0  Infrastructure    ← HAL, Config, Memory, Database    [UNIVERSAL]
Layer 1  Security          ← Auth, Secrets, Rate Limiter      [UNIVERSAL]
Layer 2  AI Core           ← Router, Failover, Leaderboard    [UNIVERSAL]
Layer 3  [YOUR DOMAIN]     ← Construction, Medical, Legal     [SWAP THIS]
Layer 4  Store             ← Discovery, Reviews, Payments     [UNIVERSAL]
Layer 5  Event Bus         ← Cross-container messaging        [UNIVERSAL]
```

**Swap Layer 3 → New Industry:**

| Industry | Container | Price | Status |
|----------|-----------|-------|--------|
| 🏗️ **Construction** | BIM, QA, Progress | $299/mo | ✅ LIVE |
| 🏥 **Medical** | DICOM, HIPAA, Clinical | $499/mo | ✅ LIVE |
| ⚖️ **Legal** | Contracts, Precedents | $399/mo | ✅ LIVE |
| 💰 **Finance** | Risk, Compliance | $599/mo | ✅ LIVE |
| 🎓 Education | *(coming)* | $199/mo | 📝 Roadmap |
| 🏛️ Government | *(coming)* | $799/mo | 📝 Roadmap |
| 🛒 Retail | *(coming)* | $249/mo | 📝 Roadmap |

**Same 5 layers. One container swap. New $B industry.**

---

## ⚡ Quickstart

### 3-Minute Construction AI Chain

```bash
curl -X POST https://cerebrum-platform-api.onrender.com/v1/chain \
  -H "Content-Type: application/json" \
  -d '{
    "steps": [
      {"block": "construction", "params": {"action": "extract_measurements"}},
      {"block": "ai_core", "params": {"action": "route"}},
      {"block": "construction", "params": {"action": "generate_report"}}
    ],
    "initial_input": {"url": "floorplan.pdf"}
  }'
```

### Medical Chain (HIPAA-Compliant)

```bash
curl -X POST https://cerebrum-platform-api.onrender.com/v1/chain \
  -H "Content-Type: application/json" \
  -d '{
    "steps": [
      {"block": "security", "params": {"action": "auth"}},
      {"block": "medical", "params": {"action": "process_dicom"}},
      {"block": "medical", "params": {"action": "extract_entities"}},
      {"block": "medical", "params": {"action": "validate"}}
    ],
    "initial_input": {}
  }'
```

### Legal Contract Analysis

```bash
curl -X POST https://cerebrum-platform-api.onrender.com/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "block": "legal",
    "params": {"action": "process_contract"}
  }'
```

---

## 🏗️ Architecture: The 5+1 Model

**5 Universal Layers** (never change)
1. **Infrastructure** — HAL, databases, memory, configuration
2. **Security** — Auth, secrets, rate limiting, audit
3. **AI Core** — Adaptive routing, failover, provider leaderboard
4. **Store** — Block discovery, reviews, Lego Tax (20%)
5. **Event Bus** — Cross-container messaging (Block 42)

**1 Swappable Layer** (your product)
- **Layer 3** — Domain-specific containers

### How to Create a New Vertical

1. **Copy the template:**
```python
from app.core.block import BaseBlock, BlockConfig

class MyDomainContainer(BaseBlock):
    """Your domain container"""
    
    async def process_document(self, input_data, params): ...
    async def extract_entities(self, input_data, params): ...
    async def validate(self, input_data, params): ...
    async def generate_report(self, input_data, params): ...
```

2. **Implement the 5 required methods**
3. **Register in BLOCK_REGISTRY**
4. **Publish to Store** → Collect 80% of revenue

See **[DOMAIN_CONTAINER_SPEC.md](DOMAIN_CONTAINER_SPEC.md)** for the complete specification.

---

## 💰 Economics: The Lego Tax

**Platform takes 20%. Creator keeps 80%.**

| Domain Pack | Monthly Price | Platform (20%) | Creator (80%) |
|-------------|---------------|----------------|---------------|
| Construction | $299 | $59.80 | $239.20 |
| Medical | $499 | $99.80 | $399.20 |
| Legal | $399 | $79.80 | $319.20 |
| Finance | $599 | $119.80 | $479.20 |

**Community builds the verticals. You collect the Lego Tax.**

---

## 📦 Available Blocks (22 Total)

### Core AI Blocks (15)
| Block | Description |
|-------|-------------|
| 💬 **chat** | Multi-provider AI (DeepSeek, Groq, GPT-4) with streaming |
| 📄 **pdf** | PDF text/table extraction |
| 👁️ **ocr** | Image text extraction |
| 🔊 **voice** | Text-to-speech, speech-to-text |
| 🔍 **vector_search** | Semantic search with ChromaDB |
| 🖼️ **image** | Image analysis |
| 🌐 **translate** | 100+ languages |
| 💻 **code** | Code generation |
| 🌐 **web** | Web scraping |
| 🔎 **search** | Web search |
| 🔗 **zvec** | Zero-vector ops |
| 📁 **google_drive** | Google Drive integration |
| 📁 **onedrive** | OneDrive integration |
| 📁 **local_drive** | Local file system |
| 📁 **android_drive** | Android storage |

### Domain Containers (7)
| Container | Domain | Key Features | Revenue |
|-----------|--------|--------------|---------|
| 🏗️ **construction** | AEC Industry | BIM, PDF extraction, QA inspection, progress tracking | $299/mo |
| 🏥 **medical** | Healthcare | DICOM processing, clinical entities, HIPAA validation | $499/mo |
| ⚖️ **legal** | Law Firms | Contract analysis, precedent validation, brief generation | $399/mo |
| 💰 **finance** | Trading/Banking | Risk analysis, SOX/MiFID compliance, regulatory reporting | $599/mo |
| 🔐 **security** | Platform | Auth, rate limiting, sandbox, audit | Platform |
| 🤖 **ai_core** | Platform | Adaptive routing, failover, leaderboard | Platform |
| 🏪 **store** | Platform | Discovery, reviews, payment split | Platform |

---

## 🔐 Security: Layer 1 Fortress

```bash
# Generate API key
POST /execute {"block": "security", "params": {"action": "create_key"}}
# → {"api_key": "cb_abc123...", "role": "admin"}

# Check rate limit
POST /execute {"block": "security", "params": {"action": "check_rate", "key": "user_123"}}
# → {"allowed": true, "remaining": 95, "reset_at": ...}

# Sandbox validation
POST /execute {"block": "security", "params": {"action": "sandbox_check", "code": "exec('rm -rf /')"}}
# → {"safe": false, "violations": ["exec("]}
```

---

## 🤖 AI Core: Layer 2 Brain

```bash
# Provider leaderboard (auto-updated)
POST /execute {"block": "ai_core", "params": {"action": "leaderboard"}}
# → {
#   "rankings": [
#     {"provider": "deepseek", "score": 99.3, "latency_ms": 89},
#     {"provider": "groq", "score": 98.7, "latency_ms": 45},
#     {"provider": "openai", "score": 97.5, "latency_ms": 234}
#   ]
# }

# Adaptive routing
POST /execute {"block": "ai_core", "params": {"action": "route", "quality": "fast"}}
# → {"selected_provider": "groq", "estimated_cost": 0.00059}
```

---

## 🏪 Block Store: Separate Marketplace Service

The Store is a **standalone marketplace** (not part of the execution Platform).

```bash
# Store catalog stats
curl https://cerebrum-store-api.onrender.com/health
# → {"status":"healthy","service":"store","blocks":3}
```

Inside the **Platform**, the `store` container provides:

```bash
# Platform stats
POST /v1/execute {"block": "store", "params": {"action": "platform_stats"}}
# → {
#   "total_blocks": 22,
#   "published_blocks": 15,
#   "total_reviews": 847,
#   "avg_rating": 4.7
# }

# Purchase with Lego Tax
POST /v1/execute {"block": "store", "params": {"action": "purchase", "price_cents": 49900}}
# → {"platform_fee": "$99.80", "creator_earns": "$399.20"}
```

---

## 🚀 Deployment

### Render (Production)
Pushing to `main` auto-deploys **both** the Platform and the Store:

```bash
git push origin main
```

| Service | Live URL |
|---------|----------|
| Platform API | https://cerebrum-platform-api.onrender.com |
| Platform UI | https://cerebrum-platform.onrender.com |
| Store API | https://cerebrum-store-api.onrender.com |
| Store UI | https://cerebrum-store.onrender.com |

### Docker (Platform Only)
```bash
docker pull bopoadz-del/cerebrum-blocks:latest
docker run -p 8000:8000 -e API_KEY=cb_xxx bopoadz-del/cerebrum-blocks
```

Then open http://localhost:8000 for the Platform UI.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[API.md](API.md)** | Complete API reference |
| **[DOMAIN_CONTAINER_SPEC.md](DOMAIN_CONTAINER_SPEC.md)** | Build your own vertical |
| **[DEPLOYMENT.md](RENDER_DEPLOY.md)** | Deployment guide |

---

## 🎓 SDKs

### Python
```bash
pip install cerebrum-sdk
```

### JavaScript
```bash
npm install cerebrum-js
```

---

## 💡 Revenue Projection

| Stream | Units | ARPU | Monthly |
|--------|-------|------|---------|
| Construction Pro | 50 | $299 | $14,950 |
| Medical Pro | 30 | $499 | $14,970 |
| Legal Pro | 40 | $399 | $15,960 |
| Finance Pro | 20 | $599 | $11,980 |
| **Platform Fee (20%)** | | | **$11,572** |

**Plus:** Community-built verticals × 20% Lego Tax

---

## 🌐 Links

- **Platform UI:** https://cerebrum-platform.onrender.com
- **Platform API Health:** https://cerebrum-platform-api.onrender.com/health
- **Store UI:** https://cerebrum-store.onrender.com
- **Store API Health:** https://cerebrum-store-api.onrender.com/health
- **GitHub:** https://github.com/bopoadz-del/Cerebrum-Blocks
- **Docker Hub:** https://hub.docker.com/r/bopoadz-del/cerebrum-blocks

---

## 🏆 Status

**Version:** 2.0.0 — Domain Adapter Protocol  
**Blocks:** 22 (15 core + 7 containers)  
**Layers:** 5 universal + 1 swappable  
**Revenue Model:** Lego Tax (20% platform, 80% creator)  
**Status:** ✅ **PRODUCTION + ECOSYSTEM READY**

---

*One container swap. Infinite markets. The Domain Adapter Protocol.*
