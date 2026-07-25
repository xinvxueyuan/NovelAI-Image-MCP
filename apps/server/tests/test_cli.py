"""Tests for the sync typer CLI (``novelai-image-mcp``).

The CLI is a thin wrapper around the async ``NovelAIClient``; these tests
exercise argument parsing, validation, and the async dispatcher without making
real HTTP calls. ``create_novelai_client`` is patched to return a stub that
records each call and short-circuits the awaited coroutine.
"""

from __future__ import annotations

import base64
from collections.abc import Iterator
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

from _helpers import PNG_BYTES
import pytest
from typer.testing import CliRunner

from novelai_image_mcp import cli

if TYPE_CHECKING:
    from novelai_image_mcp.nai import NovelAIImage


@pytest.fixture(autouse=True)
def _no_color(monkeypatch: pytest.MonkeyPatch) -> None:
    """Disable color output so stderr assertions are stable in CI.

    Typer's Rich integration forces terminal color when GITHUB_ACTIONS is
    set (typer.rich_utils.FORCE_TERMINAL). The OptionHighlighter then wraps
    ``--option`` tokens in error messages with ANSI codes, breaking
    substring assertions like ``"emotion tool requires --emotion" in
    result.stderr``. ``NO_COLOR`` is respected by Rich's Console even when
    force_terminal is True (see rich.console._render_buffer →
    Segment.remove_color).
    """
    monkeypatch.setenv("NO_COLOR", "1")


@pytest.fixture
def runner() -> CliRunner:
    """A typer CliRunner that captures stdout and stderr separately.

    Click >= 8.2 removed the ``mix_stderr`` kwarg; ``stderr`` is now captured
    independently by default, so we just construct a vanilla runner.
    """
    return CliRunner()


@pytest.fixture
def captured_png(tmp_path: Path) -> Path:
    """Write ``PNG_BYTES`` to a temp file the CLI can read."""
    path = tmp_path / "in.png"
    path.write_bytes(PNG_BYTES)
    return path


@pytest.fixture
def mock_http_client() -> MagicMock:
    """A MagicMock standing in for ``httpx.AsyncClient``.

    The CLI checks ``is_closed`` after use; default MagicMock attributes are
    truthy, so the cleanup path runs without needing explicit setup.
    """
    http = MagicMock(name="httpx.AsyncClient")
    http.is_closed = True  # ensures cleanup skips the aclose() await
    return http


@pytest.fixture
def patched_client(
    mock_http_client: MagicMock,
    nai_image: NovelAIImage,
    settings: Any,
) -> Iterator[tuple[AsyncMock, MagicMock]]:
    """Patch ``create_novelai_client`` and ``get_novelai_settings`` for the CLI.

    Yields ``(client, http_client)`` so individual tests can assert on either.
    The mock client's async methods return canned values by default; per-test
    overrides happen directly on the mock. ``get_novelai_settings`` is patched
    to return the conftest ``settings`` fixture so subcommands don't read the
    real environment for credentials.
    """
    client = AsyncMock(name="NovelAIClient")
    client.generate.return_value = (nai_image,)
    client.upscale.return_value = nai_image
    client.director.return_value = nai_image
    client.annotate.return_value = nai_image
    client.get_subscription.return_value = {"tier": 1}
    client.aclose.return_value = None

    # Make the synchronous ``create_novelai_client`` build the AsyncMock + stub
    # pair, so the CLI's tuple-unpacking pattern continues to work. ``_http_client``
    # is intentionally unused — the CLI's ``_build_client`` constructs the
    # ``httpx.AsyncClient`` itself; only the AsyncMock return value matters here.
    def _factory(_settings: Any, *, http_client: Any = None) -> AsyncMock:  # noqa: ARG001
        return client

    with (
        patch("httpx.AsyncClient", return_value=mock_http_client),
        patch.object(cli, "create_novelai_client", side_effect=_factory),
        patch.object(cli, "get_novelai_settings", return_value=settings),
    ):
        yield client, mock_http_client


