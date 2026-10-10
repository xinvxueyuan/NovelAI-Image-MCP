"""Cross-cutting middleware for the NovelAI MCP server."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext

if TYPE_CHECKING:
    from fastmcp.tools import ToolResult
    import mcp.types as mt

logger = logging.getLogger(__name__)


class ToolCallLoggingMiddleware(Middleware):
    """Log every tool call with its name and wall-clock duration.

    Middleware keeps this concern out of the tool bodies: the hook observes the
    call, never rewrites the result, and never swallows an exception.
    """

    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next: CallNext[mt.CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        """Time the call and log its start and finish (success or failure)."""
        name = context.message.name
        started = time.perf_counter()
        logger.info("tool call started: %s", name)
        try:
            return await call_next(context)
        finally:
            logger.info(
                "tool call finished: %s (%.3fs)",
                name,
                time.perf_counter() - started,
            )


__all__ = ["ToolCallLoggingMiddleware"]
