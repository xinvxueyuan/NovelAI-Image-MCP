"""Tests for the tool-call logging middleware."""

from __future__ import annotations

from typing import Any

from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
import pytest

from novelai_image_mcp.middleware import ToolCallLoggingMiddleware

_LOGGER = "novelai_image_mcp.middleware"


def _server() -> FastMCP:
    """A minimal server carrying the production middleware."""
    server = FastMCP("middleware-test", middleware=[ToolCallLoggingMiddleware()])

    @server.tool
    def ping() -> str:
        """Return pong."""
        return "pong"

    @server.tool
    def boom() -> str:
        """Always fail."""
        raise RuntimeError("nope")

    return server


class TestToolCallLoggingMiddleware:
    async def test_forwards_the_call_and_returns_the_result(self, caplog: Any) -> None:
        with caplog.at_level("INFO", logger=_LOGGER):
            async with Client(_server()) as client:
                result = await client.call_tool("ping", {})
        assert result.data == "pong"

    async def test_logs_start_and_finish_with_a_duration(self, caplog: Any) -> None:
        with caplog.at_level("INFO", logger=_LOGGER):
            async with Client(_server()) as client:
                await client.call_tool("ping", {})

        messages = [record.getMessage() for record in caplog.records]
        assert any(message.endswith("ping") for message in messages)
        assert any("finished: ping" in message for message in messages)
        assert any("s)" in message for message in messages)

    async def test_failure_is_logged_and_propagated(self, caplog: Any) -> None:
        with (
            caplog.at_level("INFO", logger=_LOGGER),
            pytest.raises(ToolError),
        ):
            async with Client(_server()) as client:
                await client.call_tool("boom", {})

        messages = [record.getMessage() for record in caplog.records]
        assert any("started: boom" in message for message in messages)
        assert any("finished: boom" in message for message in messages)


class TestProductionWiring:
    def test_the_server_installs_the_middleware(self) -> None:
        from novelai_image_mcp import server

        assert any(
            isinstance(entry, ToolCallLoggingMiddleware)
            for entry in server.mcp.middleware
        )
