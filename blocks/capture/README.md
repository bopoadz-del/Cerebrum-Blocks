# Cerebrum Capture Block

Universal image capture block. Any client pushes an image → OCR → AI structuring → vector DB.

## What it does

```
Image (any client)
    ↓
POST /capture/upload
    ↓
OCR (Tesseract, Arabic + English)
    ↓
Raw text
    ↓
AI structuring (Ollama / OpenRouter / OpenAI)
    ↓
Entities, tags, summary, clean text
    ↓
Vector DB store
    ↓
JSON response: capture_id + extracted data
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/capture/upload` | POST | Full pipeline: image → OCR → AI → store |
| `/capture/ocr` | POST | OCR only: image → raw text |
| `/capture/structure` | POST | AI only: raw text → structured JSON |
| `/capture/search` | POST | Semantic search across stored captures |

### Upload

```bash
curl -X POST http://localhost:8000/capture/upload \
  -H "Authorization: Bearer test-key" \
  -F "file=@screenshot.png" \
  -F "source=ksnip" \
  -F "user_id=desktop-01"
```

Response:
```json
{
  "capture_id": "a1b2c3d4",
  "status": "success",
  "source": "ksnip",
  "raw_text": "Invoice #12345\nTotal: $500.00",
  "clean_text": "Invoice #12345\nTotal: $500.00",
  "summary": "Invoice for $500",
  "entities": [
    {"type": "amount", "value": "$500.00"},
    {"type": "other", "value": "#12345"}
  ],
  "tags": ["invoice", "finance", "receipt"],
  "language_detected": "en",
  "ocr_confidence": 0.94,
  "ocr_engine": "tesseract",
  "timestamp": "2026-05-04T06:23:12",
  "memory_id": "a1b2c3d4"
}
```

## Clients

### Ksnip (Linux/Mac/Windows)

```bash
chmod +x blocks/capture/clients/ksnip-script.sh
# In Ksnip: Options → Actions → Add → Post
# Command: /path/to/ksnip-script.sh %i
```

### Termux (Android)

```bash
# Install deps
pkg install termux-api curl python

# Run
bash blocks/capture/clients/termux-script.sh
```

### Telegram Bot

```bash
pip install fastapi uvicorn httpx
export TELEGRAM_BOT_TOKEN=your_token
export CAPTURE_API_URL=http://localhost:8000/capture/upload
python blocks/capture/clients/telegram-webhook.py
```

Set webhook:
```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://your-server/telegram/webhook"
```

### Web

Open `blocks/capture/clients/web-form.html` in any browser.

## Deploy

### Docker Compose (standalone)

```bash
cd blocks/capture
docker-compose up --build
```

### Orin / Edge (offline)

```bash
docker run -d \
  -e LLM_PROVIDER=ollama \
  -e OLLAMA_BASE_URL=http://orin-ollama:11434 \
  -e OLLAMA_MODEL=llama3.2:3b \
  -p 8005:8005 \
  cerebrum-capture
```

### Within Cerebrum Platform

Already integrated. The block is registered as `capture` in `BLOCK_REGISTRY`.

## Environment Variables

| Var | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama` / `openrouter` / `openai` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local LLM endpoint |
| `OLLAMA_MODEL` | `llama3.2:3b` | Default local model |
| `OPENROUTER_API_KEY` | `` | Cloud fallback |
| `OPENAI_API_KEY` | `` | Cloud fallback |
| `VECTOR_DB_URL` | `http://localhost:8001` | Chroma/ZVec endpoint |
| `OCR_LANGUAGES` | `ara+eng` | Tesseract language pack |

## Why this beats ShareX

| Feature | ShareX | Cerebrum Capture |
|---|---|---|
| OS | Windows only | Any OS (containerized) |
| API | None | Standard REST + Cerebrum Blocks |
| OCR | English only | Arabic + English |
| AI | None | Built-in LLM structuring |
| Storage | Local/cloud file | Vector DB (searchable) |
| Clients | Desktop only | Desktop + Android + Telegram + Web |
