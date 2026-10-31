# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

GitHub's auto-generated release notes (see
[`.github/release.yml`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.github/release.yml))
fold the per-commit gitmoji + Conventional Commit messages into the
per-release section headings. This file is the human-curated companion.

## [0.4.0] — 2026-08-28

### Added

- **NovelAI Diffusion V5 support**: new models `nai-diffusion-5-full`,
  `nai-diffusion-5-curated`, `nai-diffusion-5-full-inpainting`; V5 payload
  fields (`ucPresetId`, `qualityPresetId`, `straight_alpha`); content-sniffed
  response decoding (ZIP vs MessagePack); explicit guard rejecting vibe
  transfer on V5 (feature not yet released upstream).
- **Official error codes on every NovelAI error**: errors now carry the API
  error code and NovelAI's official explanation, appended to the message and
  exposed as `.code` / `.explanation` on the exception; the CLI prints them to
  stderr instead of a raw traceback.

### Changed

- **Server framework → FastMCP 4**: the MCP server layer (`server.py`,
  `tools/*`, `_ctx.py`, `_mcp.py`) now runs on [PrefectHQ/fastmcp]
  `fastmcp==4.0.0b3` (which itself targets the MCP SDK v2 `mcp>=2.0.0`),
  replacing the raw SDK `MCPServer` composition. The 11 tools, the typer
  CLI, and the `MCP_TRANSPORT`-selected stdio / streamable-http transports
  are unchanged. Image tools now return the fastmcp `Image` helper and let
  fastmcp convert it to `ImageContent`, removing the manual
  `to_image_content()` step (and the historical `PydanticSerializationError`
  workaround). Because fastmcp 4 is a prerelease, it is pinned exactly
  (`==4.0.0b3`) with `fastmcp-slim==4.0.0b3`, and `pydantic>=2.12` is now the
  floor — relax the pin when fastmcp 4 ships stable.

### Fixed

- _Nothing yet._

## [Unreleased]

### Added

- _Nothing yet._

### Changed

- _Nothing yet._

### Fixed

- _Nothing yet._

### Security

- _Nothing yet._

## [0.7.1] — 2026-10-31

### Changed

- **The CI and release pipelines run on the current GitHub Actions releases**:
  `astral-sh/setup-uv` 10.3.0 → 10.3.2 in `ci.yml`, `docs.yml` and
  `release.yml`, and `pypa/gh-action-pypi-publish` 1.14.2 → 1.14.3 in
  `release.yml`. Every action stays pinned to a full commit SHA.
- **The repo-root `prek` floor moves from `>=0.5.5` to `>=0.5.7`** in
  `pyproject.toml`, matching the `prek` 0.5.7 the lock already resolved — only
  the recorded specifier in `uv.lock` moves with it.

No third-party dependency changes version and nothing under `apps/server/src`
is touched, so the published wheel differs from 0.7.0 only in its version
string.

### Fixed

- _Nothing yet._

## [0.7.0] — 2026-10-23

### Changed

- **Every dependency is upgraded to its latest available release**: 64 Python
  packages changed version and `pnpm-lock.yaml` moved 345 lines. Nothing in the
  shipped API or CLI changes, which is why this is a minor release rather than a
  patch.
  - Runtime: `fastmcp` 4.1.0 → 4.1.3, `pydantic` 2.14.0a1 → 2.14.1 (the lock
    was pinned at an alpha) with `pydantic-core` 2.47.0 → 2.50.1,
    `pydantic-settings` 2.14.2 → 2.16.1, `curl-cffi` 0.15.0 → 0.16.3,
    `msgpack` 1.2.1 → 1.2.3, `typer` 0.27.0 → 0.27.3.
  - Transitively, through `fastmcp` and `mcp`: `uvicorn` 0.51.0 → 0.54.0,
    `starlette` 1.3.1 → 1.9.0, `websockets` 16.1.1 → 17.3 and `cyclopts`
    4.23.0 → 5.3.0 — the last two cross a major version, which is why the
    server was exercised against the live API rather than only against tests.
  - Development: `ruff` 0.16.0 → 0.17.1, `pyright` 1.1.411 → 1.1.414,
    `poethepoet` 0.48.0 → 0.49.0 and `prek` 0.5.5 → 0.5.7.
  - Already newest, so left alone: `mcp` 2.3.0, `httpx` 0.28.1,
    `httpx-curl-cffi` 0.1.5, `argon2-cffi` 25.1.0, `pytest` 9.1.1 and its
    plugins, `respx` 0.23.1 and `reuse` 6.2.0.
  - Node: `turbo` and `eslint-plugin-turbo` 2.11.8 → 2.11.10,
    `markdownlint-cli2` 0.23.3 → 0.24.0.
  - Two packages left the dependency graph: `pastel` (no longer pulled in) and
    `uc-micro-py` (`sphinx` 9 folded it in).
  - The `curl-cffi` jump crosses a minor version and is the one that could have
    broken the project, because the NovelAI edge sits behind a Cloudflare WAF
    that fingerprints TLS. Verified against the live API: the request still
    carries a Chrome TLS 1.3 fingerprint (peet.ws echoed
    `t13d1516h2_8daaf6152771_806a8c22fdea`), and `get_subscription` returned
    the same eleven keys it did before the upgrade.
