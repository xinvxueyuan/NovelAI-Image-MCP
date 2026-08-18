"""MCP server (fastmcp): lifespan owns the shared httpx session + NovelAIClient.

The server is a thin composition root over ``nai.NovelAIClient``, built on the
fastmcp 4 framework (which itself runs on the MCP SDK v2). The lifespan creates
one long-lived ``httpx.AsyncClient`` (connection pooling, with Chrome TLS +
header fingerprint impersonation via ``create_http_client``) and one
``NovelAIClient``; every tool reads them from ``ctx.lifespan_context`` (the
fastmcp ``Context`` property that exposes the lifespan yield value). Transport
is selected at runtime from ``MCP_TRANSPORT`` (stdio by default,
streamable-http for remote deployments).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ._mcp import FastMCP
from .nai import NovelAIClient, create_http_client, create_novelai_client
from .settings import (
    NovelAISettings,
    get_mcp_settings,
    get_novelai_settings,
)
from .tools import register_all


@dataclass
class AppContext:
    """Shared state yielded by the lifespan to every tool invocation."""

    client: NovelAIClient
    settings: NovelAISettings


@asynccontextmanager
async def lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
    """Build the NovelAI client from settings; tear down on shutdown."""
    settings = get_novelai_settings()
    if not settings.has_credentials():
        raise RuntimeError(
            "NovelAI credentials are not configured: set NOVELAI_TOKEN or "
            "NOVELAI_USERNAME + NOVELAI_PASSWORD (see .env.example)."
        )
    # ``create_http_client`` returns an ``httpx.AsyncClient`` backed by
    # ``curl_cffi`` (Chrome TLS fingerprint) with browser headers set as
    # defaults — required for Cloudflare's bot WAF to accept the connection.
    http_client = create_http_client(timeout=settings.timeout)
    client = create_novelai_client(settings, http_client=http_client)
    try:
        yield AppContext(client=client, settings=settings)
    finally:
        # Close the NovelAI client first; even if it raises, the underlying
        # httpx session must still be released to avoid leaking sockets.
        try:
            await client.aclose()
        finally:
            if not http_client.is_closed:
                await http_client.aclose()


mcp = FastMCP(name="novelai-image", lifespan=lifespan)

# Register all MCP tools against the server instance.
register_all(mcp)


def main() -> None:
    """Run the server with the transport selected from ``MCP_*`` settings."""
    mcp_settings = get_mcp_settings()
    if mcp_settings.transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=mcp_settings.host,
            port=mcp_settings.port,
        )
    else:
        mcp.run(transport="stdio")


__all__ = ["AppContext", "lifespan", "main", "mcp"]
