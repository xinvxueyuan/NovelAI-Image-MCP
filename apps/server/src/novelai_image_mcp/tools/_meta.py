"""Shared MCP tool annotations.

Annotations are advisory metadata clients use to decide how to present and
confirm a tool call. They are declared once per behaviour class instead of
being repeated (and drifting) across the tool modules.
"""

from __future__ import annotations

from mcp.types import ToolAnnotations

#: Tools that read remote NovelAI state without touching local files.
READ_ONLY_ANNOTATIONS = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=False,
    open_world_hint=True,
)

#: Pure offline computation: no network call, no local write, stable result.
OFFLINE_ANNOTATIONS = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=False,
)

#: Tools that spend Anlas at NovelAI and write a new PNG into the output
#: directory. They never overwrite or delete existing images, hence
#: ``destructive_hint=False``.
IMAGE_WRITE_ANNOTATIONS = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=False,
    idempotent_hint=False,
    open_world_hint=True,
)


__all__ = [
    "IMAGE_WRITE_ANNOTATIONS",
    "OFFLINE_ANNOTATIONS",
    "READ_ONLY_ANNOTATIONS",
]
