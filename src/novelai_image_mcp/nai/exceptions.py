"""Typed NovelAI domain failures."""


class NovelAIError(Exception):
    """Base class for NovelAI failures."""


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
