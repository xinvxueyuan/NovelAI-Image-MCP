"""MCP tools: text-to-image, image-to-image, and inpainting."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastmcp.dependencies import Depends
from fastmcp.utilities.types import Image
from pydantic import Field

from ..deps import AppContext, get_app_context
from ..nai import (
    Action,
    CharacterPrompt,
    GenerationRequest,
    Model,
    NoiseSchedule,
    Sampler,
    is_v5_model,
)
from ..output import save_image
from ..server import mcp
from ._errors import translate_errors
from ._meta import IMAGE_WRITE_ANNOTATIONS

#: NovelAI caps a single generation request at 8 samples.
_MAX_SAMPLES = 8


def _character(cp: dict[str, Any]) -> CharacterPrompt:
    """Build a CharacterPrompt from a permissive dict (accepts NAI wire keys)."""
    return CharacterPrompt(
        prompt=str(cp.get("prompt", "")),
        negative_prompt=str(cp.get("negative_prompt") or cp.get("uc") or ""),
        x=float(cp.get("x", 0.5)),
        y=float(cp.get("y", 0.5)),
        enabled=bool(cp.get("enabled", True)),
    )


def _save_and_return(
    images: tuple[Any, ...],
    *,
    name: str,
    output_dir: str,
) -> list[Any]:
    """Persist every image, return the first as an Image block plus all paths.

    FastMCP converts the `Image` helper (and `str`) into the corresponding
    MCP content blocks when they are returned from a tool in a list, so no
    manual `to_image_content()` step is needed.
    """
    paths = [save_image(img.data, name=name, output_dir=output_dir) for img in images]
    return [
        Image(data=images[0].data, format="png"),
        f"Saved {len(images)} image(s): {[str(p) for p in paths]}",
    ]


@mcp.tool(
    title="Generate image (text-to-image)",
    tags={"novelai", "generation"},
    annotations=IMAGE_WRITE_ANNOTATIONS,
)
@translate_errors
async def generate_image(
    prompt: str,
    negative_prompt: str = "",
    model: Model | None = None,
    width: int | None = None,
    height: int | None = None,
    steps: int | None = None,
    scale: float | None = None,
    sampler: Sampler | None = None,
    seed: int = 0,
    n_samples: Annotated[int, Field(ge=1, le=_MAX_SAMPLES)] = 1,
    quality: bool = True,
    uc_preset: Literal[0, 1, 2, 3] = 0,
    cfg_rescale: float = 0.0,
    smea: bool | None = None,
    smea_dynamic: bool | None = None,
    auto_smea: bool = False,
    straight_alpha: bool = False,
    prefer_brownian: bool = True,
    noise_schedule: NoiseSchedule = NoiseSchedule.KARRAS,
    character_prompts: list[dict[str, Any]] | None = None,
    references: list[str] | None = None,
    app: AppContext = Depends(get_app_context),
) -> list[Any]:
    """Generate one or more images from a text prompt (text-to-image).

    Supports NovelAI V3 / V4 / V4.5 / V5 models. Pass ``references`` as a
    list of base64-encoded PNG/JPEG strings to apply vibe transfer (V4/V4.5
    only - V5 does not support vibe transfer yet and rejects it). V5 models
    additionally accept English/Japanese natural-language prompts and the
    ``straight_alpha`` flag for true transparency (pair it with prompt
    tags such as ``transparent background`` or ``has alpha``).
    ``character_prompts`` enables multi-character composition with
    per-character prompts and center coordinates (x, y in 0.1-0.9).
    Dimensions are rounded up to the nearest multiple of 64.
    """
    settings = app.settings
    client = app.client
    model_enum = Model(model or settings.default_model)
    sampler_value = (
        Sampler(sampler) if sampler is not None else settings.default_sampler
    )
    if is_v5_model(model_enum) and references:
        raise ValueError("vibe transfer is not supported on V5 models yet")
    request = GenerationRequest(
        prompt=prompt,
        action=Action.GENERATE,
        negative_prompt=negative_prompt,
        model=model_enum,
        width=width or settings.default_width,
        height=height or settings.default_height,
        steps=steps or settings.default_steps,
        scale=scale or settings.default_scale,
        sampler=sampler_value,
        seed=seed,
        n_samples=n_samples,
        quality=quality,
        uc_preset=uc_preset,
        cfg_rescale=cfg_rescale,
        smea=smea,
        smea_dynamic=smea_dynamic,
        auto_smea=auto_smea,
        straight_alpha=straight_alpha,
        prefer_brownian=prefer_brownian,
        noise_schedule=NoiseSchedule(noise_schedule),
        character_prompts=tuple(_character(cp) for cp in (character_prompts or ())),
        references=tuple(references or ()),
    )
    images = await client.generate(request)
    return _save_and_return(images, name="generate", output_dir=settings.output_dir)


@mcp.tool(
    title="Restyle an image (image-to-image)",
    tags={"novelai", "generation"},
    annotations=IMAGE_WRITE_ANNOTATIONS,
)
@translate_errors
async def image_to_image(
    prompt: str,
    image: str,
    negative_prompt: str = "",
    model: Model | None = None,
    strength: Annotated[float, Field(ge=0.01, le=0.99)] = 0.3,
    noise: Annotated[float, Field(ge=0.0, le=0.99)] = 0.0,
    width: int | None = None,
    height: int | None = None,
    steps: int | None = None,
    scale: float | None = None,
    sampler: Sampler | None = None,
    seed: int = 0,
    n_samples: Annotated[int, Field(ge=1, le=_MAX_SAMPLES)] = 1,
    quality: bool = True,
    uc_preset: Literal[0, 1, 2, 3] = 0,
    noise_schedule: NoiseSchedule = NoiseSchedule.KARRAS,
    cfg_rescale: float = 0.0,
    extra_noise_seed: int | None = None,
    app: AppContext = Depends(get_app_context),
) -> list[Any]:
    """Generate a new image conditioned on an input image (image-to-image).

    ``image`` is a base64-encoded PNG/JPEG. ``strength`` (0.01-0.99)
    controls how far the result diverges from the input; ``noise`` (0-0.99)
    adds extra variation. The model must match the input image domain.
    """
    settings = app.settings
    client = app.client
    request = GenerationRequest(
        prompt=prompt,
        action=Action.IMG2IMG,
        negative_prompt=negative_prompt,
        model=Model(model or settings.default_model),
        width=width or settings.default_width,
        height=height or settings.default_height,
        steps=steps or settings.default_steps,
        scale=scale or settings.default_scale,
        sampler=Sampler(sampler) if sampler is not None else settings.default_sampler,
        seed=seed,
        n_samples=n_samples,
        quality=quality,
        uc_preset=uc_preset,
        cfg_rescale=cfg_rescale,
        noise_schedule=NoiseSchedule(noise_schedule),
        image=image,
        strength=strength,
        noise=noise,
        extra_noise_seed=extra_noise_seed,
    )
    images = await client.generate(request)
    return _save_and_return(images, name="img2img", output_dir=settings.output_dir)


@mcp.tool(
    title="Inpaint a region",
    tags={"novelai", "generation"},
    annotations=IMAGE_WRITE_ANNOTATIONS,
)
@translate_errors
async def inpaint(
    prompt: str,
    image: str,
    mask: str,
    negative_prompt: str = "",
    model: Model | None = None,
    strength: Annotated[float, Field(ge=0.01, le=0.99)] = 0.3,
    noise: Annotated[float, Field(ge=0.0, le=0.99)] = 0.0,
    width: int | None = None,
    height: int | None = None,
    steps: int | None = None,
    scale: float | None = None,
    sampler: Sampler | None = None,
    seed: int = 0,
    n_samples: Annotated[int, Field(ge=1, le=_MAX_SAMPLES)] = 1,
    quality: bool = True,
    uc_preset: Literal[0, 1, 2, 3] = 0,
    noise_schedule: NoiseSchedule = NoiseSchedule.KARRAS,
    cfg_rescale: float = 0.0,
    extra_noise_seed: int | None = None,
    app: AppContext = Depends(get_app_context),
) -> list[Any]:
    """Inpaint (locally redraw) a region of an image.

    ``image`` and ``mask`` are base64-encoded PNG/JPEG; the mask marks
    the region to regenerate (non-transparent pixels are redrawn). Requires an
    inpainting model such as ``nai-diffusion-4-5-full-inpainting`` or
    ``nai-diffusion-5-full-inpainting``.
    """
    settings = app.settings
    client = app.client
    request = GenerationRequest(
        prompt=prompt,
        action=Action.INPAINT,
        negative_prompt=negative_prompt,
        model=Model(model or settings.default_model),
        width=width or settings.default_width,
        height=height or settings.default_height,
        steps=steps or settings.default_steps,
        scale=scale or settings.default_scale,
        sampler=Sampler(sampler) if sampler is not None else settings.default_sampler,
        seed=seed,
        n_samples=n_samples,
        quality=quality,
        uc_preset=uc_preset,
        cfg_rescale=cfg_rescale,
        noise_schedule=NoiseSchedule(noise_schedule),
        image=image,
        mask=mask,
        strength=strength,
        noise=noise,
        extra_noise_seed=extra_noise_seed,
    )
    images = await client.generate(request)
    return _save_and_return(images, name="inpaint", output_dir=settings.output_dir)


__all__ = ["generate_image", "image_to_image", "inpaint"]
