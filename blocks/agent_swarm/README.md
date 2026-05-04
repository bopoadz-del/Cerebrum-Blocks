# Cerebrum Agent Swarm Block

Lightweight, containerized multi-agent orchestrator for the Cerebrum Blocks platform.

## Architecture
- **No heavy frameworks** — pure FastAPI + async Python
- **LLM Router** — Ollama (local/Orin) ↔ OpenRouter/OpenAI (cloud)
- **Dependency resolution** — topological task ordering
- **Vector memory** — plugs into existing ZVec/ChromaDB block
- **Standard API** — `POST /swarm/execute` accepts agents + tasks JSON

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/swarm/execute` | POST | Sync swarm execution |
| `/swarm/execute/async` | POST | Async queue, returns job ID |
| `/swarm/status/{job_id}` | GET | Poll async job status |
| `/swarm/health` | GET | Health check |

### Execute Swarm

```bash
curl -X POST http://localhost:8000/swarm/execute \
  -H "Authorization: Bearer test-key" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "demo-001",
    "objective": "Write a FastAPI endpoint for user auth",
    "agents": [
      {
        "name": "architect",
        "role": "planner",
        "goal": "Design clean API structure",
        "backstory": "Senior backend architect"
      },
      {
        "name": "coder",
        "role": "coder",
        "goal": "Implement the code",
        "backstory": "Python specialist"
      }
    ],
    "tasks": [
      {
        "id": "design",
        "description": "Design Pydantic models and endpoint structure",
        "agent": "architect",
        "expected_output": "JSON schema and endpoint plan"
      },
      {
        "id": "implement",
        "description": "Write the FastAPI code based on the design",
        "agent": "coder",
        "expected_output": "Complete Python file",
        "dependencies": ["design"]
      }
    ]
  }'
```

Response:
```json
{
  "project_id": "demo-001",
  "status": "completed",
  "objective": "Write a FastAPI endpoint for user auth",
  "outputs": [
    {"agent": "architect", "task_id": "design", "status": "completed", "result": "..."},
    {"agent": "coder", "task_id": "implement", "status": "completed", "result": "..."}
  ],
  "final_output": "...",
  "total_tokens": 1234,
  "total_time_ms": 4500,
  "swarm_id": "a1b2c3d4",
  "memory_id": "a1b2c3d4"
}
```

## Deploy

### Docker Compose (standalone)
```bash
cd blocks/agent_swarm
docker-compose up --build
```

### On Jetson Orin (Offline)
```bash
docker run -e LLM_PROVIDER=ollama \
  -e OLLAMA_BASE_URL=http://orin-ollama:11434 \
  -p 8006:8000 \
  cerebrum-agent-swarm
```

### Within Cerebrum Platform
Already integrated. The block is registered as `agent_swarm` in `BLOCK_REGISTRY`.

## Environment Variables

| Var | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama` / `openrouter` / `openai` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local LLM endpoint |
| `OLLAMA_MODEL` | `llama3.2:3b` | Default local model |
| `OPENROUTER_API_KEY` | `` | Cloud fallback |
| `OPENAI_API_KEY` | `` | Cloud fallback |
| `VECTOR_DB_URL` | `http://localhost:8001` | ZVec/Chroma endpoint |
| `MAX_CONCURRENT_AGENTS` | `5` | Parallel agent limit |
| `DEFAULT_TIMEOUT` | `120` | LLM timeout (seconds) |

## Why Not CrewAI/AutoGen

| Framework | Issue | This Block |
|---|---|---|
| **CrewAI** | Heavy deps, slow startup, overkill for edge | Pure Python, instant cold start |
| **AutoGen** | Microsoft complexity, hard to containerize | Single container, 50MB image |
| **Ruflo** | Node.js/Claude Code dependency | Python-native, any LLM |
