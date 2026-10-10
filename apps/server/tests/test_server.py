"""Tests for the server composition root and lifespan.

The server is a thin module over `NovelAIClient`; these tests exercise the
lifespan setup/teardown (resource ownership), the `main()` transport
selection and the published server metadata, without spinning up a real MCP
transport.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from novelai_image_mcp import __version__, server


class TestLifespan:
    async def test_lifespan_yields_app_context_with_client_and_settings(
        self,
        settings: Any,
    ) -> None:
        """The lifespan constructs the client from settings and yields it."""
        fake_client = AsyncMock(name="NovelAIClient")
        fake_http = MagicMock(name="httpx.AsyncClient")
        fake_http.is_closed = False
        fake_http.aclose = AsyncMock()

        with (
            patch.object(server, "get_novelai_settings", return_value=settings),
            patch.object(server, "create_novelai_client", return_value=fake_client),
            patch.object(server, "create_http_client", return_value=fake_http),
        ):
            async with server.lifespan(MagicMock(name="server")) as ctx:
                assert ctx.client is fake_client
                assert ctx.settings is settings

        # On exit the lifespan closes the NovelAI client and the http session.
        fake_client.aclose.assert_awaited_once()
        fake_http.aclose.assert_awaited_once()

    async def test_lifespan_raises_when_credentials_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Without credentials the lifespan refuses to start."""
        monkeypatch.delenv("NOVELAI_TOKEN", raising=False)
        monkeypatch.delenv("NOVELAI_USERNAME", raising=False)
        monkeypatch.delenv("NOVELAI_PASSWORD", raising=False)
        with pytest.raises(RuntimeError, match="credentials are not configured"):
            async with server.lifespan(MagicMock()):
                pass

    async def test_lifespan_closes_http_when_client_close_raises(
        self, settings: Any
    ) -> None:
        """Even if ``client.aclose`` raises, ``http.aclose`` still runs."""
        fake_client = AsyncMock(name="NovelAIClient")
        fake_client.aclose.side_effect = RuntimeError("boom")
        fake_http = MagicMock(name="httpx.AsyncClient")
        fake_http.is_closed = False
        fake_http.aclose = AsyncMock()

        with (
            patch.object(server, "get_novelai_settings", return_value=settings),
            patch.object(server, "create_novelai_client", return_value=fake_client),
            patch.object(server, "create_http_client", return_value=fake_http),
            pytest.raises(RuntimeError, match="boom"),
        ):
            async with server.lifespan(MagicMock()):
                pass

        fake_http.aclose.assert_awaited_once()

    async def test_lifespan_skips_http_close_if_already_closed(
        self, settings: Any
    ) -> None:
        """If the http session is already closed, ``aclose`` is skipped."""
        fake_client = AsyncMock(name="NovelAIClient")
        fake_http = MagicMock(name="httpx.AsyncClient")
        fake_http.is_closed = True
        fake_http.aclose = AsyncMock()

        with (
            patch.object(server, "get_novelai_settings", return_value=settings),
            patch.object(server, "create_novelai_client", return_value=fake_client),
            patch.object(server, "create_http_client", return_value=fake_http),
        ):
            async with server.lifespan(MagicMock()):
                pass

        fake_http.aclose.assert_not_awaited()


class TestMain:
    @staticmethod
    def _capture(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
        captured: dict[str, Any] = {}

        def _fake_run(**kwargs: Any) -> None:
            captured.update(kwargs)

        monkeypatch.setattr(server.mcp, "run", _fake_run)
        return captured

    def test_main_runs_stdio_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """`main()` with no MCP_TRANSPORT env var calls ``mcp.run(stdio)``."""
        # `MCPServerSettings.transport` defaults to "stdio" (see settings.py).
        monkeypatch.delenv("MCP_TRANSPORT", raising=False)
        captured = self._capture(monkeypatch)
        server.main()
        assert captured.get("transport") == "stdio"

    def test_main_runs_http_when_configured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MCP_TRANSPORT", "http")
        monkeypatch.setenv("MCP_HOST", "0.0.0.0")
        monkeypatch.setenv("MCP_PORT", "9000")
        captured = self._capture(monkeypatch)
        server.main()
        assert captured.get("transport") == "http"
        assert captured.get("host") == "0.0.0.0"
        assert captured.get("port") == 9000
        assert captured.get("path") == "/mcp"

    def test_main_accepts_the_legacy_transport_alias(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`MCP_TRANSPORT=streamable-http` still selects the HTTP transport."""
        monkeypatch.setenv("MCP_TRANSPORT", "streamable-http")
        captured = self._capture(monkeypatch)
        server.main()
        assert captured.get("transport") == "http"

    def test_main_passes_the_configured_path(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`MCP_PATH` reaches FastMCP instead of being silently ignored."""
        monkeypatch.setenv("MCP_TRANSPORT", "http")
        monkeypatch.setenv("MCP_PATH", "/custom-mcp")
        captured = self._capture(monkeypatch)
        server.main()
        assert captured.get("path") == "/custom-mcp"

    def test_main_passes_the_log_level(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MCP_LOG_LEVEL", "WARNING")
        captured = self._capture(monkeypatch)
        server.main()
        assert captured.get("log_level") == "WARNING"


class TestModuleShape:
    def test_app_context_dataclass_holds_client_and_settings(
        self, fake_client: Any, settings: Any
    ) -> None:
        ctx = server.AppContext(client=fake_client, settings=settings)
        assert ctx.client is fake_client
        assert ctx.settings is settings

    def test_server_metadata_is_published(self) -> None:
        assert server.mcp.name == "novelai-image"
        # The version comes from the package, not from the framework.
        assert server.mcp.version == __version__
        assert server.mcp.website_url == (
            "https://github.com/xinvxueyuan/NovelAI-Image-MCP"
        )
        assert "NovelAI" in (server.mcp.instructions or "")

    async def test_unexpected_errors_are_masked(
        self, mcp_client: Any, fake_client: Any
    ) -> None:
        """An unexpected exception never leaks its message to the client.

        Expected failures raise `ToolError` with their domain message (see
        `test_tools.TestGenerateTools.test_provider_error_becomes_tool_error`);
        anything else is masked, which keeps internal details off the wire.
        """
        from fastmcp.exceptions import ToolError

        fake_client.generate.side_effect = RuntimeError("secret-internals")
        with pytest.raises(ToolError) as excinfo:
            await mcp_client.call_tool("generate_image", {"prompt": "a cat"})
        assert "secret-internals" not in str(excinfo.value)

    async def test_module_registers_every_component(self) -> None:
        """The shared server exposes all tools, prompts and resources."""
        assert len(await server.mcp.list_tools()) == 11
        assert {p.name for p in await server.mcp.list_prompts()} == {
            "novelai_image_workflow",
            "novelai_prompt_writer",
        }
        assert {str(r.uri) for r in await server.mcp.list_resources()} == {
            "novelai://defaults",
            "novelai://models",
            "novelai://samplers",
        }
        templates = await server.mcp.list_resource_templates()
        assert [t.uri_template for t in templates] == ["novelai://outputs/{name}"]
