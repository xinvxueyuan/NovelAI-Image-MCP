"""NovelAI Image MCP — exposes NovelAI image generation as MCP tools.

This package wraps the NovelAI HTTP client as a Model Context Protocol server.
Tools cover the full NovelAI image API surface: text-to-image, image-to-image,
inpainting, upscaling, Director tools, ControlNet annotation, tag suggestion,
vibe encoding, and account queries.
"""

from __future__ import annotations

import importlib.metadata as _metadata
from importlib.metadata import PackageNotFoundError

# The package version is taken from ``[project] version`` in
# ``apps/server/pyproject.toml`` at build time and embedded in the
# installed wheel's METADATA. Reading it from there keeps ``__version__``
# in lock-step with the canonical pyproject value — even when the source
# is used outside an install (Docker build stages, IDE introspection of
# an un-synced checkout, etc.). The release workflow's ``sync-version``
# composite action validates that the wheel version, the Node workspace
# ``package.json`` versions, and the input version all agree.
try:
    __version__ = _metadata.version("novelai-image-mcp")
except PackageNotFoundError:
    # Dev fallback: the package is not installed in the current interpreter
    # (e.g. running ``python -c`` against a fresh source checkout without
    # ``uv sync``). The placeholder is intentionally non-empty so callers
    # that assert truthiness still pass, but the suffix makes the missing
    # install obvious in logs and error reports.
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
