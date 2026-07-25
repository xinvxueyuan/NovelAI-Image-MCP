"""Shared helper for pulling ``AppContext`` off an MCP v2 ``Context``.

In MCP v2 the lifespan state lives on the per-request ``ServerRequestContext``
dataclass (``ctx.request_context.lifespan_context``), not on the top-level
``Context`` BaseModel. Centralising the lookup here keeps every tool group
consistent and gives the test-suite one shape to mirror.

The ``Context`` is parameterised as ``Context[Any, Any]`` because the SDK
infers ``dict[str, Any]`` for the lifespan type at the ``@mcp.tool`` boundary
(there is no way to thread ``AppContext`` through the decorator). Returning
``Any`` here lets each tool site narrow via attribute access without a cast.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .._mcp import Context

if TYPE_CHECKING:
    from ..server import AppContext


def app_context(ctx: Context[Any, Any]) -> AppContext:
    """Return the lifespan ``AppContext`` for the current request."""
    return ctx.request_context.lifespan_context


__all__ = ["app_context"]
