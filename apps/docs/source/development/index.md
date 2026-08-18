# Development

How to hack on the NovelAI Image MCP server itself.

```{toctree}
:maxdepth: 1
:hidden:

architecture
contributing
testing
releasing
```

## Quick start

```bash
# 1. Clone + sync the workspace virtualenv
git clone https://github.com/xinvxueyuan/NovelAI-Image-MCP.git
cd NovelAI-Image-MCP
uv sync

# 2. Install Node tooling (turbo, husky, markdownlint) — optional but recommended
corepack enable pnpm
pnpm install --frozen-lockfile

# 3. Run all checks
uv run --directory apps/server poe check
# or via turbo:
pnpm check  # (runs: pnpm lint, pnpm typecheck, pnpm test via turbo)
```

## Repository layout

```text
NovelAI-Image-MCP/
├── apps/
│   ├── server/                     # ← MCP server (Python package)
│   │   ├── src/novelai_image_mcp/
│   │   │   ├── server.py           # FastMCP server + lifespan
│   │   │   ├── settings.py         # pydantic-settings env config
│   │   │   ├── cli.py / __main__.py  # typer sync CLI
│   │   │   ├── output.py           # save-image helper
│   │   │   ├── tools/              # 11 MCP tool definitions
│   │   │   │   ├── generate.py     # generate_image / image_to_image / inpaint
│   │   │   │   ├── enhance.py      # upscale / director / annotate
│   │   │   │   ├── tags.py         # suggest_tags / encode_vibe
│   │   │   │   └── account.py      # subscription / user_data / cost
│   │   │   └── nai/                # NovelAI HTTP client (httpx transport)
│   │   ├── tests/                  # pytest + respx
│   │   ├── docker/smoke-test.py    # container entrypoint smoke test
│   │   ├── Dockerfile              # multi-stage production image
│   │   ├── pyproject.toml          # server project + tool config (ruff/pyright/pytest/poe)
│   │   └── package.json            # turbo-script wrappers (no Node deps)
│   └── docs/                       # ← Sphinx documentation site
│       ├── source/                # MyST markdown sources
│       │   ├── conf.py             # Sphinx configuration
│       │   ├── *.md                # narrative docs
│       │   └── api/                # autodoc API reference
│       ├── Makefile                # sphinx-build / live / linkcheck targets
│       ├── pyproject.toml          # docs deps (sphinx, myst, furo)
│       └── package.json            # turbo-script wrappers
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                  # ruff / pyright / pytest / docker smoke
│   │   ├── docs.yml                # GitHub Pages deploy
│   │   └── release.yml             # PyPI + GHCR + GitHub Release
│   └── actions/detect-changes/     # composite change-detection action
├── docker-compose.yml              # orchestrates the server image
├── pyproject.toml                  # uv workspace root (virtual)
├── uv.lock                         # unified Python lockfile
├── pnpm-workspace.yaml             # pnpm workspace declaration
├── package.json                    # root workspace + turbo + husky + markdownlint
├── pnpm-lock.yaml                  # unified Node lockfile
├── turbo.json                      # cross-workspace task definition
├── prek.toml                       # pre-commit hook config
├── .husky/pre-commit               # husky pre-commit hook (4 phases)
├── REUSE.toml                      # SPDX license declarations
└── .markdownlint-cli2.jsonc        # markdown lint config
```

## Common commands

| Action | Command |
|---|---|
| Sync all deps | `uv sync` |
| Run server (stdio) | `uv run python -m novelai_image_mcp serve` |
| Run server (http) | `MCP_TRANSPORT=streamable-http uv run python -m novelai_image_mcp serve` |
| Run tests | `uv run --directory apps/server pytest` |
| Lint Python | `uv run --directory apps/server ruff check src tests` |
| Format Python | `uv run --directory apps/server ruff format src tests` |
| Type-check | `uv run --directory apps/server pyright` |
| All checks | `uv run --directory apps/server poe check` |
| Build docs | `uv run --package novelai-image-mcp-docs sphinx-build -b html apps/docs/source apps/docs/_build/html` |
| Live docs | `uv run --package novelai-image-mcp-docs sphinx-autobuild apps/docs/source apps/docs/_build/html` |
| REUSE compliance | `uv run reuse lint` |

The same commands work via turbo once `pnpm install` has run:

| Action | Turbo command |
|---|---|
| Build all workspaces | `pnpm build` |
| Lint all workspaces | `pnpm lint` |
| Type-check | `pnpm typecheck` |
| Test all workspaces | `pnpm test` |
| Format | `pnpm format` |
| Build docs only | `pnpm docs:build` |
| Live docs | `pnpm docs:serve` |
| Clean all artifacts | `pnpm clean` |

## Contributing

See [Contributing](contributing.md). TL;DR:

1. Open an issue describing your change.
2. Branch off `main`.
3. Implement + add tests.
4. `uv run --directory apps/server poe check` must pass.
5. Open a PR with a clear description.

## Testing

See [Testing](testing.md) for the test layout, fixture strategy, and how to
run a specific test.

## Releasing

See [Releasing](releasing.md) for the cut-a-release process (PyPI + GHCR +
GitHub Release + cosign signing).

## Architecture

See [Architecture](architecture.md) for the server's composition root, the
`NovelAIClient` design, and how tools wire into the MCP lifespan.
