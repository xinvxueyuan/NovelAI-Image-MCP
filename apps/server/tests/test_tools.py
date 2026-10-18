"""Tests for the MCP tool wrappers in `novelai_image_mcp.tools`.

Two layers are covered here. Direct calls (`await generate.generate_image(app=...)`)
assert exactly which request reaches `NovelAIClient` and which content blocks
come back. Calls through the `mcp_client` fixture cover everything FastMCP
adds on top: schema validation, dependency injection, annotations and the
conversion of returned helpers into MCP content blocks.
"""

from __future__ import annotations

import asyncio
import base64
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock

from _helpers import PNG_BYTES
import pytest

from novelai_image_mcp import server as server_module
from novelai_image_mcp.features import EXPERIMENTAL_TOOLS
from novelai_image_mcp.nai import (
    Action,
    ControlNetModel,
    DirectorTool,
    Emotion,
    EmotionLevel,
    Model,
    NoiseSchedule,
    NovelAIError,
    Sampler,
)
from novelai_image_mcp.routing import RoutingContext
from novelai_image_mcp.schemas import AnlasEstimate, TagSuggestion
from novelai_image_mcp.tools import account, enhance, generate, tags

if TYPE_CHECKING:
    from novelai_image_mcp.deps import AppContext
    from novelai_image_mcp.nai import NovelAIImage


def _b64(data: bytes = PNG_BYTES) -> str:
    """Encode bytes as a base64 ASCII string (the wire format tools expect)."""
    return base64.b64encode(data).decode("ascii")


def _assert_image_block(result: list[Any]) -> bytes:
    """Pull the raw bytes out of the returned image item.

    Tools return the FastMCP `Image` helper (whose `.data` is the raw PNG
    bytes) because FastMCP converts it to `ImageContent` only when it passes
    through the real server pipeline; direct invocation hands the helper back
    as-is.
    """
    image_block = next(item for item in result if hasattr(item, "data"))
    return image_block.data


def _assert_path_str(result: list[Any]) -> str:
    """Pull the saved-path string out of the returned text block."""
    return next(item for item in result if isinstance(item, str))


def _routing(*, enabled: bool = False, route: str = "alpha") -> RoutingContext:
    """A routing context for direct (in-process) tool calls.

    Direct calls bypass FastMCP's dependency injection, so every `Depends`
    parameter has to be supplied by hand; routing is off unless a test asks for
    it, which is also the production default for a client that sends no routing
    headers.
    """
    if not enabled:
        return RoutingContext.disabled()
    return RoutingContext(enabled=True, route=route, transport="http")


#: The feature set a request that opted into the experimental surface sees.
_EXPERIMENTAL = frozenset({EXPERIMENTAL_TOOLS})


async def _saved_pngs(directory: Path) -> list[Path]:
    """Return the PNGs written directly under `directory`.

    The scan runs in a worker thread: these tests are async, so a synchronous
    `Path.glob` inside one would block the event loop (ASYNC230).
    """
    return await asyncio.to_thread(lambda: sorted(directory.glob("*.png")))


