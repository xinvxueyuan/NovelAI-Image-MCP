"""MCP tools: upscale, Director tools, and ControlNet annotation."""

from __future__ import annotations

import base64
from typing import Annotated, Any, Literal

from fastmcp.dependencies import Depends
from fastmcp.utilities.types import Image
from pydantic import Field

from ..deps import AppContext, get_app_context
from ..nai import (
    ControlNetModel,
    DirectorTool,
    Emotion,
    EmotionLevel,
    NovelAIImage,
)
from ..output import save_image
from ..server import mcp
from ._errors import translate_errors
from ._meta import IMAGE_WRITE_ANNOTATIONS

#: NovelAI's line-art sharpening parameter is clamped to this range.
_MAX_DEFRY = 10


def _save_and_return(
    image: NovelAIImage,
    *,
    name: str,
    output_dir: str,
) -> list[Any]:
    """Persist a single image and return an ImageContent block + saved path.

    FastMCP auto-converts its `Image` helper into an `ImageContent` block
    when returned from a tool, so returning `Image(...)` needs no manual
    conversion step.
    """
    path = save_image(image.data, name=name, output_dir=output_dir)
    return [
        Image(data=image.data, format="png"),
        f"Saved image: {path}",
    ]


@mcp.tool(
    title="Upscale an image",
    tags={"novelai", "enhancement"},
    annotations=IMAGE_WRITE_ANNOTATIONS,
)
@translate_errors
async def upscale_image(
    image: str,
    factor: Literal[2, 4] = 4,
    app: AppContext = Depends(get_app_context),
) -> list[Any]:
    """Upscale an image by 2× or 4× using NovelAI's dedicated upscaler.

    ``image`` is a base64-encoded PNG/JPEG. ``factor`` must be 2 or 4.
    The upscaler is model-independent and consumes Anlas based on the source
    resolution and factor.
    """
    settings = app.settings
    client = app.client
    result = await client.upscale(base64.b64decode(image), factor=factor)
    return _save_and_return(result, name="upscale", output_dir=settings.output_dir)


@mcp.tool(
    title="Apply a Director tool",
    tags={"novelai", "enhancement"},
    annotations=IMAGE_WRITE_ANNOTATIONS,
)
@translate_errors
async def director_tool(
    tool: DirectorTool,
    image: str,
    prompt: str = "",
    defry: Annotated[int, Field(ge=0, le=_MAX_DEFRY)] = 0,
    emotion: Emotion | None = None,
    emotion_level: EmotionLevel = EmotionLevel.NORMAL,
    app: AppContext = Depends(get_app_context),
) -> list[Any]:
    """Apply a NovelAI Director tool to an image.

    ``tool`` is one of: ``lineart``, ``sketch``, ``bg-removal``,
    ``declutter``, ``colorize``, ``emotion``. ``image`` is a
    base64-encoded PNG/JPEG. The ``emotion`` tool additionally requires an
    ``emotion`` name (e.g. ``happy``, ``sad``) and accepts an
    ``emotion_level`` (0-5, where 0 is normal intensity and 5 is weakest).
    ``prompt`` guides ``colorize`` and ``emotion``; ``defry``
    (0-10) sharpens line art.
    """
    settings = app.settings
    client = app.client
    director = DirectorTool(tool)
    emotion_enum = Emotion(emotion) if emotion is not None else None
    if director is DirectorTool.EMOTION and emotion_enum is None:
        raise ValueError(
            "emotion tool requires an emotion name; expected one of: "
            + ", ".join(item.value for item in Emotion)
        )
    result = await client.director(
        director,
        base64.b64decode(image),
        prompt=prompt,
        defry=defry,
        emotion=emotion_enum,
        emotion_level=EmotionLevel(emotion_level),
    )
    return _save_and_return(
        result, name=f"director-{director.value}", output_dir=settings.output_dir
    )


@mcp.tool(
    title="Annotate an image (ControlNet)",
    tags={"novelai", "enhancement"},
    annotations=IMAGE_WRITE_ANNOTATIONS,
)
@translate_errors
async def annotate_image(
    image: str,
    model: ControlNetModel,
    app: AppContext = Depends(get_app_context),
) -> list[Any]:
    """Annotate an image with a ControlNet preprocessor.

    ``image`` is a base64-encoded PNG/JPEG. ``model`` is one of:
    ``hed`` (palette swap), ``midas`` (form lock / depth),
    ``fake_scribble`` (scribbler), ``mlsd`` (building control),
    ``uniformer`` (landscaper). The returned image is the annotation (e.g. a
    line-art map) suitable for use as a ControlNet condition in a subsequent
    generation.
    """
    settings = app.settings
    client = app.client
    controlnet = ControlNetModel(model)
    result = await client.annotate(base64.b64decode(image), controlnet)
    return _save_and_return(
        result,
        name=f"annotate-{controlnet.value}",
        output_dir=settings.output_dir,
    )


__all__ = ["annotate_image", "director_tool", "upscale_image"]
