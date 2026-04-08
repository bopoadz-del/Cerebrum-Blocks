# AI Block System v1.0 🚀

**Build AI Like Lego** - 13 Blocks. Infinite Possibilities.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](./RENDER_DEPLOY.md)

![Blocks](https://img.shields.io/badge/Blocks-13-blue)
![Tests](https://img.shields.io/badge/Tests-Complete-green)
![Render](https://img.shields.io/badge/Render-Ready-purple)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Integrated-orange)

## 🎯 Overview

A modular AI system where each block is a fully-featured AI capability. Snap them together to build anything you can imagine.

### 9 AI Blocks
| Block | Description |
|-------|-------------|
| **PDF** | Extract text, images, and metadata from PDF files |
| **OCR** | Extract text from images using OCR |
| **Chat** | AI chat completions (OpenAI, Anthropic, local) |
| **Voice** | Speech-to-text and text-to-speech |
| **Vector Search** | Semantic search with ChromaDB ⭐ |
| **Image** | Image analysis and generation |
| **Translate** | Text translation |
| **Code** | Code execution, analysis, and transformation |
| **Web** | Web scraping and HTTP requests |

### 4 Drive Blocks
| Block | Description |
|-------|-------------|
| **Google Drive** | Full Google Drive integration |
| **OneDrive** | Microsoft OneDrive integration |
| **Local Drive** | Local filesystem operations |
| **Android Drive** | Android storage access |

---

## 🚀 Quick Start

### Option 1: Deploy to Render (Recommended)

1. Fork this repository
2. Create account on [render.com](https://render.com)
3. Click **New +** → **Web Service**
4. Connect your GitHub repo
5. Use settings:
   - **Build**: `pip install -r requirements.txt`
   - **Start**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add Disk for persistence (optional): `/app/data`
7. Deploy!

See [RENDER_DEPLOY.md](./RENDER_DEPLOY.md) for detailed instructions.

### Option 2: Local Development

```bash
# Clone
git clone <repository-url>
cd ai-block-system

# Install
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys

# Run
uvicorn app.main:app --reload
```

### Option 3: Docker

```bash
# Build
docker-compose up --build

# Or use Docker directly
docker build -t ai-block-system .
docker run -p 8000:8000 ai-block-system
```

---

## 📡 API Usage

### Health Check
```bash
curl http://localhost:8000/health
```

### List All Blocks
```bash
curl http://localhost:8000/blocks
```

### Vector Search (ChromaDB) - NEW!

```bash
# 1. Create a collection
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "block": "vector_search",
    "input": "my_documents",
    "params": {"operation": "create_collection"}
  }'

# 2. Add documents
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "block": "vector_search",
    "input": {
      "documents": [
        {"text": "Machine learning is amazing", "metadata": {"topic": "ml"}},
        {"text": "Deep learning is powerful", "metadata": {"topic": "dl"}},
        {"text": "Neural networks are cool", "metadata": {"topic": "nn"}}
      ]
    },
    "params": {"operation": "add", "collection": "my_documents"}
  }'

# 3. Search
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "block": "vector_search",
    "input": "artificial intelligence",
    "params": {"operation": "search", "collection": "my_documents", "top_k": 3}
  }'

# 4. List collections
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "block": "vector_search",
    "input": {},
    "params": {"operation": "list_collections"}
  }'

# 5. Count documents
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "block": "vector_search",
    "input": {},
    "params": {"operation": "count", "collection": "my_documents"}
  }'
```

### Execute Single Block
```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "block": "chat",
    "input": "Hello, how are you?",
    "params": {"provider": "mock"}
  }'
```

### Chain Multiple Blocks
```bash
curl -X POST http://localhost:8000/chain \
  -H "Content-Type: application/json" \
  -d '{
    "steps": [
      {"block": "ocr", "params": {"language": "eng"}},
      {"block": "vector_search", "params": {"operation": "add"}},
      {"block": "chat", "params": {"prompt": "Summarize:"}}
    ],
    "initial_input": {"image_path": "/path/to/image.png"}
  }'
```

### Drive Operations
```bash
# List files in local drive
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "block": "local_drive",
    "input": {},
    "params": {"operation": "list", "folder_path": "/"}
  }'

# Google Drive (requires auth)
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "block": "google_drive",
    "input": {},
    "params": {"operation": "list"}
  }'
```

---

## 🐍 Python SDK

```python
from app.core import CerebrumClient, chain

# Initialize client
client = CerebrumClient("http://localhost:8000")

# Vector Search Example
result = await client.execute_block(
    "vector_search",
    "machine learning",
    {
        "operation": "search",
        "collection": "my_docs",
        "top_k": 5
    }
)

# Chain blocks
result = await chain(client) \
    .then("pdf", {"extract_text": True}) \
    .then("vector_search", {"operation": "add"}) \
    .then("chat", {"prompt": "Answer based on context:"}) \
    .run("document.pdf")

print(result.final_output)
```

---

## 📁 Project Structure

```
ai-block-system/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application (Render ready)
│   ├── core/                      # Framework
│   │   ├── __init__.py
│   │   ├── block.py              # Base block class
│   │   ├── chain.py              # Block chaining
│   │   ├── client.py             # CerebrumClient SDK
│   │   └── response.py           # Standard response
│   └── blocks/                    # 13 Blocks
│       ├── __init__.py
│       ├── pdf.py                # PDF extraction
│       ├── ocr.py                # OCR text recognition
│       ├── chat.py               # AI chat
│       ├── voice.py              # STT/TTS
│       ├── vector_search.py      # ChromaDB vector search ⭐ NEW!
│       ├── image.py              # Image analysis/generation
│       ├── translate.py          # Translation
│       ├── code.py               # Code execution
│       ├── web.py                # Web scraping
│       ├── google_drive.py       # Google Drive ⭐
│       ├── onedrive.py           # OneDrive ⭐
│       ├── local_drive.py        # Local filesystem ⭐
│       └── android_drive.py      # Android storage ⭐
├── tests/                         # Comprehensive test suite
│   ├── blocks/                    # 14 test files
│   ├── integration/               # API & chain tests
│   └── run_tests.py               # Test runner
├── render.yaml                    # Render configuration
├── Dockerfile                     # Docker build
├── docker-compose.yml             # Docker compose
├── start.sh                       # Start script
├── Procfile                       # Render Procfile
├── runtime.txt                    # Python version
├── requirements.txt               # Dependencies
├── .env.example                   # Environment template
└── README.md                      # This file
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific block
pytest tests/blocks/test_vector_search.py -v

# Generate test report
python tests/run_tests.py
```

See [tests/reports/TEST_REPORT.md](tests/reports/TEST_REPORT.md)

---

## 🔐 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `PORT` | Server port | Auto on Render |
| `DATA_DIR` | Data storage path | `/app/data` |
| `CHROMA_PERSIST_DIR` | ChromaDB storage | `/app/data/chroma_db` |
| `VECTOR_COLLECTION` | Default vector collection | `default` |
| `EMBEDDING_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` |
| `OPENAI_API_KEY` | OpenAI API (for embeddings) | Optional |
| `ANTHROPIC_API_KEY` | Anthropic API | Optional |
| `GOOGLE_CREDENTIALS_PATH` | Google OAuth | For Google Drive |
| `ONEDRIVE_ACCESS_TOKEN` | MS Graph | For OneDrive |

See `.env.example` for complete list.

---

## 📚 API Documentation

Once running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🛠️ Development

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run in development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Build Docker image
docker build -t ai-block-system .
```

---

## 📄 License

MIT License

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a PR

---

## 🆕 What's New

### v1.0 - Vector Search Block
- **ChromaDB integration** for semantic document search
- **Local embeddings** with sentence-transformers
- **OpenAI embeddings** support (optional)
- **Collection management** (create, delete, list)
- **Full CRUD operations** on vector documents

**Built with ❤️ for the AI community**
