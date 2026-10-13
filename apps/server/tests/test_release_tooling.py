"""Tests for the release tooling in ``apps/server/scripts`` (version sync, notes)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import release_notes
import sync_versions

CANONICAL_VERSION = "0.2.0"


def _write_checkout(
    root: Path,
    *,
    package_version: str = "0.1.0",
    server_version: str = "0.1.0",
    oci_version: str = "0.1.0",
    canonical: str = CANONICAL_VERSION,
) -> None:
    """Create a minimal checkout with one canonical and four derived manifests."""
    (root / "apps/server").mkdir(parents=True, exist_ok=True)
    (root / "apps/docs").mkdir(parents=True, exist_ok=True)
    (root / sync_versions.CANONICAL).write_text(
        f'[project]\nname = "x"\nversion = "{canonical}"\n', encoding="utf-8"
    )
    for relative in sync_versions.PACKAGE_JSONS:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"name": "x", "version": package_version}, indent=2) + "\n",
            encoding="utf-8",
        )
    (root / sync_versions.SERVER_JSON).write_text(
        json.dumps(
            {
                "version": server_version,
                "packages": [
                    {
                        "registryType": "pypi",
                        "identifier": "novelai-image-mcp",
                        "version": server_version,
                    },
                    {
                        "registryType": "oci",
                        "identifier": f"ghcr.io/o/r:{oci_version}",
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


class TestSyncVersions:
    """The canonical version is propagated to every derived manifest."""

    def test_reads_canonical_version(self, tmp_path: Path) -> None:
        _write_checkout(tmp_path)
        assert sync_versions.read_canonical_version(tmp_path) == CANONICAL_VERSION

    def test_missing_version_line_is_an_error(self, tmp_path: Path) -> None:
        _write_checkout(tmp_path)
        (tmp_path / sync_versions.CANONICAL).write_text('[project]\nname = "x"\n')
        with pytest.raises(SystemExit):
            sync_versions.read_canonical_version(tmp_path)

    def test_find_repo_root_walks_up(self, tmp_path: Path) -> None:
        _write_checkout(tmp_path)
        nested = tmp_path / "apps" / "server" / "scripts"
        nested.mkdir(parents=True)
        assert sync_versions.find_repo_root(nested) == tmp_path

    def test_find_repo_root_reports_failure(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit):
            sync_versions.find_repo_root(tmp_path)

    def test_check_reports_drift_without_writing(self, tmp_path: Path) -> None:
        _write_checkout(tmp_path)
        drift = sync_versions.collect(tmp_path, CANONICAL_VERSION, write=False)
        # three package.json files + server.json's .version + its pypi version
        # + its oci identifier
        assert len(drift) == 6
        assert any("package.json" in line for line in drift)
        assert any("packages[pypi].version" in line for line in drift)
        assert any("packages[oci].identifier" in line for line in drift)
        # nothing was rewritten
        assert sync_versions.collect(tmp_path, CANONICAL_VERSION, write=False)

    def test_write_mode_syncs_everything(self, tmp_path: Path) -> None:
        _write_checkout(tmp_path)
        assert sync_versions.main(["--root", str(tmp_path)]) == 0
        assert sync_versions.collect(tmp_path, CANONICAL_VERSION, write=False) == []
        for relative in sync_versions.PACKAGE_JSONS:
            payload = json.loads((tmp_path / relative).read_text(encoding="utf-8"))
            assert payload["version"] == CANONICAL_VERSION
        server = json.loads(
            (tmp_path / sync_versions.SERVER_JSON).read_text(encoding="utf-8")
        )
        assert server["version"] == CANONICAL_VERSION
        assert server["packages"][0]["version"] == CANONICAL_VERSION
        assert server["packages"][1]["identifier"].endswith(f":{CANONICAL_VERSION}")

    def test_check_mode_exits_non_zero_on_drift(self, tmp_path: Path) -> None:
        _write_checkout(tmp_path)
        assert sync_versions.main(["--root", str(tmp_path), "--check"]) == 1

    def test_check_mode_passes_when_in_sync(self, tmp_path: Path) -> None:
        _write_checkout(
            tmp_path,
            package_version=CANONICAL_VERSION,
            server_version=CANONICAL_VERSION,
            oci_version=CANONICAL_VERSION,
        )
        assert sync_versions.main(["--root", str(tmp_path), "--check"]) == 0


def _notes_document(**overrides: Any) -> dict[str, Any]:
    """Return a valid release-notes document with optional overrides."""
    document: dict[str, Any] = {
        "version": "9.9.9",
        "date": "2026-10-13",
        "summary": "One paragraph.",
    }
    document.update(overrides)
    return document


def _write_notes(root: Path, document: dict[str, Any], version: str = "9.9.9") -> Path:
    notes_dir = root / release_notes.NOTES_DIR
    notes_dir.mkdir(parents=True, exist_ok=True)
    path = notes_dir / f"{version}.json"
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return path


class TestReleaseNotes:
    """Release notes are authored as JSON and rendered to the release body."""

    def test_renders_every_section(self, tmp_path: Path) -> None:
        document = _notes_document(
            highlights=[{"title": "Headline", "body": "Body text."}],
            sections=[
                {"title": "Security", "items": ["Item A", "Item B"]},
                {"title": "Notes", "items": "Prose form."},
            ],
            upgrade_notes="Run the sync task.",
            contributors=["@alice"],
            footer="Closing line.",
        )
        body = release_notes.render(
            release_notes.load_notes(_write_notes(tmp_path, document), "9.9.9")
        )
        assert body.startswith("One paragraph.")
        assert "## ✨ Highlights" in body and "### Headline" in body
        assert "## Security" in body and "- Item A" in body and "- Item B" in body
        assert "## Notes" in body and "Prose form." in body
        assert "## ⬆️ Upgrade notes" in body
        assert "## 🙌 Contributors" in body and "- @alice" in body
        assert body.rstrip().endswith("Closing line.")

    def test_minimal_document_renders_summary_only(self, tmp_path: Path) -> None:
        path = _write_notes(tmp_path, _notes_document())
        assert (
            release_notes.render(release_notes.load_notes(path, "9.9.9"))
            == "One paragraph.\n"
        )

    def test_missing_document_is_an_error(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit, match="missing"):
            release_notes.load_notes(tmp_path / "release-notes" / "9.9.9.json", "9.9.9")

    @pytest.mark.parametrize(
        ("override", "message"),
        [
            ({"summary": ""}, "summary"),
            ({"version": "1.0.0"}, "does not match"),
            ({"typo_key": "x"}, "unknown key"),
            ({"contributors": []}, "contributors"),
            ({"sections": []}, "sections"),
            ({"sections": [{"title": "T"}]}, "items"),
            ({"highlights": [{"title": "T", "body": ""}]}, "body"),
            ({"upgrade_notes": "   "}, "upgrade_notes"),
        ],
    )
    def test_invalid_documents_are_rejected(
        self, tmp_path: Path, override: dict[str, Any], message: str
    ) -> None:
        document = _notes_document(**override)
        with pytest.raises(SystemExit, match=message):
            release_notes.load_notes(_write_notes(tmp_path, document), "9.9.9")

    def test_cli_writes_the_rendered_body(self, tmp_path: Path) -> None:
        _write_notes(tmp_path, _notes_document())
        output = tmp_path / "RELEASE_NOTES.md"
        argv = ["--version", "9.9.9", "--root", str(tmp_path), "--output", str(output)]
        assert release_notes.main(argv) == 0
        assert output.read_text(encoding="utf-8") == "One paragraph.\n"

    def test_shipped_notes_files_are_valid(self) -> None:
        """Every committed release-notes document must load and render."""
        repo_root = sync_versions.find_repo_root(Path(__file__).resolve())
        notes_dir = repo_root / release_notes.NOTES_DIR
        for path in sorted(notes_dir.glob("*.json")):
            document = release_notes.load_notes(path, path.stem)
            assert release_notes.render(document).strip()
