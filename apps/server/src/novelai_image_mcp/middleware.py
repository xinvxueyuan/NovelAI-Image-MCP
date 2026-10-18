"""Cross-cutting middleware for the NovelAI MCP server.

``ToolCallLoggingMiddleware`` observes every tool call: it times it, writes a
line to a route-derived logger, appends one record to the append-only audit
trail while ``model-routing`` is active, and gates the experimental tool
surface. It never rewrites a result and never swallows an exception.

The gate is deliberately two-sided. ``on_list_tools`` hides insiders-tagged
tools from a client that has not opted in, and ``on_call_tool`` rejects a call
to one *by name*, so guessing the name is not a way around the listing filter.

No tool shipped today carries the tag. The mechanism is opt-in by design:
tagging an existing tool would remove it from every client that does not send
the insiders header, which would break the promise that a request without the
header behaves exactly as it did before.
"""

from __future__ import annotations

import logging
import sys
import time
from typing import TYPE_CHECKING, Any

from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_headers
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext

from .audit import append_record, artifact_paths, build_record, resolve_audit_path
from .deps import get_effective_features, get_routing_context
from .features import EXPERIMENTAL_TOOLS, MODEL_ROUTING
from .insiders import InsidersConfig, parse_insiders
from .settings import get_mcp_settings, get_novelai_settings

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from fastmcp.tools import Tool, ToolResult
    import mcp.types as mt

    from .routing import RoutingContext

logger = logging.getLogger(__name__)

#: Tag that marks a tool as part of the experimental insiders surface.
INSIDERS_TAG = "insiders"

#: Prefix of the per-route audit loggers (`novelai_image_mcp.audit.<route>`).
AUDIT_LOGGER_PREFIX = "novelai_image_mcp.audit"


def _request_insiders() -> tuple[dict[str, str], InsidersConfig, frozenset[str]]:
    """Return the request headers, the parsed insiders config and its features.

    ``get_http_headers()`` never raises and returns an empty mapping when there
    is no HTTP request, so over stdio the config is disabled and every feature
    keeps its default.

    Middleware is *not* a dependency-injection call site. ``get_effective_features``
    and ``get_routing_context`` declare their parameter default as
    ``CurrentHeaders()``, which is a dependency *marker* rather than a value:
    calling them with no argument would hand the unresolved marker to the body
    instead of a header mapping. The middleware therefore resolves the headers
    itself and passes them explicitly, which also keeps both calls on one
    consistent snapshot of the request.
    """
    headers = get_http_headers()
    settings = get_mcp_settings()
    config = parse_insiders(headers.get(settings.insiders_header.strip().lower()))
    return headers, config, get_effective_features(config)


async def _is_insiders_tool(context: MiddlewareContext[Any], name: str) -> bool:
    """True when the registered tool ``name`` carries the insiders tag."""
    fastmcp_context = context.fastmcp_context
    if fastmcp_context is None:  # pragma: no cover - defensive
        return False
    try:
        tool = await fastmcp_context.fastmcp.get_tool(name)
    except RuntimeError:  # pragma: no cover - defensive
        return False
    return tool is not None and INSIDERS_TAG in tool.tags


def _arguments(context: MiddlewareContext[Any]) -> Mapping[str, Any]:
    """Return the call's arguments, or an empty mapping when there are none."""
    arguments = getattr(context.message, "arguments", None)
    if not isinstance(arguments, dict):
        return {}
    return {str(key): value for key, value in arguments.items()}


# Every record field is a separate keyword argument: the audit schema is the
# contract, and a request object would hide which fields a caller supplied.
def _audit(  # noqa: PLR0913
    *,
    name: str,
    routing: RoutingContext,
    config: InsidersConfig,
    features: frozenset[str],
    outcome: str,
    elapsed: float,
    artifacts: list[str],
    arguments: Mapping[str, Any],
) -> None:
    """Log the routed summary and, while routing is active, append an audit row."""
    logging.getLogger(f"{AUDIT_LOGGER_PREFIX}.{routing.route}").info(
        "tool=%s route=%s model=%s agent=%s client=%s session=%s "
        "duration_ms=%.3f outcome=%s features=%s",
        name,
        routing.route,
        routing.model,
        routing.agent,
        routing.client,
        routing.session,
        elapsed * 1000,
        outcome,
        ",".join(sorted(features)) or "-",
    )

    if MODEL_ROUTING not in features:
        return
    settings = get_mcp_settings()
    audit_log_path = settings.audit_log_path
    path = resolve_audit_path(
        audit_log_path=audit_log_path,
        output_dir=None if audit_log_path else get_novelai_settings().output_dir,
    )
    append_record(
        build_record(
            routing=routing,
            tool=name,
            duration_ms=elapsed * 1000,
            outcome=outcome,
            features=features,
            artifacts=artifacts,
            arguments=arguments,
            unknown_keys=config.unknown_keys,
            malformed=config.malformed,
        ),
        path=path,
    )


class ToolCallLoggingMiddleware(Middleware):
    """Log every tool call, audit routed calls, and gate experimental tools.

    Middleware keeps these concerns out of the tool bodies: the hooks observe
    the call, never rewrite the result, and never swallow an exception.
    """

    async def on_list_tools(
        self,
        context: MiddlewareContext[mt.ListToolsRequest],
        call_next: CallNext[mt.ListToolsRequest, Sequence[Tool]],
    ) -> Sequence[Tool]:
        """Hide insiders-tagged tools unless the client opted in."""
        tools = await call_next(context)
        _headers, _config, features = _request_insiders()
        if EXPERIMENTAL_TOOLS in features:
            return tools
        return [tool for tool in tools if INSIDERS_TAG not in tool.tags]

    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next: CallNext[mt.CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        """Time the call, audit it, and refuse a gated tool called by name."""
        name = context.message.name
        started = time.perf_counter()
        logger.info("tool call started: %s", name)

        # ``headers`` is passed explicitly: see ``_request_insiders`` for why the
        # ``CurrentHeaders()`` default cannot be relied on outside DI.
        headers, config, features = _request_insiders()
        routing = get_routing_context(headers)

        artifacts: list[str] = []
        rejected = False
        try:
            if EXPERIMENTAL_TOOLS not in features and await _is_insiders_tool(
                context, name
            ):
                rejected = True
                logger.warning("tool call rejected (experimental): %s", name)
                # The message is the caller's only clue about how to opt in.
                raise ToolError(  # noqa: TRY003
                    f"tool {name!r} is experimental and is not enabled for this "
                    "client; send the insiders opt-in header to enable it."
                )
            tool_result = await call_next(context)
            artifacts = artifact_paths(tool_result)
            return tool_result
        finally:
            elapsed = time.perf_counter() - started
            logger.info("tool call finished: %s (%.3fs)", name, elapsed)
            if rejected:
                outcome = "rejected"
            else:
                outcome = "error" if sys.exc_info()[0] is not None else "ok"
            _audit(
                name=name,
                routing=routing,
                config=config,
                features=features,
                outcome=outcome,
                elapsed=elapsed,
                artifacts=artifacts,
                arguments=_arguments(context),
            )


__all__ = ["AUDIT_LOGGER_PREFIX", "INSIDERS_TAG", "ToolCallLoggingMiddleware"]
