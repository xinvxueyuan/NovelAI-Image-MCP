"""Tests for the environment-driven settings surface."""

from __future__ import annotations

from typing import Any

import pytest

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
