"""Shared pytest fixtures for the NovelAI Image MCP test suite."""

from __future__ import annotations

import base64
from pathlib import Path
import sys
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

# Make tests/ importable so test files can `from _helpers import ...`.
sys.path.insert(0, str(Path(__file__).parent))

from _helpers import PNG_BYTES

if TYPE_CHECKING:
    from novelai_image_mcp.deps import AppContext
    from novelai_image_mcp.nai import NovelAIImage
    from novelai_image_mcp.settings import NovelAISettings


@pytest.fixture
def png_bytes() -> bytes:
    """Return a minimal valid PNG byte string."""
    return PNG_BYTES


@pytest.fixture
def png_b64() -> str:
    """Return the same PNG as a base64-encoded ASCII string (wire format)."""
    return base64.b64encode(PNG_BYTES).decode("ascii")


@pytest.fixture
def nai_image(png_bytes: bytes) -> NovelAIImage:
    """A canned NovelAIImage returned by mocked client methods."""
    from novelai_image_mcp.nai import NovelAIImage

    return NovelAIImage(filename="test.png", data=png_bytes)


@pytest.fixture
def settings(tmp_path: Path) -> NovelAISettings:
    """NovelAISettings with a token and a tmp output dir."""
    from novelai_image_mcp.settings import NovelAISettings

    return NovelAISettings(
        token="pst-test-token",
        output_dir=str(tmp_path),
        default_width=832,
        default_height=1216,
        default_steps=28,
        default_scale=5.0,
        default_sampler="k_euler_ancestral",
        default_model="nai-diffusion-4-5-full",
    )


@pytest.fixture
def fake_client(nai_image: NovelAIImage) -> Any:
    """An AsyncMock of NovelAIClient that returns canned images by default.

    Individual tests override specific `return_value` / `side_effect` values
    on the mock's methods (`generate`, `upscale`, `director`, ...).
    """
    client = AsyncMock()
    client.generate.return_value = (nai_image,)
    client.upscale.return_value = nai_image
    client.director.return_value = nai_image
    client.annotate.return_value = nai_image
    client.suggest_tags.return_value = ({"text": "cat", "count": 100},)
    client.encode_vibe.return_value = "vibe-token-base64"
    client.get_subscription.return_value = {
        "tier": 1,
        "trainingStepsLeft": {"fixed": 10000},
    }
    client.get_user_data.return_value = {"email": "tester@example.com"}
    client.aclose.return_value = None
    return client


@pytest.fixture
def fake_app(fake_client: Any, settings: NovelAISettings) -> AppContext:
    """An `AppContext` as the lifespan yields it.

    Tools declare `app: AppContext = Depends(get_app_context)`; passing this
    value directly exercises the tool body without going through FastMCP.
    """
    from novelai_image_mcp.deps import AppContext

    return AppContext(client=fake_client, settings=settings)


# The client must be entered on the same event loop that the test body runs
# on: the in-memory transport is bound to whichever loop opened it, so the
# session-scoped fixture loop (asyncio_default_fixture_loop_scope) would hang
# every `await` in a function-scoped test.
@pytest_asyncio.fixture(loop_scope="function")
async def mcp_client(
    monkeypatch: pytest.MonkeyPatch,
    settings: NovelAISettings,
    fake_client: Any,
) -> Any:
    """An in-memory `fastmcp.Client` driving the real server pipeline.

    The server's lifespan is patched to build the canned client instead of a
    real `curl_cffi` session, so tests exercise the production registration,
    schema generation, dependency injection and result conversion without
    touching the network.
    """
    from fastmcp import Client

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

    async with Client(server_module.mcp) as client:
        yield client
