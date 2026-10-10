"""MCP tools: account queries and Anlas cost estimation."""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp.dependencies import Depends
from pydantic import Field

from ..deps import get_client
from ..nai import Action, GenerationRequest, Model, NovelAIClient
from ..schemas import AnlasEstimate
from ..server import mcp
from ._errors import translate_errors
from ._meta import OFFLINE_ANNOTATIONS, READ_ONLY_ANNOTATIONS

#: NovelAI caps a single generation request at 8 samples.
_MAX_SAMPLES = 8
#: V5 Opus free generations are limited to normal resolution and 28 steps.
_OPUS_MAX_STEPS = 28
_OPUS_MAX_PIXELS = 1_024 * 1_024
_MIN_PIXELS = 65_536


@mcp.tool(
    title="Get subscription and Anlas balance",
    tags={"novelai", "account"},
    annotations=READ_ONLY_ANNOTATIONS,
)
@translate_errors
async def get_subscription(
    client: NovelAIClient = Depends(get_client),
) -> dict[str, Any]:
    """Return the account subscription details and Anlas balance.

    The shape mirrors NovelAI's ``/user/subscription`` response: it
    includes ``tier`` (0 = free, 1 = starter, 2 = ...), ``active``, the
    ``trainingStepsLeft`` breakdown, ``fixedTrainingStepsLeft``,
    ``perStepUsage`` flag, and ``subscriptionId``. Use this to inspect
    remaining Anlas or the active plan before a generation.
    """
    return await client.get_subscription()


@mcp.tool(
    title="Get user data",
    tags={"novelai", "account"},
    annotations=READ_ONLY_ANNOTATIONS,
)
@translate_errors
async def get_user_data(
    client: NovelAIClient = Depends(get_client),
) -> dict[str, Any]:
    """Return the authenticated account's user data.

    Includes ``email``, ``accountChain`` (registration source), and the
    ``priority`` epoch. Useful to confirm which account the server is
    authenticated as before issuing generation commands.
    """
    return await client.get_user_data()


@mcp.tool(
    title="Estimate Anlas cost",
    tags={"novelai", "account"},
    annotations=OFFLINE_ANNOTATIONS,
)
@translate_errors
async def estimate_anlas_cost(
    width: int,
    height: int,
    steps: int,
    n_samples: Annotated[int, Field(ge=1, le=_MAX_SAMPLES)] = 1,
    model: Model = Model.V4_5,
    action: Action = Action.GENERATE,
    strength: Annotated[float, Field(ge=0.01, le=0.99)] | None = None,
    smea: bool | None = None,
    smea_dynamic: bool | None = None,
    auto_smea: bool = False,
    opus: bool = False,
) -> AnlasEstimate:
    """Estimate the Anlas cost of a generation without calling the API.

    Mirrors NovelAI's public web-client cost formula. ``action`` is one of
    ``generate``, ``img2img``, ``infill`` (inpaint). For
    ``img2img``, ``strength`` (0.01-0.99) scales the cost proportionally.
    ``smea`` / ``smea_dynamic`` / ``auto_smea`` apply the SMEA
    multiplier. ``opus`` grants a free sample when the request is within
    Opus limits. Returns ``{"anlas": <cost>, "opus_free_sample": <bool>}``.

    Note: on V5 models, Opus free generations are capped by NovelAI's
    refillable "battery" usage limit (normal resolution, <=28 steps); once
    exhausted the API silently bills Anlas instead of erroring, so check
    ``get_subscription``'s ``usage`` field before costly V5 runs.
    """
    request = GenerationRequest(
        prompt="cost-estimate",
        action=Action(action),
        model=Model(model),
        width=width,
        height=height,
        steps=steps,
        n_samples=n_samples,
        smea=smea,
        smea_dynamic=smea_dynamic,
        auto_smea=auto_smea,
        strength=strength if action is not Action.GENERATE else None,
    )
    cost = request.estimate_anlas_cost(opus=opus)
    free_sample = (
        opus
        and steps <= _OPUS_MAX_STEPS
        and max(width * height, _MIN_PIXELS) <= _OPUS_MAX_PIXELS
    )
    return AnlasEstimate(anlas=cost, opus_free_sample=free_sample)


__all__ = ["estimate_anlas_cost", "get_subscription", "get_user_data"]
