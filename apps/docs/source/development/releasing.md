# Releasing

This page describes the release process: bumping the version, authoring the
release notes, and publishing to PyPI + GHCR + GitHub Releases + the MCP
Registry. Pushing a version tag runs the whole pipeline; the tag is the only
trigger.

## Versioning

The project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html):

- `MAJOR.MINOR.PATCH`
- `MAJOR`: breaking API changes
- `MINOR`: new features, backward-compatible
- `PATCH`: bug fixes, backward-compatible

### Single source of truth

The canonical version lives in
[`apps/server/pyproject.toml`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/pyproject.toml)'s
`[project] version` field. Every other place that carries the version is
**derived** from it, and one command writes them all:

```bash
uv run --directory apps/server poe sync-versions    # write
uv run --directory apps/server poe check-versions   # verify only (what CI runs)
```

| Location | How it stays in sync |
|---|---|
| `apps/server/pyproject.toml` | **Edit this** (canonical). |
| `package.json`, `apps/server/package.json`, `apps/docs/package.json` | `poe sync-versions` writes the top-level `version`. |
| `server.json` (MCP registry manifest) | `poe sync-versions` writes the top-level `.version`, the PyPI entry's `version` and the OCI entry's `identifier` tag. |
| `apps/server/src/novelai_image_mcp/__init__.py` (`__version__`) | Resolved at import time from the installed wheel's METADATA, which is generated from `pyproject.toml`. No edit needed. |
| `apps/docs/source/conf.py` (`release`) | Resolved at Sphinx build time from the installed package metadata, with a `0.0.0` fallback for un-synced checkouts. |
| `apps/server/Dockerfile` (`ARG VERSION`) | Injected at build time from `validate.outputs.version`. |
| Docker image labels (`org.opencontainers.image.version`) | Injected via `docker/metadata-action` from `validate.outputs.version`. |
| Git tag, PyPI version, GitHub Release | All sourced from the tag that triggered the run. |

:::{important}
The release workflow **verifies** these files, it never writes them. Nothing
is pushed back to the repository while a release runs, so a published
artifact can never disagree with the commit it was built from. Run
`poe sync-versions` and commit *before* tagging — `poe check-versions` fails
the run otherwise.
:::

## Release notes are authored in JSON

Each release carries an announcement in
[`release-notes/<version>.json`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/tree/main/release-notes):

```json
{
  "version": "0.5.2",
  "date": "2026-10-13",
  "summary": "One paragraph summarising the release.",
  "highlights": [{ "title": "Headline", "body": "Markdown body" }],
  "sections": [{ "title": "🛡️ Security", "items": ["Bullet one"] }],
  "upgrade_notes": "Anything an operator must do.",
  "contributors": ["@someone"],
  "footer": "Optional closing Markdown."
}
```

`version`, `date` and `summary` are required; the remaining keys are optional
and an **unknown key is an error**, so a typo cannot silently drop part of an
announcement. The `🚀 Release` workflow renders the document with
[`apps/server/scripts/release_notes.py`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/scripts/release_notes.py)
and publishes the result as the GitHub Release body, appending the
auto-generated commit list (grouped by `.github/release.yml`) below it.

```bash
# preview exactly what the release page will show
uv run --directory apps/server poe release-notes --version 0.5.2
```

`CHANGELOG.md` remains the cumulative, human-curated changelog of the
repository; the JSON document is the shorter announcement shown on the
release page. Both are required for a release.

## Pre-release checklist

Before pushing the tag:

- [ ] All CI checks pass on `main`, and `main` is pushed.
- [ ] `apps/server/pyproject.toml`'s `version` is bumped (the **only**
      version string you edit by hand).
- [ ] `CHANGELOG.md` has a section for the new version (rename `## [Unreleased]`
      to `## [X.Y.Z] - YYYY-MM-DD` and add a fresh `[Unreleased]`).
- [ ] `release-notes/X.Y.Z.json` exists and renders.
- [ ] `poe sync-versions` has been run and committed (three `package.json`
      files plus `server.json`).
- [ ] `uv lock` is up to date (`uv lock`).
- [ ] `poe check`, `uv run reuse lint` and `poe check-versions` are green.
- [ ] Tutorials that quote the previous version's feature set are updated.

## Triggering a release

### Option A: push the tag (the normal path)

The tag is the release decision. It must point at a commit that is already on
`main` — the `validate` job checks the ancestry and refuses a tag that is not
on the baseline:

```bash
git tag -a v0.5.2 -m "v0.5.2"
git push origin v0.5.2
```

The workflow resolves the version from the tag name and runs the full
pipeline against that commit.

### Option B: workflow_dispatch (re-run an existing tag)

Manually trigger from the GitHub Actions UI (or the CLI) to rebuild and
re-publish an **existing** tag — useful after a transient failure or to
refresh the release notes:

```bash
gh workflow run release.yml -f version=0.5.2
```

The tag must already exist; this path never rewrites it.

