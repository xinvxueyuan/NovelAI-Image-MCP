# Releasing

This page describes the release process: bumping the version, building
artifacts, and publishing to PyPI + GHCR + GitHub Releases. Most of the
process is automated by [`release.yml`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.github/workflows/release.yml).

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
**derived** from it at release time — you only ever edit one file:

| Location | How it stays in sync |
|---|---|
| `apps/server/pyproject.toml` | **Edit this** (canonical). |
| `apps/server/src/novelai_image_mcp/__init__.py` (`__version__`) | Resolved at import time from the installed wheel's METADATA, which is generated from `pyproject.toml`. No edit needed. |
| `package.json`, `apps/server/package.json`, `apps/docs/package.json` | Auto-updated by the `.github/actions/sync-version` composite action in `release.yml` and committed back to the release branch. |
| `apps/docs/source/conf.py` (`release`) | Resolved at Sphinx build time from the installed package metadata, with a `0.0.0` fallback for un-synced checkouts. |
| `apps/server/Dockerfile` (`ARG VERSION`) | Injected at build time from `validate.outputs.version`. |
| Docker image labels (`org.opencontainers.image.version`) | Injected via `docker/metadata-action` from `validate.outputs.version`. |
| Git tag, PyPI version, GitHub Release | All sourced from `validate.outputs.version`. |

### What you do NOT edit

The release workflow ([`release.yml`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.github/workflows/release.yml))
runs the `.github/actions/sync-version` composite action as part of the
`validate` job. That action:

1. Re-reads `apps/server/pyproject.toml` to confirm the canonical version
   matches the release input.
2. Updates every Node `package.json` to that version with `jq`, and syncs
   the MCP registry manifest `server.json` (top-level `.version`, the PyPI
   package entry's `version`, and the OCI entry's `identifier` `:X.Y.Z`
   suffix).
3. Asserts that every version-bearing file agrees. The release fails fast
   if anything has drifted.

For branch-based releases (`releases/X.Y.Z`), the synced
`package.json`/`server.json` edits are pushed back to the same branch as a
`🔧 chore(release): sync manifest versions to X.Y.Z` commit, so the
workspace tree stays consistent after the run.

:::{note}
Tutorials and changelogs that mention historical versions (e.g. "v0.1.0
supports references but not ControlNet") are **content**, not config — the
sync action does not touch them. Update them by hand when the relevant
feature changes.
:::

## Pre-release checklist

Before triggering a release:

- [ ] All CI checks pass on `main`.
- [ ] `apps/server/pyproject.toml`'s `version` is bumped to the target
      (this is the **only** version string you need to edit).
- [ ] `CHANGELOG.md` has an entry for the new version (under `## [Unreleased]`
      → rename to `## [X.Y.Z] - YYYY-MM-DD`).
- [ ] `uv.lock` is up to date (`uv lock`).
- [ ] Tutorials that quote the previous version's feature set have been
      updated to reflect the new behaviour.
- [ ] The release branch (`releases/X.Y.Z`) has been pushed.

## Triggering a release

### Option A: release branch (preferred)

Push a branch named `releases/X.Y.Z` to trigger the workflow:

```bash
git checkout -b releases/0.2.0
# Edit apps/server/pyproject.toml: version = "0.2.0"
# Edit CHANGELOG.md
git add apps/server/pyproject.toml CHANGELOG.md
git commit -m "🏷️ chore(release): 0.2.0"
git push -u origin releases/0.2.0
```

The workflow extracts the version from the branch name and runs the full
release pipeline.

### Option B: workflow_dispatch

Manually trigger from the GitHub Actions UI:

1. Go to **Actions** → **🚀 Release** → **Run workflow**.
2. Enter the version (e.g. `0.2.0`).
3. Click **Run workflow**.

Useful for re-running a failed release after fixing the underlying issue.

## Release pipeline

The `release.yml` workflow runs these jobs in order:

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

- Verifies the input version matches `apps/server/pyproject.toml`.
- Calls `.github/actions/sync-version`, which auto-bumps every Node
  `package.json` to the validated version and re-asserts that every
  version-bearing file agrees. For branch-based releases, the synced
  `package.json` edits are pushed back to the release branch.

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

- Generates release notes via `gh api .../generate-notes` (configured by
  `.github/release.yml`).
- Creates a GitHub Release with the wheel + sdist attached.

### 6. Publish to MCP Registry

- Runs in parallel with the GitHub Release, after PyPI and GHCR are live
  (`needs: [validate, publish-pypi, publish-ghcr]`).
- Installs `mcp-publisher`, validates `server.json` against the registry
  schema, logs in via GitHub OIDC, publishes, then verifies the server is
  listed at `registry.modelcontextprotocol.io`.
- Inlined into `release.yml` because the `v*` tag created by the
  `github-release` job uses `GITHUB_TOKEN`, which GitHub does not
  re-dispatch as a tag-push event — a separate tag-triggered workflow would
  never fire. The standalone `publish-mcp.yml` remains available for manual
  re-runs (`gh workflow run publish-mcp.yml -f version=X.Y.Z`).

## Cutting a release

A typical release flow:

```bash
# 1. Make sure main is green
git checkout main
git pull
uv run --directory apps/server poe check

# 2. Bump version — this is the ONLY version string you edit
#    Edit apps/server/pyproject.toml: version = "0.2.0"
#    (The release workflow will propagate this to every package.json
#    and commit them back to the release branch automatically.)

# 3. Update CHANGELOG
#    Edit CHANGELOG.md: rename [Unreleased] to [0.2.0] - 2026-07-25

# 4. Update tutorials that pin to a previous version
#    e.g. "v0.1.0 supports references but not ControlNet"

# 5. Re-lock
uv lock

# 6. Commit + push
git add apps/server/pyproject.toml CHANGELOG.md uv.lock
git commit -m "🏷️ chore(release): 0.2.0"
git push

# 7. Create the release branch (triggers the workflow).
#    The workflow's sync-version step will auto-bump the package.json
#    files and push a follow-up commit to this branch.
git checkout -b releases/0.2.0
git push -u origin releases/0.2.0

# 8. Watch the workflow
gh run watch
```

## Post-release

- Verify the package on PyPI: <https://pypi.org/project/novelai-image-mcp/>
- Verify the image on GHCR: `docker pull ghcr.io/<owner>/<repo>:0.2.0`
- Verify the GitHub Release: <https://github.com/xinvxueyuan/NovelAI-Image-MCP/releases>
- Verify the MCP Registry listing (automatic via the `publish-mcp` job):
  <https://github.com/mcp/xinvxueyuan/novelai-image-mcp>
- Announce in the project's discussion / chat.

## Rollback

If a release is broken:

1. **Do not re-publish the same version on PyPI** (PyPI doesn't allow
   re-uploads). Yank the broken release: `twine uninstall` or via the
   PyPI web UI.
2. Cut a patch release with the fix (`0.2.1`).
3. Mark the broken release as a pre-release / yanked on GitHub.

## See also

- [CHANGELOG](../about/changelog.md) — what changed in each release
- [`release.yml`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.github/workflows/release.yml)
- [`.github/release.yml`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.github/release.yml) — release-notes auto-generation config
- [PyPI trusted publishing setup](https://docs.pypi.org/trusted-publishers/)
