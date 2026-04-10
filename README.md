# 🧠 Cerebrum Blocks

> **AI for Developers in 3 Lines of Code**

Build AI applications like Lego. One API key. 15 blocks. Infinite possibilities.

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

# Streaming chat
async for chunk in client.chat.stream("Explain AI in simple terms"):
    print(chunk.text, end="")
```

### JavaScript

```bash
npm install cerebrum-js
```

```javascript
import { Cerebrum } from 'cerebrum-js';

const client = new Cerebrum({ apiKey: 'cb_your_key' });

// Streaming chat
for await (const chunk of client.chatStream('Explain AI in simple terms')) {
  process.stdout.write(chunk.text);
}
```

---

## 🔑 Get Your API Key

👉 **[Get your API key](https://cerebrumblocks.com/dashboard)**

- **Free**: 1,000 requests/month
- **Pro**: $29/month, 50,000 requests
- **Enterprise**: Custom pricing

---

## 🧱 15 AI Blocks

| Block | Description |
|-------|-------------|
| 💬 **Chat** | GPT-4, Claude, Groq with streaming |
| 📄 **PDF** | Extract text, tables, images |
| 👁️ **OCR** | Image text extraction |
| 🔊 **Voice** | Text-to-speech, speech-to-text |
| 🔍 **Vector Search** | Semantic search with embeddings |
| 🖼️ **Image** | Image analysis & generation |
| 🌐 **Translate** | 100+ languages |
| 💻 **Code** | Code generation & execution |
| 🕸️ **Web** | Web scraping & browsing |
| 🔎 **Search** | Web search with multiple providers |
| 🧮 **Zvec** | Zero-shot vector embeddings |
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

# Document AI: PDF → OCR → Chat
result = await chain(client) \
    .then("pdf", {"extract": "text"}) \
    .then("ocr", {"lang": "eng"}) \
    .then("chat", {"prompt": "Extract invoice data:"}) \
    .run("invoice.pdf")

print(result.final_output)
```

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
```

### Docker

```bash
docker build -t cerebrum .
docker run -p 8000:8000 -e CEREBRUM_API_KEY=cb_key cerebrum
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

# Run
uvicorn app.main:app --reload
```

---

## 💰 Pricing

| Feature | Free | Pro $29/mo | Enterprise |
|---------|------|------------|------------|
| Requests/month | 1,000 | 50,000 | Unlimited |
| Blocks | 9 | 16 | 16 + Custom |
| Support | Community | Priority | Dedicated |
| Streaming | ✅ | ✅ | ✅ |
| Vector Search | ✅ | ✅ | ✅ |
| SLA | - | - | ✅ |

---

## 🛠️ API Endpoints

```
POST /v1/chat              # Chat completion
POST /v1/chat/stream       # Streaming chat
GET  /v1/blocks            # List blocks
POST /v1/execute           # Execute block
POST /v1/chain             # Chain blocks
POST /v1/vector/add        # Add to vector DB
POST /v1/vector/search     # Semantic search
GET  /v1/health            # Health check
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
