#!/usr/bin/env python3
"""Container entrypoint for NovelAI Image MCP smoke tests.

The script verifies the production image boots cleanly: it imports the
package, instantiates the MCP server, registers every tool against a
recording stub (without making real HTTP calls), and writes a JUnit-style
XML report to ``/app/smoke-test-results.xml`` (override with
``SMOKE_TEST_RESULTS_XML``).

Designed to run with ``SMOKE_TEST=true`` (set as a Docker build-arg in
``Dockerfile``). The CI workflow ``.github/workflows/ci.yml`` invokes the
image with that flag and an inert ``NOVELAI_TOKEN`` to avoid hitting the
real NovelAI API.
"""

from __future__ import annotations

import logging
import os
import sys
import time
import traceback
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

# Ensure the source tree is importable both in the container (PYTHONPATH=/app)
# and when running the script from the repository root.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

_LOGGER = logging.getLogger("smoke-test")


def _init_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )


class _RecordingMCPServer:
    """Minimal MCPServer stub that records ``@mcp.tool()`` registrations.

    Mirrors the ``RecordingMCPServer`` used by the test suite (see
    ``tests/_helpers.py``): the real ``MCPServer.tool`` decorator returns
    the original function unchanged after registering it, so the recording
    stub mimics that contract while exposing each tool under its function
    name for inspection.
    """

    def __init__(self) -> None:
        self.tools: dict[str, object] = {}

    def tool(self, **_kwargs: object) -> object:
        def decorator(fn: object) -> object:
            assert hasattr(fn, "__name__"), "tool decorator received a nameless callable"
            self.tools[fn.__name__] = fn  # type: ignore[reportGeneralTypeIssues]
            return fn

        return decorator


async def _check_import() -> None:
    """The package must import cleanly under the production environment."""
    import novelai_image_mcp

    assert novelai_image_mcp.__version__, "novelai_image_mcp.__version__ is falsy"


async def _check_settings_instantiate() -> None:
    """Settings models load from environment without raising.

    With ``NOVELAI_TOKEN=pst-smoke-test`` set by the CI entrypoint, the
    ``has_credentials()`` guard should pass.
    """
    from novelai_image_mcp.settings import get_novelai_settings

    settings = get_novelai_settings()
    assert settings.has_credentials(), "smoke-test credentials are not set"


async def _check_tool_registration() -> None:
    """Every tool group must register against an MCPServer without errors.

    Uses the recording stub so we don't actually start the MCP server (which
    would block on stdio). The check confirms that the tool decorators, type
    annotations, and registration logic are sound at import time.
    """
    from novelai_image_mcp.tools import register_all

    mcp = _RecordingMCPServer()
    register_all(mcp)

    expected_tools = {
        # generation
        "generate_image",
        "image_to_image",
        "inpaint",
        # enhance
        "upscale_image",
        "director_tool",
        "annotate_image",
        # tags
        "suggest_tags",
        "encode_vibe",
        # account
        "get_subscription",
        "get_user_data",
        "estimate_anlas_cost",
    }
    missing = expected_tools - set(mcp.tools)
    assert not missing, f"missing tool registrations: {sorted(missing)}"


async def _check_cli_app_loads() -> None:
    """The typer CLI must construct without runtime errors."""
    from novelai_image_mcp.cli import app as cli_app

    # Typer's `app` is a Typer instance; touching it ensures import-time
    # side effects (decorator evaluation) succeed.
    assert cli_app is not None, "CLI app did not construct"


_CHECKS: list[tuple[str, object]] = [
    ("test_import", _check_import),
    ("test_settings_instantiate", _check_settings_instantiate),
    ("test_tool_registration", _check_tool_registration),
    ("test_cli_app_loads", _check_cli_app_loads),
]


async def _run_checks() -> list[dict[str, object]]:
    """Run each smoke check, collecting pass/fail metadata."""
    import asyncio

    results: list[dict[str, object]] = []
    for name, check in _CHECKS:
        start = time.monotonic()
        error: Exception | None = None
        try:
            await check()  # type: ignore[misc]
        except Exception as exc:  # noqa: BLE001
            error = exc
        duration = time.monotonic() - start
        results.append({
            "name": name,
            "error": error,
            "duration": duration,
        })
    return results


def _write_junit_xml(results: list[dict[str, object]], output_path: Path) -> None:
    """Write a minimal JUnit XML report with one testcase per smoke check."""
    failures = sum(1 for result in results if result["error"] is not None)
    testsuites = Element("testsuites")
    testsuite = SubElement(
        testsuites,
        "testsuite",
        {
            "name": "smoke-tests",
            "tests": str(len(results)),
            "failures": str(failures),
        },
    )

    for result in results:
        error = result["error"]
        duration = float(result["duration"])
        testcase = SubElement(
            testsuite,
            "testcase",
            {
                "name": str(result["name"]),
                "time": f"{duration:.3f}",
            },
        )
        if error is not None:
            failure = SubElement(
                testcase,
                "failure",
                {"message": f"{type(error).__name__}: {error}"},
            )
            failure.text = "".join(traceback.format_exception(error))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        tostring(testsuites, encoding="unicode"),
        encoding="utf-8",
    )


def _ensure_smoke_env() -> None:
    """Provide minimal credentials if the env file is empty."""
    if not os.environ.get("NOVELAI_TOKEN"):
        os.environ["NOVELAI_TOKEN"] = "pst-smoke-test"


async def _async_main() -> int:
    """Run the smoke-test workflow and return an exit code."""
    output_path = Path(
        os.environ.get("SMOKE_TEST_RESULTS_XML", "/app/smoke-test-results.xml")
    )
    results = await _run_checks()
    _write_junit_xml(results, output_path)

    failed = [result for result in results if result["error"] is not None]
    if failed:
        for result in failed:
            error = result["error"]
            _LOGGER.error("FAIL %s: %s", result["name"], error)
        return 1

    _LOGGER.info("All %d smoke check(s) passed", len(results))
    return 0


def main() -> int:
    """Synchronous wrapper around the async smoke-test workflow."""
    _init_logging()
    _ensure_smoke_env()

    import asyncio

    return asyncio.run(_async_main())


if __name__ == "__main__":
    sys.exit(main())
