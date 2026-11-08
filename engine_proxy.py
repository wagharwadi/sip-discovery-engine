"""Serve the Discovery Engine (Streamlit) at /engine/ from the same server as the MVP.

Why: on Render's free plan only one free service would run at a time (waking one left the other stuck), so the two
apps share one server and still get two separate links that work at the same time:
    /         Rhythm SIP MVP (rhythm_app.py)
    /engine/  Discovery Engine (streamlit_app.py, run as a child process on localhost)
This module starts Streamlit and forwards its HTTP requests and its WebSocket to it.
"""
import asyncio
import os
import subprocess
import sys
from pathlib import Path

import httpx
from starlette.background import BackgroundTask
from starlette.responses import HTMLResponse, RedirectResponse, StreamingResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

PREFIX = "engine"
PORT = int(os.environ.get("ENGINE_PORT", "8611"))
UPSTREAM = f"127.0.0.1:{PORT}"
HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers", "transfer-encoding",
       "upgrade", "host", "accept-encoding", "content-length"}
STARTING = ("<!doctype html><meta charset=utf-8><meta http-equiv=refresh content=4><title>Starting…</title>"
            "<body style=\"font-family:system-ui;color:#44475B;display:grid;place-items:center;height:90vh\">"
            "<p>The Discovery Engine is waking up. This page refreshes by itself in a few seconds.</p>")
_proc, _client = None, None


def start(root: Path):
    """Launch Streamlit on localhost under the /engine base path (once)."""
    global _proc
    if _proc and _proc.poll() is None:
        return
    _proc = subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(root / "streamlit_app.py"),
                              "--server.port", str(PORT), "--server.address", "127.0.0.1", "--server.headless", "true",
                              "--server.baseUrlPath", PREFIX, "--server.enableCORS", "false",
                              "--server.enableXsrfProtection", "false", "--browser.gatherUsageStats", "false"],
                             cwd=str(root))


def stop():
    if _proc and _proc.poll() is None:
        _proc.terminate()


async def _http(request):
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=httpx.Timeout(120, connect=5))
    url = f"http://{UPSTREAM}{request.url.path}" + (f"?{request.url.query}" if request.url.query else "")
    headers = [(k, v) for k, v in request.headers.items() if k.lower() not in HOP] + [("accept-encoding", "identity")]
    try:
        resp = await _client.send(_client.build_request(request.method, url, headers=headers, content=await request.body()),
                                  stream=True)
    except httpx.TransportError:                         # Streamlit still booting after a cold start
        return HTMLResponse(STARTING, status_code=503, headers={"Retry-After": "4", "Cache-Control": "no-store"})
    out = {k: v for k, v in resp.headers.items() if k.lower() not in HOP}
    return StreamingResponse(resp.aiter_raw(), status_code=resp.status_code, headers=out, background=BackgroundTask(resp.aclose))


async def _ws(ws: WebSocket):
    """Relay Streamlit's browser WebSocket both ways, keeping its subprotocol and cookies."""
    target = f"ws://{UPSTREAM}{ws.url.path}" + (f"?{ws.url.query}" if ws.url.query else "")
    protos = [p.strip() for p in ws.headers.get("sec-websocket-protocol", "").split(",") if p.strip()]
    fwd = {k: v for k, v in ws.headers.items() if k.lower() in ("cookie", "user-agent")}
    try:
        up = await connect(target, subprotocols=protos or None, additional_headers=fwd, max_size=None,
                           compression=None, open_timeout=15)
    except Exception:
        await ws.close(code=1011)
        return
    await ws.accept(subprotocol=up.subprotocol)

    async def browser_to_engine():
        try:
            while True:
                m = await ws.receive()
                if m["type"] == "websocket.disconnect":
                    break
                if m.get("bytes") is not None:
                    await up.send(m["bytes"])
                elif m.get("text") is not None:
                    await up.send(m["text"])
        finally:
            await up.close()

    async def engine_to_browser():
        try:
            async for m in up:
                await (ws.send_bytes(m) if isinstance(m, bytes) else ws.send_text(m))
        except ConnectionClosed:
            pass
        finally:
            try:
                await ws.close()
            except Exception:
                pass
    await asyncio.gather(browser_to_engine(), engine_to_browser(), return_exceptions=True)


ROUTES = [
    Route(f"/{PREFIX}", lambda r: RedirectResponse(f"/{PREFIX}/")),
    WebSocketRoute(f"/{PREFIX}/_stcore/stream", _ws),
    Route(f"/{PREFIX}/{{path:path}}", _http, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]),
]
