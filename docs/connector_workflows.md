# Connector Workflows

Reactive video analytics and medical EHR connector patterns for Cerebrum Blocks.

## Video ingest → anomaly trigger → notification

```json
{
  "workflow_id": "video-anomaly-alert",
  "steps": [
    {
      "block": "video_metadata_ingest",
      "params": { "action": "ingest" },
      "input": {
        "camera_id": "lobby-1",
        "source_id": "jetson-edge-01",
        "zones": [
          { "zone_id": "lobby", "count": 42, "capacity": 50 }
        ],
        "anomalies": [
          {
            "anomaly_type": "overcrowding",
            "severity": "high",
            "zone_id": "lobby",
            "confidence": 0.92
          }
        ]
      }
    },
    {
      "block": "video_anomaly_trigger",
      "params": {
        "action": "evaluate",
        "channel": "webhook",
        "send_notification": "true"
      },
      "input": {
        "url": "https://hooks.example.com/video-alerts",
        "message": "Lobby overcrowding detected"
      }
    }
  ]
}
```

## REST shortcut (auto-chains trigger on anomaly)

```bash
curl -X POST http://localhost:8000/v1/video/ingest \
  -H "Authorization: Bearer $CEREBRUM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "lobby-1",
    "anomalies": [{"anomaly_type": "intrusion", "severity": "critical"}],
    "auto_trigger": true,
    "notify_channel": "webhook",
    "notify_to": "https://hooks.example.com/alerts"
  }'
```

## Medical EHR (FHIR) fetch

```bash
curl -X POST http://localhost:8000/v1/connectors/medical/ehr \
  -H "Authorization: Bearer $CEREBRUM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"resource": "Patient", "resource_id": "example"}'
```

Environment:

- `FHIR_BASE_URL` — FHIR server base (e.g. `https://fhir.example.com/r4`)
- `FHIR_ACCESS_TOKEN` — Bearer token (preferred)
- `FHIR_CLIENT_ID` / `FHIR_CLIENT_SECRET` — optional client credentials

## Storage

Set `DATABASE_URL` to a PostgreSQL/Timescale connection string for durable video event storage. Without it, an in-memory store is used (tests and local dev).
