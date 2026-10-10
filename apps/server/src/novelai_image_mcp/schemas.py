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

    Unknown fields are preserved (``extra="allow"``) and every field is
    optional with a default so an upstream vocabulary change never turns a
    suggestion into a validation failure.
    """

    model_config = ConfigDict(extra="allow")

    text: str = ""
    count: int = 0
    description: str | None = None


__all__ = ["AnlasEstimate", "TagSuggestion"]
