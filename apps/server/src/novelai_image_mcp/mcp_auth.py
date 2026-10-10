"""Optional bearer-token authentication for the HTTP transport.

The stdio transport is a local, single-client channel and needs no
authentication. When the server is exposed over HTTP (containers, remote
deployments, shared hosts) an operator can set ``MCP_AUTH_TOKEN`` to require a
bearer token: FastMCP then validates the ``Authorization`` header before any
MCP request is served. Without the setting the server behaves exactly as
before, so this stays opt-in and backward compatible.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

if TYPE_CHECKING:
    from fastmcp.server.auth import TokenVerifier

    from .settings import MCPServerSettings

#: Identity reported to the server for the single configured token.
CLIENT_ID = "novelai-image-mcp"


def build_auth(settings: MCPServerSettings) -> TokenVerifier | None:
    """Return a bearer-token verifier, or ``None`` when auth is not configured.

    ``StaticTokenVerifier`` compares the presented token against a fixed
    mapping; it is the documented FastMCP pattern for operator-managed static
    tokens. Rotate the token by changing ``MCP_AUTH_TOKEN`` and restarting.
    """
    token = (settings.auth_token or "").strip()
    if not token:
        return None
    return StaticTokenVerifier(
        tokens={token: {"client_id": CLIENT_ID, "scopes": []}},
    )


__all__ = ["CLIENT_ID", "build_auth"]
