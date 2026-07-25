"""MCP tools: text-to-image, image-to-image, and inpainting."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .._mcp import Context, Image
from ..nai import Action, CharacterPrompt, GenerationRequest, Model
from ..output import save_image
from ._ctx import app_context as _app

if TYPE_CHECKING:
    from .._mcp import MCPServer


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
    """Persist every image, return the first as an ImageContent block plus all paths.

    The ``Image`` helper is converted to an ``ImageContent`` (a pydantic
    ``ContentBlock``) via ``to_image_content()`` so the MCP v2 SDK's
    structured-content ``model_dump(mode="json")`` path can serialize it.
    Returning the raw ``Image`` helper triggers
    ``PydanticSerializationError: Unable to serialize unknown type: Image``
    because the helper is a plain Python class, not a pydantic model.
    """
    paths = [save_image(img.data, name=name, output_dir=output_dir) for img in images]
    return [
        Image(data=images[0].data, format="png").to_image_content(),
        f"Saved {len(images)} image(s): {[str(p) for p in paths]}",
    ]


def register(mcp: MCPServer) -> None:
    """Register the generation tools."""

    @mcp.tool()
    async def generate_image(
        ctx: Context,
        prompt: str,
        negative_prompt: str = "",
        model: str | None = None,
        width: int | None = None,
        height: int | None = None,
        steps: int | None = None,
        scale: float | None = None,
        sampler: str | None = None,
        seed: int = 0,
        n_samples: int = 1,
        quality: bool = True,
        uc_preset: int = 0,
        cfg_rescale: float = 0.0,
        smea: bool | None = None,
        smea_dynamic: bool | None = None,
        auto_smea: bool = False,
        prefer_brownian: bool = True,
        noise_schedule: str = "karras",
        character_prompts: list[dict[str, Any]] | None = None,
        references: list[str] | None = None,
    ) -> list[Any]:
        """Generate one or more images from a text prompt (text-to-image).

        Supports NovelAI V3 / V4 / V4.5 models. Pass ``references`` as a list of
        base64-encoded PNG/JPEG strings to apply vibe transfer (V4+ only).
        ``character_prompts`` enables multi-character composition with per-character
        prompts and center coordinates (x, y in 0.1–0.9). Dimensions are rounded up
        to the nearest multiple of 64.
        """
        app = _app(ctx)
        settings = app.settings
        client = app.client
        request = GenerationRequest(
            prompt=prompt,
            action=Action.GENERATE,
            negative_prompt=negative_prompt,
            model=Model(model or settings.default_model),
            width=width or settings.default_width,
            height=height or settings.default_height,
            steps=steps or settings.default_steps,
            scale=scale or settings.default_scale,
            sampler=sampler or settings.default_sampler,
            seed=seed,
            n_samples=n_samples,
            quality=quality,
            uc_preset=uc_preset,
            cfg_rescale=cfg_rescale,
            smea=smea,
            smea_dynamic=smea_dynamic,
            auto_smea=auto_smea,
            prefer_brownian=prefer_brownian,
            noise_schedule=noise_schedule,
            character_prompts=tuple(_character(cp) for cp in (character_prompts or ())),
            references=tuple(references or ()),
        )
        images = await client.generate(request)
        return _save_and_return(images, name="generate", output_dir=settings.output_dir)

    @mcp.tool()
    async def image_to_image(
        ctx: Context,
        prompt: str,
        image: str,
        negative_prompt: str = "",
        model: str | None = None,
        strength: float = 0.3,
        noise: float = 0.0,
        width: int | None = None,
        height: int | None = None,
        steps: int | None = None,
        scale: float | None = None,
        sampler: str | None = None,
        seed: int = 0,
        n_samples: int = 1,
        quality: bool = True,
        uc_preset: int = 0,
        noise_schedule: str = "karras",
        cfg_rescale: float = 0.0,
        extra_noise_seed: int | None = None,
    ) -> list[Any]:
        """Generate a new image conditioned on an input image (image-to-image).

        ``image`` is a base64-encoded PNG/JPEG. ``strength`` (0.01–0.99) controls
        how far the result diverges from the input; ``noise`` (0–0.99) adds extra
        variation. The model must match the input image domain.
        """
        app = _app(ctx)
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
            sampler=sampler or settings.default_sampler,
            seed=seed,
            n_samples=n_samples,
            quality=quality,
            uc_preset=uc_preset,
            cfg_rescale=cfg_rescale,
            noise_schedule=noise_schedule,
            image=image,
            strength=strength,
            noise=noise,
            extra_noise_seed=extra_noise_seed,
        )
        images = await client.generate(request)
        return _save_and_return(images, name="img2img", output_dir=settings.output_dir)

    @mcp.tool()
    async def inpaint(
        ctx: Context,
        prompt: str,
        image: str,
        mask: str,
        negative_prompt: str = "",
        model: str | None = None,
        strength: float = 0.3,
        noise: float = 0.0,
        width: int | None = None,
        height: int | None = None,
        steps: int | None = None,
        scale: float | None = None,
        sampler: str | None = None,
        seed: int = 0,
        n_samples: int = 1,
        quality: bool = True,
        uc_preset: int = 0,
        noise_schedule: str = "karras",
        cfg_rescale: float = 0.0,
        extra_noise_seed: int | None = None,
    ) -> list[Any]:
        """Inpaint (locally redraw) a region of an image.

        ``image`` and ``mask`` are base64-encoded PNG/JPEG; the mask marks the region
        to regenerate (non-transparent pixels are redrawn). Requires an inpainting
        model such as ``nai-diffusion-4-5-full-inpainting``.
        """
        app = _app(ctx)
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
            sampler=sampler or settings.default_sampler,
            seed=seed,
            n_samples=n_samples,
            quality=quality,
            uc_preset=uc_preset,
            cfg_rescale=cfg_rescale,
            noise_schedule=noise_schedule,
            image=image,
            mask=mask,
            strength=strength,
            noise=noise,
            extra_noise_seed=extra_noise_seed,
        )
        images = await client.generate(request)
        return _save_and_return(images, name="inpaint", output_dir=settings.output_dir)


__all__ = ["register"]
