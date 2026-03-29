#!/usr/bin/env python3
"""Simple web portal to browse OpenClaw workspace files - with landing page."""

import os
import re
import html
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote

# Base workspace directory
WORKSPACE = Path('/home/lobster/.openclaw/workspace')

# Additional directories to expose
EXTRA_DIRS = {
    'qwen-images': Path('/home/lobster/.qwen-image-studio'),
}

# Portal links for landing page
PORTAL_LINKS = [
    {'title': 'OpenClaw Workspace', 'url': '/workspace/', 'desc': 'Browse workspace files, scripts, and documents', 'icon': '📁', 'external': False},
    {'title': 'ComfyUI', 'url': '/', 'desc': 'Node-based image generation workflow', 'icon': '🔗', 'external': True, 'port': 8188},
    {'title': 'Qwen Image Studio', 'url': '/', 'desc': 'Generate images with Qwen-Image (Web UI)', 'icon': '🎨', 'external': True, 'port': 8000},
    {'title': 'Qwen Image Exports', 'url': '/qwen-images/', 'desc': 'View generated images and job history', 'icon': '🖼️', 'external': False},
]

# Code file extensions
CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss', '.sass',
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.sh', '.bash',
    '.zsh', '.fish', '.rs', '.go', '.rb', '.php', '.java', '.c', '.cpp', '.h',
    '.hpp', '.cs', '.swift', '.kt', '.scala', '.sql', '.graphql', '.xml',
    '.txt', '.log', '.env', '.gitignore', '.dockerfile', '.md', '.markdown'
}

MARKDOWN_EXTENSIONS = {'.md', '.markdown'}

# Image extensions
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp', '.ico'}

