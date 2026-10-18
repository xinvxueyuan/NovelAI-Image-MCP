"""End-to-end HTTP tests for the insiders header, routing and the tag gate.

These are the only tests that exercise the whole wire path: a real uvicorn
server, a real fastmcp Client speaking streamable HTTP, and real request
headers. Nothing here calls an internal function to stand in for a request --
every assertion is made on what an MCP client observes.

Two servers are driven:

* the **production** novelai_image_mcp.server.mcp instance, with the canned
  NovelAIClient from conftest behind its lifespan (no network), to pin the
  observable behaviour of the shipped tools: routing, the audit trail,
  route-scoped output and the director_tool emotion gate;
* a **test-only** FastMCP instance carrying the same
  ToolCallLoggingMiddleware and one tool tagged "insiders", to cover the tag
  gate itself. No tool in the production registry carries that tag, on purpose:
  tagging one would remove it from every client that does not send the header,
  breaking the promise that a header-less request behaves as before.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

from fastmcp import Client, FastMCP
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.exceptions import ToolError
import pytest
import uvicorn

from novelai_image_mcp.middleware import ToolCallLoggingMiddleware

if TYPE_CHECKING:
    from novelai_image_mcp.settings import NovelAISettings

#: Header that opts a request into the experimental surface.
INSIDERS_HEADER = "X-MCP-Insiders"

#: Routing header taken first by the default MCP_AGENT_HEADERS candidates.
AGENT_HEADER = "X-MCP-Agent-ID"

#: Routing header taken first by the default MCP_MODEL_HEADERS candidates.
MODEL_HEADER = "X-MCP-Model"

#: The agent identity the routed tests declare.
ROUTE = "team-a"

#: The model the routed tests declare.
MODEL = "nai-diffusion-4-5-full"

#: Number of tools the production registry publishes (see AGENTS.md).
PRODUCTION_TOOL_COUNT = 11

#: Every MCP_* setting the insiders/routing layer reads. A test starts from the
#: documented defaults so a developer's shell cannot change what it observes.
_INSIDERS_ENV = (
    "MCP_INSIDERS_HEADER",
    "MCP_MODEL_HEADERS",
    "MCP_AGENT_HEADERS",
    "MCP_CLIENT_HEADERS",
    "MCP_INSIDERS_DISABLED_FEATURES",
    "MCP_AUDIT_LOG_PATH",
    "MCP_ROUTE_SCOPED_OUTPUT",
    "MCP_ROUTE_TOKENS",
)


@pytest.fixture(autouse=True)
def _default_insiders_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Pin the insiders/routing settings to their documented defaults.

    MCPServerSettings is rebuilt from the environment on every request, so a
    stray variable would silently rewrite what these tests assert.
    NOVELAI_OUTPUT_DIR points at the per-test tmp dir, which is also where the
    audit trail lands (output_dir/audit.jsonl).
    """
    for name in _INSIDERS_ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("NOVELAI_OUTPUT_DIR", str(tmp_path))


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


@asynccontextmanager
async def _client(base_url: str, headers: dict[str, str]) -> AsyncIterator[Client]:
    """Connect a real MCP client to base_url, sending headers.

    Client itself accepts no headers argument in fastmcp 4: the headers belong
    to the HTTP transport, which is what actually puts them on the wire.
    """
    transport = StreamableHttpTransport(f"{base_url}/mcp", headers=headers)
    async with Client(transport) as client:
        yield client


def _texts(result: Any) -> str:
    """Return the text blocks of a tool result, joined by newlines."""
    return "\n".join(
        block.text for block in result.content if getattr(block, "text", None)
    )


def _png_names(directory: Path) -> list[str]:
    """Return the sorted names of the PNG files directly under directory."""
    return sorted(path.name for path in directory.glob("*.png"))


def _subdirectory_names(directory: Path) -> list[str]:
    """Return the sorted names of the subdirectories under directory."""
    return sorted(entry.name for entry in directory.iterdir() if entry.is_dir())


def _audit_records(tmp_path: Path) -> list[dict[str, Any]]:
    """Return the audit rows written under tmp_path."""
    lines = (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line]


