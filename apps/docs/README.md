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

## Deployment

GitHub Pages deployment is automated via `.github/workflows/docs.yml`. On every
push to `main` that touches `apps/docs/**` or `apps/server/src/**`, the workflow
builds the site and publishes it to GitHub Pages.

## Layout

```text
apps/docs/
├── source/
│   ├── conf.py            # Sphinx configuration
│   ├── index.md           # Landing page
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
│   └── _templates/          # Sphinx Jinja templates
├── pyproject.toml          # Docs project + Sphinx dependencies
├── Makefile                # sphinx-build / live / linkcheck / clean targets
├── package.json            # turbo-script wrappers
└── README.md               # This file
```

## License

MIT — see [LICENSE](../../LICENSE). Per-file SPDX annotations live in
[REUSE.toml](../../REUSE.toml).
