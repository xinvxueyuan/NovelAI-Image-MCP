# NovelAI Image MCP

## Languages

| English | 简体中文 | 日本語 |
|---|---|---|
| [English](README.md) | [简体中文](.github/docs/README-zh.md) | [日本語](.github/docs/README-ja.md) |

[![CI][ci-badge]][ci-workflow]
[![Docs][docs-badge]][docs]
[![License: MIT][mit-badge]][license]
[![Python 3.13+][python-badge]][python]
[![uv][uv-badge]][uv]
[![REUSE status][reuse-badge]][reuse]
[![DeepWiki][deepwiki-badge]][deepwiki]
[![skills.sh][skills-badge]][skills-sh]

[![NovelAI Image MCP - MCP server for integrating NovelAI Image generation into AI | Product Hunt][product-hunt-badge]][product-hunt] [![Featured on Lifto][lifto-badge]][lifto]

An [MCP (Model Context Protocol)][mcp] server that exposes **NovelAI image
generation** to AI agents (Claude Desktop, Cline, custom agents, remote
clients), plus a sync CLI and three [skills.sh][skills-site] packages that teach
those agents how to drive either surface.

Built on FastMCP 4 (the fastmcp framework over the MCP SDK v2 `mcp>=2.3.0`),
it covers txt2img / img2img / inpaint, 4× upscale, Director tools (line art,
emotion, background removal, …), ControlNet annotation, tag suggestions, vibe
encoding and account subscription — all through the standard MCP tool
interface.

> 📖 **Documentation**: [xinvxueyuan.github.io/NovelAI-Image-MCP][docs]

## Three ways to drive it

All three wrap the same async `NovelAIClient`; they differ in how you invoke
it.

- **MCP tools** — interactive agent sessions (Claude Desktop, Cline, …). The
  agent sees base64 `Image` content blocks.
- **CLI** — shell scripting, CI jobs, one-off commands. Saves a PNG and prints
  its path; no image blocks.
- **Agent skills** — portable instructions that tell an agent how to use the
  other two. They inherit the mode they drive.

## Features

- **11 MCP tools** covering the full NovelAI image API surface.
- **2 prompts + 3 resources + 1 resource template**: house-style prompt drafting and tool sequencing
  (`novelai_prompt_writer`, `novelai_image_workflow`), plus `novelai://models`,
  `novelai://samplers`, `novelai://defaults` and `novelai://outputs/{name}` for
  discovering the model/sampler vocabulary and reading generated PNGs back.
- **Three agent skills** (`novelai-cli`, `novelai-mcp-tools`,
  `novelai-workflows`) grouped as CLI / MCP Tools / Workflows, installable with
  one `npx skills add` command.
- **A sync `typer` CLI** with six subcommands for scripting outside an MCP host.
- **Two transports**: stdio (local agents) + HTTP (remote / multi-client), the
  latter optionally protected by a bearer token (`MCP_AUTH_TOKEN`).
- **Opt-in routing and audit (HTTP)**: a client that sends `X-MCP-Insiders`
  gets per-route output directories, per-route loggers and an append-only JSONL
  audit trail (prompts and credentials are never written verbatim). Without the
  header nothing changes. See
  [Insiders header, routing and audit][insiders-docs].
- **Structured results**: enum-validated tool schemas, MCP tool annotations and
  `ToolError` for expected failures.
- **Dual image return**: base64 `Image` content blocks (the agent *sees* the image)
  **and** PNG saved to disk (path returned as text).
- **Monorepo**: uv workspace (Python) + pnpm workspace (Node tooling) orchestrated
  by Turbo; MIT-licensed, Docker-ready, GitHub Pages docs.

## Quick start

### 1. Install the agent skills

```bash
npx skills add --yes --global xinvxueyuan/NovelAI-Image-MCP
```

