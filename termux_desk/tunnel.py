"""Cloudflare Quick Tunnel process management."""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path
from queue import Empty, Queue
from typing import Optional, TextIO

from termux_desk.server import TermuxDeskError

_TUNNEL_URL = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
_LOCAL_BIN = Path.home() / ".local" / "bin"


def _ensure_cloudflared() -> str:
    """Return the cloudflared binary path, downloading it if necessary."""
    binary = shutil.which("cloudflared")
    if binary:
        return binary

    cached = _LOCAL_BIN / "cloudflared"
    if cached.is_file():
        return str(cached)

    _LOCAL_BIN.mkdir(parents=True, exist_ok=True)

    arch = platform.machine()
    arch_map = {"aarch64": "arm64", "armv7l": "arm", "x86_64": "amd64", "i686": "386"}
    cf_arch = arch_map.get(arch, arch)
    url = f"https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-{cf_arch}"

    print(f"Downloading cloudflared for {arch}...", flush=True)
    try:
        subprocess.run(
            ["curl", "-fsSL", "-o", str(cached), url],
            check=True,
            timeout=60,
        )
        cached.chmod(0o755)
        print(f"cloudflared installed to {cached}", flush=True)
        return str(cached)
    except Exception as exc:
        cached.unlink(missing_ok=True)
        raise TermuxDeskError(
            f"Failed to download cloudflared: {exc}\n"
            "Install manually:\n"
            "  Termux: pkg install cloudflared\n"
            "  Linux:  curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared"
        ) from exc


class CloudflareTunnel:
    """Manage a temporary ``cloudflared tunnel --url`` subprocess."""

    def __init__(self, local_url: str, *, executable: str = "cloudflared") -> None:
        self.local_url = local_url
        self.executable = executable
        self.url: Optional[str] = None
        self._process: Optional[subprocess.Popen[str]] = None

    def start(self, timeout: float = 20.0) -> str:
        """Start cloudflared and wait for its public URL."""
        if self._process is not None:
            if self.url:
                return self.url
            raise TermuxDeskError("Cloudflare tunnel is already starting.")
        binary = _ensure_cloudflared()
        self._process = subprocess.Popen(
            [binary, "tunnel", "--url", self.local_url, "--no-autoupdate"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        lines: Queue[str] = Queue()
        url_found = threading.Event()
        reader = threading.Thread(
            target=self._read_output,
            args=(self._process.stdout, lines, url_found),
            daemon=True,
        )
        reader.start()
        deadline = time.monotonic() + timeout
        output: list[str] = []
        while time.monotonic() < deadline:
            if self._process.poll() is not None and lines.empty():
                detail = "\n".join(output[-5:]) or "cloudflared exited without output"
                self.stop()
                raise TermuxDeskError(f"Cloudflare tunnel failed to start:\n{detail}")
            try:
                line = lines.get(timeout=0.2)
            except Empty:
                continue
            output.append(line.rstrip())
            match = _TUNNEL_URL.search(line)
            if match:
                self.url = match.group(0)
                url_found.set()
                return self.url
        url_found.set()
        self.stop()
        raise TermuxDeskError("Timed out waiting for a Cloudflare Quick Tunnel URL.")

    @staticmethod
    def _read_output(
        stream: Optional[TextIO], lines: Queue[str], url_found: threading.Event
    ) -> None:
        if stream is not None:
            for line in stream:
                if not url_found.is_set():
                    lines.put(line)

    def stop(self) -> None:
        """Terminate the cloudflared subprocess if it is running."""
        process, self._process = self._process, None
        self.url = None
        if process is None or process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    def __enter__(self) -> "CloudflareTunnel":
        self.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.stop()
