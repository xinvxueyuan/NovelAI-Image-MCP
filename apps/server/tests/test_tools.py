"""Tests for the MCP tool wrappers in ``novelai_image_mcp.tools``."""

from __future__ import annotations

import base64
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import AsyncMock

from _helpers import PNG_BYTES, RecordingMCPServer
import pytest

from novelai_image_mcp.tools import account, enhance, generate, tags

if TYPE_CHECKING:
    from novelai_image_mcp._mcp import FastMCP
    from novelai_image_mcp.nai import NovelAIImage


def _b64(data: bytes = PNG_BYTES) -> str:
    """Encode bytes as a base64 ASCII string (the wire format tools expect)."""
    return base64.b64encode(data).decode("ascii")


def _register_all(mcp: RecordingMCPServer) -> None:
    # ``RecordingMCPServer`` is a structural test double that exposes the same
    # ``tool()`` decorator contract as fastmcp's ``FastMCP``; cast to satisfy
    # the production-typed ``register(mcp: FastMCP)`` signatures.
    server = cast("FastMCP", mcp)
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
    """Pull the raw bytes out of the returned image item.

    Tools returned the fastmcp ``Image`` helper (whose ``.data`` is the raw PNG
    bytes) because fastmcp converts it to ``ImageContent`` only when it passes
    through the real server pipeline; direct (recording-stub) invocation hands
    back the helper as-is. The helper decodes nothing — ``.data`` is already the
    original ``NovelAIImage.data`` bytes.
    """
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


class TestSerializationRegression:
    """Verify image returns serialize correctly through fastmcp's real path.

    ``RecordingMCPServer`` bypasses fastmcp's result conversion, so these tests
    close that gap by invoking the production ``server.mcp`` through
    ``call_tool`` — fastmcp's full execution pipeline, which converts the
    returned ``Image`` helper into an ``ImageContent`` block. They assert the
    resulting content blocks are the MIME-typed MCP content blocks and that
    each JSON-serializes (the historical ``PydanticSerializationError`` lived
    in the SDK's structured-content ``model_dump(mode="json")`` path).
    """

    @staticmethod
    def _seed_lifespan(client: Any, settings: Any) -> None:
        """Give the shared server a lifespan value so tools see AppContext.

        fastmcp's ``Context.lifespan_context`` reads the server's
        ``_lifespan_result`` (the value the lifespan yielded). Seeding it here
        lets ``call_tool`` run the tool body without a live session.
        """
        from novelai_image_mcp.server import mcp

        mcp._lifespan_result = SimpleNamespace(client=client, settings=settings)

    async def test_generate_image_serializes_through_real_path(
        self,
        settings: Any,
        fake_client: AsyncMock,
        nai_image: NovelAIImage,
        tmp_path: Path,
    ) -> None:
        """``generate_image`` yields a ``ToolResult`` with ``ImageContent``."""
        from mcp_types import ImageContent, TextContent

        from novelai_image_mcp.server import mcp

        fake_client.generate.return_value = (nai_image,)
        settings.output_dir = str(tmp_path)
        self._seed_lifespan(fake_client, settings)

        result = await mcp.call_tool(
            "generate_image",
            {
                "prompt": "test",
                "seed": 42,
                "width": 512,
                "height": 512,
                "steps": 1,
                "n_samples": 1,
                "quality": False,
            },
        )

        assert any(isinstance(b, ImageContent) for b in result.content)
        assert any(isinstance(b, TextContent) for b in result.content)
        # The historical bug was here: content must JSON-serialize.
        for block in result.content:
            assert block.model_dump(mode="json") is not None
        image_block = next(b for b in result.content if isinstance(b, ImageContent))
        assert base64.b64decode(image_block.data) == nai_image.data

    async def test_upscale_image_serializes_through_real_path(
        self,
        settings: Any,
        fake_client: AsyncMock,
        nai_image: NovelAIImage,
        tmp_path: Path,
    ) -> None:
        """``upscale_image`` yields a ``ToolResult`` with ``ImageContent``."""
        from mcp_types import ImageContent

        from novelai_image_mcp.server import mcp

        fake_client.upscale.return_value = nai_image
        settings.output_dir = str(tmp_path)
        self._seed_lifespan(fake_client, settings)

        result = await mcp.call_tool("upscale_image", {"image": _b64(), "factor": 2})

        assert any(isinstance(b, ImageContent) for b in result.content)
        for block in result.content:
            assert block.model_dump(mode="json") is not None
