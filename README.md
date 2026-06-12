# TermuxDesk

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![PyPI](https://img.shields.io/pypi/v/termux-desk.svg)](https://pypi.org/project/termux-desk/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Web-based remote desktop for Android — no root, no VNC, no RDP.**

Stream your X11 desktop to any browser. Control mouse, keyboard, and clipboard remotely.

![TermuxDesk remote desktop in browser](https://raw.githubusercontent.com/amirghm/termux-desk/main/docs/screenshot.jpg)

## One-Line Install & Run

```bash
curl -fsSL https://raw.githubusercontent.com/amirghm/termux-desk/main/run.sh | bash
```

Works on **Termux**, **PRoot** (Ubuntu/Debian/Arch), and any Linux.

<details>
<summary>Manual install</summary>

### Termux (native)

```bash
pkg install python cloudflared
pip install termux-desk
termux-desk start --tunnel
```

### PRoot (Debian/Ubuntu)

```bash
pip install termux-desk --break-system-packages
termux-desk start --tunnel
```

### Any Linux

```bash
pip install termux-desk --break-system-packages
termux-desk start --tunnel
```

</details>

## Features

- 🖱️ Zero-delay click & drag
- 📋 Clipboard sync (browser ↔ remote desktop)
- 🎨 Clean UI with FPS counter & connection status
- 📱 Works on any device with a browser
- 🔒 HTTPS via Cloudflare — no exposed ports
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
| `--quality` | `70` | JPEG quality (1-95) |
| `--tunnel` | off | Start Cloudflare Quick Tunnel |

## Troubleshooting

**`DISPLAY is not set`**
```bash
export DISPLAY=:0
```

**`cloudflared was not found`**

The installer auto-downloads it. If it fails:
```bash
# Termux
pkg install cloudflared

# Linux
curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared
```

## License

[MIT](LICENSE) © 2026 TermuxDesk contributors.