`--yes` skips the interactive picker; `--global` installs to
`~/.agents/skills/` so every project on the machine can use them. Drop
`--global` to install into the current project's `.agents/skills/` instead.
See [Agent skills](#agent-skills) for what each skill covers.

### 2. Install the server (from source, development)

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
MCP_TRANSPORT=http uv run python -m novelai_image_mcp serve
#   → http://127.0.0.1:8000/mcp
```

### 3. Install the server (PyPI, runtime only)

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

The MCP server supports two transports (stdio + http), all configured under
`mcpServers`:

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

#### Alternative: uvx (published package)

```json
{
  "mcpServers": {
    "novelai-image": {
      "command": "uvx",
      "args": ["novelai-image-mcp", "serve"],
      "env": { "NOVELAI_TOKEN": "pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" }
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
      "url": "http://127.0.0.1:8000/mcp",
      "headers": {
        "Authorization": "Bearer pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

Replace `http://127.0.0.1:8000/mcp` with your self-deployed endpoint (e.g.
`https://mcp.example.com/mcp` behind a TLS-terminating reverse proxy). Swap
the literal token placeholder for a host-managed secret reference if your
MCP host supports one (Claude Desktop, Cline, etc. expose this via their
own secrets UI).

### Standard FastMCP entry points

The repository ships a [`fastmcp.json`](fastmcp.json) whose source points at
`apps/server/mcp_server.py`, so plain FastMCP tooling works too (run from the
repository root, after `uv sync`):

```bash
uv run fastmcp run fastmcp.json                     # stdio server
uv run fastmcp inspect                              # list tools/prompts/resources
uv run --directory apps/server fastmcp dev inspector mcp_server.py   # Inspector
```

`fastmcp.json` has no `environment` block on purpose: the workspace virtualenv
already has the package installed, and an `environment` entry would make
FastMCP build a second, throwaway environment for every run.

## CLI (sync, for scripting)

The CLI exposes six subcommands: `serve`, `generate`, `upscale`, `director`,
`annotate`, `info`.

```bash
# Run the MCP server (stdio by default; -t http for the HTTP transport)
novelai-image-mcp serve

# Text-to-image — prints one absolute PNG path per generated image
novelai-image-mcp generate --prompt "a cat, masterpiece" --width 832 --height 1216

# 4x upscale (V5 model only)
novelai-image-mcp upscale --image ./in.png --factor 4

# Director tools: lineart | sketch | bg-removal | declutter | colorize | emotion
novelai-image-mcp director lineart ./photo.png --defry 5

# ControlNet annotation: hed | midas | fake_scribble | mlsd | uniformer
novelai-image-mcp annotate ./photo.png --model hed

# Subscription / Anlas balance
novelai-image-mcp info

novelai-image-mcp --help
```

Install it with `pip install novelai-image-mcp`, run it ad hoc with
`uvx novelai-image-mcp <command>`, or from the monorepo with
`uv run --directory apps/server novelai-image-mcp <command>`. Every
image-producing command saves a PNG to `NOVELAI_OUTPUT_DIR` (default
`outputs`) and prints its path; `-o` / `--output-dir` overrides the
directory for one invocation. The full flag list lives in the
[`novelai-cli` skill][skills-docs].

## Agent skills

Three [skills.sh][skills-site] packages ship in `skills/`. They teach AI
agents (Claude Code, Codex, GitHub Copilot, Cursor, …) how to drive the CLI and
the MCP tools, so you do not have to paste docs into the conversation.

```bash
npx skills add --yes --global xinvxueyuan/NovelAI-Image-MCP
```

```mermaid
graph TD
    Q{How will you drive NovelAI?}
    Q -->|"Interactive session with an MCP host"| MCP["MCP tools<br/>11 tools over stdio / http"]
    Q -->|"Shell script, CI job, one-off command"| CLI["CLI<br/>novelai-image-mcp generate ..."]
    Q -->|"Let an agent pick the right one"| SK["Agent skills<br/>novelai-cli / novelai-mcp-tools / novelai-workflows"]
    SK --> MCP
    SK --> CLI
```

| Skill | Group | What it teaches |
|---|---|---|
| `novelai-cli` | CLI | Typer CLI commands (serve, generate, upscale, director, annotate, info) for shell scripting |
| `novelai-mcp-tools` | MCP Tools | The 11 MCP tools — model selection, parameters, return shape, Anlas cost |
| `novelai-workflows` | Workflows | Multi-step creative pipelines (txt2img→upscale, annotate→img2img, Director edits) |

Skills and the CLI/MCP tools are complementary, not either/or: install all
three and the agent picks the mode that fits the task. Each skill points at the
other two instead of repeating them. See the [Agent skills docs][skills-docs]
for the group descriptions and a mode-comparison table.

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
├── skills/                      # skills.sh packages (novelai-cli, ...)
├── skills.sh.json               # skill groupings for skills.sh
├── .github/                     # workflows, CODEOWNERS, issue templates
├── pyproject.toml               # uv workspace root (virtual)
├── uv.lock                      # single shared lockfile
├── pnpm-workspace.yaml          # pnpm workspace declaration
├── pnpm-lock.yaml               # Node toolchain lockfile
├── turbo.json                   # cross-workspace task graph
├── package.json                 # root scripts + dev toolchain
└── docker-compose.yml           # local container orchestration
```

See [`CONTRIBUTING.md`][contributing] for the developer guide and
[`apps/docs/source/`][docs-source] for the full documentation source.

## Tools

| Tool | Description |
|---|---|
| `generate_image` | Text-to-image (V3 / V4 / V4.5 / V5 models, character prompts; vibes V4/V4.5 only) |
| `image_to_image` | Image-to-image with strength/noise |
| `inpaint` | Inpainting (requires an inpaint model + mask) |
| `upscale_image` | 4× upscale (V5 model) |
| `director_tool` | Line art / sketch / bg-removal / declutter / colorize / emotion |
| `annotate_image` | ControlNet annotation (hed, midas, scribble, mlsd, uniformer) |
| `suggest_tags` | Prompt tag suggestions |
| `encode_vibe` | Encode a reference image into a vibe token |
| `get_subscription` | Account subscription + Anlas balance |
| `get_user_data` | Account user data |
| `estimate_anlas_cost` | Estimate Anlas cost for a generation (no API call) |

See the [tools reference][tools-docs]
on the docs site for parameters and examples.

## Configuration

All settings are environment variables (see `.env.example`). Key ones:

| Variable | Default | Notes |
|---|---|---|
| `NOVELAI_TOKEN` | — | Persistent API token (preferred auth) |
| `NOVELAI_USERNAME` / `NOVELAI_PASSWORD` | — | Access-key login (argon2id) |
| `NOVELAI_OUTPUT_DIR` | `outputs` | Where generated PNGs are saved |
| `NOVELAI_DEFAULT_MODEL` | `nai-diffusion-4-5-full` | Model id used when a tool call omits one |
| `NOVELAI_DEFAULT_WIDTH` / `NOVELAI_DEFAULT_HEIGHT` | `832` / `1216` | Default image size |
| `NOVELAI_DEFAULT_STEPS` | `28` | Default sampling steps (1–50) |
| `NOVELAI_DEFAULT_SCALE` | `5.0` | Default CFG scale (≤20) |
| `NOVELAI_DEFAULT_SAMPLER` | `k_euler_ancestral` | Default sampler |
| `NOVELAI_UPSCALE_MODEL` | `nai-diffusion-5-full` | Model for the standalone 4× upscaler (V5 line only) |
| `NOVELAI_TIMEOUT` | `120` | HTTP timeout in seconds |
| `NOVELAI_IMAGE_BASE_URL` | `https://image.novelai.net` | Consolidated API host for generation and account endpoints |
| `NOVELAI_LEGACY_IMAGE_BASE_URL` | `https://api.novelai.net` | Primary API host; only `/ai/annotate-image` still uses it |
| `MCP_TRANSPORT` | `stdio` | `stdio` or `http` (`streamable-http` is a legacy alias) |
| `MCP_HOST` / `MCP_PORT` / `MCP_PATH` | `127.0.0.1` / `8000` / `/mcp` | For the HTTP transport |
| `MCP_AUTH_TOKEN` | — | When set, the HTTP transport requires `Authorization: Bearer <token>` |
| `MCP_ROUTE_TOKENS` | — | JSON `{"<route>": "<token>"}` route-bound bearer tokens (401 on route mismatch) |
| `MCP_INSIDERS_HEADER` | `X-MCP-Insiders` | Header a client opts in with (HTTP only) |
| `MCP_MODEL_HEADERS` / `MCP_AGENT_HEADERS` / `MCP_CLIENT_HEADERS` | see below | JSON lists of routing candidates, first non-empty wins |
| `MCP_INSIDERS_DISABLED_FEATURES` | `[]` | Operator kill switch (JSON list), wins over any client |
| `MCP_ROUTE_SCOPED_OUTPUT` | `true` | Write images under `<output>/<route>/` while routing is active |
| `MCP_AUDIT_LOG_PATH` | `<output>/audit.jsonl` | Append-only JSONL audit trail |
| `MCP_LOG_LEVEL` | — | `DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL` |

List- and dict-valued settings are read as **JSON**: `MCP_MODEL_HEADERS='["X-MCP-Model"]'`
works, while `A,B` raises a settings error and an empty value is not valid JSON.

Routing candidate defaults (JSON lists, first non-empty header wins):

- `MCP_MODEL_HEADERS` — `["X-MCP-Model", "X-MCP-Model-Name"]`
- `MCP_AGENT_HEADERS` — `["X-MCP-Agent-ID", "X-MCP-Agent", "X-MCP-Agent-Source"]`
- `MCP_CLIENT_HEADERS` — `["X-MCP-Client", "X-MCP-Client-Session-Id"]`

### Insiders header and routing

Over HTTP a client can opt in to experimental behaviour and declare which route,
model, agent and session a request belongs to:

```text
X-MCP-Insiders: true
X-MCP-Agent-ID: team-a
X-MCP-Model: nai-diffusion-5-full
```

The server then writes that request's images under
`<NOVELAI_OUTPUT_DIR>/team-a/`, emits one line to the
`novelai_image_mcp.audit.team-a` logger, and appends one record to the audit
JSONL (the record keeps a prompt's length and a truncated SHA-256, never the
prompt, and never a credential header or an image payload).

**Nothing changes without the header** -- no scoped directory, no audit file, no
tool added or removed -- with one deliberate exception: `director_tool`'s
`emotion` and `emotion_level` parameters now require the opt-in and fail with a
`ToolError` otherwise (see the CHANGELOG). Routing headers are client-supplied
and forgeable, so grant the opt-in only behind a trusted gateway.

Full contract: [Insiders header, routing and audit][insiders-docs].

NovelAI API reference: [image.novelai.net/docs][nai-docs]

## Development

The project is a uv + pnpm monorepo orchestrated by Turbo. See
[`CONTRIBUTING.md`][contributing] for the full setup; the short version:

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

The Dockerfile lives at [`apps/server/Dockerfile`][dockerfile] but
the build context is the repository root (so uv can resolve the workspace
graph). See [`docker-compose.yml`][docker-compose].

## Documentation

The Sphinx documentation site is built with Furo + MyST Markdown and
auto-deploys to GitHub Pages on every push to `main`:

- **Live site**: [xinvxueyuan.github.io/NovelAI-Image-MCP][docs]
- **Source**: [`apps/docs/source/`][docs-source]
- **Build locally**: `pnpm docs:serve`

## License

MIT — see [LICENSE][license]. Per-file SPDX annotations live in
[REUSE.toml][reuse-toml]. Contributions are subject to the
[Developer Certificate of Origin][dco] (the `commit-msg` hook signs off
commits automatically).

## Links

[ci-badge]: https://github.com/xinvxueyuan/NovelAI-Image-MCP/actions/workflows/ci.yml/badge.svg
[ci-workflow]: https://github.com/xinvxueyuan/NovelAI-Image-MCP/actions/workflows/ci.yml
[docs-badge]: https://github.com/xinvxueyuan/NovelAI-Image-MCP/actions/workflows/docs.yml/badge.svg
[mit-badge]: https://img.shields.io/badge/License-MIT-blue.svg
[python-badge]: https://img.shields.io/badge/python-3.13+-blue.svg
[uv-badge]: https://img.shields.io/badge/uv-managed-261230.svg
[reuse-badge]: https://api.reuse.software/badge/github.com/xinvxueyuan/NovelAI-Image-MCP
[deepwiki-badge]: https://img.shields.io/badge/DeepWiki-Ask%20DeepWiki-blue
[skills-badge]: https://skills.sh/b/xinvxueyuan/NovelAI-Image-MCP
[product-hunt-badge]: https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=1206099&theme=light&t=1784973837616
[lifto-badge]: https://liftoapp.com/badges/featured-light.svg

[docs]: https://xinvxueyuan.github.io/NovelAI-Image-MCP/
[reuse]: https://api.reuse.software/info/github.com/xinvxueyuan/NovelAI-Image-MCP
[python]: https://www.python.org/downloads/
[uv]: https://docs.astral.sh/uv/
[deepwiki]: https://deepwiki.com/xinvxueyuan/NovelAI-Image-MCP
[skills-sh]: https://skills.sh/xinvxueyuan/NovelAI-Image-MCP
[product-hunt]: https://www.producthunt.com/products/novelai-image-mcp?embed=true&utm_source=badge-featured&utm_medium=badge&utm_campaign=badge-novelai-image-mcp
[lifto]: https://liftoapp.com/product/novelai-image-mcp
[mcp]: https://modelcontextprotocol.io/
[contributing]: CONTRIBUTING.md
[docs-source]: apps/docs/source/
[skills-site]: https://skills.sh
[skills-docs]: https://xinvxueyuan.github.io/NovelAI-Image-MCP/skills.html
[tools-docs]: https://xinvxueyuan.github.io/NovelAI-Image-MCP/tools/index.html
[insiders-docs]: https://xinvxueyuan.github.io/NovelAI-Image-MCP/development/insiders-and-routing.html
[nai-docs]: https://image.novelai.net/docs/index.html
[dockerfile]: apps/server/Dockerfile
[docker-compose]: docker-compose.yml
[license]: LICENSE
[reuse-toml]: REUSE.toml
[dco]: https://developercertificate.org/

<!-- mcp-name: io.github.xinvxueyuan/novelai-image-mcp -->
