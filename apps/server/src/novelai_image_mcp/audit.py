"""Append-only JSONL audit trail for routed tool calls.

One record per line, one ``os.write`` per record. The file is opened with
``O_APPEND`` so concurrent writers append whole lines rather than overwrite one
another: a crash mid-write can lose a line but never corrupt a line already
written.

Nothing here may break a tool call. Every I/O or serialisation failure is logged
and swallowed, because observability must never become a dependency of the
business path.

Credentials and image payloads are never recorded. Prompts are reduced to their
length plus a truncated SHA-256, image arguments are replaced by a marker, and
any over-long string is digested instead of written verbatim, so a base64 blob
cannot reach the trail even under an unexpected argument name.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import hashlib
import json
import logging
import os
from pathlib import Path
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Collection

    from .routing import RoutingContext

logger = logging.getLogger(__name__)

#: File name used when no explicit audit path is configured.
AUDIT_FILENAME = "audit.jsonl"

#: Number of hex characters kept from a digest.
DIGEST_LENGTH = 16

#: Longest argument string recorded verbatim; longer values are digested.
MAX_ARGUMENT_LENGTH = 256

#: Largest number of headers kept in an audit record. The routing layer already
#: caps its snapshot at 64; this is a second, tighter bound so a hostile client
#: cannot grow an audit line without limit.
MAX_RECORDED_HEADERS = 32

#: Longest header value kept in an audit record.
MAX_RECORDED_HEADER_LENGTH = 256

#: Argument names whose values are prompts and therefore digested.
_PROMPT_KEYS = frozenset({
    "negative_prompt",
    "negativeprompt",
    "prompt",
    "prompts",
})

#: Argument names that carry image bytes (base64 or raw) and are never recorded.
_IMAGE_KEYS = frozenset({
    "base64",
    "image",
    "images",
    "init_image",
    "mask",
    "reference",
    "references",
})

#: Marker written in place of an image argument.
_REDACTED_IMAGE = "[redacted image]"

#: Generated-image references inside a tool result's text blocks.
_ARTIFACT_PATTERN = re.compile(r"""[^\s\[\]',"]+[.]png""")


def digest_text(value: str) -> dict[str, Any]:
    """Return the length and truncated SHA-256 of ``value``, never the text."""
    digest = hashlib.sha256(value.encode("utf-8", "replace")).hexdigest()
    return {"length": len(value), "sha256": digest[:DIGEST_LENGTH]}


def _summarise_value(value: Any) -> Any:
    """Return a recordable stand-in for one argument value."""
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return digest_text(value) if len(value) > MAX_ARGUMENT_LENGTH else value
    if isinstance(value, Mapping):
        return {"keys": len(value)}
    if isinstance(value, (list, tuple, set, frozenset)):
        return {"items": len(value)}
    return type(value).__name__


def summarise_arguments(arguments: Mapping[str, Any] | None) -> dict[str, Any]:
    """Summarise tool arguments so the record can never leak a payload.

    Prompts become a length plus a truncated SHA-256, image arguments become a
    marker, and every other value is reduced to something small and
    JSON-serialisable.
    """
    if not arguments:
        return {}
    summary: dict[str, Any] = {}
    for key, value in arguments.items():
        name = str(key)
        normalised = name.strip().lower()
        if normalised in _IMAGE_KEYS:
            summary[name] = _REDACTED_IMAGE
        elif normalised in _PROMPT_KEYS and isinstance(value, str):
            summary[name] = digest_text(value)
        else:
            summary[name] = _summarise_value(value)
    return summary


def artifact_paths(result: Any) -> list[str]:
    """Return the sorted ``*.png`` paths a tool result mentions.

    Image tools report what they wrote as text (``Saved 1 image(s): [...]``);
    this reads those paths back for the audit record. The result is only
    observed, never rewritten, and a result without text blocks yields ``[]``.
    """
    texts: list[str] = []
    for block in getattr(result, "content", None) or []:
        text = getattr(block, "text", None)
        if isinstance(text, str):
            texts.append(text)
    return sorted(set(_ARTIFACT_PATTERN.findall("\n".join(texts))))


# One record field per keyword argument: the audit schema is the contract, and a
# request object would hide which fields a caller actually supplied.
def cap_headers(headers: Mapping[str, str] | None) -> dict[str, str]:
    """Apply the audit-side cap to an already-sanitised header snapshot.

    The input is expected to be ``RoutingContext.recorded_headers``, which the
    routing layer has already stripped of every credential-bearing name. This
    only bounds the size: at most :data:``MAX_RECORDED_HEADERS`` entries, each
    value at most :data:``MAX_RECORDED_HEADER_LENGTH`` characters, kept in
    lexicographic order of the (lower-cased) name.
    """
    if not headers:
        return {}
    capped = {
        name.lower(): value[:MAX_RECORDED_HEADER_LENGTH]
        for name, value in headers.items()
    }
    if len(capped) > MAX_RECORDED_HEADERS:
        kept = sorted(capped)[:MAX_RECORDED_HEADERS]
        capped = {name: capped[name] for name in kept}
    return capped


# One record field per keyword argument: the audit schema is the contract, and a
# request object would hide which fields a caller actually supplied.
def build_record(  # noqa: PLR0913
    *,
    routing: RoutingContext,
    tool: str,
    duration_ms: float,
    outcome: str,
    features: Collection[str] = (),
    artifacts: Collection[str] = (),
    arguments: Mapping[str, Any] | None = None,
    unknown_keys: Collection[str] = (),
    malformed: Collection[str] = (),
) -> dict[str, Any]:
    """Build one JSON-serialisable audit record.

    ``features``, ``artifacts``, ``unknown_keys`` and ``malformed`` are sorted so
    two records describing the same state are byte-identical.
    """
    return {
        "ts": datetime.now(UTC).isoformat(),
        "route": routing.route,
        "model": routing.model,
        "agent": routing.agent,
        "client": routing.client,
        "session": routing.session,
        "tool": tool,
        "duration_ms": round(duration_ms, 3),
        "outcome": outcome,
        "features": sorted(features),
        "artifacts": sorted(artifacts),
        "unknown_keys": sorted(unknown_keys),
        "malformed": sorted(malformed),
        "headers": cap_headers(routing.recorded_headers),
        "arguments": summarise_arguments(arguments),
    }


def resolve_audit_path(
    *,
    audit_log_path: str | None,
    output_dir: str | Path | None = None,
) -> Path:
    """Resolve the audit destination.

    An explicit ``audit_log_path`` wins; otherwise the trail lives beside the
    generated images at ``<output_dir>/audit.jsonl``.
    """
    if audit_log_path:
        return Path(audit_log_path)
    return Path(output_dir) / AUDIT_FILENAME if output_dir else Path(AUDIT_FILENAME)


def append_record(record: Mapping[str, Any], *, path: str | Path) -> bool:
    """Append ``record`` as a single JSON line; return whether it was written.

    The record is serialised first and then handed to exactly one ``os.write``
    on a descriptor opened ``O_APPEND``, so concurrent writers cannot interleave
    halves of a line. Failures are logged and reported as ``False`` -- this
    function never raises, because a tool call must not fail on account of the
    audit trail.
    """
    destination = Path(path)
    try:
        line = json.dumps(record, ensure_ascii=False, sort_keys=True, default=str)
        if destination.parent and not destination.parent.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_BINARY", 0)
        descriptor = os.open(destination, flags, 0o600)
        try:
            os.write(descriptor, (line + "\n").encode("utf-8"))
        finally:
            os.close(descriptor)
    except (OSError, TypeError, ValueError):
        logger.error(
            "could not append the audit record to %s", destination, exc_info=True
        )
        return False
    return True


__all__ = [
    "AUDIT_FILENAME",
    "DIGEST_LENGTH",
    "MAX_ARGUMENT_LENGTH",
    "MAX_RECORDED_HEADERS",
    "MAX_RECORDED_HEADER_LENGTH",
    "append_record",
    "artifact_paths",
    "build_record",
    "cap_headers",
    "digest_text",
    "resolve_audit_path",
    "summarise_arguments",
]
