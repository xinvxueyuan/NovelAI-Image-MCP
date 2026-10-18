"""Registry of the features the insiders header can switch on.

The header only *overrides*: a feature that is absent from
:attr:`InsidersConfig.features` keeps the default declared here. Two gates can
then force a feature off -- the header itself (``enabled=False``) and an
operator-level kill switch passed as ``force_disabled``, which wins over
everything else. Keys that are not registered in :data:`INSIDERS_FEATURES` can
never become active, no matter what a client sends.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Collection, Mapping

    from .insiders import InsidersConfig

#: Identifier of the per-request model routing feature.
MODEL_ROUTING = "model-routing"

#: Identifier of the experimental-tools surface.
EXPERIMENTAL_TOOLS = "experimental-tools"


def _normalize(text: str) -> str:
    """Return ``text`` case-folded with ``-`` and ``_`` collapsed to ``-``."""
    return text.strip().lower().replace("_", "-")


@dataclass(frozen=True)
class FeatureSpec:
    """One switchable feature: its canonical name, default and description."""

    name: str
    default_enabled: bool
    summary: str


#: Every feature a client may toggle, keyed by canonical name.
INSIDERS_FEATURES: Mapping[str, FeatureSpec] = {
    MODEL_ROUTING: FeatureSpec(
        name=MODEL_ROUTING,
        default_enabled=True,
        summary=(
            "Resolve the request's route and model from the routing headers "
            "instead of the single configured model."
        ),
    ),
    EXPERIMENTAL_TOOLS: FeatureSpec(
        name=EXPERIMENTAL_TOOLS,
        default_enabled=True,
        summary="Expose the experimental tool surface to the caller.",
    ),
}


def resolve_features(
    config: InsidersConfig,
    *,
    force_disabled: Collection[str] = (),
) -> frozenset[str]:
    """Return the names of the features active for this request.

    Precedence, strongest last: registered default, per-request override from
    the header, then ``force_disabled``. A disabled header yields no features at
    all, and names absent from :data:`INSIDERS_FEATURES` never take effect.
    """
    if not config.enabled:
        return frozenset()
    disabled = {_normalize(name) for name in force_disabled}
    return frozenset(
        name
        for name, spec in INSIDERS_FEATURES.items()
        if name not in disabled and config.features.get(name, spec.default_enabled)
    )


__all__ = [
    "EXPERIMENTAL_TOOLS",
    "INSIDERS_FEATURES",
    "MODEL_ROUTING",
    "FeatureSpec",
    "resolve_features",
]
