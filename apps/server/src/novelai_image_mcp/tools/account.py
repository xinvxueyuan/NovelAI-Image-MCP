"""MCP tools: account queries and Anlas cost estimation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .._mcp import Context
from ..nai import Action, GenerationRequest, Model
from ._ctx import app_context as _app

if TYPE_CHECKING:
    from .._mcp import FastMCP


def register(mcp: FastMCP) -> None:
    """Register the account and cost-estimation tools."""

    @mcp.tool()
    async def get_subscription(ctx: Context) -> dict[str, Any]:
        """Return the account subscription details and Anlas balance.

        The shape mirrors NovelAI's ``/user/subscription`` response: it
        includes ``tier`` (0 = free, 1 = starter, 2 = …), ``active``, the
        ``trainingStepsLeft`` breakdown, ``fixedTrainingStepsLeft``,
        ``perStepUsage`` flag, and ``subscriptionId``. Use this to inspect
        remaining Anlas or the active plan before a generation.
        """
        client = _app(ctx).client
        return await client.get_subscription()

    @mcp.tool()
    async def get_user_data(ctx: Context) -> dict[str, Any]:
        """Return the authenticated account's user data.

        Includes ``email``, ``accountChain`` (registration source), and the
        ``priority`` epoch. Useful to confirm which account the server is
        authenticated as before issuing generation commands.
        """
        client = _app(ctx).client
        return await client.get_user_data()

    @mcp.tool()
    async def estimate_anlas_cost(
        ctx: Context,
        width: int,
        height: int,
        steps: int,
        n_samples: int = 1,
        model: str = "nai-diffusion-4-5-full",
        action: str = "generate",
        strength: float | None = None,
        smea: bool | None = None,
        smea_dynamic: bool | None = None,
        auto_smea: bool = False,
        opus: bool = False,
    ) -> dict[str, int | bool]:
        """Estimate the Anlas cost of a generation without calling the API.

        Mirrors NovelAI's public web-client cost formula. ``action`` is one of
        ``generate``, ``img2img``, ``infill`` (inpaint). For ``img2img``,
        ``strength`` (0.01–0.99) scales the cost proportionally. ``smea`` /
        ``smea_dynamic`` / ``auto_smea`` apply the SMEA multiplier. ``opus``
        grants a free sample when the request is within Opus limits. Returns
        ``{"anlas": <cost>, "opus_free_sample": <bool>}``.

        Note: on V5 models, Opus free generations are capped by NovelAI's
        refillable "battery" usage limit (normal resolution, <=28 steps); once
        exhausted the API silently bills Anlas instead of erroring, so check
        ``get_subscription``'s ``usage`` field before costly V5 runs.
        """
        _ = ctx  # settings unused: estimation is pure and offline
        try:
            model_enum = Model(model)
        except ValueError as exc:
            raise ValueError(
                f"unknown model '{model}'; expected one of: "
                f"{', '.join(m.value for m in Model)}"
            ) from exc
        try:
            action_enum = Action(action)
        except ValueError as exc:
            raise ValueError(
                f"unknown action '{action}'; expected one of: "
                f"{', '.join(a.value for a in Action)}"
            ) from exc
        request = GenerationRequest(
            prompt="cost-estimate",
            action=action_enum,
            model=model_enum,
            width=width,
            height=height,
            steps=steps,
            n_samples=n_samples,
            smea=smea,
            smea_dynamic=smea_dynamic,
            auto_smea=auto_smea,
            strength=strength if action_enum is not Action.GENERATE else None,
        )
        cost = request.estimate_anlas_cost(opus=opus)
        free_sample = (
            opus and steps <= 28 and max(width * height, 65_536) <= 1_024 * 1_024
        )
        return {"anlas": cost, "opus_free_sample": free_sample}


__all__ = ["register"]