@pytest.fixture
def production_app(
    monkeypatch: pytest.MonkeyPatch,
    settings: NovelAISettings,
    fake_client: Any,
) -> Any:
    """The production ASGI app, with a canned NovelAI client behind it.

    The server lifespan builds a real curl_cffi session and a real
    NovelAIClient; both are replaced exactly as conftest.mcp_client replaces
    them, so the app under test is the production one while no request leaves
    the machine.
    """
    from novelai_image_mcp import server as server_module

    fake_http = MagicMock(name="httpx.AsyncClient")
    fake_http.is_closed = False
    fake_http.aclose = AsyncMock()

    monkeypatch.setattr(server_module, "get_novelai_settings", lambda: settings)
    monkeypatch.setattr(
        server_module, "create_http_client", lambda **_kwargs: fake_http
    )
    monkeypatch.setattr(
        server_module,
        "create_novelai_client",
        lambda _settings, **_kwargs: fake_client,
    )
    # The module-level instance binds its auth provider at import time; dropping
    # it keeps a developer's MCP_AUTH_TOKEN from turning these requests into 401s.
    monkeypatch.setattr(server_module.mcp, "auth", None)
    return server_module.mcp.http_app()


def _gated_app() -> Any:
    """A test-only server: the production middleware plus one tagged tool."""
    server = FastMCP("insiders-http-test", middleware=[ToolCallLoggingMiddleware()])

    # The literal tag pins the documented wire contract rather than restating a
    # constant from the module under test.
    @server.tool(tags={"insiders"})
    def experimental_ping() -> str:
        """Return the experimental tool's canned answer."""
        return "experimental-pong"

    @server.tool
    def public_ping() -> str:
        """Return the always-available tool's canned answer."""
        return "pong"

    return server.http_app()


class TestTagGateOverHttp:
    """Mechanism coverage for the "insiders" tag gate.

    The production registry ships no tagged tool (see the module docstring), so
    the gate is exercised with a test-only tagged tool on an instance carrying
    the same ToolCallLoggingMiddleware. The experimental surface a production
    client actually meets is the director_tool emotion parameter, covered by
    TestDirectorEmotionGateOverHttp.
    """

    async def test_without_the_header_the_tagged_tool_is_hidden_and_rejected(
        self,
    ) -> None:
        async with _serve(_gated_app()) as url, _client(url, {}) as client:
            names = [tool.name for tool in await client.list_tools()]
            # Hidden from the listing ...
            assert names == ["public_ping"]
            # ... and unreachable by name, so guessing it is not a way in.
            with pytest.raises(ToolError, match="experimental"):
                await client.call_tool("experimental_ping", {})

    async def test_with_the_header_the_tagged_tool_is_listed_and_callable(
        self,
    ) -> None:
        headers = {INSIDERS_HEADER: "true"}
        async with _serve(_gated_app()) as url, _client(url, headers) as client:
            names = [tool.name for tool in await client.list_tools()]
            assert names == ["experimental_ping", "public_ping"]
            result = await client.call_tool("experimental_ping", {})
            assert result.is_error is False
            assert _texts(result) == "experimental-pong"


