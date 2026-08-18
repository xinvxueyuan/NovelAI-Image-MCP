"""MCP tools: upscale, Director tools, and ControlNet annotation."""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING, Any

from .._mcp import Context, Image
from ..nai import (
    ControlNetModel,
    DirectorTool,
    Emotion,
    EmotionLevel,
    NovelAIImage,
)
from ..output import save_image
from ._ctx import app_context as _app

if TYPE_CHECKING:
    from .._mcp import FastMCP


def _save_and_return(
    image: NovelAIImage,
    *,
    name: str,
    output_dir: str,
) -> list[Any]:
    """Persist a single image and return ImageContent block + saved path.

    fastmcp auto-converts its ``Image`` helper into an ``ImageContent`` block
    when returned from a tool, so returning ``Image(...)`` needs no manual
    ``to_image_content()`` step.
    """
    path = save_image(image.data, name=name, output_dir=output_dir)
    return [
        Image(data=image.data, format="png"),
        f"Saved image: {path}",
    ]


def register(mcp: FastMCP) -> None:
    """Register the image-enhancement tools."""

    @mcp.tool()
    async def upscale_image(
        ctx: Context,
        image: str,
        factor: int = 4,
    ) -> list[Any]:
        """Upscale an image by 2× or 4× using NovelAI's dedicated upscaler.

        ``image`` is a base64-encoded PNG/JPEG. ``factor`` must be 2 or 4. The
        upscaler is model-independent and consumes Anlas based on the source
        resolution and factor.
        """
        app = _app(ctx)
        settings = app.settings
        client = app.client
        result = await client.upscale(base64.b64decode(image), factor=factor)
        return _save_and_return(result, name="upscale", output_dir=settings.output_dir)

    @mcp.tool()
    async def director_tool(
        ctx: Context,
        tool: str,
        image: str,
        prompt: str = "",
        defry: int = 0,
        emotion: str | None = None,
        emotion_level: int = 0,
    ) -> list[Any]:
        """Apply a NovelAI Director tool to an image.

        ``tool`` is one of: ``lineart``, ``sketch``, ``bg-removal``,
        ``declutter``, ``colorize``, ``emotion``. ``image`` is a base64-encoded
        PNG/JPEG. The ``emotion`` tool additionally requires an ``emotion``
        name (e.g. ``happy``, ``sad``) and accepts an ``emotion_level`` (0–5,
        where 0 is normal intensity and 5 is weakest). ``prompt`` guides
        ``colorize`` and ``emotion``; ``defry`` (0–10) sharpens line art.
        """
        app = _app(ctx)
        settings = app.settings
        client = app.client
        try:
            director = DirectorTool(tool)
        except ValueError as exc:
            raise ValueError(
                f"unknown director tool '{tool}'; expected one of: "
                f"{', '.join(t.value for t in DirectorTool)}"
            ) from exc
        emotion_enum: Emotion | None = None
        if director is DirectorTool.EMOTION:
            if not emotion:
                raise ValueError("emotion tool requires an emotion name")
            try:
                emotion_enum = Emotion(emotion)
            except ValueError as exc:
                raise ValueError(
                    f"unknown emotion '{emotion}'; expected one of: "
                    f"{', '.join(e.value for e in Emotion)}"
                ) from exc
        try:
            level = EmotionLevel(emotion_level)
        except ValueError as exc:
            raise ValueError(
                f"emotion_level must be between {EmotionLevel.NORMAL} and "
                f"{max(EmotionLevel)}"
            ) from exc
        result = await client.director(
            director,
            base64.b64decode(image),
            prompt=prompt,
            defry=defry,
            emotion=emotion_enum,
            emotion_level=level,
        )
        return _save_and_return(
            result, name=f"director-{director.value}", output_dir=settings.output_dir
        )

    @mcp.tool()
    async def annotate_image(
        ctx: Context,
        image: str,
        model: str,
    ) -> list[Any]:
        """Annotate an image with a ControlNet preprocessor.

        ``image`` is a base64-encoded PNG/JPEG. ``model`` is one of: ``hed``
        (palette swap), ``midas`` (form lock / depth), ``fake_scribble``
        (scribbler), ``mlsd`` (building control), ``uniformer`` (landscaper).
        The returned image is the annotation (e.g. a line-art map) suitable for
        use as a ControlNet condition in a subsequent generation.
        """
        app = _app(ctx)
        settings = app.settings
        client = app.client
        try:
            controlnet = ControlNetModel(model)
        except ValueError as exc:
            raise ValueError(
                f"unknown controlnet model '{model}'; expected one of: "
                f"{', '.join(m.value for m in ControlNetModel)}"
            ) from exc
        result = await client.annotate(base64.b64decode(image), controlnet)
        return _save_and_return(
            result,
            name=f"annotate-{controlnet.value}",
            output_dir=settings.output_dir,
        )


__all__ = ["register"]
