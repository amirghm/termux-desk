"""Command-line interface for TermuxDesk."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from typing import Optional, Sequence

from termux_desk import __version__
from termux_desk.server import TermuxDeskError, TermuxDeskServer
from termux_desk.tunnel import LocalhostRunTunnel


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="termux-desk", description="Web-based remote desktop for X11")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    start = subparsers.add_parser("start", help="start the remote desktop server")
    start.add_argument("--host", default="127.0.0.1", help="listen address (default: %(default)s)")
    start.add_argument("--port", type=int, default=8765, help="listen port (default: %(default)s)")
    start.add_argument("--display", help="X11 display; defaults to DISPLAY")
    start.add_argument("--fps", type=float, default=12.0, help="maximum frames per second")
    start.add_argument("--quality", type=int, default=70, help="JPEG quality from 1 to 95")
    start.add_argument("--tunnel", action="store_true", help="start a localhost.run tunnel")
    return parser


def _print_banner(version: str, remote_url: Optional[str], local_url: str, code: str) -> None:
    """Print a styled startup banner."""
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    GRAY = "\033[37m"
    R = "\033[0m"

    banner = (
        " ______                               ____            __  \n"
        " /_  __/__  _________ ___  __  ___  __/ __ \\___  _____/ /__\n"
        "  / / / _ \\/ ___/ __ `__ \\/ / / / |/_/ / / / _ \\/ ___/ //_/\n"
        " / / /  __/ /  / / / / / / /_/ />  </ /_/ /  __(__  ) ,<   \n"
        "/_/  \\___/_/  /_/ /_/ /_/\\__,_/_/|_/_____/\\___/____/_/|_|"
    )
    print()
    for line in banner.split("\n"):
        print("  " + CYAN + line + R)
    print("  " + GRAY + " v" + version + R)
    print()
    if remote_url:
        print("  Remote  " + GREEN + remote_url + R)
    print("  Local   " + GREEN + local_url + R)
    print()
    print("  Code    " + YELLOW + code + R)
    print()
    print("  " + GRAY + "Press Ctrl+C to stop." + R)
    print()


async def _start(args: argparse.Namespace) -> None:
    display = args.display or os.environ.get("DISPLAY")
    if not display:
        raise TermuxDeskError(
            "DISPLAY is not set. Start your X11/VNC desktop, then run "
            "`export DISPLAY=:0` (using the display number from your session)."
        )
    server = TermuxDeskServer(
        args.host, args.port, display=display, fps=args.fps, quality=args.quality
    )
    tunnel: Optional[LocalhostRunTunnel] = None
    await server.start()
    try:
        local_url = server.local_url
        remote_url: Optional[str] = None
        if args.tunnel:
            tunnel = LocalhostRunTunnel(args.port)
            remote_url = await asyncio.to_thread(tunnel.start)
        _print_banner(__version__, remote_url, local_url, server._auth_code)
        await asyncio.Event().wait()
    finally:
        if tunnel is not None:
            await asyncio.to_thread(tunnel.stop)
        await server.stop()


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the TermuxDesk command-line interface."""
    args = build_parser().parse_args(argv)
    try:
        if args.command == "start":
            asyncio.run(_start(args))
    except KeyboardInterrupt:
        print("\nTermuxDesk stopped.", file=sys.stderr)
    except (TermuxDeskError, ValueError, OSError) as exc:
        print(f"termuxdesk: error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
