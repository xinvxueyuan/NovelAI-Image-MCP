"""Tests for the environment-driven settings surface."""

from __future__ import annotations

from typing import Any

import pytest

from novelai_image_mcp.deps import (
    get_effective_features,
    get_insiders_config,
    get_route_scoped_output,
    get_routing_context,
)
from novelai_image_mcp.insiders import parse_insiders
from novelai_image_mcp.settings import MCPServerSettings, NovelAISettings


class TestNovelAISettings:
    def test_upscale_model_defaults_to_the_v5_full_model(self) -> None:
        """The standalone upscaler only accepts the V5 line."""
        assert NovelAISettings(token="pst-x").upscale_model == "nai-diffusion-5-full"

    def test_upscale_model_reads_the_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("NOVELAI_UPSCALE_MODEL", "nai-diffusion-5-curated")
        assert NovelAISettings(token="pst-x").upscale_model == (
            "nai-diffusion-5-curated"
        )


class TestMCPServerSettings:
    def test_transport_defaults_to_stdio(self) -> None:
        assert MCPServerSettings().resolved_transport == "stdio"

    @pytest.mark.parametrize("value", ["http", "streamable-http"])
    def test_http_and_its_legacy_alias_resolve_to_http(
        self, monkeypatch: pytest.MonkeyPatch, value: str
    ) -> None:
        monkeypatch.setenv("MCP_TRANSPORT", value)
        assert MCPServerSettings().resolved_transport == "http"

    def test_auth_token_is_opt_in(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MCP_AUTH_TOKEN", raising=False)
        assert MCPServerSettings().auth_token is None

    def test_auth_token_reads_the_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MCP_AUTH_TOKEN", "s3cret")
        assert MCPServerSettings().auth_token == "s3cret"

    def test_log_level_is_optional(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MCP_LOG_LEVEL", raising=False)
        assert MCPServerSettings().log_level is None

    def test_unknown_variables_are_ignored(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MCP_NOT_A_REAL_SETTING", "1")
        dumped: dict[str, Any] = MCPServerSettings().model_dump()
        assert "not_a_real_setting" not in dumped


class TestMCPServerSettingsInsiders:
    """Defaults and environment overrides for the insiders/routing surface.

    The canonical candidate lists asserted here are the same fixed chains the
    routing tests resolve against, so the two suites pin one contract.
    """

    def test_insiders_header_defaults_to_the_canonical_name(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("MCP_INSIDERS_HEADER", raising=False)
        assert MCPServerSettings().insiders_header == "X-MCP-Insiders"

    def test_insiders_header_reads_the_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MCP_INSIDERS_HEADER", "X-Tenant-Insiders")
        assert MCPServerSettings().insiders_header == "X-Tenant-Insiders"

    def test_routing_candidate_lists_default_to_the_fixed_chains(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        for name in ("MCP_MODEL_HEADERS", "MCP_AGENT_HEADERS", "MCP_CLIENT_HEADERS"):
            monkeypatch.delenv(name, raising=False)
        settings = MCPServerSettings()
        assert settings.model_headers == ["X-MCP-Model", "X-MCP-Model-Name"]
        assert settings.agent_headers == [
            "X-MCP-Agent-ID",
            "X-MCP-Agent",
            "X-MCP-Agent-Source",
        ]
        assert settings.client_headers == [
            "X-MCP-Client",
            "X-MCP-Client-Session-Id",
        ]

    def test_routing_candidate_lists_read_json_from_the_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MCP_MODEL_HEADERS", '["X-Model"]')
        monkeypatch.setenv("MCP_AGENT_HEADERS", '["X-Agent"]')
        monkeypatch.setenv("MCP_CLIENT_HEADERS", '["X-Client"]')
        settings = MCPServerSettings()
        assert settings.model_headers == ["X-Model"]
        assert settings.agent_headers == ["X-Agent"]
        assert settings.client_headers == ["X-Client"]

    def test_the_default_lists_are_not_shared_between_instances(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("MCP_MODEL_HEADERS", raising=False)
        first = MCPServerSettings()
        first.model_headers.append("X-Injected")
        assert "X-Injected" not in MCPServerSettings().model_headers

    def test_disabled_features_default_to_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("MCP_INSIDERS_DISABLED_FEATURES", raising=False)
        assert MCPServerSettings().insiders_disabled_features == []

    def test_disabled_features_read_json_from_the_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MCP_INSIDERS_DISABLED_FEATURES", '["model-routing"]')
        assert MCPServerSettings().insiders_disabled_features == ["model-routing"]

    def test_audit_log_path_is_opt_in(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MCP_AUDIT_LOG_PATH", raising=False)
        assert MCPServerSettings().audit_log_path is None

    def test_audit_log_path_reads_the_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MCP_AUDIT_LOG_PATH", "logs/audit.jsonl")
        assert MCPServerSettings().audit_log_path == "logs/audit.jsonl"

    def test_route_scoped_output_defaults_to_enabled(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("MCP_ROUTE_SCOPED_OUTPUT", raising=False)
        assert MCPServerSettings().route_scoped_output is True

    def test_route_scoped_output_reads_the_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MCP_ROUTE_SCOPED_OUTPUT", "false")
        assert MCPServerSettings().route_scoped_output is False
        monkeypatch.setenv("MCP_ROUTE_SCOPED_OUTPUT", "true")
        assert MCPServerSettings().route_scoped_output is True

    def test_route_tokens_are_opt_in(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MCP_ROUTE_TOKENS", raising=False)
        assert MCPServerSettings().route_tokens is None

    def test_route_tokens_read_json_from_the_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MCP_ROUTE_TOKENS", '{"s3cret": "team-a"}')
        assert MCPServerSettings().route_tokens == {"s3cret": "team-a"}

    def test_the_new_fields_do_not_disturb_the_existing_defaults(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        for name in (
            "MCP_INSIDERS_HEADER",
            "MCP_MODEL_HEADERS",
            "MCP_AGENT_HEADERS",
            "MCP_CLIENT_HEADERS",
            "MCP_INSIDERS_DISABLED_FEATURES",
            "MCP_AUDIT_LOG_PATH",
            "MCP_ROUTE_SCOPED_OUTPUT",
            "MCP_ROUTE_TOKENS",
        ):
            monkeypatch.delenv(name, raising=False)
        settings = MCPServerSettings()
        assert settings.resolved_transport == "stdio"
        assert settings.auth_token is None
        assert settings.log_level is None
        assert settings.port == 8000
        assert settings.path == "/mcp"


class TestInsidersProviders:
    """The settings-backed providers that read the request headers.

    ``CurrentHeaders()`` cannot be resolved outside a FastMCP request, so these
    tests call the providers directly with an explicit header mapping -- the same
    value FastMCP would inject.
    """

    def test_no_headers_means_the_insiders_surface_is_disabled(self) -> None:
        config = get_insiders_config({})
        assert config.enabled is False
        assert get_effective_features(config) == frozenset()

    def test_the_configured_header_is_read_case_insensitively(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("MCP_INSIDERS_HEADER", raising=False)
        # FastMCP lower-cases every incoming header name.
        assert get_insiders_config({"x-mcp-insiders": "true"}).enabled is True

    def test_a_custom_header_name_is_honoured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MCP_INSIDERS_HEADER", "X-Tenant-Insiders")
        assert get_insiders_config({"x-mcp-insiders": "true"}).enabled is False
        assert get_insiders_config({"x-tenant-insiders": "true"}).enabled is True

    def test_the_operator_kill_switch_wins_over_the_header(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MCP_INSIDERS_DISABLED_FEATURES", '["model-routing"]')
        features = get_effective_features(parse_insiders("true"))
        assert "model-routing" not in features
        assert "experimental-tools" in features

    def test_route_scoped_output_follows_the_setting(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("MCP_ROUTE_SCOPED_OUTPUT", raising=False)
        assert get_route_scoped_output() is True
        monkeypatch.setenv("MCP_ROUTE_SCOPED_OUTPUT", "false")
        assert get_route_scoped_output() is False

    def test_routing_is_disabled_without_headers(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("MCP_INSIDERS_DISABLED_FEATURES", raising=False)
        context = get_routing_context({})
        assert context.enabled is False
        assert context.route == "unknown"
        assert context.model is None
        assert context.agent is None

    def test_routing_uses_the_configured_candidate_lists(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MCP_INSIDERS_HEADER", "X-MCP-Insiders")
        monkeypatch.setenv("MCP_MODEL_HEADERS", '["X-Model"]')
        monkeypatch.delenv("MCP_INSIDERS_DISABLED_FEATURES", raising=False)
        context = get_routing_context({
            "x-mcp-insiders": "true",
            "x-model": "nai-diffusion-5-full",
            "x-mcp-agent-id": "team-a",
        })
        assert context.enabled is True
        assert context.model == "nai-diffusion-5-full"
        assert context.agent == "team-a"
        assert context.route == "team-a"


class TestRoutingInsideARealRequest:
    """Drive the provider through FastMCP so the live-context path is exercised.

    The client-info lookup can only succeed while a request is actually being
    served, so this runs the provider inside a real (in-memory) MCP tool call.
    """

    async def test_the_route_falls_back_to_the_client_info_name(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from fastmcp import Client, FastMCP
        from fastmcp.server.dependencies import get_context

        monkeypatch.delenv("MCP_INSIDERS_HEADER", raising=False)
        monkeypatch.delenv("MCP_INSIDERS_DISABLED_FEATURES", raising=False)

        server = FastMCP("routing-probe")

        @server.tool
        def probe() -> dict[str, str | bool | None]:
            """Resolve routing with the opt-in on and no routing headers."""
            params = get_context().session.client_params
            advertised = None if params is None else params.client_info.name
            context = get_routing_context({"x-mcp-insiders": "true"})
            return {
                "enabled": context.enabled,
                "route": context.route,
                "advertised": advertised,
            }

        async with Client(server) as client:
            result = await client.call_tool("probe", {})

        assert result.data["enabled"] is True
        assert result.data["advertised"]
        assert result.data["route"] == result.data["advertised"]
