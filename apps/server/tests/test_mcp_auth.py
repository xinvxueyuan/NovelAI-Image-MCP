"""Tests for the optional bearer-token authentication."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import json
from typing import Any

import httpx
import uvicorn

from novelai_image_mcp.mcp_auth import CLIENT_ID, build_auth
from novelai_image_mcp.settings import MCPServerSettings

TOKEN = "s3cret-token"


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


def _auth_server() -> Any:
    """A minimal server carrying the same auth wiring as production."""
    from fastmcp import FastMCP

    server = FastMCP("auth-test", auth=build_auth(MCPServerSettings(auth_token=TOKEN)))

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
