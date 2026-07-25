"""Tests for the MCP tool wrappers in ``novelai_image_mcp.tools``."""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import AsyncMock

from _helpers import PNG_BYTES, RecordingMCPServer
import pytest

from novelai_image_mcp._mcp import MCPServer
from novelai_image_mcp.tools import account, enhance, generate, tags

if TYPE_CHECKING:
    from novelai_image_mcp.nai import NovelAIImage


def _b64(data: bytes = PNG_BYTES) -> str:
    """Encode bytes as a base64 ASCII string (the wire format tools expect)."""
    return base64.b64encode(data).decode("ascii")


def _register_all(mcp: RecordingMCPServer) -> None:
    # ``RecordingMCPServer`` is a structural test double that exposes the same
    # ``tool()`` decorator contract as the SDK's ``MCPServer``; cast to satisfy
    # the production-typed ``register(mcp: MCPServer)`` signatures.
    server = cast(MCPServer, mcp)
    generate.register(server)
    enhance.register(server)
    tags.register(server)
    account.register(server)


@pytest.fixture
def tools(recording_mcp: RecordingMCPServer) -> dict[str, Any]:
    """Register every tool group and expose them as a name → callable dict."""
    _register_all(recording_mcp)
    return recording_mcp.tools


@pytest.fixture
def ctx(fake_ctx: Any) -> Any:
    """Forward the conftest ``fake_ctx`` fixture (lifespan_context)."""
    return fake_ctx


def _assert_image_block(result: list[Any]) -> bytes:
    """Pull the bytes out of the returned Image content block."""
    image_block = next(item for item in result if hasattr(item, "data"))
    return image_block.data


def _assert_path_str(result: list[Any]) -> str:
    """Pull the saved-path string out of the returned text block."""
    return next(item for item in result if isinstance(item, str))


class TestGenerateTools:
    async def test_generate_image_calls_client(
        self,
        tools: dict[str, Any],
        ctx: Any,
        fake_client: AsyncMock,
        nai_image: NovelAIImage,
    ) -> None:
        fake_client.generate.return_value = (nai_image,)
        result = await tools["generate_image"](
            ctx,
            prompt="a cat, masterpiece",
            negative_prompt="lowres",
            seed=42,
        )
        fake_client.generate.assert_awaited_once()
        request = fake_client.generate.await_args.args[0]
        assert request.prompt == "a cat, masterpiece"
        assert request.seed == 42
        assert _assert_image_block(result) == nai_image.data
        assert "Saved 1 image(s)" in _assert_path_str(result)

    async def test_generate_image_with_character_prompts(
        self, tools: dict[str, Any], ctx: Any, fake_client: AsyncMock
    ) -> None:
        await tools["generate_image"](
            ctx,
            prompt="a girl and a boy",
            character_prompts=[{"prompt": "girl", "x": 0.3, "y": 0.5}],
        )
        request = fake_client.generate.await_args.args[0]
        assert len(request.character_prompts) == 1
        assert request.character_prompts[0].x == 0.3

    async def test_img2img_passes_image_through(
        self, tools: dict[str, Any], ctx: Any, fake_client: AsyncMock
    ) -> None:
        await tools["image_to_image"](
            ctx, prompt="restyle", image="base64-image-string", strength=0.5
        )
        request = fake_client.generate.await_args.args[0]
        assert request.image == "base64-image-string"
        assert request.strength == 0.5

    async def test_inpaint_passes_mask_through(
        self, tools: dict[str, Any], ctx: Any, fake_client: AsyncMock
    ) -> None:
        await tools["inpaint"](
            ctx,
            prompt="redraw",
            image="base64-image",
            mask="base64-mask",
            model="nai-diffusion-4-5-full-inpainting",
        )
        request = fake_client.generate.await_args.args[0]
        assert request.mask == "base64-mask"
        assert request.action.value == "infill"


