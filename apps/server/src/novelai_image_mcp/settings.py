"""Environment-driven configuration for the NovelAI Image MCP server.

Two ``pydantic-settings`` models expose the runtime configuration surface:
``NovelAISettings`` (credentials + generation defaults, ``NOVELAI_*`` env
vars) and ``MCPServerSettings`` (transport, ``MCP_*`` env vars).

``NovelAISettings`` structurally satisfies ``nai.NovelAIConfigLike`` so the
client factory consumes it directly.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class NovelAISettings(BaseSettings):
    """NovelAI credentials, endpoints, and generation defaults.

    All fields are read from ``NOVELAI_*`` environment variables (and an optional
    ``.env`` file in the working directory). Exactly one auth method is required
    at runtime: either ``token`` (preferred) or the ``username``+``password`` pair.
    """

    model_config = SettingsConfigDict(
        env_prefix="NOVELAI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Credentials ──
    token: str | None = None
    username: str | None = None
    password: str | None = None

    # ── Endpoints ──
    # ``image.novelai.net`` is the consolidated host for most third-party API
    # traffic (generation, director, account, etc.). ``legacy_image_base_url``
    # points at the Primary API (``api.novelai.net``) which still hosts
    # ``/ai/upscale`` and ``/ai/annotate-image`` — these two endpoints were not
    # migrated to ``image.novelai.net`` and 404 there. The Primary API's own
    # docs (https://api.novelai.net/docs/) state that third-party users may use
    # its ``/ai/`` routes.
    image_base_url: str = "https://image.novelai.net"
    account_base_url: str = "https://image.novelai.net"
    legacy_image_base_url: str = "https://api.novelai.net"
    timeout: float = Field(default=120.0, gt=0)

    # ── Generation defaults (overridable per tool call) ──
    # Default stays on V4.5 for compatibility — V5 is ~2.5x heavier and its
    # Opus free quota is refillable/limited; switch to "nai-diffusion-5-full"
    # via NOVELAI_DEFAULT_MODEL when V5 is desired.
    default_model: str = "nai-diffusion-4-5-full"
    default_width: int = Field(default=832, ge=64, le=49_152)
    default_height: int = Field(default=1216, ge=64, le=49_152)
    default_steps: int = Field(default=28, ge=1, le=50)
    default_scale: float = Field(default=5.0, gt=0, le=20)
    default_sampler: str = "k_euler_ancestral"

    # ── Client ──
    vibe_cache_entries: int = Field(default=64, ge=1, le=1024)

    # ── Output ──
    output_dir: str = "outputs"

    def has_credentials(self) -> bool:
        """True when either a token or a complete username/password pair is set."""
        return bool(self.token) or bool(self.username and self.password)


class MCPServerSettings(BaseSettings):
    """MCP server transport selection (``MCP_*`` env vars)."""

    model_config = SettingsConfigDict(
        env_prefix="MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    transport: Literal["stdio", "streamable-http"] = "stdio"
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65_535)
    path: str = "/mcp"


def get_novelai_settings() -> NovelAISettings:
    """Load NovelAI settings from environment / .env."""
    return NovelAISettings()


def get_mcp_settings() -> MCPServerSettings:
    """Load MCP server settings from environment / .env."""
    return MCPServerSettings()


__all__ = [
    "MCPServerSettings",
    "NovelAISettings",
    "get_mcp_settings",
    "get_novelai_settings",
]
