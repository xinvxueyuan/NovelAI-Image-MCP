"""MCP tools: prompt-tag suggestion and vibe encoding."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .._mcp import Context
from ..nai import Model
from ._ctx import app_context as _app

if TYPE_CHECKING:
    from .._mcp import FastMCP


def register(mcp: FastMCP) -> None:
    """Register the tag-suggestion and vibe-encoding tools."""

    @mcp.tool()
    async def suggest_tags(
        ctx: Context,
        prompt: str,
        model: str = "nai-diffusion-4-5-full",
        language: str = "en",
    ) -> list[dict[str, Any]]:
        """Suggest NovelAI tags that complete or refine a prompt.

        ``prompt`` is the partial prompt text to complete. ``model`` selects
        the tagger vocabulary (default ``nai-diffusion-4-5-full``). ``language``
        is the ISO 639-1 code for the response language (e.g. ``en``, ``ja``,
        ``zh``). Returns a list of tag descriptors (``description``, ``text``,
        ``count`` of training occurrences).
        """
        client = _app(ctx).client
        try:
            model_enum = Model(model)
        except ValueError as exc:
            raise ValueError(
                f"unknown model '{model}'; expected one of: "
                f"{', '.join(m.value for m in Model)}"
            ) from exc
        tags = await client.suggest_tags(
            prompt,
            model=model_enum,
            language=language,
        )
        return list(tags)

    @mcp.tool()
    async def encode_vibe(
        ctx: Context,
        reference: str,
        information_extracted: float = 1.0,
        model: str = "nai-diffusion-4-5-full",
    ) -> str:
        """Encode a reference image into a NovelAI vibe token.

        ``reference`` is a base64-encoded PNG/JPEG to encode.
        ``information_extracted`` (0.01–1.0) controls how strongly the vibe
        captures the reference's identity (lower = more stylistic, higher =
        more literal). ``model`` must be a V4/V4.5 model (vibes are not
        supported on V3). Returns a base64 vibe token suitable for the
        ``references`` parameter of ``generate_image``.
        """
        client = _app(ctx).client
        try:
            model_enum = Model(model)
        except ValueError as exc:
            raise ValueError(
                f"unknown model '{model}'; expected one of: "
                f"{', '.join(m.value for m in Model)}"
            ) from exc
        if not 0.01 <= information_extracted <= 1.0:
            raise ValueError("information_extracted must be between 0.01 and 1.0")
        return await client.encode_vibe(
            reference,
            information_extracted=information_extracted,
            model=model_enum,
        )


__all__ = ["register"]
