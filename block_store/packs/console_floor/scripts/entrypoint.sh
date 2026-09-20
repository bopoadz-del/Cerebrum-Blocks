#!/bin/sh
# Console Floor pack — boot order contract:
#   python -m alembic upgrade head BEFORE serving.
#   A migration failure refuses boot: uvicorn is never started.
set -e
cd /app

echo "[pack:console_floor] applying migrations before serving (alembic upgrade head)"
python3 -m alembic upgrade head

echo "[pack:console_floor] migrations applied — starting uvicorn on :8000"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
