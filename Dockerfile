# ═══════════════════════════════════════════════════════════════════════
# Cerebrum Blocks — Production Dockerfile
# ═══════════════════════════════════════════════════════════════════════

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (single layer to reduce image size)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build tools
    build-essential gcc g++ gfortran pkg-config \
    # PDF / image processing
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev \
    poppler-utils \
    # OCR (critical for capture, ocr, ocr_v2 blocks)
    tesseract-ocr libtesseract-dev \
    # Networking / healthchecks
    curl \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Persistent data volume
VOLUME /app/data

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
