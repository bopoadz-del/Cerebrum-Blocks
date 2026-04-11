# 🧠 Cerebrum Blocks

> **AI for Developers in 3 Lines of Code**

Build AI applications like Lego. One API key. 23+ blocks. Infinite possibilities.

[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-bopoadz--del%2Fcerebrum--blocks-blue?logo=docker)](https://hub.docker.com/r/bopoadz-del/cerebrum-blocks)
[![API Status](https://img.shields.io/badge/api-up-success)](https://cerebrum-blocks.onrender.com/v1/health)

---

## ⚡ Quickstart

### Python

```bash
pip install cerebrum-sdk
```

```python
from cerebrum_sdk import Cerebrum

client = Cerebrum(api_key="cb_your_key")

# Streaming chat with DeepSeek (cheapest LLM!)
async for chunk in client.chat.stream("Explain AI in simple terms", provider="deepseek"):
    print(chunk.text, end="")
```

### JavaScript

```bash
npm install cerebrum-js
```

```javascript
import { Cerebrum } from 'cerebrum-js';

const client = new Cerebrum({ apiKey: 'cb_your_key' });

// Streaming chat with DeepSeek (cheapest LLM!)
for await (const chunk of client.chatStream('Explain AI in simple terms', { provider: 'deepseek' })) {
  process.stdout.write(chunk.text);
}
```

### cURL

```bash
# Chat with DeepSeek - $0.14/M tokens (5x cheaper than OpenAI!)
curl -X POST https://cerebrum-blocks.onrender.com/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello!",
    "model": "deepseek-chat",
    "provider": "deepseek"
  }'
```

---

## 🔥 DeepSeek - The Cheapest LLM

**Default Provider: DeepSeek** - Only **$0.14/M input tokens** ($0.28/M output)

| Provider | Input Price | Output Price | Speed | Best For |
|----------|-------------|--------------|-------|----------|
| 🏆 **DeepSeek** | **$0.14/M** | **$0.28/M** | Fast | **Default - Best value** |
| Groq | $0.59/M | $0.79/M | Fastest | Speed critical |
| OpenAI GPT-4 | $2.50/M | $10.00/M | Medium | Complex reasoning |
| OpenAI GPT-3.5 | $0.50/M | $1.50/M | Fast | General tasks |
| Anthropic Claude | $0.80/M | $2.40/M | Medium | Long context |

**DeepSeek is 5x cheaper than GPT-3.5 and 18x cheaper than GPT-4!**

---

## 🔑 Get Your API Key

👉 **[Get your API key](https://cerebrumblocks.com/dashboard)**

- **Free**: 1,000 requests/month
- **Pro**: $29/month, 50,000 requests
- **Enterprise**: Custom pricing

---

## 🧱 23+ AI Blocks

### Core AI Blocks
| Block | Description |
|-------|-------------|
| 💬 **Chat** | DeepSeek (cheapest!), Groq (fastest), GPT-4, Claude - with streaming |
| 📄 **PDF** | Extract text, tables, images with OCR support |
| 👁️ **OCR** | Image text extraction with Tesseract |
| 🔊 **Voice** | Text-to-speech, speech-to-text |
| 🔍 **Vector** | ChromaDB semantic search with sentence-transformers |
| 🖼️ **Image** | Image analysis & generation |
| 🌐 **Translate** | 100+ languages with Google Translate |
| 💻 **Code** | Code generation & execution |
| 🕸️ **Web** | Web scraping & browsing |
| 🔎 **Search** | Web search with multiple providers |
| 🧮 **Zvec** | Zero-shot vector embeddings |

### Infrastructure Blocks
| Block | Description |
|-------|-------------|
| 🔧 **HAL** | Hardware Abstraction Layer - auto-detects cloud/edge/local |
| ⚙️ **Config** | Centralized configuration management with profile support |
| 🧠 **Memory** | High-speed cache with TTL & LRU eviction |
| 📊 **Monitoring** | Provider leaderboard & predictive failover |
| 🔐 **Auth** | API keys, rate limiting, RBAC (admin/pro/basic/readonly) |
| 📬 **Queue** | Async job processing (Redis/memory) |
| 💾 **Storage** | Multi-backend file storage (local/cloud) |
| 🛡️ **Failover** | Circuit breaker, failure counting, route switching |

### Integration Blocks
| Block | Description |
|-------|-------------|
| 🏗️ **BIM** | IFC/DWG/PDF parsing with ifcopenshell & ezdxf |
| 🗄️ **Database** | SQL/NoSQL database operations |
| 📧 **Email** | Send/receive emails with SMTP/IMAP |
| 🎯 **Webhook** | Incoming/outgoing webhook handlers |
| ⚡ **Workflow** | Workflow orchestration & automation |
| 💰 **Billing** | Usage tracking & billing management |

### Storage Blocks
| Block | Description |
|-------|-------------|
| 📁 **Google Drive** | Cloud file processing |
| ☁️ **OneDrive** | Microsoft integration |
| 💾 **Local Drive** | Local file processing |
| 📱 **Android Drive** | Android storage access |

---

## 🔗 Chain Blocks Together

Build complex AI pipelines by chaining blocks:

```python
from cerebrum_sdk import Cerebrum, chain

client = Cerebrum(api_key="cb_your_key")

# Document AI: PDF → OCR → Chat (using DeepSeek - cheapest!)
result = await chain(client) \
    .then("pdf", {"extract": "text"}) \
    .then("ocr", {"lang": "eng"}) \
    .then("chat", {"prompt": "Extract invoice data:", "provider": "deepseek"}) \
    .run("invoice.pdf")

print(result.final_output)
```

---

## 🏗️ Infrastructure Deep Dive

### 🔧 HAL Block
Auto-detects hardware environment and selects optimal configuration profile.

```python
# HAL automatically detects your environment
# cloud_render, cloud_aws, edge_jetson, local_gpu, local_std
profile = await client.hal.detect()
print(f"Running on: {profile}")  # "cloud_render" or "edge_jetson"
```

### 🧠 Memory Block
High-speed in-memory cache with TTL and LRU eviction. Perfect for edge deployments without Redis.

```python
# Store with 60s TTL
await client.memory.set("key", {"data": "value"}, ttl=60)

# Retrieve
result = await client.memory.get("key")

# Stats
stats = await client.memory.stats()
print(f"Hit rate: {stats['hit_rate']}%")
```

### 📊 Monitoring Block
Provider reliability leaderboard with predictive failover. Automatically routes to the best AI provider.

```bash
# Get provider rankings
curl https://cerebrum-blocks.onrender.com/v1/leaderboard \
  -H "Authorization: Bearer cb_your_key"
```

Response:
```json
{
  "leaderboard": [
    {"rank": 1, "name": "DeepSeek", "reliability_score": 96.5, "status": "excellent"},
    {"rank": 2, "name": "Groq", "reliability_score": 94.2, "status": "excellent"}
  ]
}
```

### 🔐 Auth Block
Multi-tenant API key management with role-based access control.

| Role | Rate Limit | Blocks |
|------|------------|--------|
| Admin | 1M/hour | All + user management |
| Pro | 50K/hour | All AI blocks |
| Basic | 1K/hour | Core blocks only |
| Readonly | 500/hour | View-only access |

```bash
# Create API key (admin only)
curl -X POST https://cerebrum-blocks.onrender.com/v1/auth/keys \
  -H "Authorization: Bearer cb_admin_key" \
  -d '{"name": "production", "role": "pro"}'
```

### 🛡️ Failover Block
Circuit breaker pattern with automatic failure detection and route switching.

```python
# Automatic provider failover
result = await client.chat.complete(
    "Hello!",
    failover=True  # Auto-switches if provider fails
)
```

---

## 🏗️ BIM Block (NEW!)
Real BIM/CAD file processing with native parsing:

```python
# Parse IFC file
result = await client.bim.process({
    "file_path": "/path/to/model.ifc",
    "action": "extract_metadata"
})
print(result["schema"])  # "IFC4"
print(result["entities"])  # 15420

# Parse DWG file
result = await client.bim.process({
    "file_path": "/path/to/drawing.dwg",
    "action": "extract_metadata"
})
```

**Supported formats:** IFC (via ifcopenshell), DWG (via ezdxf), PDF drawings (via OCR)

---

## 📚 Documentation

- **[Full Documentation](https://docs.cerebrumblocks.com)**
- **[API Reference](https://docs.cerebrumblocks.com/api)**
- **[Python SDK](https://github.com/bopoadz-del/cerebrum-blocks/tree/main/packages/python)**
- **[JavaScript SDK](https://github.com/bopoadz-del/cerebrum-blocks/tree/main/packages/js)**

---

## 🚀 Deploy Your Own

### Render (Recommended)

```yaml
# render.yaml
services:
  - type: web
    name: cerebrum-api
    env: python
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DEEPSEEK_API_KEY
        sync: false
      - key: GROQ_API_KEY
        sync: false
```

### Docker

```bash
docker build -t cerebrum .
docker run -p 8000:8000 \
  -e DEEPSEEK_API_KEY=your_key \
  -e CEREBRUM_API_KEY=cb_key \
  cerebrum
```

### Local Development

```bash
# Clone
git clone https://github.com/bopoadz-del/cerebrum-blocks.git
cd cerebrum-blocks

# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set DeepSeek API key (get one at platform.deepseek.com)
export DEEPSEEK_API_KEY=your_key

# Run
uvicorn app.main:app --reload
```

---

## 💰 Pricing

| Feature | Free | Pro $29/mo | Enterprise |
|---------|------|------------|------------|
| Requests/month | 1,000 | 50,000 | Unlimited |
| Blocks | 23+ | 23+ | 23+ + Custom |
| DeepSeek Access | ✅ | ✅ | ✅ |
| Streaming | ✅ | ✅ | ✅ |
| Vector Search | ✅ | ✅ | ✅ |
| BIM Processing | ✅ | ✅ | ✅ |
| Support | Community | Priority | Dedicated |
| SLA | - | - | ✅ |

---

## 🛠️ API Endpoints

### AI Blocks
```
POST /v1/chat              # Chat completion (DeepSeek default)
POST /v1/chat/stream       # Streaming chat
GET  /v1/blocks            # List blocks
POST /v1/execute           # Execute block
POST /v1/chain             # Chain blocks
POST /v1/vector/add        # Add to vector DB
POST /v1/vector/search     # Semantic search
POST /v1/bim/process       # BIM/CAD processing
```

### Infrastructure Blocks
```
GET  /v1/leaderboard       # Provider reliability rankings
GET  /v1/recommend         # AI-powered provider selection
GET  /v1/predict           # Predictive failure analysis
GET  /v1/system/health     # Full system health report
GET  /v1/memory/stats      # Cache statistics
POST /v1/memory/{action}   # Cache operations (get/set/delete)
POST /v1/auth/validate     # Validate API key
POST /v1/auth/keys         # Create API key (admin)
GET  /v1/auth/keys         # List API keys
POST /v1/auth/check        # Check permission
GET  /v1/hal/profile       # Get hardware profile
GET  /v1/failover/status   # Failover system status
```

### Health
```
GET  /v1/health            # Health check
```

### Example: Chat with DeepSeek

```bash
curl -X POST https://cerebrum-blocks.onrender.com/v1/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer cb_your_key" \
  -d '{
    "message": "Explain quantum computing",
    "model": "deepseek-chat",
    "provider": "deepseek"
  }'
```

Response:
```json
{
  "text": "Quantum computing uses quantum bits (qubits)...",
  "model": "deepseek-chat",
  "provider": "deepseek"
}
```

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with 💜 by the Cerebrum Team<br>
  <a href="https://cerebrumblocks.com">cerebrumblocks.com</a>
</p>
