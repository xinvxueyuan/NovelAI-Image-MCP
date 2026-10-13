#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 NovelAI Image MCP contributors
# SPDX-License-Identifier: MIT
"""Render a release-notes JSON document into the Markdown GitHub Release body.

Release notes are **authored in JSON** so the pipeline never has to guess what
a release means: ``release-notes/<version>.json`` is committed alongside the
version bump, and the release workflow renders it with this script. The shape
is small on purpose -- prose belongs in ``CHANGELOG.md``, and this document is
the release announcement shown on GitHub::

    {
      "version": "0.5.2",
      "date": "2026-10-13",
      "summary": "One paragraph summarising the release.",
      "highlights": [{"title": "Headline", "body": "Markdown body"}],
      "sections": [{"title": "Security", "items": ["Bullet one"]}],
      "upgrade_notes": "What an operator must do.",
      "contributors": ["@someone"],
      "footer": "Optional closing Markdown."
    }

``version``, ``date`` and ``summary`` are required; every other key is
optional, and an unknown key is an error so a typo cannot silently drop part
of a release announcement. Rendered Markdown goes to stdout, or to ``--output``
for the workflow to hand to ``gh release create --notes-file``.

Usage::

    uv run --directory apps/server poe release-notes --version 0.5.2
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, NoReturn

#: Directory, relative to the repository root, holding one JSON per release.
NOTES_DIR = "release-notes"
#: Canonical manifest used to locate the repository root.
CANONICAL = "apps/server/pyproject.toml"

_REQUIRED = ("version", "date", "summary")
_KNOWN = (
    *_REQUIRED,
    "highlights",
    "sections",
    "upgrade_notes",
    "contributors",
    "footer",
)


def find_repo_root(start: Path) -> Path:
    """Return the repository root at or above *start*."""
    for candidate in (start, *start.parents):
        if (candidate / CANONICAL).is_file():
            return candidate
    message = f"cannot locate the repository root (no {CANONICAL}) above {start}"
    raise SystemExit(message)


def _fail(path: Path, detail: str) -> NoReturn:
    message = f"{path}: {detail}"
    raise SystemExit(message)


def _require_text(path: Path, document: dict[str, Any], key: str) -> str:
    """Return a required non-empty string field of *document*."""
    value = document.get(key)
    if not isinstance(value, str) or not value.strip():
        _fail(path, f"{key!r} must be a non-empty string")
    return value


def _check_entry_body(
    path: Path, label: str, entry: dict[str, Any], field: str
) -> None:
    """Validate the ``body`` (highlights) or ``items`` (sections) of one entry."""
    value = entry.get(field)
    if isinstance(value, str):
        if value.strip():
            return
        _fail(path, f"{label}.{field} must not be empty")
    if isinstance(value, list) and value:
        if all(isinstance(item, str) and item.strip() for item in value):
            return
        _fail(path, f"{label}.{field} must be a list of non-empty strings")
    _fail(path, f"{label}.{field} must be a non-empty string or list")


def _check_entry_list(path: Path, key: str, entries: Any) -> None:
    """Validate the optional ``highlights`` / ``sections`` list."""
    if entries is None:
        return
    if not isinstance(entries, list) or not entries:
        _fail(path, f"{key!r} must be a non-empty list when present")
    field = "body" if key == "highlights" else "items"
    for index, entry in enumerate(entries):
        label = f"{key}[{index}]"
        if not isinstance(entry, dict):
            _fail(path, f"{label} must be an object")
        title = entry.get("title")
        if not isinstance(title, str) or not title.strip():
            _fail(path, f"{label}.title must be a non-empty string")
        _check_entry_body(path, label, entry, field)


def _check_text_list(path: Path, key: str, values: Any) -> None:
    """Validate an optional list of non-empty strings (``contributors``)."""
    if values is None:
        return
    well_formed = (
        isinstance(values, list)
        and bool(values)
        and all(isinstance(item, str) and item.strip() for item in values)
    )
    if not well_formed:
        _fail(path, f"{key!r} must be a non-empty list of strings")


def load_notes(path: Path, expected_version: str) -> dict[str, Any]:
    """Load and validate a release-notes document."""
    if not path.is_file():
        _fail(path, "missing; author the release notes as JSON before tagging")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        _fail(path, "the document must be a JSON object")

    unknown = sorted(set(raw) - set(_KNOWN))
    if unknown:
        _fail(path, f"unknown key(s) {unknown}; known keys are {list(_KNOWN)}")

    version = _require_text(path, raw, "version")
    for key in ("date", "summary"):
        _require_text(path, raw, key)
    if version != expected_version:
        _fail(path, f"version {version!r} does not match {expected_version!r}")

    _check_entry_list(path, "highlights", raw.get("highlights"))
    _check_entry_list(path, "sections", raw.get("sections"))
    _check_text_list(path, "contributors", raw.get("contributors"))
    for key in ("upgrade_notes", "footer"):
        value = raw.get(key)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            _fail(path, f"{key!r} must be a non-empty string when present")
    return raw


def _bullets(items: list[str]) -> str:
    """Render a list of strings as a Markdown bullet list."""
    return "\n".join(f"- {item.strip()}" for item in items)


def render(notes: dict[str, Any]) -> str:
    """Render validated release notes as the Markdown release body."""
    blocks: list[str] = [notes["summary"].strip()]

    highlights = notes.get("highlights")
    if highlights:
        parts = ["## ✨ Highlights"]
        for entry in highlights:
            parts.append(f"### {entry['title'].strip()}")
            entry_body = entry["body"].strip() if entry.get("body") else ""
            parts.append(entry_body)
        blocks.append("\n\n".join(part for part in parts if part))

    for entry in notes.get("sections") or []:
        items = entry["items"]
        section_body = _bullets(items) if isinstance(items, list) else items.strip()
        blocks.append(f"## {entry['title'].strip()}\n\n{section_body}")

    if notes.get("upgrade_notes"):
        blocks.append(f"## ⬆️ Upgrade notes\n\n{notes['upgrade_notes'].strip()}")

    if notes.get("contributors"):
        blocks.append("## 🙌 Contributors\n\n" + _bullets(notes["contributors"]))

    if notes.get("footer"):
        blocks.append(notes["footer"].strip())

    return "\n\n".join(blocks) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Entry point: render ``release-notes/<version>.json``."""
    parser = argparse.ArgumentParser(
        description="Render release-notes/<version>.json as the GitHub Release body."
    )
    parser.add_argument("--version", required=True, help="release version, e.g. 0.5.2")
    parser.add_argument(
        "--notes-dir",
        type=Path,
        default=None,
        help=f"directory holding the JSON documents (default: <root>/{NOTES_DIR})",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="repository root (defaults to the checkout containing this script)",
    )
    parser.add_argument(
        "--output", type=Path, default=None, help="write here instead of stdout"
    )
    args = parser.parse_args(argv)

    if args.root:
        root = args.root.resolve()
    else:
        root = find_repo_root(Path(__file__).resolve())
    notes_dir = args.notes_dir or root / NOTES_DIR
    path = notes_dir / f"{args.version}.json"

    body = render(load_notes(path, args.version))
    if args.output:
        args.output.write_text(body, encoding="utf-8")
        print(f"rendered {path} -> {args.output} ({len(body)} bytes)")
    else:
        sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