- **The documentation stack crosses a major version.** The docs project pinned
  `sphinx>=8.1.3,<9.0`, which silently capped it below the current release;
  the ceiling is now `<10.0` and the stack is `sphinx` 8.2.3 → 9.2.0, with
  `sphinxcontrib-mermaid` 2.1.0 → 2.1.1 following and `myst-parser` 5.1.0,
  `furo` 2025.12.19, `sphinx-design` 0.7.0 and `sphinx-togglebutton` 0.4.5
  already current. Sphinx 9 qualifies the type names
  it emits for pydantic's field constraints, so the bare-name `nitpick_ignore`
  rule for `Ge`/`Le`/`Gt`/`Lt` stopped matching and thirteen warnings appeared;
  a `annotated_types.` prefixed rule replaces it, scoped so a genuinely
  missing reference is still reported. All three languages build with
  `-E -W` and no warnings, and none of them has a dead link.

### Fixed

- _Nothing yet._

### Security

- _Nothing yet._

## [0.6.3] — 2026-10-19

### Added

- **`api/audit.md`**: the audit trail had no reference page while every other
  module under `api/` had one. The page documents when a record is written,
  its fields, the redaction that makes the trail safe to keep (prompts become a
  length and a truncated SHA-256, image arguments become `[redacted image]`,
  credential headers never reach the file), the single `os.write` on an
  `O_APPEND` descriptor that makes concurrent writers safe, and the rule that an
  unwritable trail is logged and swallowed rather than failing a tool call.

### Changed

- **The English documentation site has no dead links**: it had 87. Eighty came
  from the breadcrumb trail the site injects above each article, which walked
  one directory too far up and sent every page under `tools/`, `tutorials/`,
  `transports/`, `development/` and `api/` to a `../../index.html` that does not
  exist. The other seven came from Sphinx's `viewcode`, whose back-links named
  the module a definition was re-exported through rather than the one it is
  documented under; `viewcode_follow_imported_members = False` fixes that and
  stops the source tree growing pages for stdlib modules.

### Fixed

- **The account page documented a subscription response the API does not
  return**: it listed `perStepUsage` and `subscriptionId`, neither of which
  exists, read `trainingStepsLeft` as `{fixed, perStepUsage}`, and its example
  would have raised a `KeyError`; the quickstart example payload carried the same
  invented keys. Both are rewritten from a live response, in all three
  languages, and the example payloads are now parsed and checked key by key.
- **The Anlas cost table was wrong**: it listed 2, 5, 5 and 7 Anlas for four
  resolutions at 28 steps, which matches no configuration. The tool returns 8,
  20, 20 and 30 without Opus and 0, 0, 0 and 30 with it, because Opus makes small
  generations free. The table is now two sub-tables -- txt2img and img2img at
  strength 0.5 -- with both Opus columns, all measured rather than recalled.
- **The translated `installation.md` had drifted from the English source**: the
  Chinese and Japanese pages pointed their Docker link at the wrong target,
  dropped two of three next-step bullets, linked to the English site where a
  translated page existed, and translated the shell comments inside their code
  blocks. Code blocks stay byte-identical to the source; all three pages now
  agree on headings, admonitions, bullet order, link targets and code blocks.

- **`estimate_anlas_cost` now works for `img2img` and `infill`**: the
  tool advertised both actions but always failed with
  `image-conditioned actions require an image`, because it built a
  `GenerationRequest` without the image the cost formula never uses. A cost
  estimate is a pure price calculation, so `GenerationRequest` gained an
  `estimate_only` flag that relaxes the image / mask / inpaint-model
  requirements _for estimation only_; the real generation path is unchanged and
  still enforces every one of them. Price inputs (dimensions, steps, sample
  count, strength range, resolution limits) remain validated in both modes.
