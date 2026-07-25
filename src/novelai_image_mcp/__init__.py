"""NovelAI Image MCP — exposes NovelAI image generation as MCP tools.

This package wraps the NovelAI HTTP client (ported from lingchu-bot and
decoupled from NoneBot) as a Model Context Protocol server. Tools cover the
full NovelAI image API surface: text-to-image, image-to-image, inpainting,
upscaling, Director tools, ControlNet annotation, tag suggestion, vibe
encoding, and account queries.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]