class TestGenerateTools:
    async def test_generate_image_calls_client(
        self,
        fake_app: AppContext,
        fake_client: AsyncMock,
        nai_image: NovelAIImage,
    ) -> None:
        fake_client.generate.return_value = (nai_image,)
        result = await generate.generate_image(
            prompt="a cat, masterpiece",
            negative_prompt="lowres",
            seed=42,
            routing=_routing(),
            route_scoped_output=False,
            app=fake_app,
        )
        fake_client.generate.assert_awaited_once()
        request = fake_client.generate.await_args.args[0]
        assert request.prompt == "a cat, masterpiece"
        assert request.seed == 42
        assert _assert_image_block(result) == nai_image.data
        assert "Saved 1 image(s)" in _assert_path_str(result)

    async def test_generate_image_with_character_prompts(
        self, fake_app: AppContext, fake_client: AsyncMock
    ) -> None:
        await generate.generate_image(
            prompt="a girl and a boy",
            character_prompts=[{"prompt": "girl", "x": 0.3, "y": 0.5}],
            routing=_routing(),
            route_scoped_output=False,
            app=fake_app,
        )
        request = fake_client.generate.await_args.args[0]
        assert len(request.character_prompts) == 1
        assert request.character_prompts[0].x == 0.3

    async def test_generate_image_accepts_enum_values(
        self, fake_app: AppContext, fake_client: AsyncMock
    ) -> None:
        await generate.generate_image(
            prompt="a cat",
            model=Model.V5,
            sampler=Sampler.EULER,
            noise_schedule=NoiseSchedule.EXPONENTIAL,
            uc_preset=2,
            routing=_routing(),
            route_scoped_output=False,
            app=fake_app,
        )
        request = fake_client.generate.await_args.args[0]
        assert request.model is Model.V5
        assert request.sampler.value == "k_euler"
        assert request.noise_schedule.value == "exponential"
        assert request.uc_preset == 2

    async def test_generate_image_v5_rejects_references(
        self, fake_app: AppContext
    ) -> None:
        from fastmcp.exceptions import ToolError

        with pytest.raises(ToolError, match="not supported on V5"):
            await generate.generate_image(
                prompt="a cat",
                model=Model.V5,
                references=["vibe"],
                routing=_routing(),
                route_scoped_output=False,
                app=fake_app,
            )

    async def test_generate_image_v5_straight_alpha_passthrough(
        self, fake_app: AppContext, fake_client: AsyncMock
    ) -> None:
        await generate.generate_image(
            prompt="a cat",
            model=Model.V5,
            straight_alpha=True,
            routing=_routing(),
            route_scoped_output=False,
            app=fake_app,
        )
        request = fake_client.generate.await_args.args[0]
        assert request.straight_alpha is True

    async def test_img2img_passes_image_through(
        self, fake_app: AppContext, fake_client: AsyncMock
    ) -> None:
        await generate.image_to_image(
            prompt="restyle",
            image="base64-image-string",
            strength=0.5,
            routing=_routing(),
            route_scoped_output=False,
            app=fake_app,
        )
        request = fake_client.generate.await_args.args[0]
        assert request.image == "base64-image-string"
        assert request.strength == 0.5

    async def test_inpaint_passes_mask_through(
        self, fake_app: AppContext, fake_client: AsyncMock
    ) -> None:
        await generate.inpaint(
            prompt="redraw",
            image="base64-image",
            mask="base64-mask",
            model=Model.V4_5_INPAINT,
            routing=_routing(),
            route_scoped_output=False,
            app=fake_app,
        )
        request = fake_client.generate.await_args.args[0]
        assert request.mask == "base64-mask"
        assert request.action is Action.INPAINT

    async def test_provider_error_becomes_tool_error(
        self, fake_app: AppContext, fake_client: AsyncMock
    ) -> None:
        from fastmcp.exceptions import ToolError

        fake_client.generate.side_effect = NovelAIError("rate limited")
        with pytest.raises(ToolError, match="rate limited"):
            await generate.generate_image(
                prompt="a cat",
                routing=_routing(),
                route_scoped_output=False,
                app=fake_app,
            )


