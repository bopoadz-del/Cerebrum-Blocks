# Cerebrum Notification Hub Block

One endpoint for all outbound notifications: Telegram, Email, Webhook, Slack.

## Channels

| Channel | Config Required | How |
|---|---|---|
| **Telegram** | `TELEGRAM_BOT_TOKEN` | Bot message to chat_id |
| **Email** | `SENDGRID_API_KEY` or `SMTP_HOST` | Send email |
| **Webhook** | None (per-request URL) | POST to any URL |
| **Slack** | `SLACK_WEBHOOK_URL` | Incoming webhook |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/notify/send` | POST | Send via single channel |
| `/notify/broadcast` | POST | Send to multiple channels |
| `/notify/health` | GET | Available channels |

### Send Telegram

```bash
curl -X POST http://localhost:8000/notify/send \
  -H "Authorization: Bearer test-key" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "telegram",
    "to": "123456789",
    "message": "🧠 Swarm complete!"
  }'
```

### Send Email

```bash
curl -X POST http://localhost:8000/notify/send \
  -H "Authorization: Bearer test-key" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "email",
    "to": "user@example.com",
    "subject": "Daily Report",
    "message": "Plain text body",
    "html": "<b>HTML body</b>"
  }'
```

### Webhook

```bash
curl -X POST http://localhost:8000/notify/send \
  -H "Authorization: Bearer test-key" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "webhook",
    "url": "https://hooks.zapier.com/hooks/catch/...",
    "payload": {"event": "swarm_done", "data": "..."}
  }'
```

### Broadcast

```bash
curl -X POST http://localhost:8000/notify/broadcast \
  -H "Authorization: Bearer test-key" \
  -H "Content-Type: application/json" \
  -d '{
    "channels": ["telegram", "slack"],
    "to": "123456789",
    "message": "Critical alert!"
  }'
```

## Environment Variables

| Var | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `SENDGRID_API_KEY` | SendGrid API key |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS` | SMTP fallback |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook |
| `DEFAULT_FROM_EMAIL` | From address for emails |
