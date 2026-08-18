"""Shared helper for pulling ``AppContext`` off a fastmcp ``Context``.

In fastmcp, a tool declares its request context with a ``ctx: Context``
parameter and reads the lifespan yield value from ``ctx.lifespan_context``
(fastmcp's convenience property; the same object the lifespan ``yield``ed).
Centralising the lookup here keeps every tool group consistent and gives the
test-suite one shape to mirror. Returning the typed ``AppContext`` lets each
tool site access ``client`` / ``settings`` without a cast.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from .._mcp import Context

if TYPE_CHECKING:
    from ..server import AppContext


def app_context(ctx: Context) -> AppContext:
    """Return the lifespan ``AppContext`` for the current request."""
    # fastmcp types ``Context.lifespan_context`` as ``dict[str, Any]`` even
    # though the lifespan ``yield``s an ``AppContext``; recover the type here.
    return cast("AppContext", ctx.lifespan_context)


__all__ = ["app_context"]
