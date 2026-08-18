"""Centralized fastmcp imports.

The server framework is fastmcp 4 (PrefectHQ/fastmcp), which builds on the MCP
SDK v2 (``mcp>=2.0.0``). This shim imports once so the rest of the package is
insulated from where fastmcp re-exports each symbol. ``FastMCP`` is the server
class replacing the SDK's v2 ``MCPServer``; ``Context`` is the request context
injected into tools; ``Image`` is fastmcp's media helper, which fastmcp
automatically converts to an ``ImageContent`` block when returned from a tool.
"""

from __future__ import annotations

try:
    from fastmcp import Context, FastMCP
    from fastmcp.utilities.types import Image
except ImportError:  # pragma: no cover - fallback for alternate fastmcp layouts
    from fastmcp.server.context import Context  # type: ignore[no-redef]
    from fastmcp.server.fastmcp import FastMCP  # type: ignore[no-redef]
    from fastmcp.utilities.types import Image  # type: ignore[no-redef]

__all__ = ["Context", "FastMCP", "Image"]
