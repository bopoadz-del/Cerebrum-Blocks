FROM python:3.11-slim

WORKDIR /app

# Install system deps: tesseract with Arabic + English, plus build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-ara \
    tesseract-ocr-eng \
    gcc \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from project root (assumes shared deps)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Ensure pytesseract is available
RUN pip install --no-cache-dir pytesseract Pillow easyocr httpx

# Copy app source
COPY app/ ./app/
COPY blocks/ ./blocks/
COPY tests/ ./tests/

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV DATA_DIR=/app/data

EXPOSE 8000

# Standalone mode: run just the capture router on a dedicated port
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
