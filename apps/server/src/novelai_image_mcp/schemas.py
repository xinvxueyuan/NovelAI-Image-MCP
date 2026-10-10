"""Structured-output models for tools that compute their own results.

Tools that pass a NovelAI payload straight through keep returning
``dict[str, Any]`` (an object return already yields structured content, and
modelling an upstream payload risks dropping unknown fields). The models here
cover only the shapes this server computes itself, so their output schema is
precise and stable.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class AnlasEstimate(BaseModel):
    """Anlas cost estimate returned by ``estimate_anlas_cost``."""

    anlas: int
    opus_free_sample: bool


class TagSuggestion(BaseModel):
    """One tag suggested by NovelAI's tagger for a partial prompt.

    The wire shape is live-verified (2026-10-10):
    ``{"tag": "1girl", "count": 10000, "confidence": 0.79}``. Unknown
    fields are preserved (``extra="allow"``) and every field has a
    default, so an upstream vocabulary change never turns a suggestion into a
    validation failure.
    """

    model_config = ConfigDict(extra="allow")

    tag: str = ""
    count: int = 0
    confidence: float = 0.0


__all__ = ["AnlasEstimate", "TagSuggestion"]
