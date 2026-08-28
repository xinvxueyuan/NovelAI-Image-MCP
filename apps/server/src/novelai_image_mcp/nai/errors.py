"""NovelAI error-body parsing and official error-code explanations.

Every error raised toward NovelAI's API carries the error ``code`` and —
where documented — NovelAI's official explanation text (see
``OFFICIAL_CODE_EXPLANATIONS``). Codes sent inside MessagePack stream errors by
the API itself (``{code, message}`` events) are passed through verbatim.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any


@dataclass(frozen=True, slots=True)
class ErrorInfo:
    """Normalized error payload extracted from a NovelAI error body."""

    code: int | str | None
    message: str
    raw: str


#: Official error codes documented by NovelAI's API docs
#: (https://api.novelai.net/docs) and the official FAQ. 5xx are deliberately
#: folded into the generic provider-error bucket rather than enumerated.
OFFICIAL_CODE_EXPLANATIONS: dict[int, str] = {
    400: "invalid request (validation failed)",
    401: "authentication failed (missing, invalid, or expired credentials)",
    402: "active subscription or Anlas required",
    409: "request conflicted with server state",
    429: "rate limit or concurrency limit reached",
}


def explain(code: int | str | None) -> str | None:
    """Return NovelAI's official explanation for a documented error code.

    Undocumented codes (including API-supplied MessagePack stream codes)
    return ``None`` — the API's own message is then the best explanation.
    """
    if isinstance(code, int) and code in OFFICIAL_CODE_EXPLANATIONS:
        return OFFICIAL_CODE_EXPLANATIONS[code]
    return None


def parse_error_body(content: bytes) -> ErrorInfo:
    """Extract ``(code, message)`` from a NovelAI error body.

    NovelAI returns JSON in several shapes — ``{"statusCode", "message"}``,
    ``{"code", "message"}``, ``{"error": ...}``, or a bare ``{"message"}`` —
    or, on some legacy paths, raw text. Falls back to the decoded text when
    neither a code nor a message field is present.
    """
    raw = content[:4_096].decode("utf-8", errors="replace")
    try:
        value: Any = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return ErrorInfo(code=None, message=raw, raw=raw)
    if not isinstance(value, dict):
        return ErrorInfo(code=None, message=raw, raw=raw)
    code: int | str | None = value.get("statusCode", value.get("code"))
    if not isinstance(code, (int, str)):
        code = None
    message = value.get("message") or value.get("error") or value.get("detail")
    if isinstance(message, str) and message.strip():
        return ErrorInfo(code=code, message=message.strip(), raw=raw)
    return ErrorInfo(code=code, message=raw, raw=raw)


__all__ = [
    "OFFICIAL_CODE_EXPLANATIONS",
    "ErrorInfo",
    "explain",
    "parse_error_body",
]