class TestCliCredentials:
    def test_generate_without_credentials_exits_2(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Missing credentials abort before any HTTP client is built."""
        monkeypatch.delenv("NOVELAI_TOKEN", raising=False)
        monkeypatch.delenv("NOVELAI_USERNAME", raising=False)
        monkeypatch.delenv("NOVELAI_PASSWORD", raising=False)
        result = runner.invoke(cli.app, ["generate", "--prompt", "x"])
        assert result.exit_code == 2
        assert "credentials are not configured" in result.stderr


class TestCliGenerate:
    def test_generate_invokes_client_and_echoes_path(
        self,
        runner: CliRunner,
        patched_client: tuple[AsyncMock, MagicMock],
        tmp_path: Path,
    ) -> None:
        client, _ = patched_client
        result = runner.invoke(
            cli.app,
            [
                "generate",
                "--prompt",
                "a cat",
                "--negative",
                "lowres",
                "--seed",
                "42",
                "--output-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0, result.stderr
        client.generate.assert_awaited_once()
        request = client.generate.await_args.args[0]
        assert request.prompt == "a cat"
        assert request.negative_prompt == "lowres"
        assert request.seed == 42
        # The CLI echoes the saved path; assert it points at an existing file.
        echoed = result.stdout.strip().splitlines()[-1]
        assert Path(echoed).exists()
        assert Path(echoed).read_bytes() == PNG_BYTES

    def test_generate_unknown_model_returns_bad_parameter(
        self,
        runner: CliRunner,
        patched_client: tuple[AsyncMock, MagicMock],
        tmp_path: Path,
    ) -> None:
        """An invalid model id surfaces as a typer BadParameter (exit code 2)."""
        result = runner.invoke(
            cli.app,
            [
                "generate",
                "--prompt",
                "x",
                "--model",
                "bogus-model",
                "--output-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 2
        assert "unknown model" in result.stderr
        patched_client[0].generate.assert_not_called()


class TestCliEnhance:
    def test_upscale_invokes_client(
        self,
        runner: CliRunner,
        patched_client: tuple[AsyncMock, MagicMock],
        captured_png: Path,
        tmp_path: Path,
    ) -> None:
        client, _ = patched_client
        result = runner.invoke(
            cli.app,
            [
                "upscale",
                str(captured_png),
                "--factor",
                "4",
                "--output-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0, result.stderr
        client.upscale.assert_awaited_once_with(PNG_BYTES, factor=4)

    def test_upscale_missing_file_returns_bad_parameter(
        self,
        runner: CliRunner,
        patched_client: tuple[AsyncMock, MagicMock],
        tmp_path: Path,
    ) -> None:
        missing = tmp_path / "does-not-exist.png"
        result = runner.invoke(
            cli.app, ["upscale", str(missing), "--output-dir", str(tmp_path)]
        )
        assert result.exit_code == 2
        assert "cannot read image file" in result.stderr

    def test_director_emotion_requires_emotion_flag(
        self,
        runner: CliRunner,
        patched_client: tuple[AsyncMock, MagicMock],
        captured_png: Path,
        tmp_path: Path,
    ) -> None:
        result = runner.invoke(
            cli.app,
            [
                "director",
                "emotion",
                str(captured_png),
                "--output-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 2
        assert "emotion tool requires --emotion" in result.stderr

    def test_director_unknown_tool_returns_bad_parameter(
        self,
        runner: CliRunner,
        patched_client: tuple[AsyncMock, MagicMock],
        captured_png: Path,
        tmp_path: Path,
    ) -> None:
        result = runner.invoke(
            cli.app,
            [
                "director",
                "bogus",
                str(captured_png),
                "--output-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 2
        assert "unknown director tool" in result.stderr

    def test_director_emotion_success_invokes_client(
        self,
        runner: CliRunner,
        patched_client: tuple[AsyncMock, MagicMock],
        captured_png: Path,
        tmp_path: Path,
    ) -> None:
        client, _ = patched_client
        result = runner.invoke(
            cli.app,
            [
                "director",
                "emotion",
                str(captured_png),
                "--emotion",
                "happy",
                "--emotion-level",
                "1",
                "--output-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0, result.stderr
        client.director.assert_awaited_once()
        call = client.director.await_args
        assert call.kwargs["emotion"].value == "happy"

    def test_annotate_invokes_client(
        self,
        runner: CliRunner,
        patched_client: tuple[AsyncMock, MagicMock],
        captured_png: Path,
        tmp_path: Path,
    ) -> None:
        client, _ = patched_client
        result = runner.invoke(
            cli.app,
            [
                "annotate",
                str(captured_png),
                "--model",
                "hed",
                "--output-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0, result.stderr
        client.annotate.assert_awaited_once()
        call = client.annotate.await_args
        assert call.args[1].value == "hed"

    def test_annotate_unknown_model_returns_bad_parameter(
        self,
        runner: CliRunner,
        patched_client: tuple[AsyncMock, MagicMock],
        captured_png: Path,
        tmp_path: Path,
    ) -> None:
        result = runner.invoke(
            cli.app,
            [
                "annotate",
                str(captured_png),
                "--model",
                "bogus",
                "--output-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 2
        assert "unknown controlnet model" in result.stderr


class TestCliInfo:
    def test_info_prints_subscription_as_json(
        self,
        runner: CliRunner,
        patched_client: tuple[AsyncMock, MagicMock],
    ) -> None:
        client, _ = patched_client
        client.get_subscription.return_value = {"tier": 2, "active": True}
        result = runner.invoke(cli.app, ["info"])
        assert result.exit_code == 0, result.stderr
        # ``info`` echoes a multi-line indented JSON document; parse the whole
        # stdout buffer rather than just the trailing line.
        payload = json.loads(result.stdout)
        assert payload == {"tier": 2, "active": True}


class TestCliServe:
    def test_serve_stdio_invokes_mcp_run(
        self,
        runner: CliRunner,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``serve`` without ``--transport`` runs the MCP server on stdio."""
        captured: dict[str, Any] = {}

        class _FakeMCP:
            def run(self, **kwargs: Any) -> None:
                captured.update(kwargs)

        # Inject a fake ``mcp`` onto the imported server module so the CLI
        # picks it up without invoking the real ``MCPServer.run``.
        from novelai_image_mcp import server as server_module

        original = server_module.mcp
        monkeypatch.setattr(server_module, "mcp", _FakeMCP())
        try:
            result = runner.invoke(cli.app, ["serve"])
        finally:
            monkeypatch.setattr(server_module, "mcp", original)

        assert result.exit_code == 0, result.stderr
        assert captured.get("transport") == "stdio"

    def test_serve_http_passes_host_and_port(
        self,
        runner: CliRunner,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: dict[str, Any] = {}

        class _FakeMCP:
            def run(self, **kwargs: Any) -> None:
                captured.update(kwargs)

        from novelai_image_mcp import server as server_module

        original = server_module.mcp
        monkeypatch.setattr(server_module, "mcp", _FakeMCP())
        try:
            result = runner.invoke(
                cli.app,
                [
                    "serve",
                    "--transport",
                    "streamable-http",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "9000",
                ],
            )
        finally:
            monkeypatch.setattr(server_module, "mcp", original)

        assert result.exit_code == 0, result.stderr
        assert captured.get("transport") == "streamable-http"
        assert captured.get("host") == "0.0.0.0"
        assert captured.get("port") == 9000


class TestCliReadImageBase64:
    """``_read_image_file`` is reused by every image-input subcommand."""

    def test_read_image_file_returns_bytes(self, captured_png: Path) -> None:
        data = cli._read_image_file(captured_png)
        assert data == PNG_BYTES

    def test_read_image_file_missing_raises_bad_parameter(self, tmp_path: Path) -> None:
        import typer

        missing = tmp_path / "ghost.png"
        with pytest.raises(typer.BadParameter, match="cannot read image file"):
            cli._read_image_file(missing)


class TestCliParseModel:
    def test_parse_model_uses_settings_default(self, settings: Any) -> None:
        resolved = cli._parse_model(None, settings)
        assert resolved.value == settings.default_model

    def test_parse_model_unknown_raises_bad_parameter(self, settings: Any) -> None:
        import typer

        with pytest.raises(typer.BadParameter, match="unknown model"):
            cli._parse_model("bogus-model", settings)


# Re-export the local PNG constant for any external test consumers that may
# import it from this module (kept for parity with _helpers).
PNG_BYTES_B64 = base64.b64encode(PNG_BYTES).decode("ascii")