class TestEnhanceTools:
    async def test_upscale_image(
        self,
        fake_app: AppContext,
        fake_client: AsyncMock,
        nai_image: NovelAIImage,
    ) -> None:
        fake_client.upscale.return_value = nai_image
        result = await enhance.upscale_image(
            image=_b64(),
            factor=4,
            routing=_routing(),
            route_scoped_output=False,
            app=fake_app,
        )
        # The standalone upscaler needs a V5 model; the tool takes it from
        # NOVELAI_UPSCALE_MODEL (default nai-diffusion-5-full).
        fake_client.upscale.assert_awaited_once_with(
            PNG_BYTES, factor=4, model=Model.V5
        )
        assert _assert_image_block(result) == nai_image.data

    async def test_director_emotion_requires_emotion(
        self, fake_app: AppContext
    ) -> None:
        from fastmcp.exceptions import ToolError

        with pytest.raises(ToolError, match="emotion tool requires an emotion"):
            await enhance.director_tool(
                tool=DirectorTool.EMOTION,
                image="b64",
                emotion=None,
                routing=_routing(),
                route_scoped_output=False,
                features=_EXPERIMENTAL,
                app=fake_app,
            )

    async def test_director_emotion_success(
        self,
        fake_app: AppContext,
        fake_client: AsyncMock,
        nai_image: NovelAIImage,
    ) -> None:
        fake_client.director.return_value = nai_image
        await enhance.director_tool(
            tool=DirectorTool.EMOTION,
            image=_b64(),
            emotion=Emotion.HAPPY,
            emotion_level=EmotionLevel.NORMAL,
            routing=_routing(),
            route_scoped_output=False,
            features=_EXPERIMENTAL,
            app=fake_app,
        )
        fake_client.director.assert_awaited_once()
        call = fake_client.director.await_args
        assert call.kwargs["emotion"].value == "happy"

    async def test_annotate_image(
        self,
        fake_app: AppContext,
        fake_client: AsyncMock,
        nai_image: NovelAIImage,
    ) -> None:
        fake_client.annotate.return_value = nai_image
        await enhance.annotate_image(
            image=_b64(),
            model=ControlNetModel.PALETTE_SWAP,
            routing=_routing(),
            route_scoped_output=False,
            app=fake_app,
        )
        fake_client.annotate.assert_awaited_once()
        call = fake_client.annotate.await_args
        assert call.args[1].value == "hed"


class TestStringCoercion:
    """Direct Python callers may pass plain strings: the tools coerce them.

    MCP callers are validated against the generated enum schema before the
    function runs; in-process callers (scripts, notebooks, tests) bypass that
    layer, so the tool bodies still resolve the value through the enum.
    """

    async def test_director_tool_accepts_strings(
        self, fake_app: AppContext, fake_client: AsyncMock
    ) -> None:
        await enhance.director_tool(
            tool="emotion",  # type: ignore[arg-type]
            image=_b64(),
            emotion="happy",  # type: ignore[arg-type]
            emotion_level=2,  # type: ignore[arg-type]
            routing=_routing(),
            route_scoped_output=False,
            features=_EXPERIMENTAL,
            app=fake_app,
        )
        call = fake_client.director.await_args
        assert call.args[0] is DirectorTool.EMOTION
        assert call.kwargs["emotion"] is Emotion.HAPPY
        assert call.kwargs["emotion_level"] is EmotionLevel.WEAK

    async def test_annotate_image_accepts_strings(
        self, fake_app: AppContext, fake_client: AsyncMock
    ) -> None:
        await enhance.annotate_image(
            image=_b64(),
            model="mlsd",  # type: ignore[arg-type]
            routing=_routing(),
            route_scoped_output=False,
            app=fake_app,
        )
        assert (
            fake_client.annotate.await_args.args[1] is ControlNetModel.BUILDING_CONTROL
        )