- **Corrected two docstrings that documented fields a live account does not
  return**: `get_subscription` listed `perStepUsage` and
  `subscriptionId`, and `estimate_anlas_cost` pointed at a
  `usage` field on the subscription response. None of the three exists;
  the docstrings now describe the keys a real `/user/subscription` response
  carries (`tier`, `active`, `expiresAt`, `accountType`, `perks`,
  `trainingStepsLeft` with `fixedTrainingStepsLeft` /
  `purchasedTrainingSteps`, ...), and state that the remaining Opus
  "battery" is not exposed at all.

### Security

- _Nothing yet._

## [0.6.2] — 2026-10-19

### Added

- **The documentation site is fully translated into Chinese and Japanese**: both
  languages went from four pages to all 48, so the language selector no longer
  leads to a fragment of the site. Every page is a full translation, not a stub,
  and every page is structurally identical to its English source — the same
  headings in the same order, the same code blocks byte for byte, the same table
  rows and admonitions. Code, commands, paths, URLs, identifiers and default
  values are left untranslated.

### Changed

- **`configuration.md` is up to date in both languages**: the Chinese and
  Japanese versions predated the insiders variables and the MCP transport
  section, so the configuration page listed a configuration surface that no
  longer matched the server.
- **Link fragments now name the target heading's slug in the page's own
  language.** A fragment that matches neither the MyST slug nor the rendered id
  degrades to a plain link: the build stays silent and the link is dead, so both
  the warning-free build and the rendered hrefs were checked.

## [0.6.1] — 2026-10-19

### Changed

- **The three READMEs are rebuilt around the agent skills**: quick start now
  leads with installing the skills, the skills get their own section with the
  install command, a decision diagram and a table grouped by the sections
  `skills.sh.json` declares, and the configuration table gains the ten
  `NOVELAI_*` defaults that were missing. All three languages carry the same 39
  headings; `pnpm readme:check` enforces that they stay in step.

## [0.6.0] — 2026-10-19

### Added

