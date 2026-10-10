#!/usr/bin/env python3
"""Container entrypoint for NovelAI Image MCP smoke tests.

The script verifies the production image boots cleanly: it imports the
package, asks the real server instance for its registered components (without
starting a transport or making HTTP calls), and writes a JUnit-style XML
report to `/app/smoke-test-results.xml` (override with
`SMOKE_TEST_RESULTS_XML`).

The checks run through the FastMCP server API (`list_tools`,
`list_prompts`, `list_resources`, `list_resource_templates`) rather than
a recording stub, so a registration or schema regression fails the image
build instead of only the unit suite.

Designed to run with `SMOKE_TEST=true` (set as a Docker build-arg in
`Dockerfile`). The CI workflow `.github/workflows/ci.yml` invokes the
image with that flag and an inert `NOVELAI_TOKEN` to avoid hitting the real
NovelAI API.
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
import sys
import time
import traceback
from xml.etree.ElementTree import Element, SubElement, tostring

# Ensure the source tree is importable both in the container (PYTHONPATH=/app)
# and when running the script from the repository root.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

_LOGGER = logging.getLogger("smoke-test")

_EXPECTED_TOOLS = {
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
_EXPECTED_PROMPTS = {"novelai_image_workflow", "novelai_prompt_writer"}
_EXPECTED_RESOURCES = {
    "novelai://defaults",
    "novelai://models",
    "novelai://samplers",
}
_EXPECTED_TEMPLATES = {"novelai://outputs/{name}"}


def _init_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )


async def _check_import() -> None:
    """The package must import cleanly under the production environment."""
    import novelai_image_mcp

    assert novelai_image_mcp.__version__, "novelai_image_mcp.__version__ is falsy"


async def _check_settings_instantiate() -> None:
    """Settings models load from environment without raising.

    With `NOVELAI_TOKEN=pst-smoke-test` set by the CI entrypoint, the
    `has_credentials()` guard should pass.
    """
    from novelai_image_mcp.settings import get_novelai_settings

    settings = get_novelai_settings()
    assert settings.has_credentials(), "smoke-test credentials are not set"


async def _check_server_metadata() -> None:
    """The server reports the package version and faces the same defaults."""
    import novelai_image_mcp
    from novelai_image_mcp.server import mcp

    assert mcp.name == "novelai-image", f"unexpected server name: {mcp.name}"
    assert mcp.version == novelai_image_mcp.__version__, (
        f"server version {mcp.version!r} does not match the package version "
        f"{novelai_image_mcp.__version__!r}"
    )
    assert mcp.instructions, "the server publishes no instructions"


async def _check_components() -> None:
    """Every tool, prompt and resource must be registered on the server."""
    from novelai_image_mcp.server import mcp

    tools = {tool.name for tool in await mcp.list_tools()}
    missing_tools = _EXPECTED_TOOLS - tools
    assert not missing_tools, f"missing tool registrations: {sorted(missing_tools)}"

    prompts = {prompt.name for prompt in await mcp.list_prompts()}
    missing_prompts = _EXPECTED_PROMPTS - prompts
    assert not missing_prompts, f"missing prompts: {sorted(missing_prompts)}"

    resources = {str(resource.uri) for resource in await mcp.list_resources()}
    missing_resources = _EXPECTED_RESOURCES - resources
    assert not missing_resources, f"missing resources: {sorted(missing_resources)}"

    templates = {
        template.uri_template for template in await mcp.list_resource_templates()
    }
    missing_templates = _EXPECTED_TEMPLATES - templates
    assert not missing_templates, (
        f"missing resource templates: {sorted(missing_templates)}"
    )


async def _check_cli_app_loads() -> None:
    """The typer CLI must construct without runtime errors."""
    from novelai_image_mcp.cli import app as cli_app

    # Typer's `app` is a Typer instance; touching it ensures import-time
    # side effects (decorator evaluation) succeed.
    assert cli_app is not None, "CLI app did not construct"


_CHECKS: list[tuple[str, object]] = [
    ("test_import", _check_import),
    ("test_settings_instantiate", _check_settings_instantiate),
    ("test_server_metadata", _check_server_metadata),
    ("test_components", _check_components),
    ("test_cli_app_loads", _check_cli_app_loads),
]


async def _run_checks() -> list[dict[str, object]]:
    """Run each smoke check, collecting pass/fail metadata."""
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
    return asyncio.run(_async_main())


if __name__ == "__main__":
    sys.exit(main())
