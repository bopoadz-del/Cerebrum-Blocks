# Cerebrum Workflow / Pipeline Block

Declarative pipeline orchestrator. Chain any Cerebrum blocks together with variable interpolation.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/workflow/run` | POST | Execute pipeline synchronously |
| `/workflow/schedule` | POST | Schedule recurring pipeline |
| `/workflow/unschedule` | POST | Cancel scheduled pipeline |
| `/workflow/list` | GET | List all pipelines |
| `/workflow/{id}` | GET | Get pipeline definition |
| `/workflow/history/recent` | GET | Recent execution history |

### Run Pipeline

```bash
curl -X POST http://localhost:8000/workflow/run \
  -H "Authorization: Bearer test-key" \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_id": "morning-report",
    "steps": [
      {
        "id": "capture",
        "block": "capture",
        "input": {"file_path": "/data/dashboard.png"},
        "params": {"action": "capture", "source": "cron"}
      },
      {
        "id": "analyze",
        "block": "agent_swarm",
        "input": {
          "objective": "Analyze this capture",
          "agents": [{"name": "analyst", "role": "custom", "goal": "Analyze"}],
          "tasks": [{"id": "t1", "description": "Analyze capture", "agent": "analyst"}]
        },
        "params": {"action": "execute"}
      },
      {
        "id": "notify",
        "block": "notification",
        "input": {
          "channel": "telegram",
          "to": "123456",
          "message": "{{steps.analyze.result.final_output}}"
        },
        "params": {"action": "send"}
      }
    ]
  }'
```

### Variable Interpolation

Use `{{steps.step_id.result.path}}` to pass data between steps:

```json
{
  "id": "notify",
  "block": "notification",
  "input": {
    "message": "Capture done: {{steps.capture.result.capture_id}}"
  }
}
```

### Schedule

```bash
curl -X POST http://localhost:8000/workflow/schedule \
  -H "Authorization: Bearer test-key" \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_id": "daily",
    "trigger": {"interval_seconds": 3600},
    "steps": [...]
  }'
```

## Environment Variables

| Var | Default | Description |
|---|---|---|
| `MAX_PIPELINE_STEPS` | `20` | Max steps per pipeline |
| `WORKFLOW_STEP_TIMEOUT` | `60` | Per-step timeout (seconds) |
| `ENABLE_WORKFLOW_SCHEDULER` | `true` | Enable cron/interval scheduling |
