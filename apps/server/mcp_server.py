"""Canonical FastMCP entry point for `fastmcp run` and `fastmcp dev`.

`fastmcp run` (and a `fastmcp.json` source) loads a Python file by path via
`importlib.util.spec_from_file_location`, so the loaded module has no package
context and the package's relative imports cannot resolve. This shim imports
the installed package and re-exports the server instance instead, which is what
`fastmcp.json` points at:

    uv run fastmcp run fastmcp.json
    uv run --directory apps/server fastmcp dev inspector mcp_server.py
"""

from __future__ import annotations

from novelai_image_mcp.server import mcp

__all__ = ["mcp"]
