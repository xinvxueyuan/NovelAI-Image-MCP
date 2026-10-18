"""Optional bearer-token authentication for the HTTP transport.

The stdio transport is a local, single-client channel and needs no
authentication. When the server is exposed over HTTP (containers, remote
deployments, shared hosts) an operator can set `MCP_AUTH_TOKEN` to require a
bearer token: FastMCP then validates the `Authorization` header before any
MCP request is served. Without the setting the server behaves exactly as
before, so this stays opt-in and backward compatible.

`MCP_AUTH_TOKEN` keeps its original meaning: one static token whose client id
is :data:`CLIENT_ID`. `MCP_ROUTE_TOKENS` adds *route-bound* tokens on top --
a JSON object (`{"<route>": "<token>"}`, since `pydantic-settings` parses
list/dict values as JSON only). A route token authenticates as its route and is
rejected when the same request declares a *different* route through the routing
headers. Both settings may be combined: the static token never takes part in
route checking, so its semantics are unchanged. When neither is configured,
:func:`build_auth` returns `None` and no auth middleware is installed.

Route mismatch is handled in this module, in the single place that sees both the
presented token and the request headers. A mismatch makes the verifier return
`None`, which the bearer middleware turns into `401` with a
`WWW-Authenticate` challenge; the two routes are recorded with
`logger.warning` so the rejection stays auditable. Nothing is raised here on
purpose: an exception from a verifier surfaces as a 500 instead of a clean
authentication failure. A request without a usable declared route (no routing
header, or a header that sanitises to `unknown`) is accepted and attributed to
the token's own route; only two *different*, both-present routes fail closed.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from fastmcp.server.auth.providers.jwt import StaticTokenVerifier
from fastmcp.server.dependencies import get_http_headers

from .routing import ROUTE_UNKNOWN, resolve_routing, sanitize_route

if TYPE_CHECKING:
    from collections.abc import Mapping

    from fastmcp.server.auth import AccessToken, TokenVerifier

    from .settings import MCPServerSettings

logger = logging.getLogger(__name__)

#: Identity reported to the server for the single configured token.
CLIENT_ID = "novelai-image-mcp"


def _route_bindings(
    settings: MCPServerSettings, *, static_token: str
) -> dict[str, str]:
    """Return the usable `{token: route}` bindings from `route_tokens`.

    Iteration is sorted by route so the result is deterministic, and entries are
    dropped -- with a warning, never silently -- when they cannot be honoured:

    * an empty route token would authenticate nobody, so it is skipped;
    * a route token equal to `MCP_AUTH_TOKEN` would make one secret mean two
      identities; the static token wins and keeps its documented semantics;
    * a route name that does not pass :func:`~.routing.sanitize_route` cannot
      be compared against a declared route, so the token is not registered at
      all (fail closed: it never authenticates);
    * a token bound to two routes is ambiguous, so the first route wins.
    """
    configured = settings.route_tokens or {}
    bindings: dict[str, str] = {}
    for route in sorted(configured):
        token = configured.get(route, "").strip()
        safe_route = sanitize_route(route)
        if not token:
            logger.warning("ignoring empty route token for route %r", route)
            continue
        if token == static_token:
            logger.warning(
                "route %r reuses MCP_AUTH_TOKEN; keeping its static identity",
                route,
            )
            continue
        if safe_route == ROUTE_UNKNOWN:
            logger.warning("ignoring route token for unusable route %r", route)
            continue
        if token in bindings:
            logger.warning(
                "duplicate route token for routes %r and %r; keeping %r",
                bindings[token],
                route,
                bindings[token],
            )
            continue
        bindings[token] = safe_route
    return bindings


class RouteTokenVerifier(StaticTokenVerifier):
    """Static tokens, plus fail-closed route checking for route-bound tokens.

    Tokens registered in `route_tokens` must not disagree with the route the
    request declares through the routing headers; every other token (the static
    `MCP_AUTH_TOKEN`) is returned untouched, exactly as before.
    """

    def __init__(
        self,
        tokens: dict[str, dict[str, Any]],
        *,
        routes: Mapping[str, str],
        settings: MCPServerSettings,
    ) -> None:
        super().__init__(tokens=tokens)
        self._routes = dict(routes)
        self._settings = settings

    async def verify_token(self, token: str) -> AccessToken | None:
        """Return the token's access rights, or `None` to reject the request."""
        access = await super().verify_token(token)
        if access is None:
            return None
        expected = self._routes.get(token)
        if expected is None:
            # Not a route token: the static token's semantics are untouched.
            return access
        declared = self._declared_route()
        if declared in (ROUTE_UNKNOWN, expected):
            # No usable declared route: the token's own route is the route.
            return access
        logger.warning(
            "route token mismatch: token route %r != declared header route %r",
            expected,
            declared,
        )
        return None

    def _declared_route(self) -> str:
        """Return the route the request declares through its routing headers."""
        headers = get_http_headers()
        if not headers:
            return ROUTE_UNKNOWN
        settings = self._settings
        return resolve_routing(
            headers,
            enabled=True,
            model_headers=settings.model_headers,
            agent_headers=settings.agent_headers,
            client_headers=settings.client_headers,
            client_info_name=None,
            has_http_request=True,
        ).route


def build_auth(settings: MCPServerSettings) -> TokenVerifier | None:
    """Return a bearer-token verifier, or `None` when auth is not configured.

    `StaticTokenVerifier` compares the presented token against a fixed
    mapping; it is the documented FastMCP pattern for operator-managed static
    tokens. Rotate the token by changing `MCP_AUTH_TOKEN` and restarting.

    `MCP_ROUTE_TOKENS` entries are merged into the same mapping, each with
    `client_id` set to its route, and additionally checked against the route
    the request declares (see :class:`RouteTokenVerifier`). With no
    `MCP_AUTH_TOKEN` and no usable route token the function returns `None`,
    which leaves the transport exactly as it is today.
    """
    static_token = (settings.auth_token or "").strip()
    routes = _route_bindings(settings, static_token=static_token)
    if not static_token and not routes:
        return None
    tokens: dict[str, dict[str, Any]] = {}
    if static_token:
        tokens[static_token] = {"client_id": CLIENT_ID, "scopes": []}
    for token, route in routes.items():
        tokens[token] = {"client_id": route, "scopes": []}
    return RouteTokenVerifier(tokens, routes=routes, settings=settings)


__all__ = ["CLIENT_ID", "RouteTokenVerifier", "build_auth"]
