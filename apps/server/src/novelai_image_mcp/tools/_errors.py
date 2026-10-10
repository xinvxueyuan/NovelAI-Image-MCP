"""Translation of expected failures into MCP ``ToolError``.

The server runs with ``mask_error_details=True``: FastMCP replaces the message
of any non-``ToolError`` exception with a generic "Error calling tool" text so
internal details never reach the client. Expected failures (NovelAI domain
errors, validation failures) therefore have to be raised as ``ToolError``
explicitly, and they have to be raised inside the tool body: by the time a
middleware hook observes the call, FastMCP has already masked the exception.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import functools
import logging

from fastmcp.exceptions import ToolError

from ..nai import NovelAIError

logger = logging.getLogger(__name__)


def translate_errors[F: Callable[..., Awaitable[object]]](fn: F) -> F:
    """Turn expected tool failures into ``ToolError`` with their real message.

    ``functools.wraps`` keeps the wrapped function's signature, docstring and
    default values intact, so FastMCP's schema generation (including
    ``Depends`` defaults) sees the original function. The full traceback is
    logged server-side, which keeps operators' diagnostics even though the
    client-visible message is the domain message only.
    """

    @functools.wraps(fn)
    async def wrapper(*args: object, **kwargs: object) -> object:
        try:
            return await fn(*args, **kwargs)
        except (NovelAIError, ValueError) as exc:
            logger.exception("tool %s failed", fn.__name__)
            raise ToolError(str(exc)) from exc

    return wrapper  # type: ignore[return-value]


__all__ = ["translate_errors"]
