#!/bin/bash
# Start script for AI Block System

# Use PORT from environment (Render sets this) or default to 8000
PORT=${PORT:-8000}

echo "🚀 Starting AI Block System..."
echo "📍 Port: $PORT"
echo "📁 Data Directory: ${DATA_DIR:-/app/data}"

# Create data directory if it doesn't exist
mkdir -p ${DATA_DIR:-/app/data}

# Start the server
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
