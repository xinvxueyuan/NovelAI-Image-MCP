"""Centralized MCP SDK v2 imports.

The v2 SDK renamed ``FastMCP`` to ``MCPServer`` and re-exports ``Context`` /
``Image`` / ``MCPServer`` from ``mcp.server.mcpserver`` (the v2 module path used
by the official quickstart). This shim imports once so the rest of the package
is insulated from SDK layout variations between beta and stable v2 releases.
"""

from __future__ import annotations

try:
    from mcp.server.mcpserver import Context, Image, MCPServer
except ImportError:  # pragma: no cover - fallback for alternate v2 layouts
    from mcp.server import Context, Image, MCPServer  # type: ignore[no-redef]

__all__ = ["Context", "Image", "MCPServer"]
