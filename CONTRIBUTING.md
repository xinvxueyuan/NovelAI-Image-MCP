# Contributing to NovelAI Image MCP

Thanks for your interest in contributing! This document covers everything you
need to get a local development environment running and to land a change.

> 📖 The full developer guide (architecture, testing, releasing) lives on the
> [docs site](https://xinvxueyuan.github.io/NovelAI-Image-MCP/development/).
> This README is the short-form "first PR" guide.

## Repository layout

This is a **uv + pnpm monorepo** orchestrated by **Turbo**:

```text
NovelAI-Image-MCP/
├── apps/
│   ├── server/                 # uv workspace member — MCP server (PyPI package)
│   │   ├── src/novelai_image_mcp/
│   │   ├── tests/
│   │   ├── docker/              # smoke-test entrypoint
│   │   ├── Dockerfile           # built with repo root as context
│   │   ├── pyproject.toml       # ruff / pyright / pytest config
│   │   └── package.json         # turbo-script wrappers
│   └── docs/                    # uv workspace member — Sphinx site (virtual)
│       ├── source/              # MyST Markdown sources + conf.py
│       ├── Makefile
│       ├── pyproject.toml       # Sphinx deps; pulls server via `{ workspace = true }`
│       └── package.json
├── .github/                     # workflows, CODEOWNERS, issue templates
├── .husky/                      # pre-commit + commit-msg hooks
├── pyproject.toml               # uv workspace root (virtual, no deps)
├── uv.lock                      # single shared lockfile for both members
├── pnpm-workspace.yaml          # pnpm workspace declaration (apps/*)
├── pnpm-lock.yaml               # Node toolchain lockfile
├── turbo.json                   # cross-workspace task graph
├── package.json                 # root scripts + dev toolchain
├── prek.toml                    # pre-commit hook config
├── REUSE.toml                   # SPDX license annotations
└── docker-compose.yml           # local container orchestration
```

- **Python tooling** is uv-managed: one virtualenv at the repo root holds
  both `apps/server` (the installable package) and `apps/docs` (a virtual
  project). Run `uv sync` to materialize it.
- **Node tooling** is pnpm-managed and only used for the cross-cutting
  toolchain (turbo, husky, markdownlint-cli2, rimraf). No workspace package
  ships Node runtime code.
- **Turbo** orchestrates cross-workspace tasks (`turbo run build`, `lint`,
  `test`, `serve`, `clean`) with caching and dependency ordering.

## Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| [uv](https://docs.astral.sh/uv/) | ≥ 0.5 | Python package + workspace manager |
| [Node.js](https://nodejs.org/) | ≥ 24 | Required by pnpm + husky + markdownlint |
| [pnpm](https://pnpm.io/) | ≥ 10 (via `corepack enable pnpm`) | Node toolchain |
| [Docker](https://www.docker.com/) | ≥ 24 (optional) | Local container builds |

## First-time setup

```bash
# 1. Clone
git clone https://github.com/xinvxueyuan/NovelAI-Image-MCP.git
cd NovelAI-Image-MCP

# 2. Sync the Python workspace (installs server + docs + dev tools)
uv sync

# 3. Install the Node toolchain (turbo + husky + markdownlint)
corepack enable pnpm      # one-time, if pnpm isn't already on PATH
pnpm install --frozen-lockfile

# 4. Configure credentials (for runtime testing only)
cp .env.example .env
#   edit .env → set NOVELAI_TOKEN=pst-...
```

`pnpm install` automatically wires the husky hooks (see `prepare` in
`package.json`).

## Day-to-day commands

### via Turbo (preferred — caches + parallelizes)

```bash
pnpm build           # build all workspace members (server wheel + docs HTML)
pnpm lint            # ruff (server) + markdownlint (docs)
pnpm typecheck       # pyright (server)
pnpm test            # pytest (server)
pnpm format          # ruff format (server)
pnpm check           # lint + typecheck + test
pnpm clean           # remove all build artifacts

pnpm docs:build      # build only the docs site
pnpm docs:serve      # sphinx-autobuild with live reload
pnpm server:build     # build only the server wheel + sdist
pnpm server:serve     # run the MCP server (stdio)
```

### via uv (when you need to scope to one member)

```bash
# Server (the installable package)
uv run --directory apps/server ruff check src tests
uv run --directory apps/server ruff format src tests
uv run --directory apps/server -m pyright
uv run --directory apps/server -m pytest
uv run --package novelai-image-mcp build              # build wheel + sdist

# Docs
uv run --package novelai-image-mcp-docs sphinx-build -b html apps/docs/source apps/docs/_build/html
uv run --package novelai-image-mcp-docs sphinx-autobuild apps/docs/source apps/docs/_build/html

# Repo-wide
uv run reuse lint     # FSFE REUSE 3.0 license compliance
```

## Commit message format

Commits MUST follow [gitmoji](https://gitmoji.dev/) +
[Conventional Commits](https://www.conventionalcommits.org/):

```text
<gitmoji> <type>[!](<scope>)?[!]: <subject>

[body]

[footer(s)]
```

- `type` ∈ `feat | fix | docs | style | refactor | perf | test | build | ci | chore | revert`
- `!` after `type` *or* after `scope` marks a breaking change
- The `commit-msg` hook auto-appends `Signed-off-by` for
  [DCO](https://developercertificate.org/) compliance

### Examples

```text
✨ feat: add NovelAI V4.5 inpainting tool
🐛 fix(generate): handle zero-seed randomization
♻️ refactor(client)!: rename generate() to generate_image()
📝 docs: document the lifespan AppContext contract
🔧 build(deps): bump mcp from 2.0.0b2 to 2.0.0b3
```

## Pre-commit hooks

Hooks are wired via husky (`.husky/pre-commit` + `.husky/commit-msg`):

| Phase | Tool | Trigger |
|---|---|---|
| 1 | prek (ruff --fix + ruff-format + general hooks) | always |
| 2 | markdownlint-cli2 | only on `.md` changes |
| 3 | pyright | only on `apps/server/**/*.py` changes |
| 4 | pytest | only on `apps/server/**/*.py` changes |

Bypass with `git commit --no-verify` **only** for WIP commits — never for
PRs targeting `main`.

## Pull request checklist

- [ ] Branch is up to date with `main`
- [ ] Commit messages follow the gitmoji + Conventional Commits format
- [ ] `pnpm check` passes locally
- [ ] `uv run reuse lint` passes
- [ ] New tools / settings have docs (under `apps/docs/source/`)
- [ ] New dependencies are added to the correct member's `pyproject.toml`
      (server runtime → `apps/server`, docs build → `apps/docs`, repo-wide
      dev → root `pyproject.toml`)
- [ ] `uv.lock` and `pnpm-lock.yaml` are regenerated if deps changed

## Adding a new MCP tool

1. Create `apps/server/src/novelai_image_mcp/tools/<name>.py` with a
   `register(mcp: MCPServer) -> None` function.
2. Wire it into `apps/server/src/novelai_image_mcp/tools/__init__.py`.
3. Add tests at `apps/server/tests/test_tools.py` (extend the existing
   parametrized cases).
4. Document the tool at `apps/docs/source/tools/<name>.md` and add it to
   the toctree in `apps/docs/source/index.md`.
5. Add a row to the tools table in `README.md` + `README-zh.md`.

## Translating docs

The docs site supports multiple languages via per-language source trees.
English lives at the `apps/docs/source/` root; each additional language
lives under `apps/docs/source/<lang-code>/` (e.g., `source/zh/`,
`source/ja/`). All languages share the same `conf.py`.

### Rules

1. **Full translations only — no stubs.** A translated page must cover
   the full English source. Code blocks remain unchanged; only prose is
   translated. Do NOT create "translation in progress" placeholder
   pages — they break the build's `-W` warning gate and confuse users.

2. **Toctree scope = translated pages only.** The `index.md` toctree in
   each language directory must only reference pages that exist under
   that language's directory. If a section (e.g., `tools/`,
   `tutorials/`) is not translated, omit it from the translated
   toctree — users switch to English for untranslated sections.

3. **Preserve MyST directives.** Keep all MyST syntax (`:::tip`,
   `=== "Unix"` tabs, `{toctree}`, `{image}`, etc.) intact. Only
   translate the prose inside them.

4. **CJK punctuation in headings.** `MD026` forbids trailing `.,;:!` in
   headings — use `。、！？` instead. (`MD013` line-length is disabled,
   so long CJK lines are fine.)

### Adding a new language

1. Create `apps/docs/source/<code>/` with at minimum `index.md`.
2. Add the language to `AVAILABLE_LANGUAGES` in
   `apps/docs/source/conf.py` (tuple of `(code, label, base_path)`).
3. Add the language to the matrix in `.github/workflows/docs.yml`.
4. Build locally and confirm zero warnings:

   ```bash
   uv run --package novelai-image-mcp-docs sphinx-build -b html \
     apps/docs/source/<code> apps/docs/_build/<code>/html \
     -c apps/docs/source -D language=<code> -W --keep-going
   ```

### Keeping translations in sync

When English source changes, update the translated page in the same PR
if practical. Translated pages that fall badly out of sync should be
deleted rather than left stale — a missing translation is better than a
misleading one.

## License

By contributing, you agree that your contributions will be licensed under the
[MIT License](LICENSE). The project follows
[DCO](https://developercertificate.org/) (Developer Certificate of Origin);
the `commit-msg` hook signs off your commits automatically.
