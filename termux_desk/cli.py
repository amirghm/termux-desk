"""Command-line interface for TermuxDesk."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from typing import Optional, Sequence

from termux_desk import __version__
from termux_desk.server import TermuxDeskError, TermuxDeskServer
from termux_desk.tunnel import CloudflareTunnel


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
    start.add_argument("--tunnel", action="store_true", help="start a Cloudflare Quick Tunnel")
    return parser


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
    tunnel: Optional[CloudflareTunnel] = None
    await server.start()
    try:
        url = server.local_url
        if args.tunnel:
            tunnel = CloudflareTunnel(url)
            url = await asyncio.to_thread(tunnel.start)
        print(f"TermuxDesk is running at {url}", flush=True)
        print("Press Ctrl+C to stop.", flush=True)
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
