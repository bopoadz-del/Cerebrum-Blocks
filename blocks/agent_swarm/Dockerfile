FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from project root
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Ensure httpx is available
RUN pip install --no-cache-dir httpx

# Copy app source
COPY app/ ./app/
COPY blocks/ ./blocks/
COPY tests/ ./tests/

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
