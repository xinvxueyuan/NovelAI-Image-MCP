"""Parser for the experimental ``X-MCP-Insiders`` opt-in header.

The header is a single, self-contained value supplied by the HTTP client: the
server never reads insiders state from the environment or from disk. Its
grammar is deliberately forgiving so a typo can never break a request -- every
problem is *reported* on :class:`InsidersConfig` (``unknown_keys`` /
``malformed``) and ignored for behaviour. Nothing in this module performs I/O,
so the whole surface is unit-testable.

Grammar (comma separated, case-insensitive, ``-`` and ``_`` are equivalent):

=======================  ====================================================
``<missing>``            disabled
``""``                   disabled
``false``                disabled (also ``0`` / ``off`` / ``no``)
``true``                 enabled, every feature at its default (``1``/``on``/``yes``)
``model-routing=false``  enabled, ``model-routing`` overridden to ``False``
``model-routing``        enabled, ``model-routing`` overridden to ``True``
``k=v, k2=v2``           enabled, each key overridden individually
=======================  ====================================================

Keys that are not registered in :data:`features.INSIDERS_FEATURES` are recorded
in ``unknown_keys`` and otherwise ignored, so a client can never activate a
feature the server does not know about. An unparsable value is recorded in
``malformed`` and applies no override -- it never raises and never switches the
header off. The surface is on whenever the header is present and non-empty;
only a bare ``false``-style token, an empty header or a header longer than
``max_length`` switches it off.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .features import INSIDERS_FEATURES

if TYPE_CHECKING:
    from collections.abc import Mapping

#: Canonical spelling of the opt-in header.
INSIDERS_HEADER = "X-MCP-Insiders"

#: Bare values that switch the insiders surface on.
_TRUTHY = frozenset({"true", "1", "on", "yes"})

#: Bare values that switch the insiders surface off.
_FALSY = frozenset({"false", "0", "off", "no"})


def _normalize(text: str) -> str:
    """Return ``text`` case-folded with ``-`` and ``_`` collapsed to ``-``.

    Header keys are matched case-insensitively and treat the two separator
    spellings as the same key, so ``Model_Routing`` and ``model-routing``
    address one feature.
    """
    return text.strip().lower().replace("_", "-")


def _split(token: str) -> tuple[str, str | None]:
    """Split ``token`` into ``(key, value)``; ``value`` is ``None`` when bare."""
    key, separator, value = token.partition("=")
    return (key, value) if separator else (token, None)


def _as_flag(value: str) -> bool | None:
    """Return the boolean ``value`` denotes, or ``None`` when unparsable."""
    flag = value.strip().lower()
    if flag in _TRUTHY:
        return True
    if flag in _FALSY:
        return False
    return None


@dataclass(frozen=True)
class InsidersConfig:
    """Parsed insiders state for one request.

    ``features`` holds only the overrides the header made for *registered*
    features, so an absent key means "use the registered default".
    ``unknown_keys`` and ``malformed`` are diagnostic only: they never change
    behaviour and exist so an operator can see a typo instead of silently
    losing the opt-in.
    """

    enabled: bool = False
    features: Mapping[str, bool] = field(default_factory=dict)
    unknown_keys: frozenset[str] = frozenset()
    malformed: frozenset[str] = frozenset()

    @classmethod
    def disabled(cls) -> InsidersConfig:
        """Return the state used when the header is absent or unusable."""
        return cls()


class _Accumulator:
    """Mutable state folded over the comma-separated entries of one header."""

    def __init__(self) -> None:
        self.enabled = False
        self.features: dict[str, bool] = {}
        self.unknown: set[str] = set()
        self.malformed: set[str] = set()

    def feed(self, token: str) -> bool:
        """Fold one entry in; return ``False`` to disable the whole header.

        Any non-empty entry switches the header on: presence is the opt-in
        signal, while the entry's value only decides the override it applies.
        A bare ``false``-style entry is the exception -- it switches the whole
        header off. A malformed entry is recorded and applies no override, but
        still counts as presence so a typo cannot silently drop the opt-in.
        """
        self.enabled = True
        key, raw_value = _split(token)
        if raw_value is None:
            flag = _as_flag(token)
            if flag is None:
                self._store(_normalize(token), flag=True)
            elif not flag:
                return False
            return True
        name = _normalize(key)
        value = _as_flag(raw_value)
        if not name or value is None:
            self.malformed.add(token)
            return True
        self._store(name, flag=value)
        return True

    def _store(self, name: str, *, flag: bool) -> None:
        """Record a syntactically valid override for ``name``."""
        if name in INSIDERS_FEATURES:
            self.features[name] = flag
        else:
            self.unknown.add(name)

    def build(self) -> InsidersConfig:
        """Freeze the accumulated state into an :class:`InsidersConfig`."""
        return InsidersConfig(
            enabled=self.enabled,
            features=self.features,
            unknown_keys=frozenset(self.unknown),
            malformed=frozenset(self.malformed),
        )


def parse_insiders(raw: str | None, *, max_length: int = 4096) -> InsidersConfig:
    """Parse an ``X-MCP-Insiders`` header value into an :class:`InsidersConfig`.

    Args:
        raw: The raw header value, or ``None`` when the header is absent.
        max_length: Largest accepted header length. Anything longer is treated
            as disabled and recorded in ``malformed``.

    Returns:
        The parsed configuration. Invalid entries are recorded in
        ``unknown_keys`` / ``malformed`` and otherwise ignored.
    """
    if raw is None:
        return InsidersConfig.disabled()
    if len(raw) > max_length:
        return InsidersConfig(malformed=frozenset({"header-too-long"}))
    value = raw.strip()
    if not value:
        return InsidersConfig.disabled()

    state = _Accumulator()
    for entry in value.split(","):
        token = entry.strip()
        if not token:
            continue
        if not state.feed(token):
            return InsidersConfig.disabled()
    return state.build()


__all__ = ["INSIDERS_HEADER", "InsidersConfig", "parse_insiders"]
