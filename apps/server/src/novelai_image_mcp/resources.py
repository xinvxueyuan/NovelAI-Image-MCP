"""MCP resources exposing the server's static capability surface.

Resources are read-only context an agent pulls without spending Anlas: the
model catalogue, the sampler vocabulary, the active generation defaults, and
the generated PNGs themselves. The vocabularies are derived from
``nai.constants`` so there is a single source of truth.
"""

from __future__ import annotations

from typing import Any

from fastmcp.dependencies import Depends
from fastmcp.exceptions import ResourceError

from .deps import AppContext, get_app_context
from .nai import (
    Model,
    NoiseSchedule,
    Sampler,
    is_inpaint_model,
    is_v4_model,
    is_v5_model,
    supports_upscale,
    supports_vibe,
)
from .output import resolve_output_path
from .server import mcp

_TAGS = {"novelai", "catalog"}


@mcp.resource(
    "novelai://models",
    mime_type="application/json",
    title="NovelAI models",
    description="Every supported model id with its capability flags.",
    tags=_TAGS,
)
def list_models() -> dict[str, Any]:
    """List the supported NovelAI models and their capabilities."""
    return {
        "models": [
            {
                "id": model.value,
                "name": model.name,
                "structured_prompt": is_v4_model(model),
                "v5": is_v5_model(model),
                "inpainting": is_inpaint_model(model),
                "vibe_transfer": supports_vibe(model),
                "standalone_upscale": supports_upscale(model),
            }
            for model in Model
        ]
    }


@mcp.resource(
    "novelai://samplers",
    mime_type="application/json",
    title="NovelAI sampler vocabulary",
    description="Sampler ids, noise schedules and UC preset indexes.",
    tags=_TAGS,
)
def list_samplers() -> dict[str, Any]:
    """List the sampler, noise-schedule and UC-preset values the API accepts."""
    return {
        "samplers": [sampler.value for sampler in Sampler],
        "noise_schedules": [schedule.value for schedule in NoiseSchedule],
        "uc_presets": [0, 1, 2, 3],
    }


@mcp.resource(
    "novelai://defaults",
    mime_type="application/json",
    title="Active generation defaults",
    description="Generation defaults this server applies when a tool omits them.",
    tags=_TAGS,
)
def generation_defaults(app: AppContext = Depends(get_app_context)) -> dict[str, Any]:
    """Return the active generation defaults (never credentials or endpoints)."""
    settings = app.settings
    return {
        "model": settings.default_model,
        "width": settings.default_width,
        "height": settings.default_height,
        "steps": settings.default_steps,
        "scale": settings.default_scale,
        "sampler": settings.default_sampler,
        "output_dir": settings.output_dir,
    }


@mcp.resource(
    "novelai://outputs/{name}",
    mime_type="image/png",
    title="Generated image",
    description="Read a previously generated PNG back from the output directory.",
    tags={"novelai", "outputs"},
)
def read_output_image(name: str, app: AppContext = Depends(get_app_context)) -> bytes:
    """Return one generated PNG by filename.

    The name must be a plain ``*.png`` filename that resolves inside the
    configured output directory; anything else is rejected.
    """
    try:
        path = resolve_output_path(name, output_dir=app.settings.output_dir)
    except (OSError, ValueError) as exc:
        raise ResourceError(str(exc)) from exc
    return path.read_bytes()


__all__ = [
    "generation_defaults",
    "list_models",
    "list_samplers",
    "read_output_image",
]
