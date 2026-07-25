"""NovelAI HTTP, ZIP, and MessagePack response parsing."""

from __future__ import annotations

from dataclasses import dataclass
import io
import json
import struct
from typing import Any, cast
import zipfile

import msgpack

from .exceptions import (
    NovelAIAuthenticationError,
    NovelAIConcurrencyError,
    NovelAIInsufficientCreditsError,
    NovelAIProviderError,
    NovelAIResponseError,
    NovelAIValidationError,
)


@dataclass(frozen=True, slots=True)
class NovelAIImage:
    filename: str
    data: bytes


@dataclass(frozen=True, slots=True)
class GenerationEvent:
    event_type: str
    sample_index: int
    step_index: int
    generation_id: str
    sigma: float
    image: NovelAIImage


def _bounded_error(content: bytes) -> str:
    raw = content[:2_048]
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return raw.decode("utf-8", errors="replace")
    return json.dumps(value, ensure_ascii=False)


def check_status(status_code: int, content: bytes) -> None:
    """Raise the domain error associated with an HTTP status."""
    if status_code < 400:
        return
    detail = _bounded_error(content)
    error_type: type[NovelAIProviderError | NovelAIValidationError]
    if status_code == 400:
        error_type = NovelAIValidationError
    elif status_code == 401:
        error_type = NovelAIAuthenticationError
    elif status_code == 402:
        error_type = NovelAIInsufficientCreditsError
    elif status_code == 429:
        error_type = NovelAIConcurrencyError
    else:
        error_type = NovelAIProviderError
    raise error_type(f"NovelAI HTTP {status_code}: {detail}")


def parse_zip_images(content: bytes) -> tuple[NovelAIImage, ...]:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            return tuple(
                NovelAIImage(filename=name, data=archive.read(name))
                for name in archive.namelist()
                if not name.endswith("/")
            )
    except (OSError, zipfile.BadZipFile) as exc:
        raise NovelAIResponseError("NovelAI returned an invalid ZIP response") from exc


def _event(value: object) -> GenerationEvent | None:
    if not isinstance(value, dict):
        return None
    data = cast("dict[str, Any]", value)
    event_type = data.get("event_type")
    if event_type == "retry":
        return None
    if event_type == "error":
        raise NovelAIProviderError(
            f"NovelAI stream error {data.get('code')}: {data.get('message')}"
        )
    image = data.get("image")
    if event_type not in {"intermediate", "final"} or not isinstance(image, bytes):
        return None
    sample_index = int(data.get("samp_ix", 0))
    extension = "png" if image.startswith(b"\x89PNG") else "jpg"
    return GenerationEvent(
        event_type=event_type,
        sample_index=sample_index,
        step_index=int(data.get("step_ix", 0)),
        generation_id=str(data.get("gen_id", "")),
        sigma=float(data.get("sigma", 0)),
        image=NovelAIImage(
            filename=f"sample-{sample_index}-{event_type}.{extension}",
            data=image,
        ),
    )


class MessagePackStreamParser:
    """Incrementally parse NovelAI's big-endian length-prefixed MessagePack."""

    def __init__(self) -> None:
        self._buffer = bytearray()
        self._expected: int | None = None

    def feed(self, chunk: bytes) -> tuple[GenerationEvent, ...]:
        self._buffer.extend(chunk)
        events: list[GenerationEvent] = []
        while True:
            if self._expected is None:
                if len(self._buffer) < 4:
                    break
                frame_length = struct.unpack(">I", self._buffer[:4])[0]
                self._expected = frame_length
                del self._buffer[:4]
                if frame_length > 128 * 1024 * 1024:
                    raise NovelAIResponseError("MessagePack frame is too large")
            expected = self._expected
            if expected is None:
                break
            if len(self._buffer) < expected:
                break
            payload = bytes(self._buffer[:expected])
            del self._buffer[:expected]
            self._expected = None
            try:
                value = msgpack.unpackb(payload, raw=False)
            except (ValueError, msgpack.ExtraData) as exc:
                raise NovelAIResponseError("invalid MessagePack frame") from exc
            parsed = _event(value)
            if parsed is not None:
                events.append(parsed)
        return tuple(events)

    def finish(self) -> None:
        if self._expected is not None or self._buffer:
            raise NovelAIResponseError("truncated MessagePack stream")


def parse_messagepack_events(content: bytes) -> tuple[GenerationEvent, ...]:
    parser = MessagePackStreamParser()
    events = parser.feed(content)
    parser.finish()
    return events


def parse_messagepack_images(content: bytes) -> tuple[NovelAIImage, ...]:
    return tuple(
        event.image
        for event in parse_messagepack_events(content)
        if event.event_type == "final"
    )
