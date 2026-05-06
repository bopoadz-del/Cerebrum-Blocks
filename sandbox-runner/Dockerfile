FROM python:3.11-slim

# Build deps for the few stdlib accelerators; nothing pip-compiled at runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Run as nobody so any process escape lands as an unprivileged uid.
RUN useradd --system --uid 999 --shell /usr/sbin/nologin sandbox \
    && mkdir -p /scratch && chown sandbox:sandbox /scratch
USER sandbox

COPY --chown=sandbox:sandbox server.py .

EXPOSE 8001
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run with no env passthrough so secrets from the parent env don't leak.
# Operators should run with: docker run --read-only --tmpfs /scratch \
#   --network=none-or-restricted --cap-drop=ALL --user=999:999 ...
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--no-access-log"]
