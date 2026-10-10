"""MCP tool registration.

Importing this package imports every tool module; each module decorates the
shared server instance imported from `..server` as a side effect of import,
so there is no registration function to call. `server.py` imports this package
at the bottom of the module, after `mcp` exists.
"""

from __future__ import annotations

from . import account, enhance, generate, tags

__all__ = ["account", "enhance", "generate", "tags"]
