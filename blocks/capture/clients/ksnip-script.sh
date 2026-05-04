#!/bin/bash
# Ksnip Capture Upload Script
# Usage: Configure in Ksnip → Options → Actions → Add → Post
#        Command: /path/to/ksnip-script.sh %i
#
# Pushes screenshot to Cerebrum Capture Block and copies URL to clipboard.

set -e

IMAGE_PATH="$1"
API_BASE_URL="${CAPTURE_API_URL:-http://localhost:8000}"
API_KEY="${CEREBRUM_API_KEY:-test-key}"
SOURCE="ksnip"

if [ -z "$IMAGE_PATH" ] || [ ! -f "$IMAGE_PATH" ]; then
    echo "Usage: $0 <image_path>"
    exit 1
fi

echo "📤 Uploading screenshot to Cerebrum Capture..."

RESPONSE=$(curl -s -X POST \
    "${API_BASE_URL}/capture/upload" \
    -H "Authorization: Bearer ${API_KEY}" \
    -F "file=@${IMAGE_PATH}" \
    -F "source=${SOURCE}" \
    -F "user_id=$(whoami)")

CAPTURE_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('capture_id',''))" 2>/dev/null || echo "")
SUMMARY=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('summary',''))" 2>/dev/null || echo "")

if [ -n "$CAPTURE_ID" ]; then
    URL="${API_BASE_URL}/capture/${CAPTURE_ID}"
    echo "$URL" | xclip -selection clipboard 2>/dev/null || echo "$URL" | pbcopy 2>/dev/null || true
    echo "✅ Capture ID: $CAPTURE_ID"
    echo "📝 Summary: $SUMMARY"
    notify-send "Cerebrum Capture" "Uploaded: $CAPTURE_ID" 2>/dev/null || true
else
    echo "❌ Upload failed"
    echo "$RESPONSE"
    exit 1
fi