class TestTagsTools:
    async def test_suggest_tags_returns_models(
        self, fake_app: AppContext, fake_client: AsyncMock
    ) -> None:
        # Live-verified wire shape (2026-10-10).
        fake_client.suggest_tags.return_value = (
            {"tag": "fox girl", "count": 10000, "confidence": 0.745},
        )
        result = await tags.suggest_tags(prompt="ca", client=fake_client)
        fake_client.suggest_tags.assert_awaited_once()
        assert result == [TagSuggestion(tag="fox girl", count=10000, confidence=0.745)]

    async def test_suggest_tags_preserves_unknown_fields(
        self, fake_app: AppContext, fake_client: AsyncMock
    ) -> None:
        fake_client.suggest_tags.return_value = (
            {"tag": "cat", "count": 3, "confidence": 0.5, "category": "animal"},
        )
        result = await tags.suggest_tags(prompt="ca", client=fake_client)
        assert result[0].model_extra == {"category": "animal"}

    async def test_encode_vibe(
        self, fake_app: AppContext, fake_client: AsyncMock
    ) -> None:
        fake_client.encode_vibe.return_value = "vibe-token"
        result = await tags.encode_vibe(
            reference="b64", information_extracted=0.5, client=fake_client
        )
        assert result == "vibe-token"
        call = fake_client.encode_vibe.await_args
        assert call.kwargs["information_extracted"] == 0.5

    async def test_encode_vibe_v5_rejected(
        self, fake_app: AppContext, fake_client: AsyncMock
    ) -> None:
        from fastmcp.exceptions import ToolError

        with pytest.raises(ToolError, match="not supported on V5"):
            await tags.encode_vibe(reference="b64", model=Model.V5, client=fake_client)


class TestAccountTools:
    async def test_get_subscription(
        self, fake_app: AppContext, fake_client: AsyncMock
    ) -> None:
        fake_client.get_subscription.return_value = {"tier": 1}
        result = await account.get_subscription(client=fake_client)
        assert result == {"tier": 1}

    async def test_get_user_data(
        self, fake_app: AppContext, fake_client: AsyncMock
    ) -> None:
        fake_client.get_user_data.return_value = {"email": "a@b.com"}
        result = await account.get_user_data(client=fake_client)
        assert result == {"email": "a@b.com"}

    async def test_estimate_anlas_cost_returns_model(
        self, fake_app: AppContext
    ) -> None:
        _ = fake_app  # estimation is pure and offline
        result = await account.estimate_anlas_cost(
            width=832, height=1216, steps=28, opus=True
        )
        assert isinstance(result, AnlasEstimate)
        assert result.anlas == 0
        assert result.opus_free_sample is True


class TestRegistration:
    async def test_every_tool_is_registered(self) -> None:
        """The shared server exposes exactly the 11 documented tools."""
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
        registered = {tool.name for tool in await server_module.mcp.list_tools()}
        assert registered == expected


class TestToolMetadata:
    def test_annotations_and_tags(self) -> None:
        from novelai_image_mcp.tools._meta import (
            IMAGE_WRITE_ANNOTATIONS,
            OFFLINE_ANNOTATIONS,
            READ_ONLY_ANNOTATIONS,
        )

        # Image tools spend Anlas and write a new PNG; the read-only tools only
        # read; the estimator is offline and idempotent.
        assert IMAGE_WRITE_ANNOTATIONS.read_only_hint is False
        assert IMAGE_WRITE_ANNOTATIONS.destructive_hint is False
        assert READ_ONLY_ANNOTATIONS.read_only_hint is True
        assert OFFLINE_ANNOTATIONS.open_world_hint is False
        assert OFFLINE_ANNOTATIONS.idempotent_hint is True

    async def test_titles_and_annotations_are_published(self) -> None:
        tools_by_name = {
            tool.name: tool for tool in await server_module.mcp.list_tools()
        }
        for tool in tools_by_name.values():
            assert tool.title, f"{tool.name} has no title"
            assert "novelai" in tool.tags
            assert tool.annotations is not None
        subscription_annotations = tools_by_name["get_subscription"].annotations
        assert subscription_annotations is not None
        assert subscription_annotations.read_only_hint is True
        estimate_annotations = tools_by_name["estimate_anlas_cost"].annotations
        assert estimate_annotations is not None
        assert estimate_annotations.open_world_hint is False
        generate_annotations = tools_by_name["generate_image"].annotations
        assert generate_annotations is not None
        assert generate_annotations.read_only_hint is False


