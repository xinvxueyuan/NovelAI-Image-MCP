# NovelAI Image MCP

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that
exposes **NovelAI image generation** as tools for AI agents (Claude Desktop,
Cline, custom agents, remote clients).

Built on the official MCP Python SDK v2 (`MCPServer`), it lets an agent generate
images (txt2img / img2img / inpaint), upscale, run Director tools (line art,
emotion, background removal, …), annotate with ControlNet, suggest tags, encode
vibes, and query account subscription — all through the standard MCP tool
interface.

## Features

- **11 MCP tools** covering the full NovelAI image API surface.
- **Transports**: stdio (local agents) + streamable-http (remote / multi-client).
- **Image return**: base64 `Image` content blocks (the agent *sees* the image)
  **and** PNG saved to disk (path returned as text).
- **Async + sync**: async tool handlers + a `typer` CLI for direct invocation.
- **uv-managed**, single Python package, MIT-licensed, Docker-ready.

## Quick start

```bash
# 1. Install (uv ≥ 0.5)
uv sync

# 2. Configure credentials
cp .env.example .env
#   set NOVELAI_TOKEN=...  (preferred)
#   or  NOVELAI_USERNAME + NOVELAI_PASSWORD

# 3. Run (stdio — for local agents)
uv run python -m novelai_image_mcp serve

# 4. Or run over HTTP
MCP_TRANSPORT=streamable-http uv run python -m novelai_image_mcp serve
#   → http://127.0.0.1:8000/mcp
```

## Connect an agent (stdio)

Claude Desktop `claude_desktop_config.json`:

```jsonc
{
  "mcpServers": {
    "novelai-image": {
      "command": "uv",
      "args": ["run", "--directory", "C:/dev/NovelAI-Image-MCP",
               "python", "-m", "novelai_image_mcp", "serve"],
      "env": { "NOVELAI_TOKEN": "pst-..." }
    }
  }
}
```

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

```bash
uv sync --group dev      # install lint + test tooling
uv run poe check         # ruff format-check + lint + pyright + tests
uv run poe lint          # ruff check
uv run poe format        # ruff format (write)
uv run poe test          # pytest
uv run poe typecheck     # pyright
```

### Docker

```bash
docker compose up --build      # builds and runs the server
```

## Project layout

```
src/novelai_image_mcp/
├── server.py          # MCPServer (mcp v2) + lifespan + transport selection
├── settings.py        # pydantic-settings env config
├── cli.py / __main__.py  # typer sync CLI
├── output.py          # save-image helper
├── tools/             # 11 MCP tool definitions
└── nai/               # NovelAI HTTP client (ported from lingchu-bot, decoupled)
    ├── auth.py  constants.py  models.py  payload.py
    ├── response.py  imaging.py  exceptions.py
    └── client.py  service.py    # adapted: NoneBot driver → httpx
```

## License

MIT — see [LICENSE](LICENSE).

The NovelAI client modules under `src/novelai_image_mcp/nai/` are derived from
the [lingchu-bot](https://github.com/xinvxueyuan/lingchu-bot) project
(LGPL-3.0-or-later). Relicensing that derivative code to MIT is valid only if you
hold the rights to the original work. See the note in [LICENSE](LICENSE) and
[REUSE.toml](REUSE.toml) for per-file SPDX annotations.