## Release pipeline

The `release.yml` workflow runs these jobs:

```{mermaid}
graph TD
    A[validate] --> B[build]
    B --> C[publish-pypi]
    B --> D[publish-ghcr]
    C --> E[github-release]
    D --> E
    C --> F[publish-mcp]
    D --> F
```

### 1. Validate

- Resolves the version from the tag (or the dispatch input) and rejects
  anything that is not `X.Y.Z`.
- Confirms the tag exists and its commit is an ancestor of `origin/main`.
- Confirms `apps/server/pyproject.toml` carries the tag's version.
- Runs `apps/server/scripts/sync_versions.py --check`: every derived manifest
  must already agree (verification only — nothing is written).
- Confirms `CHANGELOG.md` documents the version.
- Renders `release-notes/<version>.json` and uploads it as the
  `release-notes` artifact.

### 2. Build

- `uv build --package novelai-image-mcp` produces wheel + sdist.
- Uploads them as a CI artifact (`python-distributions`).

### 3. Publish to PyPI

- Uses **OIDC trusted publishing** (no API token).
- Requires the GitHub environment `pypi` to be configured for trusted
  publishing on PyPI's side.

### 4. Publish to GHCR

- Builds the Docker image (multi-platform via Buildx).
- Pushes to `ghcr.io/<owner>/<repo>:<version>`, `:<major>.<minor>`,
  `:<major>`, and `:sha-<short>`.
- **Signs the image with cosign** (keyless, via OIDC).

### 5. GitHub Release

- Renders the JSON release notes and appends the auto-generated commit list.
- Creates the GitHub Release for the **existing** tag (`--verify-tag`) with
  the wheel + sdist attached. A re-run updates the notes and re-uploads the
  assets instead of failing.

### 6. Publish to MCP Registry

- Runs after PyPI and GHCR are live
  (`needs: [validate, publish-pypi, publish-ghcr]`).
- Installs `mcp-publisher`, validates `server.json` against the registry
  schema, logs in via GitHub OIDC, publishes, then verifies the server is
  listed at `registry.modelcontextprotocol.io`.
- Inlined rather than a separate tag-triggered workflow so one tag push
  publishes everywhere atomically. The standalone `publish-mcp.yml` remains
  available for manual re-publication after a `server.json` fix.

## Cutting a release

A complete release, end to end:

```bash
# 1. Make sure main is green and current
git checkout main
git pull
uv run --directory apps/server poe check

# 2. Bump the canonical version (the ONLY version string you edit)
#    apps/server/pyproject.toml: version = "0.5.2"

# 3. Close the changelog section
#    CHANGELOG.md: rename [Unreleased] to [0.5.2] - 2026-10-13,
#    add a fresh empty [Unreleased]

# 4. Author the announcement
#    release-notes/0.5.2.json  (see the format above)

# 5. Propagate the version and re-lock
uv run --directory apps/server poe sync-versions
uv lock

# 6. Verify everything the workflow will verify, then commit and push
uv run --directory apps/server poe check
uv run --directory apps/server poe check-versions
uv run reuse lint
git add apps/server/pyproject.toml CHANGELOG.md release-notes/0.5.2.json \
        package.json apps/server/package.json apps/docs/package.json \
        server.json uv.lock
git commit -m "🏷️ chore(release): 0.5.2"
git push

# 7. Tag the release commit and push the tag — this triggers the pipeline
git tag -a v0.5.2 -m "v0.5.2"
git push origin v0.5.2

# 8. Watch it
gh run watch
```

## Post-release

- Verify the package on PyPI: <https://pypi.org/project/novelai-image-mcp/>
- Verify the image on GHCR: `docker pull ghcr.io/<owner>/<repo>:0.5.2`
- Verify the GitHub Release: <https://github.com/xinvxueyuan/NovelAI-Image-MCP/releases>
- Verify the MCP Registry listing (automatic via the `publish-mcp` job):
  <https://registry.modelcontextprotocol.io/>
- Announce in the project's discussion / chat.

## Rollback

If a release is broken:

1. **Do not re-publish the same version on PyPI** (PyPI doesn't allow
   re-uploads). Yank the broken release via the PyPI web UI.
2. Cut a patch release with the fix (`0.5.3`).
3. Mark the broken release as a pre-release / yanked on GitHub.

## History

Releases up to and including 0.5.1 were triggered by pushing a
`releases/X.Y.Z` branch, with the workflow writing the synced manifests back
to that branch. The branches were removed once the tag flow landed; the
historical `vX.Y.Z` tags remain and are the record of those releases.

## See also

- [CHANGELOG](../about/changelog.md) — what changed in each release
- [`release-notes/README.md`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/release-notes/README.md) — the JSON notes format
- [`release.yml`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.github/workflows/release.yml)
- [`.github/release.yml`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.github/release.yml) — grouping for the appended commit list
- [PyPI trusted publishing setup](https://docs.pypi.org/trusted-publishers/)
