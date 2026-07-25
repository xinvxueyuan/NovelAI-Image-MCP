"""NovelAI HTTP client built on a shared ``httpx.AsyncClient``.

Subpackage re-exports the public client surface used by the MCP server and CLI.
"""

from __future__ import annotations

from .auth import NovelAICredentials, derive_access_key, request_tracking_headers
from .client import (
    MissingNovelAITokenError,
    NovelAIClient,
    NovelAIError,
    NovelAIProviderError,
    NovelAIResponseError,
    NovelAITimeoutError,
    NovelAITransportError,
    extract_final_image,
    generate_image_from_plan,
)
from .constants import (
    Action,
    ControlNetModel,
    DirectorTool,
    Emotion,
    EmotionLevel,
    Endpoint,
    Model,
    NoiseSchedule,
    Sampler,
    is_inpaint_model,
    is_v4_model,
)
from .exceptions import (
    NovelAIAuthenticationError,
    NovelAIConcurrencyError,
    NovelAIImageError,
    NovelAIInsufficientCreditsError,
    NovelAIValidationError,
)
from .models import (
    CharacterPrompt,
    GenerationRequest,
    NovelAIGenerationPlan,
)
from .payload import build_generation_payload
from .response import (
    GenerationEvent,
    NovelAIImage,
    check_status,
    parse_messagepack_images,
    parse_zip_images,
)
from .service import NovelAIConfigLike, create_novelai_client

__all__ = [
    # auth
    "NovelAICredentials",
    "derive_access_key",
    "request_tracking_headers",
    # client
    "MissingNovelAITokenError",
    "NovelAIClient",
    "NovelAIError",
    "NovelAIProviderError",
    "NovelAIResponseError",
    "NovelAITimeoutError",
    "NovelAITransportError",
    "extract_final_image",
    "generate_image_from_plan",
    # constants
    "Action",
    "ControlNetModel",
    "DirectorTool",
    "Emotion",
    "EmotionLevel",
    "Endpoint",
    "Model",
    "NoiseSchedule",
    "Sampler",
    "is_inpaint_model",
    "is_v4_model",
    # exceptions
    "NovelAIAuthenticationError",
    "NovelAIConcurrencyError",
    "NovelAIImageError",
    "NovelAIInsufficientCreditsError",
    "NovelAIValidationError",
    # models
    "CharacterPrompt",
    "GenerationRequest",
    "NovelAIGenerationPlan",
    # payload
    "build_generation_payload",
    # response
    "GenerationEvent",
    "NovelAIImage",
    "check_status",
    "parse_messagepack_images",
    "parse_zip_images",
    # service
    "NovelAIConfigLike",
    "create_novelai_client",
]
