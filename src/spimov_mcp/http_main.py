"""HTTP / SSE transport — runs as a long-lived service (e.g. mcp.spimov.com).

Each request must include an Authorization header with a Spimov API key:
    Authorization: Bearer spk_live_XXXX
The header is forwarded to the underlying REST API as-is.
"""
from __future__ import annotations

import contextvars
import os

import uvicorn
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route

from .server import build_server


_active_key: contextvars.ContextVar[str] = contextvars.ContextVar("spimov_api_key", default="")


def _extract_key(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    # Fallback: ?api_key=... query param (handy for SSE clients that struggle with headers)
    return request.query_params.get("api_key", "").strip()


def make_app() -> Starlette:
    sse = SseServerTransport("/messages/")
    server = build_server(get_api_key=lambda: _active_key.get())

    async def handle_sse(request: Request) -> Response:
        token = _extract_key(request)
        if not token:
            return JSONResponse({"error": "missing_api_key"}, status_code=401)
        ctx_token = _active_key.set(token)
        try:
            async with sse.connect_sse(request.scope, request.receive, request._send) as (read, write):
                await server.run(read, write, server.create_initialization_options())
        finally:
            _active_key.reset(ctx_token)
        return Response()

    async def healthz(_: Request) -> Response:
        return JSONResponse({"status": "ok"})

    return Starlette(
        debug=False,
        routes=[
            Route("/healthz", endpoint=healthz),
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )


def main() -> None:
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8001"))
    uvicorn.run(make_app(), host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