class TestProductionRoutingOverHttp:
    """The shipped tools over real HTTP, with and without the opt-in header."""

    async def test_without_the_header_nothing_changes(
        self, production_app: Any, tmp_path: Path
    ) -> None:
        """A header-less request behaves exactly as it did before routing."""
        async with _serve(production_app) as url, _client(url, {}) as client:
            tools = await client.list_tools()
            result = await client.call_tool("generate_image", {"prompt": "a cat"})
        assert result.is_error is False
        assert len(tools) == PRODUCTION_TOOL_COUNT
        # The artifact lands exactly where it did before routing existed ...
        assert _png_names(tmp_path)
        assert _subdirectory_names(tmp_path) == []
        # ... the result carries no route annotation ...
        assert "[route=" not in _texts(result)
        # ... and no audit trail is written.
        assert not (tmp_path / "audit.jsonl").exists()

    async def test_the_header_does_not_change_which_tools_are_published(
        self, production_app: Any
    ) -> None:
        """The red line: no shipped tool is gated, so opting in adds nothing."""
        async with _serve(production_app) as url:
            async with _client(url, {}) as plain:
                without_header = {tool.name for tool in await plain.list_tools()}
            async with _client(url, {INSIDERS_HEADER: "true"}) as opted_in:
                with_header = {tool.name for tool in await opted_in.list_tools()}
        assert without_header == with_header
        assert len(without_header) == PRODUCTION_TOOL_COUNT

    async def test_opt_in_routes_audits_and_scopes_the_artifact(
        self, production_app: Any, tmp_path: Path
    ) -> None:
        headers = {
            INSIDERS_HEADER: "true",
            AGENT_HEADER: ROUTE,
            MODEL_HEADER: MODEL,
            # Credentials on the wire must not survive into the audit trail.
            "Authorization": "Bearer s3cret",
            "Cookie": "session=abcdef",
        }
        async with _serve(production_app) as url, _client(url, headers) as client:
            result = await client.call_tool("generate_image", {"prompt": "a cat"})
        assert result.is_error is False
        assert f"[route={ROUTE}]" in _texts(result)

        # The artifact is scoped to the route ...
        written = _png_names(tmp_path / ROUTE)
        assert len(written) == 1
        assert _png_names(tmp_path) == []

        # ... and exactly one audit row records the routed call.
        records = _audit_records(tmp_path)
        assert len(records) == 1
        record = records[0]
        assert record["route"] == ROUTE
        assert record["model"] == MODEL
        assert record["agent"] == ROUTE
        assert record["tool"] == "generate_image"
        assert record["outcome"] == "ok"
        assert record["features"] == ["experimental-tools", "model-routing"]
        assert len(record["artifacts"]) == 1
        assert Path(record["artifacts"][0]).name == written[0]

        # The prompt is reduced to a digest and the credentials are dropped.
        assert record["arguments"]["prompt"]["length"] == len("a cat")
        assert "authorization" not in record["headers"]
        assert "cookie" not in record["headers"]
        raw = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
        assert "a cat" not in raw
        assert "s3cret" not in raw
        assert "abcdef" not in raw

    async def test_model_routing_false_keeps_the_sibling_gate_on(
        self, production_app: Any, png_b64: str, tmp_path: Path
    ) -> None:
        """The two sub-keys are independent: routing off, the gate still on."""
        headers = {INSIDERS_HEADER: "model-routing=false", AGENT_HEADER: ROUTE}
        async with _serve(production_app) as url, _client(url, headers) as client:
            # experimental-tools keeps its default (on), so the experimental
            # parameter is still accepted.
            director = await client.call_tool(
                "director_tool",
                {"tool": "emotion", "image": png_b64, "emotion": "happy"},
            )
            assert director.is_error is False
            result = await client.call_tool("generate_image", {"prompt": "a cat"})
            assert result.is_error is False
        # Routing itself is off: no annotation, no route subdirectory, no audit.
        assert "[route=" not in _texts(result)
        assert _png_names(tmp_path)
        assert _subdirectory_names(tmp_path) == []
        assert not (tmp_path / "audit.jsonl").exists()

    async def test_a_renamed_declaration_header_still_resolves_the_route(
        self,
        production_app: Any,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """MCP_AGENT_HEADERS moves the declaration header; routing follows."""
        monkeypatch.setenv("MCP_AGENT_HEADERS", json.dumps(["X-Route-Id"]))
        headers = {
            INSIDERS_HEADER: "true",
            "X-Route-Id": ROUTE,
            # The default header is no longer a candidate, so it must be ignored.
            AGENT_HEADER: "other-team",
        }
        async with _serve(production_app) as url, _client(url, headers) as client:
            result = await client.call_tool("generate_image", {"prompt": "a cat"})
        assert result.is_error is False
        assert [record["route"] for record in _audit_records(tmp_path)] == [ROUTE]
        assert len(_png_names(tmp_path / ROUTE)) == 1


class TestDirectorEmotionGateOverHttp:
    """The experimental surface a production client actually meets."""

    async def test_the_emotion_gate_is_per_request(
        self, production_app: Any, png_b64: str, tmp_path: Path
    ) -> None:
        """The same call is refused header-less and served with the header."""
        args = {"tool": "emotion", "image": png_b64, "emotion": "happy"}
        async with _serve(production_app) as url:
            async with _client(url, {}) as client:
                with pytest.raises(ToolError, match="experimental"):
                    await client.call_tool("director_tool", args)
            async with _client(url, {INSIDERS_HEADER: "true"}) as client:
                allowed = await client.call_tool("director_tool", args)
        assert allowed.is_error is False
        assert "Saved image" in _texts(allowed)
        # Only the served call reached the audit trail: the refusal wrote nothing.
        records = _audit_records(tmp_path)
        assert len(records) == 1
        assert records[0]["tool"] == "director_tool"
        assert records[0]["outcome"] == "ok"

    async def test_a_non_default_emotion_level_alone_is_gated(
        self, production_app: Any, png_b64: str
    ) -> None:
        """Passing only emotion_level counts as touching the gate."""
        args = {"tool": "lineart", "image": png_b64, "emotion_level": 5}
        async with _serve(production_app) as url:
            async with _client(url, {}) as client:
                with pytest.raises(ToolError, match="experimental"):
                    await client.call_tool("director_tool", args)
            async with _client(url, {INSIDERS_HEADER: "true"}) as client:
                allowed = await client.call_tool("director_tool", args)
        assert allowed.is_error is False
