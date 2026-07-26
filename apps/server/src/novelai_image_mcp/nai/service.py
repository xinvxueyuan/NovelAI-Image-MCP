"""High-level NovelAI service construction for the MCP server and CLI consumers.

A duck-typed config object (``NovelAIConfigLike`` Protocol) keeps the ``nai``
package decoupled from the MCP wrapper. The wrapper's ``NovelAISettings``
(pydantic-settings, env-driven) satisfies this protocol structurally; see
``novelai_image_mcp.settings``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from .auth import NovelAICredentials
from .client import MissingNovelAITokenError, NovelAIClient

if TYPE_CHECKING:
    import httpx


@runtime_checkable
class NovelAIConfigLike(Protocol):
    """Structural shape of any object supplying NovelAI client configuration."""

    token: str | None
    username: str | None
    password: str | None
    image_base_url: str
    account_base_url: str
    legacy_image_base_url: str
    timeout: float
    vibe_cache_entries: int


def create_novelai_client(
    config: NovelAIConfigLike,
    *,
    http_client: httpx.AsyncClient | None = None,
) -> NovelAIClient:
    """Create a complete client from a configuration object.

    Accepts either a token or a complete username/password pair. Pass a shared
    ``http_client`` when the caller (e.g. the MCP lifespan) wants connection
    pooling across requests; otherwise the client owns a private session.
    """
    if not config.token and not (config.username and config.password):
        raise MissingNovelAITokenError("NovelAI credentials are not configured")
    return NovelAIClient(
        NovelAICredentials(
            token=config.token,
            username=config.username,
            password=config.password,
        ),
        http_client=http_client,
        image_base_url=config.image_base_url,
        account_base_url=config.account_base_url,
        legacy_image_base_url=config.legacy_image_base_url,
        timeout=config.timeout,
        vibe_cache_entries=config.vibe_cache_entries,
    )


__all__ = ["NovelAIConfigLike", "create_novelai_client"]
