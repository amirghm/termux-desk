"""Cloudflare Quick Tunnel process management."""

from __future__ import annotations

import re
import shutil
import subprocess
import threading
import time
from queue import Empty, Queue
from typing import Optional, TextIO

from termux_desk.server import TermuxDeskError

_TUNNEL_URL = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


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
        binary = shutil.which(self.executable)
        if binary is None:
            raise TermuxDeskError(
                "cloudflared was not found. In Termux run: pkg install cloudflared"
            )
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
