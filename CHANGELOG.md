# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

GitHub's auto-generated release notes (see
[`.github/release.yml`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.github/release.yml))
fold the per-commit gitmoji + Conventional Commit messages into the
per-release section headings. This file is the human-curated companion.

## [Unreleased]

### Added

- _Nothing yet._

### Changed

- _Nothing yet._

### Fixed

- _Nothing yet._

## [0.1.4] — 2026-07-26

### Added

- **Listed on the GitHub MCP Registry** (`github.com/mcp/xinvxueyuan/novelai-image-mcp`):
  the server is now discoverable and installable via the official MCP Registry
  (<https://registry.modelcontextprotocol.io>) and the GitHub MCP Registry
  directory (<https://github.com/mcp>). Added `server.json` metadata manifest
  declaring both PyPI and GHCR package sources (hybrid deployment), added the
  `mcp-name: io.github.xinvxueyuan/novelai-image-mcp` marker to README.md for
  PyPI ownership verification, and added the
  `io.modelcontextprotocol.server.name` label to the Docker image for OCI
  ownership verification. A new `publish-mcp.yml` workflow automates registry
  publication on every release tag via `mcp-publisher` (GitHub OIDC auth, no
  secrets required).
- **`LEARN.md` guided learning path**: a progressive 9-module curriculum
  (prerequisites → MCP fundamentals → architecture → first tool call →
  NovelAI API layer → adding a new tool → image return path → release
  engineering → deep dives) with hands-on checkpoints and time estimates.
  Complements the reference docs by stitching them into a syllabus rather
  than duplicating them.

## [0.1.3] — 2026-07-26

### Fixed

- **Restore `upscale_image` and `annotate_image` functionality**: the 0.1.2
  endpoint migration incorrectly routed `/ai/upscale` and `/ai/annotate-image`
  to `image.novelai.net`, which returns 404 for both — these two endpoints
  were not migrated and remain on the Primary API at `api.novelai.net`. The
  Primary API's own docs (<https://api.novelai.net/docs/>) state that
  third-party users may use its `/ai/` routes. Added
  `NovelAISettings.legacy_image_base_url` (default: `https://api.novelai.net`)
  and updated `NovelAIClient.upscale()` and `annotate()` to use this base URL.
  The `NovelAIConfigLike` Protocol and `create_novelai_client()` factory were
  extended to propagate the new field.

### Changed

- `nai/constants.py` `Endpoint` class docstring rewritten to document the
  endpoint split: most paths root at `image.novelai.net`, but `UPSCALE` and
  `ANNOTATE` remain on `api.novelai.net` (the Primary API).
- `AGENTS.md` hard constraint #2 corrected: `api.novelai.net` does not
  "explicitly reject third-party requests" — its `/ai/` routes are explicitly
  for third-party use per the Primary API docs.
- `tests/test_client.py`: 2 URL mocks updated from `image.novelai.net` to
  `api.novelai.net` for `upscale` and `annotate`.

## [0.1.2] — 2026-07-26

### Fixed

- **NovelAI API endpoint migration to `image.novelai.net`**: NovelAI
  consolidated all third-party API access to `image.novelai.net`, which now
  hosts both `/ai/*` (image generation and tools) and `/user/*` (account,
  subscription, data) endpoints. The legacy `api.novelai.net` is reserved
  for the official frontend and rejects third-party requests with a 400
  error (`Please refresh NovelAI.net. If using a third-party tool, update
  to the image URL.`). The `account_base_url` default in `NovelAISettings`
  and `NovelAIClient` is now `https://image.novelai.net`; `upscale()` and
  `annotate()` (both `/ai/*` endpoints) now use `image_base_url` instead of
  `account_base_url`. Fixes `get_subscription`, `get_user_data`,
  `upscale_image`, and `annotate_image` in production.

### Changed

- `nai/http.py` module docstring and `nai/constants.py` `Endpoint` class
  docstring updated to document the old-model vs new-model endpoint split:
  V3/Furry → `/ai/generate-image` (ZIP, HTTP 201); V4/V4.5 →
  `/ai/generate-image-stream` (MessagePack stream, HTTP 200). Also notes
  that `/ai/upscale` and `/ai/annotate-image` are not listed in the public
  OpenAPI spec but remain available in production.
- Configuration docs (en/zh/ja), `development/testing.md`,
  `about/tool-validation.md`, `AGENTS.md`, `.env.example`, and
  `pyproject.toml` comments synchronized with the endpoint migration.
- `tests/test_client.py`: 7 URL mocks updated from `api.novelai.net` to
  `image.novelai.net`.

## [0.1.1] — 2026-07-26

### Fixed

- **Image content block now serializable by MCP v2 SDK** (Fix 1): the 6
  image-returning tools (`generate_image`, `image_to_image`, `inpaint`,
  `upscale_image`, `director_tool`, `annotate_image`) raised
  `PydanticSerializationError: Unable to serialize unknown type: Image`
  because `_save_and_return` returned the SDK's `Image` helper class
  directly. The helpers now call `Image(...).to_image_content()` to
  produce a pydantic `ImageContent` block. Previously Anlas was spent and
  the image saved to disk, but the agent received an error and could not
  see the image.
- **NovelAI `api.novelai.net` endpoints reachable** (Fix 2): the 4
  account-side tools (`get_subscription`, `get_user_data`,
  `upscale_image`, `annotate_image`) failed with
  `NovelAITransportError: NovelAI request transport failed` because
  Cloudflare's bot-management WAF fingerprinted the OpenSSL TLS
  ClientHello (JA3/JA4) and silently reset the connection. A new
  `nai/http.py` module now wraps `httpx.AsyncClient` with
  `httpx_curl_cffi.AsyncCurlTransport(impersonate="chrome")` to reproduce
  Chrome's BoringSSL TLS fingerprint, plus the full Chrome 150 header
  block (User-Agent, `Sec-Ch-Ua*`, `Sec-Fetch-*`, etc.).

### Added

- **Browser fingerprint dependencies**: `curl_cffi>=0.15.0` and
  `httpx-curl-cffi>=0.1.5` are now required dependencies in
  `apps/server/pyproject.toml`. Without them NovelAI's Cloudflare WAF
  rejects requests at the TLS layer.
- **`nai/http.py`**: new module exporting `BROWSER_HEADERS` (Chrome 150
  header block) and `create_http_client()` factory used by `server.py`,
  `cli.py`, and `nai/client.py`.
- **`apps/server/dev_server.py`**: non-relative-import entry point so
  `mcp dev` can load the server (works around `mcp dev` loading
  `server.py` directly, which breaks `from ._mcp import MCPServer`).
- **Regression tests**: `TestSerializationRegression` in
  `tests/test_tools.py` exercises the real `Tool.run(convert_result=True)`
  path against `generate_image` and `upscale_image`.
  `TestCreateHttpClient` + `TestBrowserHeaders` in `tests/test_http.py`
  cover the new HTTP factory and Chrome header block.

### Changed

- `apps/server/pyproject.toml` `filterwarnings` now ignores
  `curl_cffi.utils.CurlCffiWarning` (Windows Proactor event loop lacks
  `add_reader`; curl_cffi registers a selector thread to compensate —
  informational, no functional impact).
- `apps/docs/source/about/tool-validation.md` updated: all 6
  image-returning tools now ✅ pass (was ❌); fix history section added
  documenting root cause and verification for both fixes.

## [0.1.0] — 2026-07-25

### Added

- **11 MCP tools** covering the full NovelAI image API surface:
  `generate_image`, `image_to_image`, `inpaint`, `upscale_image`,
  `director_tool`, `annotate_image`, `suggest_tags`, `encode_vibe`,
  `get_subscription`, `get_user_data`, `estimate_anlas_cost`.
- **Two transports**: stdio (local agents) + streamable-http (remote /
  multi-client).
- **Dual image return**: base64 `Image` content blocks (the agent _sees_ the
  image) **and** PNG saved to disk (path returned as text).
- **Async + sync**: async tool handlers + a `typer` CLI for direct invocation.
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
- **uv-managed**, single Python package, MIT-licensed, Docker-ready.

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

[Unreleased]: https://github.com/xinvxueyuan/NovelAI-Image-MCP/compare/v0.1.3...HEAD
[0.1.3]: https://github.com/xinvxueyuan/NovelAI-Image-MCP/releases/tag/v0.1.3
[0.1.2]: https://github.com/xinvxueyuan/NovelAI-Image-MCP/releases/tag/v0.1.2
[0.1.1]: https://github.com/xinvxueyuan/NovelAI-Image-MCP/releases/tag/v0.1.1
[0.1.0]: https://github.com/xinvxueyuan/NovelAI-Image-MCP/releases/tag/v0.1.0
