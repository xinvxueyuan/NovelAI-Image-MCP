"""MCP tools: prompt-tag suggestion and vibe encoding."""

from __future__ import annotations

from typing import Annotated

from fastmcp.dependencies import Depends
from pydantic import Field

from ..deps import get_client
from ..nai import Model, NovelAIClient, is_v5_model
from ..schemas import TagSuggestion
from ..server import mcp
from ._errors import translate_errors
from ._meta import READ_ONLY_ANNOTATIONS


@mcp.tool(
    title="Suggest prompt tags",
    tags={"novelai", "tags"},
    annotations=READ_ONLY_ANNOTATIONS,
)
@translate_errors
async def suggest_tags(
    prompt: str,
    model: Model = Model.V4_5,
    language: str = "en",
    client: NovelAIClient = Depends(get_client),
) -> list[TagSuggestion]:
    """Suggest NovelAI tags that complete or refine a prompt.

    ``prompt`` is the partial prompt text to complete. ``model`` selects
    the tagger vocabulary (default ``nai-diffusion-4-5-full``).
    ``language`` is the ISO 639-1 code for the response language (e.g.
    ``en``, ``ja``). Returns tag suggestions carrying the tag
    string, its training-set occurrence ``count`` and the tagger's
    ``confidence``.
    """
    found = await client.suggest_tags(prompt, model=Model(model), language=language)
    return [TagSuggestion.model_validate(tag) for tag in found]


@mcp.tool(
    title="Encode a vibe token",
    tags={"novelai", "tags"},
    annotations=READ_ONLY_ANNOTATIONS,
)
@translate_errors
async def encode_vibe(
    reference: str,
    information_extracted: Annotated[float, Field(ge=0.01, le=1.0)] = 1.0,
    model: Model = Model.V4_5,
    client: NovelAIClient = Depends(get_client),
) -> str:
    """Encode a reference image into a NovelAI vibe token.

    ``reference`` is a base64-encoded PNG/JPEG to encode.
    ``information_extracted`` (0.01-1.0) controls how strongly the vibe
    captures the reference's identity (lower = more stylistic, higher = more
    literal). ``model`` must be a V4/V4.5 model (vibes are not supported on
    V3, and V5 does not support vibe transfer yet). Returns a base64 vibe token
    suitable for the ``references`` parameter of ``generate_image``.
    """
    model_enum = Model(model)
    if is_v5_model(model_enum):
        raise ValueError("vibe transfer is not supported on V5 models yet")
    return await client.encode_vibe(
        reference,
        information_extracted=information_extracted,
        model=model_enum,
    )


__all__ = ["encode_vibe", "suggest_tags"]