class TestEnhanceTools:
    async def test_upscale_image(
        self,
        tools: dict[str, Any],
        ctx: Any,
        fake_client: AsyncMock,
        nai_image: NovelAIImage,
    ) -> None:
        fake_client.upscale.return_value = nai_image
        result = await tools["upscale_image"](ctx, image=_b64(), factor=4)
        fake_client.upscale.assert_awaited_once_with(PNG_BYTES, factor=4)
        assert _assert_image_block(result) == nai_image.data

    async def test_director_emotion_validates(
        self, tools: dict[str, Any], ctx: Any, fake_client: AsyncMock
    ) -> None:
        with pytest.raises(ValueError, match="emotion tool requires an emotion"):
            await tools["director_tool"](ctx, tool="emotion", image="b64", emotion=None)

    async def test_director_emotion_success(
        self,
        tools: dict[str, Any],
        ctx: Any,
        fake_client: AsyncMock,
        nai_image: NovelAIImage,
    ) -> None:
        fake_client.director.return_value = nai_image
        await tools["director_tool"](
            ctx,
            tool="emotion",
            image=_b64(),
            emotion="happy",
            emotion_level=0,
        )
        fake_client.director.assert_awaited_once()
        call = fake_client.director.await_args
        assert call.kwargs["emotion"].value == "happy"

    async def test_director_unknown_tool_raises(
        self, tools: dict[str, Any], ctx: Any
    ) -> None:
        with pytest.raises(ValueError, match="unknown director tool"):
            await tools["director_tool"](ctx, tool="bogus", image="b64")

    async def test_annotate_image(
        self,
        tools: dict[str, Any],
        ctx: Any,
        fake_client: AsyncMock,
        nai_image: NovelAIImage,
    ) -> None:
        fake_client.annotate.return_value = nai_image
        await tools["annotate_image"](ctx, image=_b64(), model="hed")
        fake_client.annotate.assert_awaited_once()
        call = fake_client.annotate.await_args
        assert call.args[1].value == "hed"

    async def test_annotate_unknown_model_raises(
        self, tools: dict[str, Any], ctx: Any
    ) -> None:
        with pytest.raises(ValueError, match="unknown controlnet model"):
            await tools["annotate_image"](ctx, image="b64", model="bogus")


class TestTagsTools:
    async def test_suggest_tags(
        self, tools: dict[str, Any], ctx: Any, fake_client: AsyncMock
    ) -> None:
        fake_client.suggest_tags.return_value = ({"text": "cat"},)
        result = await tools["suggest_tags"](ctx, prompt="ca")
        fake_client.suggest_tags.assert_awaited_once()
        assert result == [{"text": "cat"}]

    async def test_suggest_tags_unknown_model_raises(
        self, tools: dict[str, Any], ctx: Any
    ) -> None:
        with pytest.raises(ValueError, match="unknown model"):
            await tools["suggest_tags"](ctx, prompt="ca", model="bogus")

    async def test_encode_vibe(
        self, tools: dict[str, Any], ctx: Any, fake_client: AsyncMock
    ) -> None:
        fake_client.encode_vibe.return_value = "vibe-token"
        result = await tools["encode_vibe"](
            ctx, reference="b64", information_extracted=0.5
        )
        assert result == "vibe-token"
        call = fake_client.encode_vibe.await_args
        assert call.kwargs["information_extracted"] == 0.5

    async def test_encode_vibe_information_range(
        self, tools: dict[str, Any], ctx: Any
    ) -> None:
        with pytest.raises(ValueError, match="information_extracted"):
            await tools["encode_vibe"](ctx, reference="b64", information_extracted=2.0)


class TestAccountTools:
    async def test_get_subscription(
        self, tools: dict[str, Any], ctx: Any, fake_client: AsyncMock
    ) -> None:
        fake_client.get_subscription.return_value = {"tier": 1}
        result = await tools["get_subscription"](ctx)
        assert result == {"tier": 1}

    async def test_get_user_data(
        self, tools: dict[str, Any], ctx: Any, fake_client: AsyncMock
    ) -> None:
        fake_client.get_user_data.return_value = {"email": "a@b.com"}
        result = await tools["get_user_data"](ctx)
        assert result == {"email": "a@b.com"}

    async def test_estimate_anlas_cost_returns_dict(
        self, tools: dict[str, Any], ctx: Any
    ) -> None:
        result = await tools["estimate_anlas_cost"](
            ctx, width=832, height=1216, steps=28, opus=True
        )
        assert result["anlas"] == 0
        assert result["opus_free_sample"] is True

    async def test_estimate_anlas_cost_unknown_action_raises(
        self, tools: dict[str, Any], ctx: Any
    ) -> None:
        with pytest.raises(ValueError, match="unknown action"):
            await tools["estimate_anlas_cost"](
                ctx, width=832, height=1216, steps=28, action="bogus"
            )


class TestRegistration:
    def test_register_all_invokes_each_group(
        self, recording_mcp: RecordingMCPServer
    ) -> None:
        _register_all(recording_mcp)
        # 11 tools expected: 3 generate + 3 enhance + 2 tags + 3 account.
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
        assert len(expected) == 11
