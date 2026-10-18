"""Request routing derived from the MCP client's routing headers.

A client may advertise which model, agent, client and session a request belongs
to through headers. This module turns those headers into a
:class:`RoutingContext` -- a value that is *only* the result of parsing and
whitelisting, never a filesystem path: every route string passes through
:func:`sanitize_route` before it can be used as a directory name, and the
header snapshot kept for auditing is stripped of every credential-bearing
header. Nothing here performs I/O.

Security notes:

* Header values are attacker-controlled. ``route`` is restricted to
  ``[A-Za-z0-9._-]{1,64}`` and values made only of dots (``.``, ``..``) are
  rejected, so a route can never traverse out of its directory.
* ``recorded_headers`` never contains ``authorization``, ``cookie``,
  ``set-cookie``, ``proxy-authorization`` or any ``*-token`` / ``*-secret`` /
  ``*-password`` / ``*-key`` / ``*-credential`` header, and is capped so a
  hostile client cannot blow up the audit record.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

#: Route used when no usable routing information is available.
ROUTE_UNKNOWN = "unknown"

#: Route used for the local stdio transport, which has no HTTP request.
ROUTE_STDIO = "stdio"

#: Longest accepted route string; longer values are rejected outright.
MAX_ROUTE_LENGTH = 64

#: Largest number of headers kept in ``recorded_headers``.
MAX_RECORDED_HEADERS = 64

#: Longest header value kept in ``recorded_headers``.
MAX_RECORDED_VALUE_LENGTH = 512

#: Whitelist for route values: no separators, no spaces, no non-ASCII.
_ROUTE_PATTERN = re.compile(r"[A-Za-z0-9._-]{1,64}")

#: Header names that must never be recorded, after normalisation.
_SENSITIVE_NAMES = frozenset({
    "authorization",
    "cookie",
    "credential",
    "credentials",
    "key",
    "passwd",
    "password",
    "proxy-authorization",
    "secret",
    "set-cookie",
    "token",
})

#: Header-name suffixes that must never be recorded.
_SENSITIVE_SUFFIXES = (
    "-credential",
    "-credentials",
    "-key",
    "-passwd",
    "-password",
    "-secret",
    "-token",
)


def _normalize_name(name: str) -> str:
    """Return a header name lower-cased with ``_`` folded to ``-``."""
    return name.strip().lower().replace("_", "-")


def _clean(value: str | None) -> str | None:
    """Return ``value`` stripped, or ``None`` when it is absent or empty."""
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _is_sensitive(name: str) -> bool:
    """True when a normalised header name carries a credential."""
    return name in _SENSITIVE_NAMES or name.endswith(_SENSITIVE_SUFFIXES)


def sanitize_route(value: str) -> str:
    """Return ``value`` if it is a safe directory name, else ``"unknown"``.

    Accepts only ``[A-Za-z0-9._-]{1,64}``. Path separators, whitespace,
    non-ASCII text, empty strings, over-long values and dot-only values
    (``.`` / ``..``, i.e. directory traversal) are all rejected.
    """
    candidate = value.strip()
    if not candidate or len(candidate) > MAX_ROUTE_LENGTH:
        return ROUTE_UNKNOWN
    if _ROUTE_PATTERN.fullmatch(candidate) is None:
        return ROUTE_UNKNOWN
    if not candidate.strip("."):
        return ROUTE_UNKNOWN
    return candidate


@dataclass(frozen=True)
class RoutingContext:
    """Routing decision for a single request.

    ``enabled`` mirrors the insiders header: when it is ``False`` no routing
    was attempted, so every extracted field is ``None`` and ``route`` is
    :data:`ROUTE_UNKNOWN`. ``transport`` always reflects the real transport,
    and ``recorded_headers`` is the sanitised header snapshot used for audit.
    """

    enabled: bool
    route: str
    model: str | None = None
    agent: str | None = None
    client: str | None = None
    session: str | None = None
    transport: Literal["http", "stdio"] = "http"
    recorded_headers: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def disabled(
        cls, *, transport: Literal["http", "stdio"] = "http"
    ) -> RoutingContext:
        """Return the context used when routing is switched off.

        ``transport`` still carries the real transport so audit output stays
        truthful; the caller supplies it rather than relying on the default.
        """
        return cls(enabled=False, route=ROUTE_UNKNOWN, transport=transport)


def _recorded(headers: Mapping[str, str]) -> dict[str, str]:
    """Return the sanitised, capped snapshot of ``headers`` for auditing."""
    recorded: dict[str, str] = {}
    for name, value in headers.items():
        key = _normalize_name(name)
        if not key or _is_sensitive(key):
            continue
        recorded[key] = value[:MAX_RECORDED_VALUE_LENGTH]
    if len(recorded) > MAX_RECORDED_HEADERS:
        kept = sorted(recorded)[:MAX_RECORDED_HEADERS]
        recorded = {name: recorded[name] for name in kept}
    return recorded


def _first_value(lookup: Mapping[str, str], candidates: Sequence[str]) -> str | None:
    """Return the first non-empty value among ``candidates``, else ``None``."""
    for name in candidates:
        value = _clean(lookup.get(_normalize_name(name)))
        if value is not None:
            return value
    return None


# The parameter surface is the fixed routing contract every caller shares;
# collapsing it into a request object would hide the individual header groups.
def resolve_routing(  # noqa: PLR0913
    headers: Mapping[str, str],
    *,
    enabled: bool,
    model_headers: Sequence[str],
    agent_headers: Sequence[str],
    client_headers: Sequence[str],
    client_info_name: str | None = None,
    has_http_request: bool = True,
) -> RoutingContext:
    """Resolve the routing context for one request.

    ``model_headers`` / ``agent_headers`` / ``client_headers`` are ordered
    candidate lists: the first header with a non-empty value supplies the
    corresponding field, and ``agent_headers`` then ``client_headers`` also
    supply the route. ``session`` is taken from the first non-empty
    ``client_headers`` entry whose name contains ``session``. Header lookup is
    case-insensitive (and treats ``_`` as ``-``).

    When ``enabled`` is false no field is extracted at all: the request gets
    the disabled context, but still carries the real transport.
    """
    transport: Literal["http", "stdio"] = "http" if has_http_request else "stdio"
    if not enabled:
        return RoutingContext.disabled(transport=transport)

    lookup = {_normalize_name(name): value for name, value in headers.items()}
    session_headers = [
        name for name in client_headers if "session" in _normalize_name(name)
    ]
    candidate = (
        _first_value(lookup, agent_headers)
        or _first_value(lookup, client_headers)
        or _clean(client_info_name)
    )
    if candidate is None:
        route = ROUTE_STDIO if not has_http_request else ROUTE_UNKNOWN
    else:
        route = sanitize_route(candidate)

    return RoutingContext(
        enabled=True,
        route=route,
        model=_first_value(lookup, model_headers),
        agent=_first_value(lookup, agent_headers),
        client=_first_value(lookup, client_headers),
        session=_first_value(lookup, session_headers),
        transport=transport,
        recorded_headers=_recorded(headers),
    )


__all__ = [
    "MAX_RECORDED_HEADERS",
    "MAX_RECORDED_VALUE_LENGTH",
    "MAX_ROUTE_LENGTH",
    "ROUTE_STDIO",
    "ROUTE_UNKNOWN",
    "RoutingContext",
    "resolve_routing",
    "sanitize_route",
]
