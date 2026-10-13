#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 NovelAI Image MCP contributors
# SPDX-License-Identifier: MIT
"""Sync the canonical version into every derived manifest, or verify them.

The canonical version lives in ``apps/server/pyproject.toml`` (``[project]
version``). Every other manifest that carries a version is derived from it:

* ``package.json``, ``apps/server/package.json``, ``apps/docs/package.json``
  (top-level ``version``)
* ``server.json`` -- the MCP registry manifest: top-level ``.version``, the
  PyPI package entry's ``version``, and the OCI package entry's ``identifier``
  ``:X.Y.Z`` suffix

Run it locally before tagging (write mode)::

    uv run --directory apps/server poe sync-versions

The release workflow runs the same script with ``--check``, so a tag whose
manifests disagree with ``pyproject.toml`` fails before anything is published.
``--check`` never writes.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

#: Canonical manifest, relative to the repository root.
CANONICAL = "apps/server/pyproject.toml"
#: Node manifests whose top-level ``version`` mirrors the canonical one.
PACKAGE_JSONS = (
    "package.json",
    "apps/server/package.json",
    "apps/docs/package.json",
)
#: MCP registry manifest.
SERVER_JSON = "server.json"

_VERSION_LINE = re.compile(r'^version\s*=\s*"([^"]+)"', re.MULTILINE)
_OCI_TAG = re.compile(r":[^:]+$")


def find_repo_root(start: Path) -> Path:
    """Return the repository root at or above *start*."""
    for candidate in (start, *start.parents):
        if (candidate / CANONICAL).is_file():
            return candidate
    message = f"cannot locate the repository root (no {CANONICAL}) above {start}"
    raise SystemExit(message)


def read_canonical_version(root: Path) -> str:
    """Return the ``[project] version`` from the canonical manifest."""
    text = (root / CANONICAL).read_text(encoding="utf-8")
    match = _VERSION_LINE.search(text)
    if match is None:
        message = f"{CANONICAL} has no top-level version line"
        raise SystemExit(message)
    return match.group(1)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        message = f"{path.name} is not a JSON object"
        raise SystemExit(message)
    return payload


def _store(path: Path, payload: dict[str, Any]) -> None:
    """Write *payload* with the indentation every manifest in this repo uses."""
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _sync_package_json(
    root: Path, relative: str, version: str, *, write: bool
) -> str | None:
    """Return a drift description for one package.json, writing it when asked."""
    path = root / relative
    payload = _load(path)
    current = payload.get("version")
    if current == version:
        return None
    if write:
        payload["version"] = version
        _store(path, payload)
    return f"{relative}: {current!r} -> {version!r}"


def _sync_server_json(root: Path, version: str, *, write: bool) -> list[str]:
    """Return drift descriptions for server.json, writing it when asked."""
    path = root / SERVER_JSON
    payload = _load(path)
    drift: list[str] = []

    if payload.get("version") != version:
        drift.append(
            f"{SERVER_JSON}: .version {payload.get('version')!r} -> {version!r}"
        )
        payload["version"] = version

    packages = payload.get("packages")
    if not isinstance(packages, list):
        message = f"{SERVER_JSON}: .packages must be a list"
        raise SystemExit(message)

    for entry in packages:
        if not isinstance(entry, dict):
            continue
        registry = entry.get("registryType")
        if registry == "pypi" and entry.get("version") != version:
            drift.append(
                f"{SERVER_JSON}: packages[pypi].version {entry.get('version')!r} -> {version!r}"
            )
            entry["version"] = version
        elif registry == "oci":
            identifier = entry.get("identifier")
            if isinstance(identifier, str):
                synced = _OCI_TAG.sub(f":{version}", identifier)
                if synced != identifier:
                    drift.append(
                        f"{SERVER_JSON}: packages[oci].identifier {identifier!r} -> {synced!r}"
                    )
                    entry["identifier"] = synced

    if drift and write:
        _store(path, payload)
    return drift


def collect(root: Path, version: str, *, write: bool) -> list[str]:
    """Sync (or just report) every derived manifest; return the drift found."""
    drift: list[str] = []
    for relative in (*PACKAGE_JSONS,):
        described = _sync_package_json(root, relative, version, write=write)
        if described is not None:
            drift.append(described)
    drift.extend(_sync_server_json(root, version, write=write))
    return drift


def main(argv: list[str] | None = None) -> int:
    """Entry point: sync the manifests, or fail on drift with ``--check``."""
    parser = argparse.ArgumentParser(
        description="Sync the canonical version into every derived manifest."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report drift and exit 1 instead of writing the manifests",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="repository root (defaults to the checkout containing this script)",
    )
    args = parser.parse_args(argv)

    root = (
        args.root.resolve() if args.root else find_repo_root(Path(__file__).resolve())
    )
    version = read_canonical_version(root)
    head = "would update" if args.check else "synced"
    print(f"canonical version {version} ({CANONICAL})")

    drift = collect(root, version, write=not args.check)
    if not drift:
        print("all derived manifests already match")
        return 0

    for line in drift:
        print(f"  {head}: {line}")
    if args.check:
        print("run `poe sync-versions` in apps/server and commit the result")
        return 1
    print(f"{len(drift)} manifest field(s) updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
