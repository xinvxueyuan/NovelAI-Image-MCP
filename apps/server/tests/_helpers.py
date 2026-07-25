"""Shared test constants and helpers (importable from any test module).

``tests/conftest.py`` inserts this directory into ``sys.path`` so test files
can do ``from _helpers import PNG_BYTES, RecordingMCPServer`` without making
``tests`` a package (preserving pytest's importlib-mode rootdir semantics).
"""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


# Minimal 1×1 PNG (transparent black). Used everywhere a small valid PNG is
# needed; the tools under test never inspect its contents.
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M8AAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
)


class RecordingMCPServer:
    """Captures ``@mcp.tool()``-decorated functions for direct test invocation.

    The real MCP SDK ``MCPServer.tool`` decorator returns the original function
    unchanged after registering it, so the recording stub mimics that contract
    while exposing each tool under its function name for direct invocation.
    """

    def __init__(self) -> None:
        self.tools: dict[str, Callable[..., Any]] = {}

    def tool(
        self, **_kwargs: Any
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator that records a tool function under its ``__name__``."""

        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self.tools[fn.__name__] = fn
            return fn

        return decorator
