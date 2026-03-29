#!/bin/bash
# Start the OpenClaw Workspace Browser

cd "$(dirname "$0")"

# Activate OpenClaw venv for dependencies
source /home/lobster/openclaw-venv/bin/activate

echo "🦞 Starting OpenClaw Workspace Browser..."
echo "📍 Workspace: /home/lobster/.openclaw/workspace"
echo "🌐 URL: http://localhost:5000"
echo "🌐 Network: http://$(hostname -I 2>/dev/null | cut -d' ' -f1 || echo 'your-ip'):5000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 app.py
