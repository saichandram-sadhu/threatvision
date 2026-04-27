"""Reject oversized HTTP request bodies using Content-Length (M17)."""

from __future__ import annotations

from starlette.datastructures import Headers
from starlette.responses import PlainTextResponse


class MaxRequestBodyMiddleware:
    """Return 413 when ``Content-Length`` exceeds the configured maximum."""

    def __init__(self, app, max_content_length: int) -> None:
        self.app = app
        self.max_content_length = max_content_length

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        if scope.get("method", "GET").upper() not in ("POST", "PUT", "PATCH"):
            await self.app(scope, receive, send)
            return
        headers = Headers(scope=scope)
        cl = headers.get("content-length")
        if cl is None:
            await self.app(scope, receive, send)
            return
        try:
            length = int(cl)
        except ValueError:
            resp = PlainTextResponse("Invalid Content-Length", status_code=400)
            await resp(scope, receive, send)
            return
        if length > self.max_content_length:
            resp = PlainTextResponse("Payload Too Large", status_code=413)
            await resp(scope, receive, send)
            return
        await self.app(scope, receive, send)