# Landing page HTML
LANDING_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenClaw Portal</title>
    <style>
        :root { --bg-primary: #0d1117; --bg-secondary: #161b22; --bg-card: #21262d; --text-primary: #e6edf3; --text-secondary: #8b949e; --accent: #58a6ff; --accent-hover: #79c0ff; --border: #30363d; }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: linear-gradient(135deg, var(--bg-primary) 0%, #0f172a 100%); color: var(--text-primary); min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 2rem; }
        h1 { font-size: 2.5rem; margin-bottom: 0.5rem; background: linear-gradient(135deg, var(--accent) 0%, #a78bfa 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { color: var(--text-secondary); margin-bottom: 3rem; font-size: 1.1rem; }
        .cards { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.5rem; max-width: 800px; width: 100%; }
        @media (max-width: 600px) { .cards { grid-template-columns: 1fr; } }
        .card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; text-decoration: none; color: inherit; transition: all 0.2s ease; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3); }
        .card:hover { transform: translateY(-2px); border-color: var(--accent); box-shadow: 0 8px 16px rgba(96, 165, 250, 0.2); }
        .card-icon { font-size: 2.5rem; margin-bottom: 1rem; }
        .card-title { font-size: 1.25rem; font-weight: 600; margin-bottom: 0.5rem; color: var(--text-primary); }
        .card-desc { color: var(--text-secondary); font-size: 0.9rem; line-height: 1.5; }
    </style>
</head>
<body>
    <h1>🦞 OpenClaw Portal</h1>
    <p class="subtitle">Select a destination</p>
    <div class="cards">
'''

# Markdown to HTML converter using markdown2
def simple_markdown(text):
    """Convert markdown to HTML using markdown2 with extensions."""
    import markdown2
    
    # Use markdown2 with extensions for proper list/table rendering
    md = markdown2.Markdown(extras=[
        'tables',           # GitHub-style tables
        'fenced-code-blocks',  # ```code``` blocks
        'header-ids',       # Header anchors
        'toc',              # Table of contents
        'cuddled-lists',    # Better list handling
        'nested-lists',     # Properly nested lists
    ])
    
    return md.convert(text)
# HTML template
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - OpenClaw Workspace</title>
    <style>
        :root {{
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --text-primary: #e6edf3;
            --text-secondary: #8b949e;
            --border: #30363d;
            --accent: #58a6ff;
            --accent-hover: #79c0ff;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 20px;
        }}
        .header h1 {{ font-size: 1.5rem; font-weight: 600; }}
        .header a {{ color: var(--accent); text-decoration: none; }}
        .header a:hover {{ text-decoration: underline; }}
        .breadcrumb {{
            padding: 10px 0;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}
        .breadcrumb a {{ color: var(--accent); text-decoration: none; }}
        .breadcrumb a:hover {{ text-decoration: underline; }}
        .file-list {{
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 6px;
            overflow: hidden;
        }}
        .file-item {{
            display: flex;
            align-items: center;
            padding: 12px 16px;
            border-bottom: 1px solid var(--border);
            transition: background 0.2s;
        }}
        .file-item:last-child {{ border-bottom: none; }}
        .file-item:hover {{ background: var(--bg-tertiary); }}
        .file-item a {{
            color: var(--text-primary);
            text-decoration: none;
            flex: 1;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .file-item a:hover {{ color: var(--accent); }}
        .icon {{
            width: 20px;
            height: 20px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
        }}
        .file-meta {{
            color: var(--text-secondary);
            font-size: 0.85rem;
            margin-left: auto;
        }}
        .content {{
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 20px;
            overflow-x: auto;
        }}
        .content pre {{
            background: var(--bg-primary);
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
            border: 1px solid var(--border);
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .content code {{
            font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
            font-size: 0.9rem;
        }}
        .markdown-body {{ color: var(--text-primary); }}
        .markdown-body h1, .markdown-body h2, .markdown-body h3,
        .markdown-body h4, .markdown-body h5, .markdown-body h6 {{
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
            color: var(--text-primary);
        }}
        .markdown-body h1 {{ font-size: 2em; border-bottom: 1px solid var(--border); padding-bottom: 0.3em; }}
        .markdown-body h2 {{ font-size: 1.5em; border-bottom: 1px solid var(--border); padding-bottom: 0.3em; }}
        .markdown-body h3 {{ font-size: 1.25em; }}
        .markdown-body p {{ margin-bottom: 16px; }}
        .markdown-body ul, .markdown-body ol {{ margin-bottom: 16px; padding-left: 2em; }}
        .markdown-body li {{ margin-bottom: 4px; }}
        .markdown-body ul ul, .markdown-body ol ol, .markdown-body ul ol, .markdown-body ol ul {{ margin-bottom: 4px; padding-left: 1.5em; }}
        .markdown-body ol li {{ list-style-type: decimal; }}
        .markdown-body ul li {{ list-style-type: disc; }}
        .markdown-body ul ul li {{ list-style-type: circle; }}
        .markdown-body ul ul ul li {{ list-style-type: square; }}
        .markdown-body a {{ color: var(--accent); text-decoration: none; }}
        .markdown-body a:hover {{ text-decoration: underline; }}
        .markdown-body code {{
            background: var(--bg-tertiary);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
            font-size: 0.9em;
        }}
        .markdown-body table {{
            border-collapse: collapse;
            width: 100%;
            margin: 4px 0;
            border-radius: 6px;
            overflow: hidden;
            display: table;
            max-width: 100%;
        }}
        .markdown-body p + table {{
            margin-top: 0;
        }}
        .markdown-body table + p {{
            margin-top: 8px;
        }}
        .markdown-body thead {{
            display: table-header-group;
        }}
        .markdown-body tbody {{
            display: table-row-group;
        }}
        .markdown-body th {{
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            padding: 6px 10px;
            text-align: left;
            font-weight: 600;
            font-size: 0.9em;
        }}
        .markdown-body td {{
            border: 1px solid var(--border);
            padding: 6px 10px;
            font-size: 0.9em;
        }}
        .markdown-body tr {{
            display: table-row;
        }}
        .markdown-body tr:nth-child(even) {{
            background: var(--bg-tertiary);
        }}
        .markdown-body tr:hover {{
            background: var(--bg-secondary);
        }}
        .markdown-body pre {{
            background: var(--bg-primary);
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
            border: 1px solid var(--border);
        }}
        .markdown-body pre code {{
            background: transparent;
            padding: 0;
        }}
        .markdown-body blockquote {{
            border-left: 4px solid var(--border);
            padding-left: 16px;
            color: var(--text-secondary);
            margin: 16px 0;
        }}
        .markdown-body table {{
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
        }}
        .markdown-body th, .markdown-body td {{
            border: 1px solid var(--border);
            padding: 8px 12px;
            text-align: left;
        }}
        .markdown-body th {{ background: var(--bg-tertiary); font-weight: 600; }}
        .markdown-body tr:nth-child(even) {{ background: var(--bg-tertiary); }}
        .back-link {{
            display: inline-block;
            margin-bottom: 16px;
            color: var(--accent);
            text-decoration: none;
        }}
        .back-link:hover {{ text-decoration: underline; }}
        .empty-state {{
            text-align: center;
            padding: 40px;
            color: var(--text-secondary);
        }}
        /* Simple syntax highlighting */
        .keyword {{ color: #ff7b72; }}
        .string {{ color: #a5d6ff; }}
        .comment {{ color: #8b949e; font-style: italic; }}
        .number {{ color: #79c0ff; }}
        .function {{ color: #d2a8ff; }}
        .class {{ color: #f0883e; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🦞 OpenClaw Workspace</h1>
            <a href="/">Home</a>
        </div>
        {content}
    </div>
</body>
</html>'''

# Directory listing template
DIR_TEMPLATE = '''
<div class="breadcrumb">
    {breadcrumb}
</div>
<div class="file-list">
    {parent_link}
    {file_items}
</div>
{empty_state}
'''

def get_file_icon(path: Path) -> str:
    """Get icon for file type."""
    if path.is_dir():
        return '📁'
    suffix = path.suffix.lower()
    if suffix in MARKDOWN_EXTENSIONS:
        return '📝'
    if suffix == '.py':
        return '🐍'
    if suffix in {'.js', '.ts', '.jsx', '.tsx'}:
        return '📜'
    if suffix in {'.html', '.css'}:
        return '🎨'
    if suffix in {'.json', '.yaml', '.yml', '.toml'}:
        return '⚙️'
    if suffix in {'.sh', '.bash', '.zsh'}:
        return '💻'
    if suffix in {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}:
        return '🖼️'
    if suffix == '.pdf':
        return '📄'
    return '📄'

def format_size(size: int) -> str:
    """Format file size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f'{size:.1f} {unit}'
        size /= 1024
    return f'{size:.1f} TB'

class WorkspaceHandler(SimpleHTTPRequestHandler):
    def render_directory(self, path: Path, subpath: str, base_dir=WORKSPACE):
        """Render directory listing."""
        items = []
        
        try:
            entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            entries = []
        
        # Determine URL prefix
        url_prefix = ''
        if base_dir != WORKSPACE:
            for prefix, dir_path in EXTRA_DIRS.items():
                if dir_path == base_dir:
                    url_prefix = prefix + '/'
                    break
        
        for entry in entries:
            # Skip hidden files except .openclaw
            if entry.name.startswith('.') and entry.name != '.openclaw':
                continue
            if entry.name in {'__pycache__', 'node_modules', '.git'}:
                continue
            
            item_path = f'{url_prefix}{subpath}/{entry.name}'.replace('//', '/').lstrip('/')
            size_str = ''
            
            if entry.is_file():
                try:
                    size_str = f'<span class="file-meta">{format_size(entry.stat().st_size)}</span>'
                except:
                    pass
            
            items.append(f'''
            <div class="file-item">
                <a href="/{html.escape(item_path)}">
                    <span class="icon">{get_file_icon(entry)}</span>
                    <span>{html.escape(entry.name)}</span>
                    {size_str}
                </a>
            </div>
            ''')
        
        # Build breadcrumb
        breadcrumb_parts = ['<a href="/">🏠</a>']
        if url_prefix:
            breadcrumb_parts.append(f'<a href="/{url_prefix}">{url_prefix.rstrip("/")}</a>')
        parts = subpath.split('/') if subpath else []
        for i, part in enumerate(parts):
            if part:
                path_so_far = url_prefix + '/'.join(parts[:i+1])
                breadcrumb_parts.append(f'<a href="/{html.escape(path_so_far)}">{html.escape(part)}</a>')
        breadcrumb = ' / '.join(breadcrumb_parts)
        
        # Parent link
        parent_parts = parts[:-1] if len(parts) > 1 else ([] if parts else None)
        if parent_parts is not None:
            parent_path = url_prefix + '/'.join(parent_parts) if parent_parts else url_prefix or '/'
            parent_link = f'''
            <div class="file-item">
                <a href="/{html.escape(parent_path)}">
                    <span class="icon">📁</span>
                    <span>..</span>
                </a>
            </div>
            '''
        else:
            parent_link = ''
        
        file_items = '\n'.join(items)
        
        empty_state = ''
        if not items and not parent_link:
            empty_state = '<div class="empty-state"><p>This folder is empty</p></div>'
        
        content = DIR_TEMPLATE.format(
            breadcrumb=breadcrumb,
            parent_link=parent_link,
            file_items=file_items,
            empty_state=empty_state
        )
        
        html_content = HTML_TEMPLATE.format(title=path.name or 'Workspace', content=content)
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def render_file(self, path: Path, subpath: str, base_dir=WORKSPACE):
        """Render file content."""
        # Determine URL prefix
        url_prefix = ''
        if base_dir != WORKSPACE:
            for prefix, dir_path in EXTRA_DIRS.items():
                if dir_path == base_dir:
                    url_prefix = prefix + '/'
                    break
        
        # Build breadcrumb
        breadcrumb_parts = ['<a href="/">🏠</a>']
        if url_prefix:
            breadcrumb_parts.append(f'<a href="/{url_prefix}">{url_prefix.rstrip("/")}</a>')
        parts = subpath.split('/') if subpath else []
        for i, part in enumerate(parts):
            if part:
                path_so_far = url_prefix + '/'.join(parts[:i+1])
                breadcrumb_parts.append(f'<a href="/{html.escape(path_so_far)}">{html.escape(part)}</a>')
        breadcrumb = ' / '.join(breadcrumb_parts)
        
        # Back link
        back_parts = parts[:-1] if len(parts) > 1 else ([] if parts else None)
        back_path = url_prefix + '/'.join(back_parts) if back_parts else url_prefix or '/'
        
        # Read file
        try:
            content = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = path.read_text(encoding='latin-1')
        
        suffix = path.suffix.lower()
        
        # Escape content for HTML
        content_escaped = html.escape(content)
        
        if suffix in MARKDOWN_EXTENSIONS:
            # Render as markdown
            file_content = simple_markdown(content)
            file_content = f'<div class="markdown-body">{file_content}</div>'
        else:
            # Render as code with basic syntax highlighting
            file_content = f'<pre><code>{content_escaped}</code></pre>'
        
        # Download button
        download_button = f'''
        <div style="margin-bottom: 16px;">
            <a href="/download/{html.escape(url_prefix + subpath)}" 
               style="display: inline-block; padding: 8px 16px; background: var(--accent); color: white; 
                      text-decoration: none; border-radius: 4px; font-weight: 500;">
               ⬇️ Download Original File
            </a>
        </div>
        '''
        
        html_content = f'''
        <a href="/{html.escape(back_path)}" class="back-link">← Back</a>
        <div class="breadcrumb">{breadcrumb}</div>
        {download_button}
        <div class="content">
            {file_content}
        </div>
        '''
        
        full_html = HTML_TEMPLATE.format(title=path.name, content=html_content)
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(full_html.encode('utf-8'))
    
    def serve_landing(self):
        """Serve the landing page."""
        host = self.headers.get('Host', 'localhost:5000')
        host_no_port = host.split(':')[0]
        
        html_content = LANDING_HTML
        for link in PORTAL_LINKS:
            if link.get('external'):
                url = f"http://{host_no_port}:{link['port']}{link['url']}"
            else:
                url = link['url']
            html_content += f'''
        <a class="card" href="{url}">
            <div class="card-icon">{link['icon']}</div>
            <div class="card-title">{link['title']}</div>
            <div class="card-desc">{link['desc']}</div>
        </a>
'''
        html_content += '''
    </div>
</body>
</html>
'''
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def do_GET(self):
        """Handle GET requests with download support."""
        try:
            # Decode URL
            path = unquote(self.path)
            
            # Landing page
            if path == '/':
                self.serve_landing()
                return
            
            # Check if this is a download request
            if path.startswith('/download/'):
                file_path = path[len('/download/'):].lstrip('/')
                self.serve_download(file_path)
                return
            
            # Remove leading slash
            path = path.lstrip('/')
            
            # Determine base directory
            base_dir = WORKSPACE
            
            # Handle /workspace/ prefix
            if path.startswith('workspace/'):
                path = path[len('workspace/'):].lstrip('/')
            elif path == 'workspace':
                path = ''
            # Handle /qwen-images/ prefix
            elif path.startswith('qwen-images/'):
                path = path[len('qwen-images/'):].lstrip('/')
                base_dir = EXTRA_DIRS['qwen-images']
            elif path == 'qwen-images':
                path = ''
                base_dir = EXTRA_DIRS['qwen-images']
            
            full_path = (base_dir / path).resolve()
            
            # Security check
            if not str(full_path).startswith(str(base_dir)):
                self.send_error(403, 'Forbidden')
                return
            
            if not full_path.exists():
                self.send_error(404, 'Not Found')
                return
            
            if full_path.is_dir():
                self.render_directory(full_path, path, base_dir)
            else:
                self.render_file(full_path, path, base_dir)
        
        except Exception as e:
            self.send_error(500, str(e))
    
    def serve_download(self, file_path):
        """Serve file as download."""
        try:
            # Determine base directory
            base_dir = WORKSPACE
            if file_path.startswith('qwen-images/'):
                file_path = file_path[len('qwen-images/'):].lstrip('/')
                base_dir = EXTRA_DIRS['qwen-images']
            
            # Security check
            full_path = (base_dir / file_path).resolve()
            if not str(full_path).startswith(str(base_dir)):
                self.send_error(403, 'Forbidden')
                return
            
            if not full_path.exists() or full_path.is_dir():
                self.send_error(404, 'Not Found')
                return
            
            # Determine content type
            suffix = full_path.suffix.lower()
            content_types = {
                '.md': 'text/markdown',
                '.markdown': 'text/markdown',
                '.txt': 'text/plain',
                '.py': 'text/x-python',
                '.js': 'application/javascript',
                '.json': 'application/json',
                '.yaml': 'application/x-yaml',
                '.yml': 'application/x-yaml',
                '.html': 'text/html',
                '.css': 'text/css',
                '.pdf': 'application/pdf',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
            }
            content_type = content_types.get(suffix, 'application/octet-stream')
            
            # Read file
            if suffix in {'.md', '.markdown', '.txt', '.py', '.js', '.json', '.yaml', '.yml', '.html', '.css'}:
                content = full_path.read_text(encoding='utf-8')
                content_bytes = content.encode('utf-8')
            else:
                content_bytes = full_path.read_bytes()
            
            # Send file
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content_bytes)))
            self.send_header('Content-Disposition', f'attachment; filename="{full_path.name}"')
            self.end_headers()
            self.wfile.write(content_bytes)
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def log_message(self, format, *args):
        """Custom log format."""
        print(f"[{self.log_date_time_string()}] {args[0]}")

def main():
    port = 5000
    server = HTTPServer(('0.0.0.0', port), WorkspaceHandler)
    print('🦞 OpenClaw Workspace Browser')
    print(f'📍 Workspace: {WORKSPACE}')
    print(f'🌐 URL: http://localhost:{port}')
    print(f'🌐 Network: http://$(hostname -I | cut -d" " -f1):{port}')
    print('')
    print('Press Ctrl+C to stop')
    print('')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n👋 Shutting down...')
        server.shutdown()

if __name__ == '__main__':
    main()
