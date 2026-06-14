"""Stdio transport — what Claude Desktop / Claude Code spawn locally."""
from __future__ import annotations

import asyncio
import os
import sys

from mcp.server.stdio import stdio_server

from .server import build_server


def main() -> None:
    api_key = os.environ.get("SPIMOV_API_KEY", "").strip()
    if not api_key:
        print("WARNING: SPIMOV_API_KEY env var not set; calls will fail until you set it.", file=sys.stderr)

    server = build_server(get_api_key=lambda: api_key)

    async def runner() -> None:
        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())

    asyncio.run(runner())


if __name__ == "__main__":
    main()
