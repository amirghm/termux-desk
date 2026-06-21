# TermuxDesk

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![PyPI](https://img.shields.io/pypi/v/termux-desk.svg?cache=1)](https://pypi.org/project/termux-desk/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Web-based remote desktop for Android — no root, no VNC, no RDP.**

Stream your X11 desktop to any browser. Control mouse, keyboard, and clipboard remotely. A random access code is required to connect.

![TermuxDesk remote desktop in browser](https://raw.githubusercontent.com/amirghm/termux-desk/main/docs/screenshot.jpg)

## Install

### One-liner (works everywhere)

```bash
curl -fsSL https://raw.githubusercontent.com/amirghm/termux-desk/main/run.sh | bash
```

### PyPI

```bash
pip install termux-desk
```

### From source

```bash
git clone https://github.com/amirghm/termux-desk.git
cd termux-desk
pip install .
```

## Quick Start

```bash
export DISPLAY=:0
termux-desk start
```

Open `http://127.0.0.1:8765` in a browser. A 6-character access code will be printed in the terminal — enter it in the browser to connect.

### LAN access

```bash
termux-desk start --host 0.0.0.0
```

### HTTPS tunnel

```bash
termux-desk start --tunnel
```

### Access code

Each server instance generates a random 6-character code (uppercase letters + digits). The code is printed in the terminal and must be entered in the browser before the remote desktop loads. This prevents unauthorized access when using `--host 0.0.0.0` or `--tunnel`.

## Features

- 🔒 Access code authentication
- 🖱️ Click, drag, double-click, scroll
- 📋 Clipboard sync (browser ↔ remote desktop)
- 🎨 Dark UI with FPS counter & connection status
- 📱 Works on any device with a browser
- 🔐 HTTPS via Cloudflare — no exposed ports
- 🔄 Auto-downloads cloudflared if not installed

## CLI

```bash
termux-desk start [--host HOST] [--port PORT] [--display DISPLAY]
                  [--fps FPS] [--quality 1..95] [--tunnel]
```

| Option | Default | Description |
| --- | --- | --- |
| `--host` | `127.0.0.1` | HTTP listen address |
| `--port` | `8765` | HTTP listen port |
| `--display` | `$DISPLAY` | X11 display name |
| `--fps` | `12` | Maximum capture rate |
| `--quality` | `70` | JPEG quality (1–95) |
| `--tunnel` | off | Start Cloudflare Quick Tunnel |

Use `termux-desk --version` to print the installed version. Press `Ctrl+C` to stop.

## Python API

```python
from termux_desk import TermuxDeskServer

server = TermuxDeskServer(
    host="127.0.0.1",
    port=8765,
    display=":0",
    fps=12,
    quality=70,
)
print(f"Access code: {server._auth_code}")
server.run()
```

For an existing asyncio application:

```python
server = TermuxDeskServer()
await server.start()
print(server.local_url)
# ... application work ...
await server.stop()
```

`termux_desk.run_server(**options)` is a blocking convenience function.
`TermuxDeskError` is raised for missing dependencies, an unset or unreachable display, missing XTest support, and tunnel startup failures.

## Troubleshooting

**`DISPLAY is not set`**
```bash
export DISPLAY=:0
```

**`cloudflared was not found`**

Auto-downloaded by termux-desk. If it fails:
```bash
# Termux
pkg install cloudflared

# Linux
curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared
```

## License

[MIT](LICENSE) © 2026 TermuxDesk contributors.
