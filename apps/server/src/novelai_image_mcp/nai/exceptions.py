"""Typed NovelAI domain failures.

Every exception optionally carries the NovelAI error ``code`` (HTTP status or
API-supplied stream code) and, when documented, NovelAI's official
``explanation`` — see ``nai.errors``. The code and explanation are appended to
the message (so they reach MCP tool callers and the CLI) and exposed as
attributes for programmatic handling.
"""

from __future__ import annotations


class NovelAIError(Exception):
    """Base class for NovelAI failures.

    ``code`` is the NovelAI error code when known (``None`` for transport,
    timeout, or local validation failures that carry no server code);
    ``explanation`` is NovelAI's official explanation for documented codes.
    """

    def __init__(
        self,
        message: str,
        *,
        code: int | str | None = None,
        explanation: str | None = None,
    ) -> None:
        self.code = code
        self.explanation = explanation
        if code is not None:
            suffix = f" [code {code}"
            if explanation:
                suffix += f": {explanation}"
            suffix += "]"
            message = f"{message}{suffix}"
        super().__init__(message)


class NovelAIProviderError(NovelAIError):
    """NovelAI rejected or failed the request."""


class NovelAIValidationError(NovelAIProviderError):
    """The request is invalid."""


class NovelAIAuthenticationError(NovelAIProviderError):
    """Credentials are missing, invalid, or expired."""


class NovelAIInsufficientCreditsError(NovelAIProviderError):
    """The account has insufficient Anlas or no subscription."""


class NovelAIConcurrencyError(NovelAIProviderError):
    """The account hit a concurrency or rate limit."""


class NovelAITimeoutError(NovelAIError):
    """A request exceeded its timeout."""


class NovelAITransportError(NovelAIError):
    """The request could not reach NovelAI."""


class NovelAIResponseError(NovelAIError):
    """NovelAI returned malformed or unsupported data."""


class NovelAIImageError(NovelAIError):
    """An input or output image is malformed or unsupported."""
