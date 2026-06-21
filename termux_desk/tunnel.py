"""SSH-based tunnel to expose a local port via localhost.run."""

from __future__ import annotations

import os
import pty
import re
import subprocess
import threading
from typing import Optional


class LocalhostRunTunnel:
    """Expose a local HTTP server through localhost.run."""

    def __init__(self, local_port: int) -> None:
        self.local_port = local_port
        self._process: Optional[subprocess.Popen] = None
        self._url: Optional[str] = None
        self._ready = threading.Event()

    def start(self) -> str:
        """Start the tunnel and return the public URL."""
        master_fd, slave_fd = pty.openpty()
        cmd = [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ServerAliveInterval=30",
            "-R", f"80:localhost:{self.local_port}",
            "nokey@localhost.run",
        ]
        self._process = subprocess.Popen(
            cmd,
            stdout=slave_fd,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
        )
        os.close(slave_fd)

        # Read output until we get the URL
        buf = b""
        while True:
            try:
                chunk = os.read(master_fd, 1024)
            except OSError:
                break
            if not chunk:
                break
            buf += chunk
            text = buf.decode("utf-8", errors="replace")
            # localhost.run prints the URL like: https://xxxx.lhr.life
            match = re.search(r"(https://[^\s]+\.lhr\.life[^\s]*)", text)
            if match:
                self._url = match.group(1)
                self._ready.set()
                os.close(master_fd)
                return self._url

        os.close(master_fd)
        raise RuntimeError("Failed to get URL from localhost.run")

    def stop(self) -> None:
        """Stop the tunnel."""
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
