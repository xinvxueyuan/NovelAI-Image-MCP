"""Tests for the tool-call logging middleware."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.middleware import MiddlewareContext
import pytest

from novelai_image_mcp.middleware import (
    INSIDERS_TAG,
    ToolCallLoggingMiddleware,
    _arguments,
)

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


def _gate_server() -> FastMCP:
    """A server with the production middleware, a plain and a gated tool."""
    server = FastMCP("gate-test", middleware=[ToolCallLoggingMiddleware()])

    @server.tool
    def ping() -> str:
        """Return pong."""
        return "pong"

    @server.tool
    def boom() -> str:
        """Always fail."""
        raise RuntimeError("nope")

    @server.tool(tags={INSIDERS_TAG})
    def secret_tool() -> str:
        """Belong to the experimental surface."""
        return "secret"

    return server


def _fake_headers(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    headers: dict[str, str],
) -> Path:
    """Point the middleware at ``headers`` and the audit trail at ``tmp_path``."""
    from novelai_image_mcp import middleware as middleware_module

    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setenv("MCP_AUDIT_LOG_PATH", str(audit_path))
    monkeypatch.delenv("MCP_INSIDERS_HEADER", raising=False)
    monkeypatch.delenv("MCP_INSIDERS_DISABLED_FEATURES", raising=False)
    monkeypatch.setattr(middleware_module, "get_http_headers", lambda: headers)
    return audit_path


def _call_context(arguments: Any) -> MiddlewareContext[Any]:
    """A stand-in context carrying only the call message ``_arguments`` reads."""
    message = SimpleNamespace(arguments=arguments)
    return cast("MiddlewareContext[Any]", SimpleNamespace(message=message))


async def _tool_names(client: Any) -> set[str]:
    """Return the tool names the client can currently see."""
    return {tool.name for tool in await client.list_tools()}


def _only_record(audit_path: Path) -> dict[str, Any]:
    """Return the single record in ``audit_path``."""
    lines = audit_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record: dict[str, Any] = json.loads(lines[0])
    return record


class TestExperimentalToolGate:
    """The gate hides the tagged tool *and* refuses it when called by name."""

    async def test_an_opted_out_client_does_not_see_the_tagged_tool(self) -> None:
        async with Client(_gate_server()) as client:
            assert await _tool_names(client) == {"ping", "boom"}

    async def test_an_opted_out_client_cannot_call_it_by_name(self) -> None:
        with pytest.raises(ToolError):
            async with Client(_gate_server()) as client:
                await client.call_tool("secret_tool", {})

    async def test_the_untagged_tools_are_unaffected(self) -> None:
        async with Client(_gate_server()) as client:
            assert (await client.call_tool("ping", {})).data == "pong"

    async def test_an_opted_in_client_sees_and_calls_it(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _fake_headers(monkeypatch, tmp_path, {"x-mcp-insiders": "true"})
        async with Client(_gate_server()) as client:
            assert await _tool_names(client) == {"ping", "boom", "secret_tool"}
            assert (await client.call_tool("secret_tool", {})).data == "secret"

    async def test_the_header_can_switch_the_feature_off_alone(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _fake_headers(
            monkeypatch, tmp_path, {"x-mcp-insiders": "experimental-tools=false"}
        )
        async with Client(_gate_server()) as client:
            assert await _tool_names(client) == {"ping", "boom"}
            with pytest.raises(ToolError):
                await client.call_tool("secret_tool", {})

    async def test_the_operator_kill_switch_wins_over_the_header(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _fake_headers(monkeypatch, tmp_path, {"x-mcp-insiders": "true"})
        monkeypatch.setenv("MCP_INSIDERS_DISABLED_FEATURES", '["experimental-tools"]')
        async with Client(_gate_server()) as client:
            assert await _tool_names(client) == {"ping", "boom"}
            with pytest.raises(ToolError):
                await client.call_tool("secret_tool", {})


class TestAuditTrail:
    """A routed call lands exactly one safe record in the JSONL trail."""

    async def test_a_routed_call_appends_one_record(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        audit_path = _fake_headers(
            monkeypatch,
            tmp_path,
            {
                "x-mcp-insiders": "true",
                "x-mcp-agent-id": "team-a",
                "x-mcp-model": "nai-diffusion-5-full",
            },
        )
        async with Client(_gate_server()) as client:
            await client.call_tool("ping", {})

        record = _only_record(audit_path)
        assert record["route"] == "team-a"
        assert record["model"] == "nai-diffusion-5-full"
        assert record["agent"] == "team-a"
        assert record["tool"] == "ping"
        assert record["outcome"] == "ok"
        assert record["features"] == ["experimental-tools", "model-routing"]
        assert record["headers"]["x-mcp-agent-id"] == "team-a"

    async def test_a_call_without_arguments_is_still_audited(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        audit_path = _fake_headers(monkeypatch, tmp_path, {"x-mcp-insiders": "true"})
        async with Client(_gate_server()) as client:
            await client.call_tool("ping")
        assert _only_record(audit_path)["arguments"] == {}

    async def test_credentials_never_reach_the_audit_record(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        audit_path = _fake_headers(
            monkeypatch,
            tmp_path,
            {
                "x-mcp-insiders": "true",
                "x-mcp-agent-id": "team-a",
                "authorization": "Bearer super-secret",
                "cookie": "session=super-secret",
            },
        )
        async with Client(_gate_server()) as client:
            await client.call_tool("ping", {})

        raw = audit_path.read_text(encoding="utf-8")
        assert "super-secret" not in raw
        record = json.loads(raw)
        assert "authorization" not in record["headers"]
        assert "cookie" not in record["headers"]

    async def test_without_headers_nothing_is_recorded(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        audit_path = _fake_headers(monkeypatch, tmp_path, {})
        async with Client(_gate_server()) as client:
            await client.call_tool("ping", {})
        assert not audit_path.exists()

    async def test_routing_switched_off_records_nothing(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        audit_path = _fake_headers(
            monkeypatch, tmp_path, {"x-mcp-insiders": "model-routing=false"}
        )
        async with Client(_gate_server()) as client:
            await client.call_tool("ping", {})
        assert not audit_path.exists()

    async def test_a_failing_call_is_recorded_as_an_error(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        audit_path = _fake_headers(monkeypatch, tmp_path, {"x-mcp-insiders": "true"})
        with pytest.raises(ToolError):
            async with Client(_gate_server()) as client:
                await client.call_tool("boom", {})
        assert _only_record(audit_path)["outcome"] == "error"

    async def test_a_rejected_call_is_recorded_as_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        audit_path = _fake_headers(
            monkeypatch, tmp_path, {"x-mcp-insiders": "experimental-tools=false"}
        )
        with pytest.raises(ToolError):
            async with Client(_gate_server()) as client:
                await client.call_tool("secret_tool", {})
        assert _only_record(audit_path)["outcome"] == "rejected"

    async def test_an_unwritable_trail_does_not_fail_the_call(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: Any
    ) -> None:
        blocker = tmp_path / "blocker"
        blocker.write_text("not a directory", encoding="utf-8")
        _fake_headers(monkeypatch, tmp_path, {"x-mcp-insiders": "true"})
        monkeypatch.setenv("MCP_AUDIT_LOG_PATH", str(blocker / "audit.jsonl"))
        with caplog.at_level("ERROR", logger="novelai_image_mcp.audit"):
            async with Client(_gate_server()) as client:
                assert (await client.call_tool("ping", {})).data == "pong"
        assert any(record.levelname == "ERROR" for record in caplog.records)

    async def test_the_route_derived_logger_is_used(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: Any
    ) -> None:
        _fake_headers(
            monkeypatch,
            tmp_path,
            {"x-mcp-insiders": "true", "x-mcp-agent-id": "team-a"},
        )
        with caplog.at_level("INFO", logger="novelai_image_mcp.audit.team-a"):
            async with Client(_gate_server()) as client:
                await client.call_tool("ping", {})

        routed = [
            record.getMessage()
            for record in caplog.records
            if record.name == "novelai_image_mcp.audit.team-a"
        ]
        assert any("route=team-a" in message for message in routed)


class TestArgumentSnapshot:
    """MCP allows a tool call to omit ``arguments`` entirely."""

    def test_arguments_are_read_from_the_call_message(self) -> None:
        assert _arguments(_call_context({"prompt": "a cat"})) == {"prompt": "a cat"}

    def test_a_missing_arguments_payload_yields_an_empty_mapping(self) -> None:
        assert _arguments(_call_context(None)) == {}

    def test_a_non_mapping_arguments_payload_yields_an_empty_mapping(self) -> None:
        assert _arguments(_call_context(["nope"])) == {}


class TestProductionRegistry:
    async def test_no_shipped_tool_carries_the_insiders_tag(
        self, mcp_client: Any
    ) -> None:
        """Tagging a shipped tool would hide it from every header-less client."""
        from novelai_image_mcp import server

        names = await _tool_names(mcp_client)
        assert names
        for name in names:
            tool = await server.mcp.get_tool(name)
            assert tool is not None
            assert INSIDERS_TAG not in tool.tags
