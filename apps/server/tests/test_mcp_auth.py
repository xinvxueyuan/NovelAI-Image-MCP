"""Tests for the optional bearer-token authentication."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import json
import logging
from typing import Any

import httpx
import pytest
import uvicorn

from novelai_image_mcp import mcp_auth
from novelai_image_mcp.mcp_auth import CLIENT_ID, build_auth
from novelai_image_mcp.settings import MCPServerSettings

TOKEN = "s3cret-token"
ROUTE = "alpha"
ROUTE_TOKEN = "route-alpha-token"
OTHER_ROUTE = "beta"


class TestBuildAuth:
    def test_returns_none_without_a_token(self) -> None:
        assert build_auth(MCPServerSettings()) is None

    def test_returns_none_for_a_blank_token(self) -> None:
        assert build_auth(MCPServerSettings(auth_token="   ")) is None

    def test_returns_a_verifier_when_configured(self) -> None:
        verifier = build_auth(MCPServerSettings(auth_token=TOKEN))
        assert verifier is not None

    async def test_verifier_accepts_only_the_configured_token(self) -> None:
        verifier = build_auth(MCPServerSettings(auth_token=TOKEN))
        assert verifier is not None
        accepted = await verifier.verify_token(TOKEN)
        assert accepted is not None
        assert accepted.client_id == CLIENT_ID
        assert await verifier.verify_token("wrong") is None


class TestRouteTokenConfiguration:
    """`MCP_ROUTE_TOKENS` is additive: it must not change `MCP_AUTH_TOKEN`."""

    def test_no_tokens_at_all_installs_no_auth(self) -> None:
        assert build_auth(MCPServerSettings()) is None
        assert build_auth(MCPServerSettings(route_tokens={})) is None

    def test_unusable_route_tokens_install_no_auth(self) -> None:
        # An empty token authenticates nobody, and an unusable route name cannot
        # be compared with a declared route: neither may create a verifier.
        assert build_auth(MCPServerSettings(route_tokens={"": "t"})) is None
        assert build_auth(MCPServerSettings(route_tokens={"../escape": "t"})) is None
        assert build_auth(MCPServerSettings(route_tokens={ROUTE: "   "})) is None

    async def test_route_token_authenticates_as_its_route(self) -> None:
        verifier = build_auth(MCPServerSettings(route_tokens={ROUTE: ROUTE_TOKEN}))
        assert verifier is not None
        access = await verifier.verify_token(ROUTE_TOKEN)
        assert access is not None
        assert access.client_id == ROUTE
        assert await verifier.verify_token("wrong") is None

    async def test_static_and_route_tokens_coexist(self) -> None:
        verifier = build_auth(
            MCPServerSettings(auth_token=TOKEN, route_tokens={ROUTE: ROUTE_TOKEN})
        )
        assert verifier is not None
        static = await verifier.verify_token(TOKEN)
        route = await verifier.verify_token(ROUTE_TOKEN)
        assert static is not None
        assert static.client_id == CLIENT_ID
        assert route is not None
        assert route.client_id == ROUTE

    async def test_route_reusing_the_static_token_keeps_the_static_identity(
        self,
    ) -> None:
        verifier = build_auth(
            MCPServerSettings(auth_token=TOKEN, route_tokens={ROUTE: TOKEN})
        )
        assert verifier is not None
        access = await verifier.verify_token(TOKEN)
        assert access is not None
        assert access.client_id == CLIENT_ID

    async def test_every_route_token_is_registered(self) -> None:
        verifier = build_auth(
            MCPServerSettings(route_tokens={ROUTE: ROUTE_TOKEN, OTHER_ROUTE: "other"})
        )
        assert verifier is not None
        alpha = await verifier.verify_token(ROUTE_TOKEN)
        beta = await verifier.verify_token("other")
        assert alpha is not None
        assert alpha.client_id == ROUTE
        assert beta is not None
        assert beta.client_id == OTHER_ROUTE


def _stub_headers(monkeypatch: pytest.MonkeyPatch, headers: dict[str, str]) -> None:
    """Make the route check see `headers` as the current HTTP request."""
    monkeypatch.setattr(mcp_auth, "get_http_headers", lambda: headers)


class TestRouteTokenRouteCheck:
    """A route token must not disagree with the route the request declares.

    The mismatch is a fail-closed rejection (the verifier returns `None`, which
    the bearer middleware turns into a 401) and it is logged so an operator can
    audit it; nothing is raised, because a verifier exception would become a 500.
    """

    async def test_matching_declared_route_is_accepted(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _stub_headers(monkeypatch, {"x-mcp-agent-id": ROUTE})
        verifier = build_auth(MCPServerSettings(route_tokens={ROUTE: ROUTE_TOKEN}))
        assert verifier is not None
        access = await verifier.verify_token(ROUTE_TOKEN)
        assert access is not None
        assert access.client_id == ROUTE

    async def test_mismatched_declared_route_is_rejected_and_logged(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        _stub_headers(monkeypatch, {"x-mcp-agent-id": OTHER_ROUTE})
        verifier = build_auth(MCPServerSettings(route_tokens={ROUTE: ROUTE_TOKEN}))
        assert verifier is not None
        with caplog.at_level(logging.WARNING, logger=mcp_auth.__name__):
            access = await verifier.verify_token(ROUTE_TOKEN)
        assert access is None
        # The audit trail names both routes, so the mismatch is investigable.
        assert ROUTE in caplog.text
        assert OTHER_ROUTE in caplog.text

    async def test_route_from_a_client_header_is_checked_too(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _stub_headers(monkeypatch, {"x-mcp-client": OTHER_ROUTE})
        verifier = build_auth(MCPServerSettings(route_tokens={ROUTE: ROUTE_TOKEN}))
        assert verifier is not None
        assert await verifier.verify_token(ROUTE_TOKEN) is None

    async def test_missing_declared_route_uses_the_token_route(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _stub_headers(monkeypatch, {})
        verifier = build_auth(MCPServerSettings(route_tokens={ROUTE: ROUTE_TOKEN}))
        assert verifier is not None
        access = await verifier.verify_token(ROUTE_TOKEN)
        assert access is not None
        assert access.client_id == ROUTE

    async def test_unusable_declared_route_is_treated_as_absent(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _stub_headers(monkeypatch, {"x-mcp-agent-id": "../../escape"})
        verifier = build_auth(MCPServerSettings(route_tokens={ROUTE: ROUTE_TOKEN}))
        assert verifier is not None
        access = await verifier.verify_token(ROUTE_TOKEN)
        assert access is not None
        assert access.client_id == ROUTE

    async def test_static_token_ignores_a_foreign_route_header(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _stub_headers(monkeypatch, {"x-mcp-agent-id": OTHER_ROUTE})
        verifier = build_auth(
            MCPServerSettings(auth_token=TOKEN, route_tokens={ROUTE: ROUTE_TOKEN})
        )
        assert verifier is not None
        access = await verifier.verify_token(TOKEN)
        assert access is not None
        assert access.client_id == CLIENT_ID


class TestProductionWiring:
    def test_server_has_no_auth_by_default(self) -> None:
        """Without MCP_AUTH_TOKEN the server stays open (backward compatible)."""
        from novelai_image_mcp import server

        assert server.mcp.auth is None


@asynccontextmanager
async def _serve(app: Any) -> AsyncIterator[str]:
    """Run an ASGI app on an ephemeral port; yield its base URL."""
    config = uvicorn.Config(app, host="127.0.0.1", port=0, log_level="warning")
    uvicorn_server = uvicorn.Server(config)
    task = asyncio.create_task(uvicorn_server.serve())
    try:
        for _ in range(500):
            if uvicorn_server.started:
                break
            await asyncio.sleep(0.01)
        assert uvicorn_server.started, "uvicorn did not start"
        port = uvicorn_server.servers[0].sockets[0].getsockname()[1]
        yield f"http://127.0.0.1:{port}"
    finally:
        uvicorn_server.should_exit = True
        await task


_INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2026-07-28",
        "capabilities": {},
        "clientInfo": {"name": "auth-test", "version": "1"},
    },
}


def _auth_server(settings: MCPServerSettings | None = None) -> Any:
    """A minimal server carrying the same auth wiring as production."""
    from fastmcp import FastMCP

    if settings is None:
        settings = MCPServerSettings(auth_token=TOKEN)
    server = FastMCP("auth-test", auth=build_auth(settings))

    @server.tool
    def ping() -> str:
        """Return pong."""
        return "pong"

    return server


class TestHttpTransportEnforcement:
    async def _post(self, url: str, headers: dict[str, str]) -> httpx.Response:
        async with httpx.AsyncClient(timeout=10) as client:
            return await client.post(
                f"{url}/mcp",
                json=_INITIALIZE,
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                    **headers,
                },
            )

    async def test_missing_bearer_is_rejected(self) -> None:
        async with _serve(_auth_server().http_app()) as url:
            response = await self._post(url, {})
        assert response.status_code == 401
        assert response.headers.get("www-authenticate")

    async def test_wrong_bearer_is_rejected(self) -> None:
        async with _serve(_auth_server().http_app()) as url:
            response = await self._post(url, {"Authorization": "Bearer wrong"})
        assert response.status_code == 401

    async def test_correct_bearer_reaches_the_protocol(self) -> None:
        async with _serve(_auth_server().http_app()) as url:
            response = await self._post(url, {"Authorization": f"Bearer {TOKEN}"})
        assert response.status_code == 200
        assert "result" in response.text or "result" in json.dumps(
            response.headers.multi_items()
        )

    async def test_authorized_client_can_list_tools(self) -> None:
        from contextlib import AsyncExitStack

        from fastmcp import Client

        async with AsyncExitStack() as stack:
            url = await stack.enter_async_context(_serve(_auth_server().http_app()))
            client = await stack.enter_async_context(Client(f"{url}/mcp", auth=TOKEN))
            tools = await client.list_tools()
        assert [tool.name for tool in tools] == ["ping"]


class TestRouteTokenHttpEnforcement:
    """The route check through the real ASGI stack, not just the verifier."""

    async def _post(self, url: str, headers: dict[str, str]) -> httpx.Response:
        async with httpx.AsyncClient(timeout=10) as client:
            return await client.post(
                f"{url}/mcp",
                json=_INITIALIZE,
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                    **headers,
                },
            )

    def _server(self) -> Any:
        return _auth_server(MCPServerSettings(route_tokens={ROUTE: ROUTE_TOKEN}))

    async def test_matching_route_reaches_the_protocol(self) -> None:
        async with _serve(self._server().http_app()) as url:
            response = await self._post(
                url,
                {"Authorization": f"Bearer {ROUTE_TOKEN}", "X-MCP-Agent-ID": ROUTE},
            )
        assert response.status_code == 200

    async def test_mismatched_route_is_rejected_with_a_challenge(self) -> None:
        async with _serve(self._server().http_app()) as url:
            response = await self._post(
                url,
                {
                    "Authorization": f"Bearer {ROUTE_TOKEN}",
                    "X-MCP-Agent-ID": OTHER_ROUTE,
                },
            )
        assert response.status_code == 401
        assert response.headers.get("www-authenticate")

    async def test_route_token_without_a_route_header_is_accepted(self) -> None:
        async with _serve(self._server().http_app()) as url:
            response = await self._post(url, {"Authorization": f"Bearer {ROUTE_TOKEN}"})
        assert response.status_code == 200

    async def test_static_token_is_unaffected_by_route_headers(self) -> None:
        settings = MCPServerSettings(
            auth_token=TOKEN, route_tokens={ROUTE: ROUTE_TOKEN}
        )
        async with _serve(_auth_server(settings).http_app()) as url:
            response = await self._post(
                url,
                {"Authorization": f"Bearer {TOKEN}", "X-MCP-Agent-ID": OTHER_ROUTE},
            )
        assert response.status_code == 200

    async def test_route_token_can_list_tools(self) -> None:
        from contextlib import AsyncExitStack

        from fastmcp import Client

        async with AsyncExitStack() as stack:
            url = await stack.enter_async_context(_serve(self._server().http_app()))
            client = await stack.enter_async_context(
                Client(f"{url}/mcp", auth=ROUTE_TOKEN)
            )
            tools = await client.list_tools()
        assert [tool.name for tool in tools] == ["ping"]
