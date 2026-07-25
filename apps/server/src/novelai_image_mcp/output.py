"""Persist generated images to the configured output directory.

Image-returning MCP tools save the PNG bytes to ``NOVELAI_OUTPUT_DIR`` and
return the resolved path alongside the base64 ``Image`` content block so the
agent can both view the image and locate the file on disk.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import secrets


def save_image(
    data: bytes,
    *,
    name: str = "image",
    output_dir: str | Path = "outputs",
) -> Path:
    """Write image bytes to ``output_dir`` and return the resolved path.

    The filename is ``<name>-<utc-timestamp>-<6-hex>.png`` so repeated calls
    never collide. Parent directories are created on demand.
    """
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = secrets.token_hex(3)
    path = directory / f"{name}-{stamp}-{suffix}.png"
    path.write_bytes(data)
    return path


__all__ = ["save_image"]
