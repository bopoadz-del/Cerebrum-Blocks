#!/data/data/com.termux/files/usr/bin/bash
# Termux (Android) Capture Upload Script
# Usage: termux-script.sh
# Requires: termux-api (for screencap), curl

set -e

API_BASE_URL="${CAPTURE_API_URL:-http://your-server:8000}"
API_KEY="${CEREBRUM_API_KEY:-test-key}"
SOURCE="termux"
USER_ID="${USER_ID:-android}"

# Take screenshot via termux-api or adb
SCREENSHOT_PATH="/data/data/com.termux/files/home/capture_$(date +%s).png"

if command -v termux-screencap >/dev/null 2>&1; then
    termux-screencap -f "$SCREENSHOT_PATH"
elif command -v screencap >/dev/null 2>&1; then
    screencap "$SCREENSHOT_PATH"
else
    echo "❌ No screencap tool found. Install termux-api or run as root."
    exit 1
fi

echo "📤 Uploading Android screenshot to Cerebrum Capture..."

RESPONSE=$(curl -s -X POST \
    "${API_BASE_URL}/capture/upload" \
    -H "Authorization: Bearer ${API_KEY}" \
    -F "file=@${SCREENSHOT_PATH}" \
    -F "source=${SOURCE}" \
    -F "user_id=${USER_ID}")

CAPTURE_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('capture_id',''))" 2>/dev/null || echo "")
SUMMARY=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('summary',''))" 2>/dev/null || echo "")

if [ -n "$CAPTURE_ID" ]; then
    termux-toast "Capture uploaded: $CAPTURE_ID" 2>/dev/null || true
    echo "✅ Capture ID: $CAPTURE_ID"
    echo "📝 Summary: $SUMMARY"
else
    echo "❌ Upload failed"
    echo "$RESPONSE"
    exit 1
fi

# Cleanup
rm -f "$SCREENSHOT_PATH"
