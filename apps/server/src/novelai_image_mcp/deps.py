"""Dependency-injected values shared by the MCP components.

FastMCP resolves parameters declared as ``Depends(get_...)`` (or annotated with
``Context``) when the component runs, and hides them from the component's input
schema. Tools, resources and prompts therefore declare exactly what they need
instead of digging into the request context themselves. ``AppContext`` is the
single value the server lifespan yields, and every provider reads from it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from fastmcp.dependencies import CurrentContext, Depends

if TYPE_CHECKING:
    from fastmcp import Context

    from .nai import NovelAIClient
    from .settings import NovelAISettings


@dataclass
class AppContext:
    """Shared state yielded by the lifespan to every MCP request."""

    client: NovelAIClient
    settings: NovelAISettings


def get_app_context(ctx: Context = CurrentContext()) -> AppContext:
    """Return the lifespan ``AppContext`` for the current request."""
    value = ctx.lifespan_context
    if not isinstance(value, AppContext):  # pragma: no cover - defensive
        raise TypeError("the server lifespan did not yield an AppContext")
    return value


def get_client(app: AppContext = Depends(get_app_context)) -> NovelAIClient:
    """Return the shared ``NovelAIClient`` for the current request."""
    return app.client


__all__ = ["AppContext", "get_app_context", "get_client"]
