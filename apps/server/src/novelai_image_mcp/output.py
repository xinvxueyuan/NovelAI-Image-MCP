"""Persist generated images to the configured output directory.

Image-returning MCP tools save the PNG bytes to ``NOVELAI_OUTPUT_DIR`` and
return the resolved path alongside the base64 ``Image`` content block so the
agent can both view the image and locate the file on disk.

When model routing is active *and* the operator kept route-scoped output on,
images of a routed request land in a per-route subdirectory instead:
``<output_dir>/<sanitize_route(route)>/``. The subdirectory name comes from
:func:~.routing.sanitize_route, so a hostile route can never escape the output
directory, and with routing off (or route scoping off) every path is exactly the
one the server produced before routing existed.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import re
import secrets

from .routing import RoutingContext, sanitize_route

#: Plain generated-image filenames only: no separators, no traversal, no
#: hidden files. ``"[.]png"`` matches a literal dot (no backslash escape).
_PNG_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*[.]png")


def save_image(
    data: bytes,
    *,
    name: str = "image",
    output_dir: str | Path = "outputs",
) -> Path:
    """Write image bytes to ``output_dir`` and return the resolved path.

    The filename is ``<name>-<utc-timestamp>-<6-hex>.png`` so repeated calls
    never collide. Parent directories are created on demand.
    """
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = secrets.token_hex(3)
    path = directory / f"{name}-{stamp}-{suffix}.png"
    path.write_bytes(data)
    return path


def resolve_output_path(name: str, *, output_dir: str | Path = "outputs") -> Path:
    """Resolve ``name`` to an existing PNG inside ``output_dir``.

    Raises ``ValueError`` when the name is not a plain PNG filename or when it
    resolves outside the output directory, and ``FileNotFoundError`` when no
    such image exists. Used by the ``novelai://outputs/{name}`` resource.
    """
    if not _PNG_NAME_RE.fullmatch(name):
        raise ValueError(
            f"invalid image name {name!r}: expected a plain *.png filename"
        )
    directory = Path(output_dir).resolve()
    path = (directory / name).resolve()
    if path.parent != directory:
        raise ValueError(f"invalid image name {name!r}: escapes the output directory")
    if not path.is_file():
        raise FileNotFoundError(f"no such generated image: {name}")
    return path


def route_output_dir(
    output_dir: str | Path,
    routing: RoutingContext,
    *,
    route_scoped: bool,
) -> Path:
    """Return the directory a request's generated images belong in.

    Without an active route -- routing switched off, or ``route_scoped`` false --
    the configured output directory is returned unchanged, which is the
    pre-routing behaviour. With one, the result is
    ``<output_dir>/<sanitize_route(route)>/``. The route is sanitised here as
    well as when the routing context was built, so even a hand-built context
    cannot contribute a path separator, a traversal or an empty name.
    """
    if not (routing.enabled and route_scoped):
        return Path(output_dir)
    return Path(output_dir) / sanitize_route(routing.route)


__all__ = ["resolve_output_path", "route_output_dir", "save_image"]