class TestSchemaValidation:
    """Invalid arguments are rejected by the generated schema, not at runtime."""

    async def test_enum_parameter_rejects_unknown_value(self, mcp_client: Any) -> None:
        from fastmcp.exceptions import ToolError

        with pytest.raises(ToolError):
            await mcp_client.call_tool(
                "annotate_image", {"image": "b64", "model": "bogus"}
            )

    async def test_numeric_bound_rejects_out_of_range(self, mcp_client: Any) -> None:
        from fastmcp.exceptions import ToolError

        with pytest.raises(ToolError):
            await mcp_client.call_tool(
                "generate_image", {"prompt": "a cat", "n_samples": 99}
            )

    async def test_dependency_parameters_are_not_exposed(self, mcp_client: Any) -> None:
        listed = await mcp_client.list_tools()
        for tool in listed:
            properties = set((tool.input_schema or {}).get("properties", {}))
            assert "app" not in properties
            assert "client" not in properties
            assert "ctx" not in properties


class TestSerializationRegression:
    """Verify image returns serialize correctly through FastMCP's real path.

    These tests drive the production server instance through
    `fastmcp.Client`, which runs the full execution pipeline and converts the
    returned `Image` helper into an `ImageContent` block. They assert the
    blocks are MIME-typed MCP content and that each JSON-serializes (the
    historical `PydanticSerializationError` lived in the SDK's
    structured-content `model_dump(mode="json")` path).
    """

    async def test_generate_image_serializes_through_real_path(
        self,
        mcp_client: Any,
        fake_client: AsyncMock,
        nai_image: NovelAIImage,
    ) -> None:
        """`generate_image` yields an `ImageContent` block plus its path."""
        from mcp_types import ImageContent, TextContent

        fake_client.generate.return_value = (nai_image,)
        result = await mcp_client.call_tool(
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
        for block in result.content:
            assert block.model_dump(mode="json") is not None
        image_block = next(b for b in result.content if isinstance(b, ImageContent))
        assert base64.b64decode(image_block.data) == nai_image.data

    async def test_estimate_anlas_cost_returns_structured_output(
        self, mcp_client: Any
    ) -> None:
        """A pydantic return yields both content and structured content."""
        result = await mcp_client.call_tool(
            "estimate_anlas_cost",
            {"width": 832, "height": 1216, "steps": 28, "opus": True},
        )
        assert result.structured_content == {"anlas": 0, "opus_free_sample": True}


class TestToolOutputContract:
    """Every advertised output schema must be backed by structured content.

    A tool can declare ``outputSchema`` and still return content blocks only:
    fastmcp silently drops ``structured_content`` when the result is not
    JSON-serializable, which is what the ``Image`` helper did under fastmcp
    4.0.0b3 (the version behind release 0.4.0). MCP SDK v2 clients validate
    the result against the declared schema -- ``validate_tool_result`` in the
    Python SDK, ``validateToolResult`` in the TypeScript one -- and raise

        Tool <name> has an output schema but did not return structured content

    before the caller sees anything, so all three image tools were unusable on
    those hosts while this suite stayed green (issue #27).
    """

    #: Image-returning tools: the ``Image`` helper cannot be JSON-serialized.
    IMAGE_TOOLS = (
        "generate_image",
        "image_to_image",
        "inpaint",
        "upscale_image",
        "director_tool",
        "annotate_image",
    )

    @staticmethod
    def _calls() -> dict[str, dict[str, Any]]:
        """Smallest valid argument set for every registered tool."""
        image = _b64()
        return {
            "generate_image": {
                "prompt": "1girl",
                "width": 64,
                "height": 64,
                "steps": 1,
            },
            "image_to_image": {"prompt": "restyle", "image": image},
            "inpaint": {
                "prompt": "redraw",
                "image": image,
                "mask": image,
                "model": "nai-diffusion-5-full-inpainting",
            },
            "upscale_image": {"image": image, "factor": 4},
            "director_tool": {"tool": "lineart", "image": image},
            "annotate_image": {"image": image, "model": "hed"},
            "suggest_tags": {"prompt": "1girl"},
            "encode_vibe": {"reference": image},
            "get_subscription": {},
            "get_user_data": {},
            "estimate_anlas_cost": {"width": 832, "height": 1216, "steps": 28},
        }

    async def test_declared_schema_is_backed_by_structured_content(
        self, mcp_client: Any
    ) -> None:
        """An advertised ``outputSchema`` implies ``structured_content``."""
        calls = self._calls()
        declared = {
            tool.name: tool.output_schema for tool in await mcp_client.list_tools()
        }
        assert set(declared) == set(calls), (
            "keep TestToolOutputContract._calls in step with the registry: every "
            "tool must be exercised against its declared output schema"
        )

        for name, arguments in calls.items():
            result = await mcp_client.call_tool(name, arguments)
            if declared[name] is not None:
                assert result.structured_content is not None, (
                    f"{name} advertises an outputSchema but returned no "
                    "structured_content; strict MCP clients reject such a result"
                )

    async def test_image_tools_return_image_and_text_blocks(
        self, mcp_client: Any
    ) -> None:
        """Image tools keep returning the image plus its saved path."""
        from mcp_types import ImageContent, TextContent

        calls = self._calls()
        for name in self.IMAGE_TOOLS:
            result = await mcp_client.call_tool(name, calls[name])
            assert any(isinstance(b, ImageContent) for b in result.content), name
            assert any(isinstance(b, TextContent) for b in result.content), name


class TestRouteScopedOutput:
    """Route-scoped output is invisible until model routing is active."""

    async def test_route_scoped_output_writes_under_the_route(
        self,
        fake_app: AppContext,
        fake_client: AsyncMock,
        nai_image: NovelAIImage,
    ) -> None:
        fake_client.generate.return_value = (nai_image,)
        result = await generate.generate_image(
            prompt="a cat",
            routing=_routing(enabled=True, route="alpha"),
            route_scoped_output=True,
            app=fake_app,
        )
        assert "[route=alpha]" in _assert_path_str(result)
        output_dir = Path(fake_app.settings.output_dir)
        written = list((output_dir / "alpha").glob("*.png"))
        assert len(written) == 1
        assert written[0].read_bytes() == nai_image.data
        # Nothing leaks into the flat output directory.
        assert await _saved_pngs(output_dir) == []

    async def test_routing_disabled_keeps_the_flat_output_dir(
        self,
        fake_app: AppContext,
        fake_client: AsyncMock,
        nai_image: NovelAIImage,
    ) -> None:
        fake_client.generate.return_value = (nai_image,)
        result = await generate.generate_image(
            prompt="a cat",
            routing=_routing(),
            route_scoped_output=True,
            app=fake_app,
        )
        output_dir = Path(fake_app.settings.output_dir)
        assert len(await _saved_pngs(output_dir)) == 1
        assert "[route=" not in _assert_path_str(result)
        assert not (output_dir / "unknown").exists()

    async def test_route_scoping_off_keeps_the_flat_output_dir(
        self,
        fake_app: AppContext,
        fake_client: AsyncMock,
        nai_image: NovelAIImage,
    ) -> None:
        fake_client.generate.return_value = (nai_image,)
        result = await generate.generate_image(
            prompt="a cat",
            routing=_routing(enabled=True, route="alpha"),
            route_scoped_output=False,
            app=fake_app,
        )
        output_dir = Path(fake_app.settings.output_dir)
        assert len(await _saved_pngs(output_dir)) == 1
        assert not (output_dir / "alpha").exists()
        # The route is still reported: only the path is unscoped.
        assert "[route=alpha]" in _assert_path_str(result)

    async def test_route_name_is_sanitised_at_the_write_site(
        self,
        fake_app: AppContext,
        fake_client: AsyncMock,
        nai_image: NovelAIImage,
    ) -> None:
        fake_client.generate.return_value = (nai_image,)
        await generate.generate_image(
            prompt="a cat",
            routing=_routing(enabled=True, route="../../escape"),
            route_scoped_output=True,
            app=fake_app,
        )
        output_dir = Path(fake_app.settings.output_dir)
        assert len(await _saved_pngs(output_dir / "unknown")) == 1
        assert not (output_dir.parent / "escape").exists()

    async def test_upscale_is_route_scoped_too(
        self,
        fake_app: AppContext,
        fake_client: AsyncMock,
        nai_image: NovelAIImage,
    ) -> None:
        fake_client.upscale.return_value = nai_image
        result = await enhance.upscale_image(
            image=_b64(),
            factor=4,
            routing=_routing(enabled=True, route="beta"),
            route_scoped_output=True,
            app=fake_app,
        )
        assert "[route=beta]" in _assert_path_str(result)
        scoped = Path(fake_app.settings.output_dir) / "beta"
        assert len(await _saved_pngs(scoped)) == 1


class TestExperimentalParameterGate:
    """`emotion` / `emotion_level` need the insiders opt-in (v1 body check).

    A tool schema is published once, when the server starts, so the parameters
    cannot disappear per request: they stay visible and the gate lives in the
    tool body, failing with a `ToolError` -- the message a client actually sees
    under `mask_error_details=True`.
    """

    async def test_emotion_is_rejected_without_the_opt_in(
        self, fake_app: AppContext
    ) -> None:
        from fastmcp.exceptions import ToolError

        with pytest.raises(ToolError, match="experimental"):
            await enhance.director_tool(
                tool=DirectorTool.EMOTION,
                image=_b64(),
                emotion=Emotion.HAPPY,
                routing=_routing(),
                route_scoped_output=False,
                features=frozenset(),
                app=fake_app,
            )

    async def test_emotion_level_alone_is_rejected_without_the_opt_in(
        self, fake_app: AppContext
    ) -> None:
        from fastmcp.exceptions import ToolError

        with pytest.raises(ToolError, match="experimental"):
            await enhance.director_tool(
                tool=DirectorTool.LINE_ART,
                image=_b64(),
                emotion_level=EmotionLevel.WEAK,
                routing=_routing(),
                route_scoped_output=False,
                features=frozenset(),
                app=fake_app,
            )

    async def test_emotion_is_served_when_the_opt_in_is_active(
        self,
        fake_app: AppContext,
        fake_client: AsyncMock,
        nai_image: NovelAIImage,
    ) -> None:
        fake_client.director.return_value = nai_image
        await enhance.director_tool(
            tool=DirectorTool.EMOTION,
            image=_b64(),
            emotion=Emotion.HAPPY,
            emotion_level=EmotionLevel.WEAK,
            routing=_routing(),
            route_scoped_output=False,
            features=_EXPERIMENTAL,
            app=fake_app,
        )
        call = fake_client.director.await_args
        assert call.kwargs["emotion"] is Emotion.HAPPY
        assert call.kwargs["emotion_level"] is EmotionLevel.WEAK

    async def test_emotion_is_rejected_over_the_real_pipeline(
        self, mcp_client: Any
    ) -> None:
        from fastmcp.exceptions import ToolError

        # The in-memory transport sends no insiders header, so experimental-tools
        # is inactive: this proves the gate is wired through dependency injection
        # and not only reachable from a direct in-process call.
        with pytest.raises(ToolError, match="experimental"):
            await mcp_client.call_tool(
                "director_tool",
                {"tool": "emotion", "image": _b64(), "emotion": "happy"},
            )

    async def test_default_parameters_are_never_gated(
        self,
        fake_app: AppContext,
        fake_client: AsyncMock,
        nai_image: NovelAIImage,
    ) -> None:
        fake_client.director.return_value = nai_image
        await enhance.director_tool(
            tool=DirectorTool.LINE_ART,
            image=_b64(),
            routing=_routing(),
            route_scoped_output=False,
            features=frozenset(),
            app=fake_app,
        )
        fake_client.director.assert_awaited_once()
