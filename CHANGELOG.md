# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

GitHub's auto-generated release notes (see
[`.github/release.yml`](https://github.com/novelai-image-mcp/NovelAI-Image-MCP/blob/main/.github/release.yml))
fold the per-commit gitmoji + Conventional Commit messages into the
per-release section headings. This file is the human-curated companion.

## [Unreleased]

### Added

- **Monorepo structure**: introduced a uv + pnpm workspace with two members
  — `apps/server/` (the installable MCP server package) and `apps/docs/` (the
  Sphinx documentation site). Tasks are orchestrated by Turbo.
- **Sphinx documentation site** (`apps/docs/`) using Furo + MyST Markdown,
  with autodoc-generated API reference, tool guides, tutorials, transports
  guide, and developer docs. Auto-deploys to GitHub Pages on every push to
  `main` that touches docs or server source.
- **pnpm workspaces** with root dev toolchain (turbo, husky,
  markdownlint-cli2, rimraf, eslint-plugin-turbo).
- **Turbo** task graph (`turbo.json`) for cross-workspace `build` / `lint` /
  `typecheck` / `test` / `serve` / `clean` / `linkcheck` tasks with caching.
- **GitHub Pages deployment** workflow (`.github/workflows/docs.yml`).
- **`CODEOWNERS`**, **`SECURITY.md`**, **`CODE_OF_CONDUCT.md`**,
  **`CONTRIBUTING.md`**, and this **`CHANGELOG.md`** as project governance
  artifacts.
- **`.vscode/`** recommended extensions + workspace settings for the
  monorepo toolchain.
- **`apps/server/package.json`** and **`apps/docs/package.json`** as
  turbo-runnable workspace members.

### Changed

- The installable MCP server now lives at `apps/server/`; the root
  `pyproject.toml` is a virtual uv workspace root (not installable).
- `docker-compose.yml` now sets `context: .` + `dockerfile: apps/server/Dockerfile`
  so uv can resolve the workspace graph from the repository root.
- CI (`ci.yml`) and release (`release.yml`) workflows now scope Python
  tooling to `apps/server` via `uv run --directory apps/server ...` and
  build the package with `uv build --package novelai-image-mcp`.
- `dependabot.yml` adds an `npm` ecosystem updater for the root
  cross-cutting Node toolchain and scopes the Docker updater to
  `directory: /apps/server`.
- `.husky/pre-commit` now scopes Pyright + pytest to `apps/server/**/*.py`
  changes (docs `conf.py` changes no longer trigger the slow Python phases).
- `prek.toml` exclude extended to cover `apps/docs/_build/`,
  `apps/server/build/`, `apps/server/dist/`, `.turbo/`, and `node_modules/`.
- `REUSE.toml` extended to annotate `Makefile`, `LICENSE`, and Sphinx
  build output (`_build/**`) and Turborepo cache (`.turbo/**`).
- `.gitignore` extended with `.turbo/`, `apps/docs/_build/`, and per-member
  `dist/`/`build/` exclusions.

### Removed

- Root-level `Dockerfile`, `pyproject.toml` (now at `apps/server/`),
  `src/`, `tests/`, and `docker/` — moved under `apps/server/` as part of
  the workspace migration (git history preserved via `git mv`).

## [0.1.0] — 2026-07-25

### Added

- **11 MCP tools** covering the full NovelAI image API surface:
  `generate_image`, `image_to_image`, `inpaint`, `upscale_image`,
  `director_tool`, `annotate_image`, `suggest_tags`, `encode_vibe`,
  `get_subscription`, `get_user_data`, `estimate_anlas_cost`.
- **Two transports**: stdio (local agents) + streamable-http (remote /
  multi-client).
- **Dual image return**: base64 `Image` content blocks (the agent *sees* the
  image) **and** PNG saved to disk (path returned as text).
- **Async + sync**: async tool handlers + a `typer` CLI for direct invocation.
- **uv-managed**, single Python package, MIT-licensed, Docker-ready.

[Unreleased]: https://github.com/novelai-image-mcp/NovelAI-Image-MCP/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/novelai-image-mcp/NovelAI-Image-MCP/releases/tag/v0.1.0
