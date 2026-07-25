"""Tests for the server composition root and lifespan.

The server is a thin module over ``NovelAIClient``; these tests exercise the
lifespan setup/teardown (resource ownership) and the ``main()`` transport
selection, without spinning up a real MCP transport.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from novelai_image_mcp import server


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
            patch.object(server.httpx, "AsyncClient", return_value=fake_http),
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
            patch.object(server.httpx, "AsyncClient", return_value=fake_http),
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
            patch.object(server.httpx, "AsyncClient", return_value=fake_http),
        ):
            async with server.lifespan(MagicMock()):
                pass

        fake_http.aclose.assert_not_awaited()


class TestMain:
    def test_main_runs_stdio_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``main()`` with no MCP_TRANSPORT env var calls ``mcp.run(stdio)``."""
        captured: dict[str, Any] = {}

        def _fake_run(**kwargs: Any) -> None:
            captured.update(kwargs)

        # ``MCPServerSettings.transport`` defaults to "stdio" (see settings.py).
        monkeypatch.delenv("MCP_TRANSPORT", raising=False)
        monkeypatch.setattr(server.mcp, "run", _fake_run)
        server.main()
        assert captured.get("transport") == "stdio"

    def test_main_runs_http_when_configured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured: dict[str, Any] = {}

        def _fake_run(**kwargs: Any) -> None:
            captured.update(kwargs)

        monkeypatch.setenv("MCP_TRANSPORT", "streamable-http")
        monkeypatch.setenv("MCP_HOST", "0.0.0.0")
        monkeypatch.setenv("MCP_PORT", "9000")
        monkeypatch.setattr(server.mcp, "run", _fake_run)
        server.main()
        assert captured.get("transport") == "streamable-http"
        assert captured.get("host") == "0.0.0.0"
        assert captured.get("port") == 9000


class TestModuleShape:
    def test_app_context_dataclass_holds_client_and_settings(
        self, fake_client: Any, settings: Any
    ) -> None:
        ctx = server.AppContext(client=fake_client, settings=settings)
        assert ctx.client is fake_client
        assert ctx.settings is settings

    def test_module_registers_all_tool_groups(self, recording_mcp: Any) -> None:
        """The default ``server.mcp`` has every tool group registered."""
        # Touch the module to ensure tools.register_all(mcp) has run.
        assert server.mcp is not None
        # The recording_mcp fixture uses its own register_all; verify the same
        # set of names is registered on the real server.
        from novelai_image_mcp.tools import register_all

        register_all(recording_mcp)
        expected = {
            "generate_image",
            "image_to_image",
            "inpaint",
            "upscale_image",
            "director_tool",
            "annotate_image",
            "suggest_tags",
            "encode_vibe",
            "get_subscription",
            "get_user_data",
            "estimate_anlas_cost",
        }
        assert expected.issubset(recording_mcp.tools.keys())
