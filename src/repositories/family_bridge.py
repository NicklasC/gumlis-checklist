"""Worker-to-page transport for the private Gumli family API."""

from __future__ import annotations

import asyncio
import sys
import uuid
from typing import Any, Dict


IS_WEB = sys.platform == "emscripten"
_pending: Dict[str, asyncio.Future] = {}
_message_proxy: Any = None


def _install_listener() -> None:
    global _message_proxy
    if _message_proxy is not None:
        return
    if not IS_WEB:
        raise RuntimeError("Familje-API:t är bara tillgängligt i webbappen")

    import js
    from pyodide.ffi import create_proxy

    def on_message(event):
        data = event.data
        try:
            if str(data.type) != "gumli-family-response":
                return
            request_id = str(data.requestId)
        except Exception:
            return

        future = _pending.pop(request_id, None)
        if future is None or future.done():
            return
        try:
            response = data.response.to_py()
        except Exception:
            response = {"ok": False, "error": "INVALID_RESPONSE"}
        future.set_result(response)

    _message_proxy = create_proxy(on_message)
    js.self.addEventListener("message", _message_proxy)


async def request(payload: dict, timeout_seconds: float = 10.0) -> dict:
    """Send one request without exposing the device token in a URL or log."""
    _install_listener()

    import js
    from pyodide.ffi import to_js

    request_id = str(uuid.uuid4())
    future = asyncio.get_running_loop().create_future()
    _pending[request_id] = future
    message = {
        "type": "gumli-family-request",
        "requestId": request_id,
        "payload": payload,
    }
    js.self.postMessage(to_js(message, dict_converter=js.Object.fromEntries))
    try:
        return await asyncio.wait_for(future, timeout=timeout_seconds)
    finally:
        _pending.pop(request_id, None)
