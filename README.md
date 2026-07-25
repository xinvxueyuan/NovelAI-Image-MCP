# NovelAI Image MCP

[![CI](https://github.com/xinvxueyuan/NovelAI-Image-MCP/actions/workflows/ci.yml/badge.svg)](https://github.com/xinvxueyuan/NovelAI-Image-MCP/actions/workflows/ci.yml)
[![Docs](https://github.com/xinvxueyuan/NovelAI-Image-MCP/actions/workflows/docs.yml/badge.svg)](https://xinvxueyuan.github.io/NovelAI-Image-MCP/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-managed-261230.svg)](https://docs.astral.sh/uv/)
[![REUSE status](https://api.reuse.software/badge/github.com/xinvxueyuan/NovelAI-Image-MCP)](https://api.reuse.software/info/github.com/xinvxueyuan/NovelAI-Image-MCP)
[![DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/xinvxueyuan/NovelAI-Image-MCP)

<a href="https://www.producthunt.com/products/novelai-image-mcp?embed=true&utm_source=badge-featured&utm_medium=badge&utm_campaign=badge-novelai-image-mcp" target="_blank" rel="noopener noreferrer"><img alt="NovelAI Image MCP - MCP server for integrating NovelAI Image generation into AI | Product Hunt" width="250" height="54" src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=1206099&theme=light&t=1784973837616"></a>

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that
exposes **NovelAI image generation** as tools for AI agents (Claude Desktop,
Cline, custom agents, remote clients).

Built on the official MCP Python SDK v2 (`MCPServer`), it lets an agent generate
images (txt2img / img2img / inpaint), upscale, run Director tools (line art,
emotion, background removal, …), annotate with ControlNet, suggest tags, encode
vibes, and query account subscription — all through the standard MCP tool
interface.

> 📖 **Documentation**: <https://xinvxueyuan.github.io/NovelAI-Image-MCP/>

## Features

- **11 MCP tools** covering the full NovelAI image API surface.
- **Two transports**: stdio (local agents) + streamable-http (remote / multi-client).
- **Dual image return**: base64 `Image` content blocks (the agent *sees* the image)
  **and** PNG saved to disk (path returned as text).
- **Async + sync**: async tool handlers + a `typer` CLI for direct invocation.
- **Monorepo**: uv workspace (Python) + pnpm workspace (Node tooling) orchestrated
  by Turbo; MIT-licensed, Docker-ready, GitHub Pages docs.

## Repository layout

This is a **uv + pnpm monorepo**:

```text
NovelAI-Image-MCP/
├── apps/
│   ├── server/                 # MCP server (the installable PyPI package)
│   │   ├── src/novelai_image_mcp/   # 11 MCP tools + NovelAI HTTP client
│   │   ├── tests/
│   │   ├── docker/              # smoke-test entrypoint
│   │   ├── Dockerfile           # built with repo root as context
│   │   └── pyproject.toml       # ruff / pyright / pytest config
│   └── docs/                    # Sphinx documentation site
│       ├── source/              # MyST Markdown + conf.py
│       ├── Makefile
│       └── pyproject.toml
├── .github/                     # workflows, CODEOWNERS, issue templates
├── pyproject.toml               # uv workspace root (virtual)
├── uv.lock                      # single shared lockfile
├── pnpm-workspace.yaml          # pnpm workspace declaration
├── pnpm-lock.yaml               # Node toolchain lockfile
├── turbo.json                   # cross-workspace task graph
├── package.json                 # root scripts + dev toolchain
└── docker-compose.yml           # local container orchestration
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the developer guide and
[`apps/docs/source/`](apps/docs/source/) for the full documentation source.

## Quick start

### Install from source (development)

```bash
# 1. Clone
git clone https://github.com/xinvxueyuan/NovelAI-Image-MCP.git
cd NovelAI-Image-MCP

# 2. Sync the uv workspace (installs server + docs + dev tools)
uv sync

# 3. Configure credentials
cp .env.example .env
#   set NOVELAI_TOKEN=...  (preferred)
#   or  NOVELAI_USERNAME + NOVELAI_PASSWORD

# 4. Run (stdio — for local agents)
uv run python -m novelai_image_mcp serve

# 5. Or over HTTP
MCP_TRANSPORT=streamable-http uv run python -m novelai_image_mcp serve
#   → http://127.0.0.1:8000/mcp
```

### Install from PyPI (runtime only)

```bash
pip install novelai-image-mcp
export NOVELAI_TOKEN=pst-...
novelai-image-mcp serve
```

### Optional: Node tooling (contributors)

If you plan to contribute, install the cross-cutting Node toolchain (turbo,
husky, markdownlint) via pnpm:

```bash
corepack enable pnpm      # one-time
pnpm install --frozen-lockfile
```

This wires the husky pre-commit + commit-msg hooks and gives you `turbo` /
`markdownlint-cli2` for local development. The MCP server has **zero** Node
runtime dependencies — this step is only for contributors.

## Connect an agent

The MCP server supports three configuration shapes, all under `mcpServers`:

### stdio (local agent — Claude Desktop / Cline)

`claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "novelai-image": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/NovelAI-Image-MCP",
        "python",
        "-m",
        "novelai_image_mcp",
        "serve"
      ],
      "env": {
        "NOVELAI_TOKEN": "${input:novelai_token}"
      }
    }
  }
}
```

### uvx (shorthand — runs the published package)

```json
{
  "mcpServers": {
    "novelai-image-uvx": {
      "type": "uvx",
      "args": ["novelai-image-mcp", "serve"]
    }
  }
}
```

Set `NOVELAI_TOKEN` (or `NOVELAI_USERNAME` + `NOVELAI_PASSWORD`) in the host
environment before launching — `uvx` inherits the parent shell env.

### http (remote / Docker deployment)

After `docker compose up --build` (server listens on `http://HOST:8000/mcp`):

```json
{
  "mcpServers": {
    "novelai-image-http": {
      "type": "http",
      "url": "https://mcp.example.com/v1/",
      "headers": {
        "Authorization": "Bearer ${input:novelai_token}"
      }
    }
  }
}
```

`${input:novelai_token}` is a host-defined secret reference (Claude Desktop,
Cline, etc. expose this via their own secrets UI). For local Docker you can
use a literal token instead.

## CLI (sync, for scripting)

```bash
uv run python -m novelai_image_mcp generate --prompt "a cat, masterpiece" --width 832 --height 1216
uv run python -m novelai_image_mcp upscale --image ./in.png --factor 4
uv run python -m novelai_image_mcp info          # subscription / Anlas balance
uv run python -m novelai_image_mcp --help
```

## Tools

| Tool | Description |
|---|---|
| `generate_image` | Text-to-image (V3 / V4 / V4.5 models, character prompts, vibes) |
| `image_to_image` | Image-to-image with strength/noise |
| `inpaint` | Inpainting (requires an inpaint model + mask) |
| `upscale_image` | 2× / 4× upscale |
| `director_tool` | Line art / sketch / bg-removal / declutter / colorize / emotion |
| `annotate_image` | ControlNet annotation (hed, midas, scribble, mlsd, uniformer) |
| `suggest_tags` | Prompt tag suggestions |
| `encode_vibe` | Encode a reference image into a vibe token |
| `get_subscription` | Account subscription + Anlas balance |
| `get_user_data` | Account user data |
| `estimate_anlas_cost` | Estimate Anlas cost for a generation (no API call) |

See the [tools reference](https://xinvxueyuan.github.io/NovelAI-Image-MCP/tools/index.html)
on the docs site for parameters and examples.

## Configuration

All settings are environment variables (see `.env.example`). Key ones:

| Variable | Default | Notes |
|---|---|---|
| `NOVELAI_TOKEN` | — | Persistent API token (preferred auth) |
| `NOVELAI_USERNAME` / `NOVELAI_PASSWORD` | — | Access-key login (argon2id) |
| `NOVELAI_OUTPUT_DIR` | `outputs` | Where generated PNGs are saved |
| `MCP_TRANSPORT` | `stdio` | `stdio` or `streamable-http` |
| `MCP_HOST` / `MCP_PORT` | `127.0.0.1` / `8000` | For streamable-http |

NovelAI API reference: <https://image.novelai.net/docs/index.html>

## Development

The project is a uv + pnpm monorepo orchestrated by Turbo. See
[`CONTRIBUTING.md`](CONTRIBUTING.md) for the full setup; the short version:

```bash
uv sync                              # Python workspace (server + docs + dev)
pnpm install --frozen-lockfile       # Node toolchain (turbo + husky + markdownlint)

pnpm check                           # lint + typecheck + test (all workspaces)
pnpm docs:build                       # build the docs site
pnpm server:serve                     # run the MCP server
pnpm docs:serve                       # sphinx-autobuild with live reload
```

Per-member commands (via uv):

```bash
uv run --directory apps/server ruff check src tests    # lint
uv run --directory apps/server -m pyright              # typecheck
uv run --directory apps/server -m pytest               # tests
```

### Docker

```bash
docker compose up --build      # builds and runs the server (HTTP transport)
```

The Dockerfile lives at [`apps/server/Dockerfile`](apps/server/Dockerfile) but
the build context is the repository root (so uv can resolve the workspace
graph). See [`docker-compose.yml`](docker-compose.yml).

## Documentation

The Sphinx documentation site is built with Furo + MyST Markdown and
auto-deploys to GitHub Pages on every push to `main`:

- **Live site**: <https://xinvxueyuan.github.io/NovelAI-Image-MCP/>
- **Source**: [`apps/docs/source/`](apps/docs/source/)
- **Build locally**: `pnpm docs:serve`

## License

MIT — see [LICENSE](LICENSE). Per-file SPDX annotations live in
[REUSE.toml](REUSE.toml). Contributions are subject to the
[Developer Certificate of Origin](https://developercertificate.org/) (the
`commit-msg` hook signs off commits automatically).
