# NovelAI Image MCP — Documentation Site

Sphinx + MyST + Furo documentation site for the NovelAI Image MCP project.

## Build

The docs site is a uv workspace member (`novelai-image-mcp-docs`). It pulls
the MCP server package from the workspace (`{ workspace = true }`) so Sphinx
autodoc can introspect the in-tree `novelai_image_mcp` source.

### One-time setup

```bash
# From the repository root — syncs all workspace members into one virtualenv.
uv sync
```

### Build the HTML site

```bash
# Option A — uv (workspace-aware)
uv run --package novelai-image-mcp-docs sphinx-build -b html apps/docs/source apps/docs/_build/html

# Option B — turbo (also builds server first, then docs)
pnpm docs:build

# Option C — Makefile (run inside apps/docs/)
cd apps/docs && uv run --package novelai-image-mcp-docs make html
```

The rendered site lives at `apps/docs/_build/html/index.html`.

### Live-reload during development

```bash
uv run --package novelai-image-mcp-docs sphinx-autobuild apps/docs/source apps/docs/_build/html --open-browser
# Or via turbo:
pnpm docs:serve
```

### Link check

```bash
uv run --package novelai-image-mcp-docs sphinx-build -b linkcheck apps/docs/source apps/docs/_build/linkcheck
```

## Multi-language builds

The docs site supports English (default), Chinese (`zh`), and Japanese (`ja`).
Each language lives under `source/<code>/` and is built independently against
the shared `conf.py` (via `-c source` and `-D language=<code>`).

### Build all languages

```bash
# Via Makefile (run inside apps/docs/)
uv run --package novelai-image-mcp-docs make html-all

# Or via turbo (from the repository root)
pnpm docs:build:all
```

### Build a single language

```bash
# English (default)
uv run --package novelai-image-mcp-docs make html

# Chinese
uv run --package novelai-image-mcp-docs make html-zh

# Japanese
uv run --package novelai-image-mcp-docs make html-ja
```

### Live preview (with autobuild)

```bash
uv run --package novelai-image-mcp-docs make livehtml      # English
uv run --package novelai-image-mcp-docs make livehtml-zh   # Chinese
uv run --package novelai-image-mcp-docs make livehtml-ja   # Japanese
```

### Output layout

Builds are written to `_build/`:

```text
_build/
├── html/       # English (root)
├── zh/html/    # Chinese
└── ja/html/    # Japanese
```

The CI workflow (`.github/workflows/docs.yml`) builds all three languages via
a parallel matrix and combines them into a single GitHub Pages artifact with
subpath layout: English at `/`, Chinese at `/zh/`, Japanese at `/ja/`.

## Deployment

GitHub Pages deployment is automated via `.github/workflows/docs.yml`. On every
push to `main` that touches `apps/docs/**` or `apps/server/src/**`, the workflow
builds the site and publishes it to GitHub Pages.

## Layout

```text
apps/docs/
├── source/
│   ├── conf.py            # Sphinx configuration (shared by all languages)
│   ├── index.md           # Landing page (English)
│   ├── installation.md    # Installation guide
│   ├── quickstart.md      # Quick start
│   ├── configuration.md   # Configuration reference
│   ├── tools/             # Tool reference (one page per tool group)
│   ├── tutorials/         # End-to-end tutorials
│   ├── transports/        # stdio / streamable-http guides
│   ├── development/        # Architecture, contributing, testing, releasing
│   ├── api/                # API reference (autodoc)
│   ├── about/              # License, changelog
│   ├── _static/             # Custom CSS, logos, favicons
│   ├── _templates/          # Sphinx Jinja templates
│   ├── zh/                  # Chinese source tree (mirrors translated pages)
│   └── ja/                  # Japanese source tree (mirrors translated pages)
├── pyproject.toml          # Docs project + Sphinx dependencies
├── Makefile                # sphinx-build / live / linkcheck / clean + i18n targets
├── package.json            # turbo-script wrappers
└── README.md               # This file
```

## License

MIT — see [LICENSE](../../LICENSE). Per-file SPDX annotations live in
[REUSE.toml](../../REUSE.toml).
