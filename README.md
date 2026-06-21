# TermuxDesk

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![PyPI](https://img.shields.io/pypi/v/termux-desk.svg?cache=1)](https://pypi.org/project/termux-desk/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Your X11 desktop, right in the browser. No root, no VNC, no RDP.**

Works on Android (Termux/PRoot) and Linux. Point your browser at the link, enter the access code, and you're in.

![TermuxDesk terminal banner](https://raw.githubusercontent.com/amirghm/termux-desk/main/docs/terminal-banner.jpg)

![TermuxDesk browser login](https://raw.githubusercontent.com/amirghm/termux-desk/main/docs/browser-login.jpg)

![TermuxDesk browser view](https://raw.githubusercontent.com/amirghm/termux-desk/main/docs/browser-view.jpg)

## Install

One-liner for Termux:

```bash
curl -fsSL https://raw.githubusercontent.com/amirghm/termux-desk/main/run.sh | bash
```

Or from PyPI:

```bash
pip install termux-desk
```

Or from source:

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

The terminal will print a URL and a 6-character access code. Open the URL in any browser and enter the code when prompted. That's it.

### With a public link

```bash
termux-desk start --tunnel
```

This gives you a temporary HTTPS link via localhost.run. Share the link and the access code with whoever needs access.

### On your local network

```bash
termux-desk start --host 0.0.0.0
```

Other devices on the same network can connect using your IP address.

### About the access code

Every time you start TermuxDesk, it generates a random 6-character code (uppercase letters and digits). You'll see it printed right below the URL in the terminal. Type it into the browser to unlock the remote desktop. This keeps random strangers out when you're using `--tunnel` or `--host 0.0.0.0`.

## Features

🔒 Access code authentication
🖱️ Click, drag, double-click, scroll
📋 Clipboard sync (browser and remote desktop)
🎨 Dark UI with FPS counter and status
📱 Works on any device with a browser
🔐 HTTPS via localhost.run tunnel, no exposed ports
🔄 Requires ssh (built-in on most systems)

## CLI

```bash
termux-desk start [--host HOST] [--port PORT] [--display DISPLAY]
                  [--fps FPS] [--quality 1..95] [--tunnel]
```

| Option | Default | What it does |
| --- | --- | --- |
| `--host` | `127.0.0.1` | Address to listen on |
| `--port` | `8765` | Port to listen on |
| `--display` | `$DISPLAY` | X11 display to capture |
| `--fps` | `12` | Max frames per second |
| `--quality` | `70` | JPEG quality, 1 to 95 |
| `--tunnel` | off | Create a localhost.run tunnel |

Run `termux-desk --version` to check the installed version. `Ctrl+C` stops everything.

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

If you already have an asyncio loop running:

```python
server = TermuxDeskServer()
await server.start()
print(server.local_url)
# ... your app logic ...
await server.stop()
```

There's also `termux_desk.run_server(**options)` for quick blocking use.

## Troubleshooting

**`DISPLAY is not set`**

```bash
export DISPLAY=:0
```

**`tunnel fails to connect`**

The tunnel uses SSH to connect to localhost.run. Make sure `ssh` is available:

```bash
which ssh
```

## License

[MIT](LICENSE) 2026 TermuxDesk contributors.