- **`poe sync-versions` / `poe check-versions`**: the canonical version in
  `apps/server/pyproject.toml` is propagated to the three `package.json`
  files and to `server.json` (top-level `.version`, the PyPI entry's
  `version`, and the OCI entry's `identifier` tag) by
  `apps/server/scripts/sync_versions.py`. It replaces the
  `.github/actions/sync-version` composite action and also repaired drift on
  `main`, where the Node manifests were still pinned at `0.3.0` because the
  old write-back only ever reached the release branches.
- **JSON-authored release notes**: `release-notes/<version>.json` is rendered
  into the GitHub Release body by `apps/server/scripts/release_notes.py`
  (required keys enforced, unknown keys rejected, previewable locally); the
  auto-generated commit list is appended below the authored announcement.
- **Opt-in insiders surface (`X-MCP-Insiders`)**: an HTTP client can opt in per
  request and declare which route, model, agent and session it belongs to. While
  `model-routing` is active the server resolves a sanitised route from the
  routing headers (`MCP_AGENT_HEADERS` / `MCP_CLIENT_HEADERS` /
  `MCP_MODEL_HEADERS`, first non-empty wins, falling back to the MCP client's
  advertised name), writes that request's images under
  `<NOVELAI_OUTPUT_DIR>/<route>/` (`MCP_ROUTE_SCOPED_OUTPUT`, default on),
  emits one line to a per-route logger (`novelai_image_mcp.audit.<route>`) and
  appends one record to an append-only JSONL audit trail
  (`MCP_AUDIT_LOG_PATH`, default `<NOVELAI_OUTPUT_DIR>/audit.jsonl`).
  Records carry the route, model, agent, client, session, tool, duration,
  outcome, active features and the sanitised header snapshot; prompts are
  reduced to their length plus a truncated SHA-256 and image arguments are
  redacted, so no prompt text, credential header or base64 payload is ever
  written. Each record is one `os.write` on an `O_APPEND` descriptor, so
  concurrent writers cannot interleave lines. An unwritable trail is logged at
  `ERROR` and swallowed — auditing never fails a tool call.
- **Route-bound bearer tokens (`MCP_ROUTE_TOKENS`)**: a JSON object
  `{"<route>": "<token>"}` registers tokens bound to a route. Such a token
  authenticates as its route and is rejected with `401` when the same request
  declares a _different_ route through the routing headers; a request with no
  usable declared route is accepted and attributed to the token's route, so only
  two different, both-present routes fail closed. `MCP_AUTH_TOKEN` keeps its
  original meaning and never takes part in route checking.
- **Two-sided experimental-tool gate**: tools tagged `insiders` are hidden from
  `tools/list` and refused _by name_ with a `ToolError` unless the client opted
  in, so guessing a name is not a way around the listing filter. No shipped tool
  carries the tag today, which is deliberate — tagging an existing tool would
  remove it from every client that does not send the header.
- **`MCP_INSIDERS_DISABLED_FEATURES`**: an operator kill switch (JSON list)
  that forces features off regardless of what a client sends.

### Changed

- **Releases are tag-driven**: pushing `vX.Y.Z` for a commit that is already
  on `main` runs the whole pipeline — build, PyPI, GHCR, GitHub Release, MCP
  Registry. The `releases/X.Y.Z` trigger branch is gone, and the 11
  historical release branches were deleted (their `vX.Y.Z` tags remain).
- **Nothing is written back to the repository during a release**: the
  workflow verifies that `pyproject.toml`, every manifest, the CHANGELOG
  section and the release-notes document agree with the tag, so a published
  artifact can never disagree with the commit it came from.
- **`director_tool`'s `emotion` and `emotion_level` parameters are now gated**
  by the `experimental-tools` feature. Passing either one without the
  `X-MCP-Insiders` opt-in fails with a `ToolError`; a non-default
  `emotion_level` alone counts as passing it, so the default call shape is
  unaffected. **This is the only intentional behaviour change for a request that
  does not send the header**: every other tool, resource, prompt and schema is
  untouched, generated images keep the flat output layout, and no audit file is
  written. Both parameters stay visible in the tool schema, because a FastMCP
  schema is published when the server starts and cannot vary per request — the
  check runs in the tool body instead.

### Fixed

- **`.env.example` could not be copied to `.env`**: the template ended with a
  bare `MCP_LOG_LEVEL=`, and an empty value is not a valid literal for that
  setting, so the documented "copy to `.env`" step failed at startup with
  `ValidationError: Input should be 'DEBUG', 'INFO', 'WARNING', 'ERROR' or
  'CRITICAL'`. The line is now commented out with a note, and the same trap is
  documented for the list/dict settings (`MCP_MODEL_HEADERS`,
  `MCP_AGENT_HEADERS`, `MCP_CLIENT_HEADERS`,
  `MCP_INSIDERS_DISABLED_FEATURES`, `MCP_ROUTE_TOKENS`), where an empty value
  is not valid JSON either.

### Security

- _Nothing yet._

## [0.5.1] — 2026-10-13

### Added

- **Tool output-contract regression test**: `TestToolOutputContract` drives
  every registered tool through the real FastMCP pipeline (in-memory client,
  production registration, dependency injection, result conversion) and asserts
  that a tool advertising an `outputSchema` also returns
  `structured_content`. It pins the failure mode that made the image tools
  unusable on MCP SDK v2 hosts in 0.4.0
  ([#27](https://github.com/xinvxueyuan/NovelAI-Image-MCP/issues/27)).
- The `fake_client` test double is now `AsyncMock(spec=NovelAIClient)`. A bare
  mock is not an instance of the client, and FastMCP's dependency resolution
  then never handed it to the `Depends(get_client)` tools — the tool received
  an unconfigured sibling mock, so every configured return value was ignored
  (`suggest_tags`, `encode_vibe`, the account tools). The spec also makes the
  double stricter: an unknown method now raises instead of silently returning
  another mock.

### Changed

- _Nothing yet._

### Fixed

- _Nothing yet._

### Security

- **Transitive advisories patched** (all dev/build-time or auth-stack
  dependencies, no API change): `PyJWT` 2.13.0 → 2.15.1 and `urllib3` 2.7.0 →
  2.8.0 in `uv.lock`; `smol-toml` → 1.9.1, `katex` → 0.19.0 and
  `brace-expansion` → 5.0.12 in `pnpm-lock.yaml`. The two npm packages whose
  parents still pin a vulnerable version (`markdownlint-cli2` requires
  `smol-toml=1.8.0`; `micromark-extension-math` requires `katex ^0.16.0`) are
  forced through `pnpm-workspace.yaml` overrides, alongside the existing
  `js-yaml` / `markdown-it` floors.

## [0.5.0] — 2026-10-10

### Added

- **MCP prompts**: `novelai_prompt_writer` turns a plain-language idea into a
  NovelAI-style tag prompt, and `novelai_image_workflow` lays out the tool
  sequence for a goal.
- **MCP resources**: `novelai://models` (model ids + capability flags),
  `novelai://samplers` (sampler / noise-schedule / UC-preset vocabulary),
  `novelai://defaults` (the active generation defaults, no credentials) and the
  `novelai://outputs/{name}` template, which reads a generated PNG back from the
  output directory.
- **Tool metadata**: every tool now publishes a `title`, a set of `tags`, and
  MCP annotations (`readOnlyHint` / `destructiveHint` / `idempotentHint` /
  `openWorldHint`).
- **Structured output**: `suggest_tags` returns `TagSuggestion` objects and
  `estimate_anlas_cost` returns an `AnlasEstimate`, so both carry an output
  schema in addition to their content blocks.
- **Tool-call logging middleware** (`ToolCallLoggingMiddleware`): logs each tool
  name with its wall-clock duration.
- **Optional HTTP bearer auth**: setting `MCP_AUTH_TOKEN` makes the HTTP
  transport require `Authorization: Bearer <token>`. Unset (the default) keeps
  the previous open behaviour; stdio is unaffected either way.
- **Standard FastMCP entry points**: `fastmcp.json` at the repository root,
  plus `apps/server/mcp_server.py` as the path-loadable entry shim, so
  `fastmcp run`, `fastmcp inspect` and `fastmcp dev inspector` all work.
- **New settings**: `MCP_LOG_LEVEL` (forwarded to FastMCP),
  `MCP_AUTH_TOKEN` (optional HTTP bearer token) and `NOVELAI_UPSCALE_MODEL`
  (the V5 model the standalone 4× upscaler runs on).
- **API alignment audit** (`apps/docs/source/development/api-alignment.md`):
  every documented NovelAI endpoint checked against the live API, with the
  doc-lag list that keeps future readers from "fixing" working request fields.

### Changed

- **Framework → fastmcp 4.1.0 (stable)**: the `fastmcp==4.0.0b3` prerelease pin
  and the matching `fastmcp-slim` constraint are gone; the requirement is now
  `fastmcp>=4.1.0,<5` with `mcp>=2.3.0`.
- **Idiomatic FastMCP structure**: tools, resources and prompts attach to the
  shared `mcp` instance with module-level decorators instead of
  `register(mcp)` closures; the `_mcp.py` import shim, `tools/_ctx.py` and the
  `dev_server.py` entry are removed.
- **Dependency injection**: components declare
  `app: AppContext = Depends(get_app_context)` (or `client` / `settings`)
  instead of reading `ctx.lifespan_context` behind a `cast`.
- **Tool parameter tightening (schema change)**: `model`, `sampler`,
  `noise_schedule`, `action`, `tool`, `emotion` and `factor` are enums
  (`Model`, `Sampler`, `NoiseSchedule`, `Action`, `DirectorTool`, `Emotion`,
  `Literal[2, 4]`), and numeric parameters carry documented bounds
  (`n_samples` 1-8, `strength` 0.01-0.99, `information_extracted` 0.01-1.0, ...).
  Tool names, parameter names and defaults are unchanged, and direct Python
  callers may still pass plain strings — but MCP clients must refresh their
  cached tool schemas.
- **Error surface**: expected failures (NovelAI domain errors, validation
  failures) are raised as `ToolError` with their real message; the server runs
  with `mask_error_details=True`, so unexpected exceptions no longer leak
  internal details to clients.
- **Transport naming**: `http` is now the canonical `MCP_TRANSPORT` value;
  `streamable-http` is accepted as a legacy alias for both the setting and
  `serve --transport`.
- **Documentation**: architecture, testing, configuration and transport pages
  describe the decorator/DI structure, the new environment variables and the
  standard FastMCP commands.

### Fixed

- **`upscale_image` was broken (live-verified)**: NovelAI moved `/ai/upscale`
  to `image.novelai.net`, changed the body to
  `{image, model, declared_blur_sigma}` and made it **V5-only** — the previous
  request to `api.novelai.net/ai/upscale` now returns 404. The client posts to
  the image host, sends the documented body, defaults the model to the new
  `NOVELAI_UPSCALE_MODEL` (`nai-diffusion-5-full`), and rejects anything but a
  4× step (the API exposes no scaling factor; `2` is refused before any
  request).
- **`suggest_tags` published the wrong fields**: the tagger returns
  `{tag, count, confidence}` (verified live), not
  `{description, text, count}`, so `TagSuggestion` and the docs now mirror the
  wire shape.
- **`MCP_PATH` had no effect**: the configured HTTP endpoint path is now passed
  to FastMCP, so the server actually listens on it (default `/mcp` unchanged).
- **Framework version reported as the server version**: `FastMCP` now receives
  `version=__version__`, so `fastmcp inspect` shows `0.4.0` rather than the
  fastmcp release it happens to run.
- **HTTP authentication guidance was wrong**: the server never accepted a
  NovelAI token as a bearer credential; the docs now describe the real model
  (server-side `NOVELAI_TOKEN`, optional client-side `MCP_AUTH_TOKEN`).

## [0.3.0] — 2026-08-01

### Added

- **Agent skills documentation**: dedicated docs page for the three
  skills.sh packages (`novelai-cli`, `novelai-mcp-tools`,
  `novelai-workflows`), plus README / quickstart links and a contributing
  guide section for authoring new skills.

### Changed

- **Dependency stabilization**: require MCP SDK v2 `mcp>=2.0.0` (stable),
  replacing the `2.0.0b2` beta pin and dropping the workspace-wide
  `prerelease = "allow"` uv setting. `curl-cffi` now resolves to the stable
  `0.15.0` release instead of a pre-release beta. All `uvx` install
  snippets no longer need `--prerelease=allow` (README, docs, and
  agent-host config examples updated).

## [0.2.0] — 2026-07-29

### Added

- **Agent skills for skills.sh ecosystem**: three modular agent skills
  (`novelai-cli`, `novelai-mcp-tools`, `novelai-workflows`) installable
  via `npx skills add xinvxueyuan/NovelAI-Image-MCP`. Each follows the
  official skills.sh scaffold (frontmatter with `name` + `description`,
  `## When to use` → `## Instructions` body) and distributes guidance
  on demand: CLI usage for shell scripting, MCP tool reference for
  interactive agent sessions, and multi-step workflow recipes for
  creative pipelines. Wired up in `skills.sh.json` under CLI / MCP
  Tools / Workflows groupings. README badges advertise the skills.

## [0.1.5] — 2026-07-26

### Fixed

- **Fix MCP Registry PyPI ownership verification**: the `mcp-name:` marker was
  added to the repository root `README.md` in 0.1.4, but the PyPI package's
  long description is sourced from `apps/server/README.md` (per
  `readme = "README.md"` in `apps/server/pyproject.toml`, resolved relative to
  that file). The registry's PyPI validation fetches
  `pypi.org/pypi/novelai-image-mcp/json` and scans the `description` field for
  the marker — which was missing. Added the marker to `apps/server/README.md`
  so the PyPI package metadata includes it.
- **Drop forbidden `version` field from OCI package entry in `server.json`**:
  the MCP Registry schema rejects `version` on OCI packages — the version
  must be embedded in the `identifier` (e.g.
  `ghcr.io/.../novelai-image-mcp:0.1.5`), not duplicated as a sibling field.
  PyPI packages keep their `version` field (expected for PyPI); only the OCI
  entry was wrong.
- **Correct jq path in `publish-mcp.yml` verify step**: the registry v0
  search API nests each server payload under `.server`
  (`{"servers":[{"server":{"name":"..."}, "_meta":{...}}]}`), but the verify
  step filtered on `.servers[] | select(.name == ...)` — which never matched
  because `.name` is undefined at that level. The publish step had already
  succeeded; only the verification gave a false negative. Fixed to
  `.servers[] | select(.server.name == ...)`.

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

[Unreleased]: https://github.com/xinvxueyuan/NovelAI-Image-MCP/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/xinvxueyuan/NovelAI-Image-MCP/releases/tag/v0.2.0
[0.1.5]: https://github.com/xinvxueyuan/NovelAI-Image-MCP/releases/tag/v0.1.5
[0.1.4]: https://github.com/xinvxueyuan/NovelAI-Image-MCP/releases/tag/v0.1.4
[0.1.3]: https://github.com/xinvxueyuan/NovelAI-Image-MCP/releases/tag/v0.1.3
[0.1.2]: https://github.com/xinvxueyuan/NovelAI-Image-MCP/releases/tag/v0.1.2
[0.1.1]: https://github.com/xinvxueyuan/NovelAI-Image-MCP/releases/tag/v0.1.1
[0.1.0]: https://github.com/xinvxueyuan/NovelAI-Image-MCP/releases/tag/v0.1.0
