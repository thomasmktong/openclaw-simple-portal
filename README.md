# OpenClaw Simple Portal

A lightweight web portal for browsing OpenClaw workspace files with a clean GitHub-style dark theme.

## Features

- 🦞 Landing page with quick links to workspace and tools
- 📁 File browser with directory listings
- 📝 Markdown rendering with tables, lists, code blocks (using markdown2)
- 🎨 Syntax highlighting for code files
- 🖼️ Image preview support
- ⚙️ JSON/YAML viewing

## Quick Start

```bash
# Install dependencies
pip install markdown2

# Start the portal
./start.sh

# Or run directly
python3 app.py

# Access at http://localhost:5000
```

## Structure

```
web-portal/
├── app.py              # Main server (single-file, no dependencies beyond stdlib + markdown2)
├── start.sh            # Startup script
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Dependencies

- Python 3.8+
- `markdown2` (for markdown rendering)

```bash
pip install markdown2
```

## URLs

- `/` - Landing page
- `/workspace/` - Browse OpenClaw workspace
- `/qwen-images/` - Browse Qwen Image exports (if configured)

## Systemd Service (Optional)

For persistent operation, create a systemd user service:

```bash
# Create service file
cat > ~/.config/systemd/user/web-portal.service << 'EOF'
[Unit]
Description=OpenClaw Web Portal
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/web-portal
ExecStart=/usr/bin/python3 /path/to/web-portal/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

# Enable and start
systemctl --user daemon-reload
systemctl --user enable web-portal.service
systemctl --user start web-portal.service
```

## License

MIT
