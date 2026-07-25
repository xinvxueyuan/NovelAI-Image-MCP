# Releasing

This page describes the release process: bumping the version, building
artifacts, and publishing to PyPI + GHCR + GitHub Releases. Most of the
process is automated by [`release.yml`](https://github.com/novelai-image-mcp/NovelAI-Image-MCP/blob/main/.github/workflows/release.yml).

## Versioning

The project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html):

- `MAJOR.MINOR.PATCH`
- `MAJOR`: breaking API changes
- `MINOR`: new features, backward-compatible
- `PATCH`: bug fixes, backward-compatible

The version is the canonical source of truth in
[`apps/server/pyproject.toml`](https://github.com/novelai-image-mcp/NovelAI-Image-MCP/blob/main/apps/server/pyproject.toml)'s
`[project] version` field. The release workflow validates that the input
version matches this field before publishing.

## Pre-release checklist

Before triggering a release:

- [ ] All CI checks pass on `main`.
- [ ] `apps/server/pyproject.toml`'s `version` is bumped to the target.
- [ ] `CHANGELOG.md` has an entry for the new version (under `## [Unreleased]`
      → rename to `## [X.Y.Z] - YYYY-MM-DD`).
- [ ] `uv.lock` is up to date (`uv lock`).
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
```

### 1. Validate

- Verifies the input version matches `apps/server/pyproject.toml`.

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

## Cutting a release

A typical release flow:

```bash
# 1. Make sure main is green
git checkout main
git pull
uv run --directory apps/server poe check

# 2. Bump version
# Edit apps/server/pyproject.toml: version = "0.2.0"

# 3. Update CHANGELOG
# Edit CHANGELOG.md: rename [Unreleased] to [0.2.0] - 2026-07-25

# 4. Re-lock
uv lock

# 5. Commit + push
git add apps/server/pyproject.toml CHANGELOG.md uv.lock
git commit -m "🏷️ chore(release): 0.2.0"
git push

# 6. Create the release branch (triggers the workflow)
git checkout -b releases/0.2.0
git push -u origin releases/0.2.0

# 7. Watch the workflow
gh run watch
```

## Post-release

- Verify the package on PyPI: <https://pypi.org/project/novelai-image-mcp/>
- Verify the image on GHCR: `docker pull ghcr.io/<owner>/<repo>:0.2.0`
- Verify the GitHub Release: <https://github.com/novelai-image-mcp/NovelAI-Image-MCP/releases>
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
- [`release.yml`](https://github.com/novelai-image-mcp/NovelAI-Image-MCP/blob/main/.github/workflows/release.yml)
- [`.github/release.yml`](https://github.com/novelai-image-mcp/NovelAI-Image-MCP/blob/main/.github/release.yml) — release-notes auto-generation config
- [PyPI trusted publishing setup](https://docs.pypi.org/trusted-publishers/)
