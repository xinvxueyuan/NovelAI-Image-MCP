"""Tests for the header-driven routing context.

The candidate header lists used here mirror the ``MCPServerSettings`` defaults
(``model_headers`` / ``agent_headers`` / ``client_headers``); the settings test
suite asserts that the two stay in step.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from novelai_image_mcp.routing import (
    MAX_RECORDED_HEADERS,
    MAX_RECORDED_VALUE_LENGTH,
    MAX_ROUTE_LENGTH,
    ROUTE_STDIO,
    ROUTE_UNKNOWN,
    RoutingContext,
    resolve_routing,
    sanitize_route,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


# Canonical candidate lists, mirroring the MCPServerSettings defaults. Tuples
# (not lists) so they are safe as default arguments.
MODEL_HEADERS = ("X-MCP-Model", "X-MCP-Model-Name")
AGENT_HEADERS = ("X-MCP-Agent-ID", "X-MCP-Agent", "X-MCP-Agent-Source")
CLIENT_HEADERS = ("X-MCP-Client", "X-MCP-Client-Session-Id")


def _resolve(
    headers: Mapping[str, str],
    *,
    enabled: bool = True,
    model_headers: Sequence[str] = MODEL_HEADERS,
    agent_headers: Sequence[str] = AGENT_HEADERS,
    client_headers: Sequence[str] = CLIENT_HEADERS,
    client_info_name: str | None = None,
    has_http_request: bool = True,
) -> RoutingContext:
    """Resolve routing with the canonical defaults unless overridden."""
    return resolve_routing(
        headers,
        enabled=enabled,
        model_headers=model_headers,
        agent_headers=agent_headers,
        client_headers=client_headers,
        client_info_name=client_info_name,
        has_http_request=has_http_request,
    )


class TestConstants:
    def test_route_names_are_the_documented_spellings(self) -> None:
        assert ROUTE_UNKNOWN == "unknown"
        assert ROUTE_STDIO == "stdio"

    def test_limits_are_the_documented_values(self) -> None:
        assert MAX_ROUTE_LENGTH == 64
        assert MAX_RECORDED_HEADERS == 64
        assert MAX_RECORDED_VALUE_LENGTH == 512


class TestSanitizeRoute:
    @pytest.mark.parametrize(
        "value",
        [
            "../../x",
            "../../etc/passwd",
            "a/b",
            "a" + chr(92) + "b",
            ".." + chr(92) + "..",
            "..",
            ".",
            "...",
            "",
            "   ",
            chr(9),
            "with space",
            "route/../x",
            "x" * (MAX_ROUTE_LENGTH + 1),
            chr(92) + "x",
            "%2e%2e",
            "nul" + chr(0) + "byte",
        ],
    )
    def test_hostile_and_malformed_values_collapse_to_unknown(self, value: str) -> None:
        assert sanitize_route(value) == ROUTE_UNKNOWN

    @pytest.mark.parametrize(
        "value",
        [
            "route-1",
            "a.b_c-D9",
            "0",
            "-",
            "_",
            "a..b",
            "x" * MAX_ROUTE_LENGTH,
        ],
    )
    def test_whitelisted_values_pass_through(self, value: str) -> None:
        assert sanitize_route(value) == value

    def test_surrounding_whitespace_is_stripped(self) -> None:
        assert sanitize_route("  route-1  ") == "route-1"

    def test_non_ascii_is_rejected(self) -> None:
        assert sanitize_route("\u00fcn\u00efcode") == ROUTE_UNKNOWN
        assert sanitize_route("\u8def\u7531") == ROUTE_UNKNOWN

    def test_the_length_boundary_is_exclusive(self) -> None:
        assert sanitize_route("x" * MAX_ROUTE_LENGTH) != ROUTE_UNKNOWN
        assert sanitize_route("x" * (MAX_ROUTE_LENGTH + 1)) == ROUTE_UNKNOWN


class TestRoutePrecedence:
    def test_agent_header_beats_client_header_and_client_info(self) -> None:
        context = _resolve(
            {"x-mcp-agent-id": "agent-route", "x-mcp-client": "client-route"},
            client_info_name="info-route",
        )
        assert context.route == "agent-route"

    def test_client_header_beats_client_info(self) -> None:
        context = _resolve(
            {"x-mcp-client": "client-route"},
            client_info_name="info-route",
        )
        assert context.route == "client-route"

    def test_client_info_is_the_last_resort(self) -> None:
        context = _resolve({}, client_info_name="info-route")
        assert context.route == "info-route"

    def test_nothing_available_over_http_is_unknown(self) -> None:
        context = _resolve({}, has_http_request=True)
        assert context.route == ROUTE_UNKNOWN

    def test_nothing_available_without_http_is_stdio(self) -> None:
        context = _resolve({}, has_http_request=False)
        assert context.route == ROUTE_STDIO
        assert context.transport == "stdio"

    def test_default_agent_chain_is_the_fixed_priority_order(self) -> None:
        all_three = {
            "x-mcp-agent-id": "id",
            "x-mcp-agent": "agent",
            "x-mcp-agent-source": "source",
        }
        assert _resolve(all_three).route == "id"
        without_id = {k: v for k, v in all_three.items() if "id" not in k}
        assert _resolve(without_id).route == "agent"
        assert _resolve({"x-mcp-agent-source": "source"}).route == "source"

    def test_default_client_chain_is_the_fixed_priority_order(self) -> None:
        both = {"x-mcp-client": "client", "x-mcp-client-session-id": "session"}
        assert _resolve(both).route == "client"
        assert _resolve({"x-mcp-client-session-id": "session"}).route == "session"

    def test_a_custom_candidate_order_changes_the_winner(self) -> None:
        headers = {"x-mcp-agent-id": "id", "x-mcp-agent-source": "source"}
        assert _resolve(headers).route == "id"
        reordered = _resolve(
            headers,
            agent_headers=("X-MCP-Agent-Source", "X-MCP-Agent-ID"),
        )
        assert reordered.route == "source"

    def test_a_hostile_agent_header_is_sanitized_for_the_route(self) -> None:
        context = _resolve({"x-mcp-agent-id": "../../etc"})
        assert context.route == ROUTE_UNKNOWN
        # Only the route is whitelisted; the extracted field keeps the raw value
        # so an operator can still see what the client actually sent.
        assert context.agent == "../../etc"

    def test_a_hostile_client_info_name_is_sanitized_for_the_route(self) -> None:
        context = _resolve({}, client_info_name="a/b")
        assert context.route == ROUTE_UNKNOWN

    def test_an_empty_agent_value_falls_through_to_the_client(self) -> None:
        context = _resolve({"x-mcp-agent-id": "   ", "x-mcp-client": "client-route"})
        assert context.route == "client-route"


class TestDisabledContext:
    def test_a_disabled_header_extracts_nothing(self) -> None:
        context = _resolve(
            {
                "x-mcp-model": "m",
                "x-mcp-agent-id": "a",
                "x-mcp-client": "c",
                "x-mcp-client-session-id": "s",
            },
            enabled=False,
        )
        assert context.enabled is False
        assert context.route == ROUTE_UNKNOWN
        assert context.model is None
        assert context.agent is None
        assert context.client is None
        assert context.session is None

    def test_a_disabled_header_still_reports_the_real_transport(self) -> None:
        over_http = _resolve({}, enabled=False, has_http_request=True)
        without_http = _resolve({}, enabled=False, has_http_request=False)
        assert over_http.transport == "http"
        assert without_http.transport == "stdio"

    def test_a_disabled_context_records_no_headers(self) -> None:
        assert _resolve({"x-mcp-model": "m"}, enabled=False).recorded_headers == {}

    def test_the_disabled_factory_defaults_to_http(self) -> None:
        context = RoutingContext.disabled()
        assert context.enabled is False
        assert context.route == ROUTE_UNKNOWN
        assert context.transport == "http"

    def test_the_disabled_factory_accepts_a_stdio_transport(self) -> None:
        assert RoutingContext.disabled(transport="stdio").transport == "stdio"


class TestFieldExtraction:
    def test_model_uses_the_first_non_empty_candidate(self) -> None:
        assert _resolve({"x-mcp-model": "m1"}).model == "m1"
        assert _resolve({"x-mcp-model-name": "m2"}).model == "m2"
        both = {"x-mcp-model": "m1", "x-mcp-model-name": "m2"}
        assert _resolve(both).model == "m1"

    def test_absent_fields_stay_none(self) -> None:
        context = _resolve({"x-mcp-unrelated": "x"})
        assert context.model is None
        assert context.agent is None
        assert context.client is None
        assert context.session is None

    def test_agent_and_client_are_extracted_from_their_own_chains(self) -> None:
        context = _resolve(
            {"x-mcp-agent": "agent-x", "x-mcp-client": "client-y"},
        )
        assert context.agent == "agent-x"
        assert context.client == "client-y"

    def test_session_comes_from_the_session_bearing_client_candidate(self) -> None:
        context = _resolve(
            {"x-mcp-client": "client-y", "x-mcp-client-session-id": "session-z"},
        )
        assert context.client == "client-y"
        assert context.session == "session-z"

    def test_session_is_none_without_a_session_bearing_candidate(self) -> None:
        assert _resolve({"x-mcp-client": "client-y"}).session is None

    def test_values_are_stripped_and_blank_values_are_absent(self) -> None:
        assert _resolve({"x-mcp-model": "  m1  "}).model == "m1"
        assert _resolve({"x-mcp-model": "   "}).model is None

    def test_header_lookup_is_case_and_separator_insensitive(self) -> None:
        assert _resolve({"X-MCP-Model": "m1"}).model == "m1"
        assert _resolve({"X_MCP_Model": "m1"}).model == "m1"
        assert _resolve({"x_mcp_model": "m1"}).model == "m1"

    def test_a_custom_model_chain_is_honoured(self) -> None:
        context = _resolve(
            {"x-custom-model": "m9"},
            model_headers=("X-Custom-Model",),
        )
        assert context.model == "m9"


class TestRecordedHeaders:
    @pytest.mark.parametrize(
        "name",
        [
            "authorization",
            "cookie",
            "set-cookie",
            "proxy-authorization",
            "token",
            "secret",
            "password",
            "passwd",
            "key",
            "credential",
            "credentials",
            "x-api-token",
            "x-api-key",
            "x-client-secret",
            "x-db-password",
            "x-db-passwd",
            "x-service-credential",
            "x-service-credentials",
            "X_MCP_Secret",
        ],
    )
    def test_credential_headers_are_never_recorded(self, name: str) -> None:
        context = _resolve({name: "leaked-value", "x-safe": "kept"})
        assert "leaked-value" not in context.recorded_headers.values()
        assert list(context.recorded_headers) == ["x-safe"]

    def test_tool_discovery_headers_are_not_mistaken_for_credentials(self) -> None:
        context = _resolve({"x-mcp-tools": "a,b", "x-mcp-toolsets": "c"})
        assert context.recorded_headers == {
            "x-mcp-tools": "a,b",
            "x-mcp-toolsets": "c",
        }

    def test_safe_headers_are_recorded_with_normalized_names(self) -> None:
        context = _resolve({"X-MCP-Model": "m1", "X_MCP_Agent_ID": "a1"})
        assert context.recorded_headers == {
            "x-mcp-model": "m1",
            "x-mcp-agent-id": "a1",
        }

    def test_a_header_with_an_empty_name_is_dropped(self) -> None:
        context = _resolve({"   ": "blank"})
        assert context.recorded_headers == {}

    def test_values_are_truncated_to_the_documented_limit(self) -> None:
        context = _resolve({"x-big": "a" * (MAX_RECORDED_VALUE_LENGTH + 100)})
        recorded = context.recorded_headers["x-big"]
        assert len(recorded) == MAX_RECORDED_VALUE_LENGTH
        assert recorded == "a" * MAX_RECORDED_VALUE_LENGTH

    def test_exactly_the_limit_of_headers_is_kept_intact(self) -> None:
        headers = {f"x-{index:03d}": str(index) for index in range(64)}
        context = _resolve(headers)
        assert len(context.recorded_headers) == MAX_RECORDED_HEADERS

    def test_more_than_the_limit_keeps_the_lexicographically_first_headers(
        self,
    ) -> None:
        headers = {f"x-{index:03d}": str(index) for index in range(70)}
        context = _resolve(headers)
        assert len(context.recorded_headers) == MAX_RECORDED_HEADERS
        expected = {f"x-{index:03d}" for index in range(MAX_RECORDED_HEADERS)}
        assert set(context.recorded_headers) == expected

    def test_the_snapshot_is_taken_even_when_no_routing_header_is_present(
        self,
    ) -> None:
        context = _resolve({"x-mcp-unrelated": "x"})
        assert context.route == ROUTE_UNKNOWN
        assert context.recorded_headers == {"x-mcp-unrelated": "x"}
