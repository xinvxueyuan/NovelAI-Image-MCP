"""MCP tool registration entry point.

Each tool module exports a ``register(mcp)`` function that decorates its tool
functions against the passed ``FastMCP`` instance. This avoids circular imports
(tools do not import ``server``) and keeps each tool group testable in
isolation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import account, enhance, generate, tags

if TYPE_CHECKING:
    from .._mcp import FastMCP


def register_all(mcp: FastMCP) -> None:
    """Register every NovelAI tool group against ``mcp``."""
    generate.register(mcp)
    enhance.register(mcp)
    tags.register(mcp)
    account.register(mcp)


__all__ = ["register_all"]
