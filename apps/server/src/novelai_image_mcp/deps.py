"""Dependency-injected values shared by the MCP components.

FastMCP resolves parameters declared as ``Depends(get_...)`` (or annotated with
``Context``) when the component runs, and hides them from the component's input
schema. Tools, resources and prompts therefore declare exactly what they need
instead of digging into the request context themselves. ``AppContext`` is the
single value the server lifespan yields, and every provider reads from it.

The insiders/routing providers read the *request headers* instead: an HTTP
client opts into the experimental surface with the configured insiders header
and describes its route with the configured routing headers. Over stdio there is
no HTTP request at all, so the header lookup resolves to an empty mapping, the
insiders surface stays disabled and behaviour is unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from fastmcp.dependencies import CurrentContext, CurrentHeaders, Depends
from fastmcp.server.dependencies import get_context, get_http_request

from .features import MODEL_ROUTING, resolve_features
from .insiders import InsidersConfig, parse_insiders
from .routing import RoutingContext, resolve_routing
from .settings import get_mcp_settings

if TYPE_CHECKING:
    from fastmcp import Context

    from .nai import NovelAIClient
    from .settings import NovelAISettings


@dataclass
class AppContext:
    """Shared state yielded by the lifespan to every MCP request."""

    client: NovelAIClient
    settings: NovelAISettings


def get_app_context(ctx: Context = CurrentContext()) -> AppContext:
    """Return the lifespan ``AppContext`` for the current request."""
    value = ctx.lifespan_context
    if not isinstance(value, AppContext):  # pragma: no cover - defensive
        raise TypeError("the server lifespan did not yield an AppContext")
    return value


def get_client(app: AppContext = Depends(get_app_context)) -> NovelAIClient:
    """Return the shared ``NovelAIClient`` for the current request."""
    return app.client


def get_insiders_config(
    headers: dict[str, str] = CurrentHeaders(),
) -> InsidersConfig:
    """Parse the insiders opt-in header for the current request.

    ``CurrentHeaders()`` resolves to an empty mapping when there is no HTTP
    request, so over stdio the insiders surface stays disabled and behaviour is
    unchanged.
    """
    name = get_mcp_settings().insiders_header.strip().lower()
    return parse_insiders(headers.get(name))


def _effective_features(config: InsidersConfig) -> frozenset[str]:
    """Apply the operator-level kill switch to a parsed insiders config."""
    return resolve_features(
        config,
        force_disabled=get_mcp_settings().insiders_disabled_features,
    )


def get_effective_features(
    config: InsidersConfig = Depends(get_insiders_config),
) -> frozenset[str]:
    """Return the names of the features active for this request.

    The header decides per request; ``MCP_INSIDERS_DISABLED_FEATURES`` is the
    operator kill switch and wins over anything a client sends.
    """
    return _effective_features(config)


def get_route_scoped_output() -> bool:
    """True when generated images belong under a per-route subdirectory."""
    return get_mcp_settings().route_scoped_output


def _client_info_name() -> str | None:
    """Return the MCP client's advertised name, or ``None`` when unavailable.

    ``get_context()`` raises outside a request, ``Context.session`` raises until
    the MCP session exists, and ``client_params`` is ``None`` for some
    transports. None of those is an error for routing, so every case degrades to
    ``None``.
    """
    try:
        params = get_context().session.client_params
    except RuntimeError:
        return None
    if params is None:
        return None
    return params.client_info.name or None


def _has_http_request() -> bool:
    """True when the current call arrived over HTTP rather than stdio."""
    try:
        get_http_request()
    except RuntimeError:
        return False
    return True


def get_routing_context(
    headers: dict[str, str] = CurrentHeaders(),
) -> RoutingContext:
    """Resolve the routing context for the current request.

    Routing is attempted only when the ``model-routing`` feature is active;
    otherwise the disabled context is returned and every routing field stays
    ``None``.
    """
    settings = get_mcp_settings()
    config = get_insiders_config(headers)
    return resolve_routing(
        headers,
        enabled=MODEL_ROUTING in _effective_features(config),
        model_headers=settings.model_headers,
        agent_headers=settings.agent_headers,
        client_headers=settings.client_headers,
        client_info_name=_client_info_name(),
        has_http_request=_has_http_request(),
    )


__all__ = [
    "AppContext",
    "get_app_context",
    "get_client",
    "get_effective_features",
    "get_insiders_config",
    "get_route_scoped_output",
    "get_routing_context",
]
