"""PNG/JPEG image normalization without a heavyweight imaging dependency."""

from __future__ import annotations

import base64
from dataclasses import dataclass
import io
import struct

from .exceptions import NovelAIImageError


@dataclass(frozen=True, slots=True)
class ParsedImage:
    width: int
    height: int
    data: bytes

    @property
    def base64(self) -> str:
        return base64.b64encode(self.data).decode("ascii")


def _png_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 24:
        raise NovelAIImageError("truncated PNG image")
    return struct.unpack(">II", data[16:24])


def _jpeg_dimensions(data: bytes) -> tuple[int, int]:
    stream = io.BytesIO(data)
    stream.seek(2)
    while stream.tell() + 4 <= len(data):
        marker_bytes = stream.read(2)
        if len(marker_bytes) != 2:
            break
        marker = struct.unpack(">H", marker_bytes)[0]
        if marker in {0xFFD8, 0xFFD9}:
            continue
        length_bytes = stream.read(2)
        if len(length_bytes) != 2:
            break
        segment_length = struct.unpack(">H", length_bytes)[0]
        if segment_length < 2:
            break
        if marker in {
            *range(0xFFC0, 0xFFC4),
            *range(0xFFC5, 0xFFC8),
            *range(0xFFC9, 0xFFCC),
        }:
            payload = stream.read(5)
            if len(payload) != 5:
                break
            return struct.unpack(">HH", payload[1:5])[::-1]
        stream.seek(segment_length - 2, io.SEEK_CUR)
    raise NovelAIImageError("JPEG dimensions were not found")


def parse_image(data: bytes) -> ParsedImage:
    """Validate PNG/JPEG bytes and return dimensions plus original data."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        width, height = _png_dimensions(data)
    elif data.startswith(b"\xff\xd8\xff"):
        width, height = _jpeg_dimensions(data)
    else:
        raise NovelAIImageError("only PNG and JPEG images are supported")
    if width <= 0 or height <= 0:
        raise NovelAIImageError("image dimensions must be positive")
    return ParsedImage(width=width, height=height, data=data)
