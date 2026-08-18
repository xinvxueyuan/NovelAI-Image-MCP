"""Shared pytest fixtures for the NovelAI Image MCP test suite."""

from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock

import pytest

# Make tests/ importable so test files can ``from _helpers import ...``.
sys.path.insert(0, str(Path(__file__).parent))

from _helpers import PNG_BYTES, RecordingMCPServer

if TYPE_CHECKING:
    from novelai_image_mcp.nai import NovelAIImage
    from novelai_image_mcp.settings import NovelAISettings


@pytest.fixture
def png_bytes() -> bytes:
    """Return a minimal valid PNG byte string."""
    return PNG_BYTES


@pytest.fixture
def png_b64() -> str:
    """Return the same PNG as a base64-encoded ASCII string (wire format)."""
    import base64

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

    Individual tests override specific ``return_value`` / ``side_effect`` values
    on the mock's methods (``generate``, ``upscale``, ``director``, ...).
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
def fake_ctx(fake_client: Any, settings: NovelAISettings) -> Any:
    """A minimal Context stand-in exposing ``lifespan_context``.

    Tools read the lifespan value via ``ctx.lifespan_context`` (the fastmcp
    ``Context`` convenience property), so the stand-in exposes that attribute
    directly rather than the MCP v2 ``request_context.lifespan_context`` shape.
    """
    return SimpleNamespace(
        lifespan_context=SimpleNamespace(client=fake_client, settings=settings),
    )


@pytest.fixture
def recording_mcp() -> RecordingMCPServer:
    """An MCPServer stub that records tools as ``register(mcp)`` is called."""
    return RecordingMCPServer()
