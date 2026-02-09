#!/usr/bin/env bash
set -euo pipefail

# Start the Flask application using gunicorn.  The PORT environment
# variable is respected by the Render deployment environment, but it
# defaults to 5000 for local development.
gunicorn app:app --bind 0.0.0.0:${PORT:-5000} --workers 1 --threads 4 --timeout 180