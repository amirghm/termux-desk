"""aiohttp server, X11 capture, and XTest input injection."""

from __future__ import annotations

import asyncio
import contextlib
import io
import json
import os
import subprocess
from dataclasses import dataclass
from typing import Any, Optional


VIEWER_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
  <title>TermuxDesk</title>
  <style>
    :root { color-scheme: dark; font-family: system-ui, sans-serif; --bar: #1f2937; --panel: #1f2937f2;
      --button: #374151; --border: #4b5563; --text: #f9fafb; --muted: #9ca3af; --stage: #030712; }
    * { box-sizing: border-box; }
    html, body { margin: 0; width: 100%; height: 100%; overflow: hidden; background: var(--stage); color: var(--text); }
    body { display: grid; grid-template-rows: auto 1fr; }
    header { display: flex; align-items: center; gap: .65rem; padding: .55rem .7rem; background: var(--bar);
      border-bottom: 1px solid var(--border); box-shadow: 0 .15rem .75rem #0004; z-index: 2; }
    strong { white-space: nowrap; }
    .toolbar { display: flex; align-items: center; gap: .35rem; margin-left: auto; }
    .group { display: flex; gap: .3rem; }
    .divider { width: 1px; height: 1.5rem; margin: 0 .15rem; background: var(--border); }
    button { border: 1px solid var(--border); border-radius: .45rem; padding: .43rem .62rem; color: var(--text);
      background: var(--button); cursor: pointer; font: inherit; white-space: nowrap; }
    button:hover { filter: brightness(1.12); }
    button.active { border-color: #60a5fa; background: #1d4ed8; }
    .metrics { display: flex; align-items: center; gap: .45rem; color: var(--muted); font-size: .8rem; white-space: nowrap; }
    #status { width: .65rem; height: .65rem; border-radius: 50%; background: #ef4444; box-shadow: 0 0 .45rem currentColor; }
    #stage { display: grid; place-items: center; min-height: 0; background: var(--stage); touch-action: none; }
    #screen { display: block; max-width: 100%; max-height: 100%; user-select: none; -webkit-user-drag: none; }
    #help { position: fixed; inset: 4rem 1rem auto auto; width: min(25rem, calc(100% - 2rem)); padding: 1rem;
      border: 1px solid var(--border); border-radius: .75rem; background: var(--panel); box-shadow: 0 .5rem 2rem #0008; z-index: 3; }
    #help[hidden] { display: none; }
    #help h2 { margin: 0 0 .8rem; font-size: 1.1rem; }
    #help dl { display: grid; grid-template-columns: auto 1fr; gap: .65rem .9rem; margin: 0; }
    #help dt { font-weight: 700; white-space: nowrap; }
    #help dd { margin: 0; color: var(--muted); }
    #notice { position: fixed; left: 50%; bottom: 1rem; translate: -50% 0; padding: .55rem .8rem;
      border: 1px solid var(--border); border-radius: .5rem; background: var(--panel); box-shadow: 0 .3rem 1rem #0007; z-index: 4; }
    #notice[hidden] { display: none; }
    kbd { padding: .1rem .3rem; border: 1px solid #6b7280; border-radius: .2rem; background: #111827; }
    @media (max-width: 48rem) {
      header { gap: .4rem; }
      strong { display: none; }
      .toolbar { margin-left: 0; flex: 1; }
      button { padding: .42rem .5rem; }
      .metrics { margin-left: auto; }
      .statusText { display: none; }
    }
    @media (max-width: 34rem) {
      button { font-size: 0; }
      button::first-letter { font-size: 1rem; }
      .divider { margin: 0; }
      #fps { display: none; }
    }
  </style>
</head>
<body>
  <header>
    <strong>TermuxDesk</strong>
    <nav class="toolbar" aria-label="Viewer controls">
      <span class="group"><button id="clickMode" class="active">🖱️ Click</button><button id="dragMode">✋ Drag</button></span>
      <span class="divider" aria-hidden="true"></span>
      <span class="group"><button id="copyButton">📋 Copy</button><button id="pasteButton">📝 Paste</button></span>
      <span class="divider" aria-hidden="true"></span>
      <button id="helpButton">❓ Help</button>
    </nav>
    <span class="metrics"><span id="status" title="Disconnected"></span><span class="statusText">Disconnected</span><span id="fps">0 FPS</span></span>
  </header>
  <main id="stage"><img id="screen" alt="Remote desktop"></main>
  <aside id="help" hidden>
    <h2>Controls</h2>
    <dl>
      <dt>🖱️ Click</dt><dd>Tap or press to click immediately. Press twice quickly to double-click.</dd>
      <dt>✋ Drag</dt><dd>Press, move, and release to drag with the primary button.</dd>
      <dt>📋 Copy</dt><dd>Read the X11 clipboard into your browser clipboard.</dd>
      <dt>📝 Paste</dt><dd>Send browser clipboard text to the X11 clipboard. <kbd>Ctrl</kbd>+<kbd>V</kbd> also works.</dd>
      <dt>Keyboard</dt><dd>Type while this page is focused. Browser-reserved shortcuts may stay local.</dd>
      <dt>Close</dt><dd>Press <kbd>Esc</kbd> to close this panel.</dd>
    </dl>
  </aside>
  <div id="notice" hidden role="status"></div>
<script>
(() => {
  const image = document.querySelector("#screen");
  const status = document.querySelector("#status");
  const statusText = document.querySelector(".statusText");
  const fps = document.querySelector("#fps");
  const help = document.querySelector("#help");
  const notice = document.querySelector("#notice");
  const clickButton = document.querySelector("#clickMode");
  const dragButton = document.querySelector("#dragMode");
  let ws, frameUrl, noticeTimer, lastClick = 0, lastPoint = null;
  let frameCount = 0, fpsStarted = performance.now();
  let mode = "click", dragging = false, reconnectDelay = 500;

  function send(type, data = {}) {
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({type, ...data}));
  }
  function point(event) {
    const r = image.getBoundingClientRect();
    return {
      x: Math.max(0, Math.min(1, (event.clientX - r.left) / r.width)),
      y: Math.max(0, Math.min(1, (event.clientY - r.top) / r.height))
    };
  }
  function showNotice(message) {
    notice.textContent = message; notice.hidden = false;
    clearTimeout(noticeTimer); noticeTimer = setTimeout(() => notice.hidden = true, 3000);
  }
  async function pasteClipboard(text) {
    try {
      const value = text === undefined ? await navigator.clipboard.readText() : text;
      send("clipboard", {text: value}); showNotice("Clipboard sent");
    } catch (error) {
      showNotice("Clipboard access was denied");
    }
  }
  function connect() {
    const scheme = location.protocol === "https:" ? "wss" : "ws";
    ws = new WebSocket(`${scheme}://${location.host}/ws`);
    ws.binaryType = "blob";
    ws.onopen = () => {
      status.style.background = "#22c55e"; status.title = "Connected"; statusText.textContent = "Connected"; reconnectDelay = 500;
    };
    ws.onmessage = event => {
      if (!(event.data instanceof Blob)) {
        try {
          const message = JSON.parse(event.data);
          if (message.type === "clipboard") {
            navigator.clipboard.writeText(message.text).then(
              () => showNotice("Clipboard copied"),
              () => showNotice("Clipboard received, but browser access was denied")
            );
          } else if (message.type === "error") showNotice(message.message);
        } catch (error) {}
        return;
      }
      if (frameUrl) URL.revokeObjectURL(frameUrl);
      frameUrl = URL.createObjectURL(event.data);
      image.onload = () => {
        send("ready"); frameCount++;
        const now = performance.now();
        if (now - fpsStarted >= 1000) {
          fps.textContent = `${Math.round(frameCount * 1000 / (now - fpsStarted))} FPS`;
          frameCount = 0; fpsStarted = now;
        }
      };
      image.src = frameUrl;
    };
    ws.onclose = () => {
      status.style.background = "#ef4444"; status.title = "Disconnected"; statusText.textContent = "Disconnected"; fps.textContent = "0 FPS";
      setTimeout(connect, reconnectDelay); reconnectDelay = Math.min(reconnectDelay * 2, 5000);
    };
  }
  function setMode(next) {
    mode = next;
    clickButton.classList.toggle("active", mode === "click");
    dragButton.classList.toggle("active", mode === "drag");
  }
  clickButton.onclick = () => setMode("click");
  dragButton.onclick = () => setMode("drag");
  document.querySelector("#copyButton").onclick = () => send("copy_request");
  document.querySelector("#pasteButton").onclick = () => pasteClipboard();
  document.querySelector("#helpButton").onclick = () => help.hidden = !help.hidden;

  image.addEventListener("contextmenu", event => event.preventDefault());
  image.addEventListener("pointerdown", event => {
    event.preventDefault(); image.focus(); image.setPointerCapture(event.pointerId);
    const p = point(event);
    if (mode === "drag" && event.button === 0) {
      dragging = true; send("button", {...p, button: 1, down: true});
    } else if (mode === "click" && event.button === 0) {
      const now = performance.now();
      const nearby = lastPoint && Math.abs(lastPoint.x - p.x) < .02 && Math.abs(lastPoint.y - p.y) < .02;
      if (nearby && now - lastClick < 300) {
        send("dblclick", {...p, button: 1}); lastClick = 0; lastPoint = null;
      } else {
        send("click", {...p, button: 1}); lastClick = now; lastPoint = p;
      }
    } else if (mode === "click") send("click", {...p, button: event.button + 1});
  });
  image.addEventListener("pointermove", event => {
    if (event.pointerType === "mouse" || dragging) send("move", point(event));
  });
  function releaseDrag(event) {
    event.preventDefault(); const p = point(event);
    if (dragging) { send("button", {...p, button: 1, down: false}); dragging = false; }
  }
  image.addEventListener("pointerup", releaseDrag);
  image.addEventListener("pointercancel", releaseDrag);
  image.addEventListener("dblclick", event => event.preventDefault());
  image.addEventListener("wheel", event => {
    event.preventDefault();
    send("scroll", {...point(event), dx: Math.sign(event.deltaX), dy: Math.sign(event.deltaY)});
  }, {passive: false});

  window.addEventListener("keydown", event => {
    if (!help.hidden && event.key === "Escape") { help.hidden = true; return; }
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "v") return;
    if (event.key.length === 1 && !event.ctrlKey && !event.altKey && !event.metaKey) {
      send("char", {char: event.key});
    } else {
      send("key", {key: event.key, down: true, ctrl: event.ctrlKey, alt: event.altKey,
        shift: event.shiftKey, meta: event.metaKey});
    }
    if (!["F5", "F11", "F12"].includes(event.key)) event.preventDefault();
  });
  window.addEventListener("keyup", event => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "v") return;
    if (event.key.length !== 1 || event.ctrlKey || event.altKey || event.metaKey) {
      send("key", {key: event.key, down: false, ctrl: event.ctrlKey, alt: event.altKey,
        shift: event.shiftKey, meta: event.metaKey});
      event.preventDefault();
    }
  });
  document.addEventListener("paste", event => {
    const text = event.clipboardData && event.clipboardData.getData("text");
    if (text !== null && text !== undefined) {
      event.preventDefault(); pasteClipboard(text);
    }
  });
  connect();
})();
</script>
</body>
</html>
"""


class TermuxDeskError(RuntimeError):
    """Base exception for actionable TermuxDesk startup failures."""


def _runtime_imports() -> tuple[Any, Any, Any, Any, Any]:
    try:
        from aiohttp import WSMsgType, web
    except ImportError as exc:
        raise TermuxDeskError(
            "aiohttp is required. Install it with: pip install aiohttp"
        ) from exc
    try:
        from PIL import ImageGrab
    except ImportError as exc:
        raise TermuxDeskError(
            "Pillow is required. Install it with: pip install Pillow"
        ) from exc
    try:
        from Xlib import XK, X
        from Xlib.display import Display
        from Xlib.ext import xtest
    except ImportError as exc:
        raise TermuxDeskError(
            "python-xlib is required. Install it with: pip install python-xlib"
        ) from exc
    return web, WSMsgType, ImageGrab, (X, XK, Display), xtest


@dataclass
class _Runtime:
    web: Any
    ws_message_type: Any
    image_grab: Any
    x: Any
    xk: Any
    display: Any
    xtest: Any


class TermuxDeskServer:
    """Capture an X11 display and expose it through an HTTP/WebSocket server."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8765,
        *,
        display: Optional[str] = None,
        fps: float = 12.0,
        quality: int = 70,
    ) -> None:
        if not 1 <= port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        if fps <= 0:
            raise ValueError("fps must be greater than zero")
        if not 1 <= quality <= 95:
            raise ValueError("quality must be between 1 and 95")
        self.host = host
        self.port = port
        self.display_name = display or os.environ.get("DISPLAY")
        self.fps = fps
        self.quality = quality
        self._runtime: Optional[_Runtime] = None
        self._runner: Any = None
        self._site: Any = None
        self._x_lock: Optional[asyncio.Lock] = None

    @property
    def local_url(self) -> str:
        """Return the URL clients can use on the local machine."""
        public_host = "127.0.0.1" if self.host in {"0.0.0.0", "::"} else self.host
        return f"http://{public_host}:{self.port}"

    def _require_display(self) -> str:
        if not self.display_name:
            raise TermuxDeskError(
                "DISPLAY is not set. Start your X11/VNC desktop and export DISPLAY "
                "(for example: export DISPLAY=:0)."
            )
        return self.display_name

    async def start(self) -> "TermuxDeskServer":
        """Start listening without blocking the current event loop."""
        if self._runner is not None:
            return self
        display_name = self._require_display()
        web, ws_type, image_grab, xlib, xtest = _runtime_imports()
        x, xk, display_class = xlib
        try:
            x_display = display_class(display_name)
        except Exception as exc:
            raise TermuxDeskError(
                f"Could not connect to X11 display {display_name!r}: {exc}"
            ) from exc
        if not x_display.has_extension("XTEST"):
            x_display.close()
            raise TermuxDeskError(f"XTEST is not available on display {display_name!r}.")

        self._runtime = _Runtime(web, ws_type, image_grab, x, xk, x_display, xtest)
        self._x_lock = asyncio.Lock()
        app = web.Application()
        app.router.add_get("/", self._handle_index)
        app.router.add_get("/health", self._handle_health)
        app.router.add_get("/ws", self._handle_websocket)
        runner = web.AppRunner(app)
        try:
            await runner.setup()
            site = web.TCPSite(runner, self.host, self.port)
            await site.start()
        except Exception:
            await runner.cleanup()
            x_display.close()
            self._runtime = None
            raise
        self._runner, self._site = runner, site
        return self

    async def stop(self) -> None:
        """Stop the HTTP server and close the X11 connection."""
        if self._runner is not None:
            await self._runner.cleanup()
        if self._runtime is not None:
            self._runtime.display.close()
        self._runner = self._site = self._runtime = self._x_lock = None

    def run(self) -> None:
        """Run until interrupted."""
        async def serve() -> None:
            await self.start()
            try:
                await asyncio.Event().wait()
            finally:
                await self.stop()

        try:
            asyncio.run(serve())
        except KeyboardInterrupt:
            pass

    async def _handle_index(self, request: Any) -> Any:
        return self._runtime.web.Response(text=VIEWER_HTML, content_type="text/html")

    async def _handle_health(self, request: Any) -> Any:
        return self._runtime.web.json_response({"status": "ok"})

    async def _handle_websocket(self, request: Any) -> Any:
        runtime = self._runtime
        ws = runtime.web.WebSocketResponse(heartbeat=30, max_msg_size=64 * 1024)
        await ws.prepare(request)
        sender = asyncio.create_task(self._stream_frames(ws))
        try:
            async for message in ws:
                if message.type == runtime.ws_message_type.TEXT:
                    await self._handle_input(message.data, ws)
                elif message.type == runtime.ws_message_type.ERROR:
                    break
        finally:
            sender.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await sender
        return ws

    async def _stream_frames(self, ws: Any) -> None:
        interval = 1.0 / self.fps
        while not ws.closed:
            started = asyncio.get_running_loop().time()
            try:
                frame = await asyncio.to_thread(self._capture_frame)
                await ws.send_bytes(frame)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                await ws.send_str(json.dumps({"type": "error", "message": str(exc)}))
                await asyncio.sleep(1)
            elapsed = asyncio.get_running_loop().time() - started
            await asyncio.sleep(max(0, interval - elapsed))

    def _capture_frame(self) -> bytes:
        image = self._runtime.image_grab.grab(xdisplay=self.display_name)
        if image.mode != "RGB":
            image = image.convert("RGB")
        output = io.BytesIO()
        image.save(output, "JPEG", quality=self.quality, optimize=True)
        return output.getvalue()

    async def _handle_input(self, raw_message: str, ws: Any = None) -> None:
        try:
            event = json.loads(raw_message)
            if not isinstance(event, dict) or not isinstance(event.get("type"), str):
                return
            if event["type"] in {"clipboard", "copy_request"}:
                await self._handle_clipboard(event, ws)
                return
            if self._x_lock is None:
                return
            async with self._x_lock:
                self._inject_event(event)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return

    async def _handle_clipboard(self, event: dict[str, Any], ws: Any) -> None:
        try:
            if event["type"] == "clipboard":
                text = event.get("text")
                if not isinstance(text, str):
                    return
                await asyncio.to_thread(self._set_clipboard, text)
            else:
                text = await asyncio.to_thread(self._get_clipboard)
                if ws is not None and not ws.closed:
                    await ws.send_str(json.dumps({"type": "clipboard", "text": text}))
        except (OSError, subprocess.SubprocessError) as exc:
            if ws is not None and not ws.closed:
                await ws.send_str(json.dumps({
                    "type": "error",
                    "message": f"Clipboard unavailable: {exc}",
                }))

    def _run_clipboard(self, cmd: list[str], text: Optional[str] = None) -> str:
        env = os.environ.copy()
        if self.display_name:
            env["DISPLAY"] = self.display_name
        result = subprocess.run(
            cmd,
            input=text,
            capture_output=True,
            text=True,
            timeout=3,
            check=True,
            env=env,
        )
        return result.stdout

    def _set_clipboard(self, text: str) -> None:
        errors = []
        for cmd in (
            ["xclip", "-selection", "clipboard", "-filter"],
            ["xsel", "--clipboard", "--input"],
        ):
            try:
                self._run_clipboard(cmd, text)
                return
            except (FileNotFoundError, subprocess.SubprocessError) as exc:
                errors.append(f"{cmd[0]}: {exc}")
        raise OSError("; ".join(errors))

    def _get_clipboard(self) -> str:
        errors = []
        for cmd in (
            ["xclip", "-selection", "clipboard", "-o"],
            ["xsel", "--clipboard", "--output"],
        ):
            try:
                return self._run_clipboard(cmd)
            except (FileNotFoundError, subprocess.SubprocessError) as exc:
                errors.append(f"{cmd[0]}: {exc}")
        raise OSError("; ".join(errors))

    def _point(self, event: dict[str, Any]) -> tuple[int, int]:
        x = min(1.0, max(0.0, float(event["x"])))
        y = min(1.0, max(0.0, float(event["y"])))
        screen = self._runtime.display.screen()
        return round(x * (screen.width_in_pixels - 1)), round(y * (screen.height_in_pixels - 1))

    def _inject_event(self, event: dict[str, Any]) -> None:
        runtime = self._runtime
        event_type = event["type"]
        if event_type == "ready":
            return
        if event_type in {"move", "click", "dblclick", "button", "scroll"}:
            x, y = self._point(event)
            runtime.xtest.fake_input(runtime.display, runtime.x.MotionNotify, x=x, y=y)
        if event_type == "move":
            runtime.display.sync()
            return
        if event_type in {"click", "dblclick"}:
            button = self._button(event.get("button", 1))
            self._mouse_button(button, True)
            self._mouse_button(button, False)
        elif event_type == "button":
            self._mouse_button(self._button(event.get("button", 1)), bool(event["down"]))
        elif event_type == "scroll":
            dx, dy = int(event.get("dx", 0)), int(event.get("dy", 0))
            for button, count in ((4 if dy < 0 else 5, abs(dy)), (6 if dx < 0 else 7, abs(dx))):
                for _ in range(min(count, 10)):
                    self._mouse_button(button, True)
                    self._mouse_button(button, False)
        elif event_type == "char":
            char = event["char"]
            if isinstance(char, str) and len(char) == 1:
                self._type_character(char)
        elif event_type == "key":
            self._key_event(event)
        runtime.display.sync()

    @staticmethod
    def _button(value: Any) -> int:
        button = int(value)
        if button not in {1, 2, 3}:
            raise ValueError("unsupported mouse button")
        return button

    def _mouse_button(self, button: int, down: bool) -> None:
        event_type = self._runtime.x.ButtonPress if down else self._runtime.x.ButtonRelease
        self._runtime.xtest.fake_input(self._runtime.display, event_type, button)

    def _type_character(self, char: str) -> None:
        runtime = self._runtime
        keysym = runtime.xk.string_to_keysym(char)
        if keysym == 0:
            keysym = ord(char)
        keycode = runtime.display.keysym_to_keycode(keysym)
        if keycode == 0:
            return
        shift = char.isupper() or char in '~!@#$%^&*()_+{}|:"<>?'
        shift_code = runtime.display.keysym_to_keycode(runtime.xk.string_to_keysym("Shift_L"))
        if shift:
            runtime.xtest.fake_input(runtime.display, runtime.x.KeyPress, shift_code)
        runtime.xtest.fake_input(runtime.display, runtime.x.KeyPress, keycode)
        runtime.xtest.fake_input(runtime.display, runtime.x.KeyRelease, keycode)
        if shift:
            runtime.xtest.fake_input(runtime.display, runtime.x.KeyRelease, shift_code)

    def _key_event(self, event: dict[str, Any]) -> None:
        runtime = self._runtime
        names = {
            " ": "space", "Enter": "Return", "Escape": "Escape", "Backspace": "BackSpace",
            "Tab": "Tab", "Delete": "Delete", "Insert": "Insert", "Home": "Home", "End": "End",
            "PageUp": "Prior", "PageDown": "Next", "ArrowUp": "Up", "ArrowDown": "Down",
            "ArrowLeft": "Left", "ArrowRight": "Right", "Control": "Control_L",
            "Alt": "Alt_L", "Shift": "Shift_L", "Meta": "Super_L",
        }
        key = str(event["key"])
        keysym = runtime.xk.string_to_keysym(names.get(key, key))
        keycode = runtime.display.keysym_to_keycode(keysym)
        if keycode:
            event_type = runtime.x.KeyPress if bool(event["down"]) else runtime.x.KeyRelease
            runtime.xtest.fake_input(runtime.display, event_type, keycode)


def run_server(**kwargs: Any) -> None:
    """Create and run a :class:`TermuxDeskServer`."""
    TermuxDeskServer(**kwargs).run()
