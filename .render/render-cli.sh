#!/bin/bash
# Render CLI helper script using saved API key
# Usage: bash .render/render-cli.sh [command]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_KEY=$(cat "$SCRIPT_DIR/api-key")
SERVICE_ID="srv-d651qphr0fns73c50ohg"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

show_help() {
    echo "Render CLI Helper for Cerebrum Blocks"
    echo ""
    echo "Usage: bash .render/render-cli.sh [command]"
    echo ""
    echo "Commands:"
    echo "  status       - Check service status"
    echo "  deploys      - List recent deployments"
    echo "  env          - List environment variables"
    echo "  logs         - Stream logs (last 100 lines)"
    echo "  help         - Show this help"
}

check_api_key() {
    if [ -z "$API_KEY" ]; then
        echo -e "${RED}Error: API key not found in .render/api-key${NC}"
        exit 1
    fi
}

cmd_status() {
    check_api_key
    echo -e "${YELLOW}Checking service status...${NC}"
    curl -s -X GET "https://api.render.com/v1/services/$SERVICE_ID" \
        -H "Accept: application/json" \
        -H "Authorization: Bearer $API_KEY" | python3 -m json.tool 2>/dev/null || echo "Error fetching status"
}

cmd_deploys() {
    check_api_key
    echo -e "${YELLOW}Recent deployments...${NC}"
    curl -s -X GET "https://api.render.com/v1/services/$SERVICE_ID/deploys?limit=5" \
        -H "Accept: application/json" \
        -H "Authorization: Bearer $API_KEY" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for d in data[:5]:
        deploy = d['deploy']
        print(f\"📦 {deploy['id']}\")
        print(f\"   Status: {deploy['status']}\")
        print(f\"   Commit: {deploy.get('commit', {}).get('message', 'N/A')[:50]}\")
        print(f\"   Created: {deploy['createdAt']}\")
        print(f\"   Finished: {deploy.get('finishedAt', 'Still running...')}\")
        print()
except Exception as e:
    print(f'Error: {e}')
"
}

cmd_env() {
    check_api_key
    echo -e "${YELLOW}Environment variables...${NC}"
    curl -s -X GET "https://api.render.com/v1/services/$SERVICE_ID/env-vars" \
        -H "Accept: application/json" \
        -H "Authorization: Bearer $API_KEY" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if data:
        for env in data:
            e = env.get('envVar', {})
            name = e.get('key', 'N/A')
            value = e.get('value', '')
            # Mask sensitive values
            if any(s in name.lower() for s in ['key', 'secret', 'token', 'password']):
                value = '*' * min(len(value), 8) if value else '(not set)'
            print(f'{name}={value}')
    else:
        print('No environment variables set')
except Exception as e:
    print(f'Error: {e}')
"
}

cmd_logs() {
    echo -e "${YELLOW}Opening SSH to stream logs...${NC}"
    echo -e "${GREEN}Press Ctrl+C to exit${NC}"
    ssh render-cerebrum "tail -f /var/log/render/*.log" 2>/dev/null || echo "Error: SSH not configured. Run: bash .ssh/setup.sh"
}

# Main command handler
case "${1:-help}" in
    status)
        cmd_status
        ;;
    deploys)
        cmd_deploys
        ;;
    env)
        cmd_env
        ;;
    logs)
        cmd_logs
        ;;
    help|--help|-h|*)
        show_help
        ;;
esac
