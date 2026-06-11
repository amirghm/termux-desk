# TermuxDesk

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![PyPI](https://img.shields.io/pypi/v/termux-desk.svg)](https://pypi.org/project/termux-desk/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**A lightweight, web-based remote desktop for Termux and PRoot X11 environments.**

TermuxDesk captures an existing X11 display with Pillow, streams JPEG frames
through an aiohttp WebSocket, and injects mouse and keyboard events with the
XTest extension through python-xlib. It does not need root or `sudo`.

> **Project status:** `0.1.0` is an alpha release. Test it with your desktop and
> window manager before relying on it.

## Demo

<!-- Replace this placeholder with a repository screenshot or recording. -->

![TermuxDesk browser viewer demo](https://placehold.co/1200x675/111827/f9fafb?text=TermuxDesk+Demo)

## Requirements

- Python 3.9 or newer
- A running X11 server with the XTest extension
- `DISPLAY` set to that server, such as `:0`
- `cloudflared` only when using `--tunnel`

TermuxDesk provides the remote viewer; it does not start Termux:X11, Xvfb, a
desktop environment, or a window manager.

## Install

From PyPI:

```bash
python -m pip install termux-desk
```

From a checkout:

```bash
python -m pip install .
```

Termux one-liner:

```bash
curl -fsSL https://raw.githubusercontent.com/amirghm/termux-desk/main/install.sh | bash
```

The installer must run in Termux itself, not inside a Debian/Ubuntu PRoot. This
matters because PRoot's `apt` repositories do not provide Termux's `python`
package. Run Termux package installation first, then enter your PRoot if that
is where the X11 session runs.

## Quick Start

Start your X11 environment, identify its display, and run:

```bash
export DISPLAY=:0
termux-desk start
```

Open `http://127.0.0.1:8765` in a browser on the same device.

To listen on the LAN:

```bash
termux-desk start --host 0.0.0.0
```

To create a temporary HTTPS URL:

```bash
termux-desk start --tunnel
```

**Security warning:** TermuxDesk `0.1.0` has no built-in authentication. Anyone
who can reach the URL can view and control the X11 session. A Cloudflare Quick
Tunnel URL is public. Share it only with trusted people, stop it after use, and
prefer Cloudflare Access or another authenticated proxy for ongoing access.

## Browser Controls

- **Click mode** sends primary clicks immediately on press and detects quick
  second presses as double-clicks.
- **Drag mode** holds the primary button while the pointer moves.
- Mouse movement, double-click, wheel, and horizontal scroll are supported.
- **Copy** reads the X11 clipboard into the browser clipboard; **Paste** and
  browser paste events send text to the X11 clipboard. Install `xclip` or
  `xsel` in the environment running TermuxDesk to enable clipboard support.
- Keyboard events are sent while the viewer page has focus.
- The Help button shows the controls in the viewer.

Browser and operating-system reserved shortcuts may not reach the remote
desktop.

## CLI Reference

```text
termux-desk start [--host HOST] [--port PORT] [--display DISPLAY]
                  [--fps FPS] [--quality 1..95] [--tunnel]
```

| Option | Default | Description |
| --- | --- | --- |
| `--host` | `127.0.0.1` | HTTP listen address |
| `--port` | `8765` | HTTP listen port |
| `--display` | `$DISPLAY` | X11 display name |
| `--fps` | `12` | Maximum capture rate |
| `--quality` | `70` | JPEG quality from 1 to 95 |
| `--tunnel` | off | Start a Cloudflare Quick Tunnel |

Use `termux-desk --version` to print the installed version and `Ctrl+C` to stop
the server and tunnel.

## Python API

The public API has no third-party import side effects. Runtime dependencies
and the X11 connection are loaded when the server starts.

```python
from termux_desk import TermuxDeskServer

server = TermuxDeskServer(
    host="127.0.0.1",
    port=8765,
    display=":0",       # defaults to the DISPLAY environment variable
    fps=12,
    quality=70,
)
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
`TermuxDeskError` is raised for missing dependencies, an unset or unreachable
display, missing XTest support, and tunnel startup failures.

## Troubleshooting

**`DISPLAY is not set`**

Set it to the display used by your X11 session:

```bash
export DISPLAY=:0
```

**`Could not connect to X11 display`**

Verify the server is running, the display number is correct, and the process
has permission to connect. From a PRoot environment, preserve or explicitly
set `DISPLAY`.

**`cloudflared was not found`**

Install it in Termux:

```bash
pkg install cloudflared
```

**Pillow fails to install in Termux**

Install its native build dependencies, then retry:

```bash
pkg install python clang make pkg-config libjpeg-turbo libpng
python -m pip install Pillow
```

## Architecture

The root page serves a viewer embedded directly in `termux_desk.server`; there
is no runtime template or static-file lookup. Each WebSocket client receives
JPEG frames and sends small JSON input messages. Pointer coordinates are
normalized in the browser, validated by the server, and scaled to the current
X11 screen dimensions before XTest injection.

## Contributing

1. Fork and clone the repository.
2. Create a virtual environment and run `python -m pip install -e '.[dev]'`.
3. Make a focused change and add tests.
4. Run `pytest` and `python -m build`.
5. Open a pull request describing behavior changes and the X11 environment
   used for manual testing.

Bug reports should include Python version, Termux/PRoot distribution, X server,
window manager, browser, and the exact command used.

## License

[MIT](LICENSE) © 2026 TermuxDesk contributors.
