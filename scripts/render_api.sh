#!/bin/bash
# Render API helper — saved so we don't lose the key again
RENDER_API_KEY="rnd_QqJ5qS97qrfF0IwAVrJhmKpJyNX0"
PLATFORM_API_SERVICE="srv-d7dd87n7f7vs73es12kg"
PLATFORM_SERVICE="srv-d7s2f2f7f7vs73dbiq20"
STORE_API_SERVICE="srv-d7s2f2f7f7vs73dbiq30"
STORE_SERVICE="srv-d7s2f2n7f7vs73dbiq3g"

case "$1" in
  env)
    curl -s "https://api.render.com/v1/services/$PLATFORM_API_SERVICE/env-vars" \
      -H "Authorization: Bearer $RENDER_API_KEY" | python3 -m json.tool
    ;;
  deploy)
    curl -s -X POST "https://api.render.com/v1/services/$PLATFORM_API_SERVICE/deploys" \
      -H "Authorization: Bearer $RENDER_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{"clearCache":"do_not_clear"}' | python3 -m json.tool
    ;;
  status)
    curl -s "https://api.render.com/v1/services/$PLATFORM_API_SERVICE/deploys?limit=1" \
      -H "Authorization: Bearer $RENDER_API_KEY" | python3 -m json.tool
    ;;
  set-env)
    # Usage: ./render_api.sh set-env KEY_NAME "value"
    KEY_NAME="$2"
    VALUE="$3"
    curl -s -X PUT "https://api.render.com/v1/services/$PLATFORM_API_SERVICE/env-vars" \
      -H "Authorization: Bearer $RENDER_API_KEY" \
      -H "Content-Type: application/json" \
      -d "[{\"key\":\"$KEY_NAME\",\"value\":\"$VALUE\"}]" | python3 -m json.tool
    ;;
  *)
    echo "Usage: $0 {env|deploy|status|set-env KEY VALUE}"
    ;;
esac
