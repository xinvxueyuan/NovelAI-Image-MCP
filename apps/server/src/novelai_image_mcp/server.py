"""MCP server (FastMCP): lifespan owns the shared httpx session + NovelAIClient.

The server is a thin composition root over ``nai.NovelAIClient``, built on the
FastMCP 4 framework (which itself runs on the MCP SDK v2). The lifespan creates
one long-lived ``httpx.AsyncClient`` (connection pooling, with Chrome TLS +
header fingerprint impersonation via ``create_http_client``) and one
``NovelAIClient``; every MCP component receives them through dependency
injection (see ``deps``) instead of reaching into the request context.

Tools, resources and prompts are attached to the shared ``mcp`` instance by
importing their modules at the bottom of this file: each one decorates ``mcp``
at import time and imports ``mcp`` back from this module, which is safe because
``mcp`` is already bound by then.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastmcp import FastMCP

from . import __version__
from .deps import AppContext
from .mcp_auth import build_auth
from .middleware import ToolCallLoggingMiddleware
from .nai import create_http_client, create_novelai_client
from .settings import get_mcp_settings, get_novelai_settings

#: Server-level instructions: how an agent should approach this server.
INSTRUCTIONS = """NovelAI image generation server.

Tools: generate_image (text-to-image), image_to_image, inpaint, upscale_image,
director_tool (lineart / sketch / bg-removal / declutter / colorize / emotion),
annotate_image (ControlNet preprocessors), suggest_tags, encode_vibe,
get_subscription, get_user_data, estimate_anlas_cost.

Workflow: check get_subscription before expensive runs and use
estimate_anlas_cost to price a request offline; call suggest_tags to expand a
partial prompt; generate with generate_image, then refine with image_to_image,
inpaint or upscale_image. encode_vibe produces a vibe token for the
references parameter of generate_image (V4 / V4.5 only, not V5).

Results: image tools write a PNG under NOVELAI_OUTPUT_DIR and return the image
plus its path; read it back with the novelai://outputs/{name} resource. The
novelai://models, novelai://samplers and novelai://defaults resources list the
supported vocabulary and the active defaults.
"""


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
    # defaults - required for Cloudflare's bot WAF to accept the connection.
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


mcp = FastMCP(
    name="novelai-image",
    version=__version__,
    instructions=INSTRUCTIONS,
    website_url="https://github.com/xinvxueyuan/NovelAI-Image-MCP",
    lifespan=lifespan,
    # Opt-in HTTP bearer-token auth (None unless MCP_AUTH_TOKEN is set).
    auth=build_auth(get_mcp_settings()),
    # Expected failures raise ToolError (see tools/_errors.py); anything else
    # is masked so internal details never reach the client.
    mask_error_details=True,
    middleware=[ToolCallLoggingMiddleware()],
)

from . import prompts, resources, tools  # noqa: E402,F401


def main() -> None:
    """Run the server with the transport selected from ``MCP_*`` settings."""
    mcp_settings = get_mcp_settings()
    kwargs: dict[str, Any] = {"log_level": mcp_settings.log_level}
    if mcp_settings.resolved_transport == "http":
        mcp.run(
            transport="http",
            host=mcp_settings.host,
            port=mcp_settings.port,
            path=mcp_settings.path,
            **kwargs,
        )
    else:
        mcp.run(transport="stdio", **kwargs)


__all__ = ["INSTRUCTIONS", "AppContext", "lifespan", "main", "mcp"]
