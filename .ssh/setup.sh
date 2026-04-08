#!/bin/bash
# Setup script to configure SSH access to Render instance
# Run this in new sessions: bash .ssh/setup.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create ~/.ssh if it doesn't exist
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Copy keys
cp "$SCRIPT_DIR/render_id_ed25519" ~/.ssh/render_id_ed25519
cp "$SCRIPT_DIR/render_id_ed25519.pub" ~/.ssh/render_id_ed25519.pub
chmod 600 ~/.ssh/render_id_ed25519
chmod 644 ~/.ssh/render_id_ed25519.pub

# Add to SSH config if not already present
RENDER_HOST="srv-d651qphr0fns73c50ohg@ssh.oregon.render.com"
if ! grep -q "$RENDER_HOST" ~/.ssh/config 2>/dev/null; then
    cat >> ~/.ssh/config << EOF

# Cerebrum Blocks Render Instance
Host render-cerebrum
    HostName ssh.oregon.render.com
    User srv-d651qphr0fns73c50ohg
    IdentityFile ~/.ssh/render_id_ed25519
    StrictHostKeyChecking accept-new
EOF
    chmod 600 ~/.ssh/config
    echo "✅ Added Render host to ~/.ssh/config"
    echo "   Connect with: ssh render-cerebrum"
else
    echo "✅ Render host already in ~/.ssh/config"
fi

echo ""
echo "🔑 SSH keys configured!"
echo "   Test connection: ssh render-cerebrum"
echo "   Service ID: srv-d651qphr0fns73c50ohg"
