# Cerebrum Blocks

**Build AI like Lego.** One API. 13 blocks. Zero setup.

```bash
pip install cerebrum-blocks
```

```python
from cerebrum import CerebrumClient

client = CerebrumClient(api_key="your-key")
response = client.chat("Explain quantum computing in 3 sentences")
print(response.text)
```

---

## 3-Line Quickstart

```bash
pip install cerebrum-blocks
export CEREBRUM_API_KEY=your-key
python -c "from cerebrum import CerebrumClient; print(CerebrumClient().chat('Hello!').text)"
```

---

## What You Get

| Block | What It Does |
|-------|-------------|
| **chat** | OpenAI, Anthropic, local LLMs — with streaming |
| **vector_search** | Semantic search with ChromaDB |
| **image** | Analyze and generate images |
| **ocr** | Extract text from images |
| **pdf** | Extract text, images, metadata from PDFs |
| **voice** | Speech-to-text & text-to-speech |
| **translate** | Text translation |
| **code** | Execute and analyze code |
| **web** | Scrape and fetch web content |
| **search** | Web search (Serper, DuckDuckGo) |
| **google_drive** | Read/write Google Drive |
| **onedrive** | Read/write Microsoft OneDrive |
| **local_drive** | Local filesystem operations |
| **android_drive** | Android storage access |

---

## Python SDK

```bash
pip install cerebrum-blocks
```

```python
from cerebrum import CerebrumClient

client = CerebrumClient(api_key="your-key")

# Chat with streaming
for chunk in client.chat.stream("Tell me a story"):
    print(chunk.text, end="")

# Vector search
client.vector_search.add(documents=[
    {"text": "Python is great", "metadata": {"topic": "python"}},
    {"text": "JavaScript is versatile", "metadata": {"topic": "js"}}
], collection="docs")

results = client.vector_search.query(
    "What language should I learn?",
    collection="docs",
    top_k=2
)

# Chain blocks
from cerebrum import chain

result = chain(client) \
    .then("ocr") \
    .then("vector_search", {"operation": "add"}) \
    .then("chat", {"prompt": "Summarize this:"}) \
    .run("/path/to/image.png")
```

---

## JavaScript SDK

```bash
npm install cerebrum-blocks
```

```javascript
import { CerebrumClient } from 'cerebrum-blocks';

const client = new CerebrumClient({ apiKey: 'your-key' });

// Chat
const response = await client.chat("Hello!");
console.log(response.text);

// Chat with streaming
const stream = await client.chat.stream("Tell me a story");
for await (const chunk of stream) {
    process.stdout.write(chunk.text);
}

// Vector search
await client.vectorSearch.add({
    documents: [
        { text: "Python is great", metadata: { topic: "python" } },
    ],
    collection: "docs"
});

const results = await client.vectorSearch.query({
    query: "What language should I learn?",
    collection: "docs",
    topK: 2
});
```

---

## Self-Host (Optional)

Don't want to use our API? Run your own instance:

```bash
git clone https://github.com/bopoadz-del/cerebrum-blocks.git
cd cerebrum-blocks
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Or deploy to Render in one click:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](./RENDER_DEPLOY.md)

---

## API Reference

### Authentication

All requests require an API key header:

```bash
curl https://api.cerebrumblocks.com/v1/chat \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/chat` | POST | Chat completions |
| `/v1/chat/stream` | POST | Streaming chat |
| `/v1/vector/search` | POST | Semantic search |
| `/v1/vector/add` | POST | Add documents |
| `/v1/blocks` | GET | List all blocks |
| `/v1/health` | GET | Health check |

See full docs at [docs.cerebrumblocks.com](https://docs.cerebrumblocks.com)

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CEREBRUM_API_KEY` | Your API key (for SDK) |
| `CEREBRUM_BASE_URL` | Custom endpoint (default: `https://api.cerebrumblocks.com`) |

---

## Project Structure

```
cerebrum-blocks/
├── app/                    # FastAPI server
│   ├── main.py            # API entry point
│   ├── core/              # Framework (block, chain, client)
│   └── blocks/            # 13 block implementations
├── sdk/                   # Python SDK source
│   └── cerebrum/          # PyPI package
├── js-sdk/                # JavaScript SDK source
│   └── src/               # npm package
├── tests/                 # Test suite
├── render.yaml            # Render deployment config
└── Dockerfile             # Docker image
```

---

## Contributing

1. Fork the repo
2. Create a feature branch
3. Add tests
4. Submit a PR

---

## License

MIT
