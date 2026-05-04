# Cerebrum RAG Knowledge Block v2

Ask questions across all stored captures and swarm runs.

Retrieval-Augmented Generation:
```
Question → Vector search → Top-k chunks → LLM synthesis → Cited answer
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/knowledge/ask` | POST | RAG: retrieve + synthesize answer |
| `/knowledge/search` | POST | Search only (no LLM) |
| `/knowledge/summarize` | POST | Summarize a collection |

### Ask

```bash
curl -X POST http://localhost:8000/knowledge/ask \
  -H "Authorization: Bearer test-key" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What did yesterday swarms conclude about auth?",
    "collections": ["cerebrum_captures", "cerebrum_swarm"],
    "top_k": 5
  }'
```

Response:
```json
{
  "answer": "The swarms recommended JWT with refresh tokens...",
  "sources": [
    {"id": "a1b2c3d4", "collection": "cerebrum_swarm", "score": 0.94}
  ],
  "confidence": 0.88,
  "chunks_retrieved": 5
}
```

### Search Only

```bash
curl -X POST http://localhost:8000/knowledge/search \
  -H "Authorization: Bearer test-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "invoice total",
    "collections": ["cerebrum_captures"],
    "top_k": 3
  }'
```

### Summarize Collection

```bash
curl -X POST http://localhost:8000/knowledge/summarize \
  -H "Authorization: Bearer test-key" \
  -H "Content-Type: application/json" \
  -d '{
    "collection": "cerebrum_captures",
    "n_docs": 10
  }'
```

## Environment Variables

| Var | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama` / `openrouter` / `openai` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local LLM |
| `OLLAMA_MODEL` | `llama3.2:3b` | Default model |
| `VECTOR_DB_URL` | `http://localhost:8001` | Chroma/ZVec endpoint |
