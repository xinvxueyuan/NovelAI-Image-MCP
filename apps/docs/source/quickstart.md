# Quick start

This page walks through installing the server, configuring credentials, and
generating your first image in under five minutes.

:::{note}
This guide assumes you've already completed
[Installation](installation.md).
:::

---

## 1. Start the server (stdio)

The default transport is **stdio** — for local agents like Claude Desktop
or Cline. Run it as a foreground process:

```bash
uv run python -m novelai_image_mcp serve
```

The server reads from stdin and writes JSON-RPC responses to stdout. You
won't see anything until a client connects. To exit, press `Ctrl+C`.

## 2. Generate an image (CLI)

For quick experimentation without spinning up an MCP host, use the sync
`typer` CLI:

```bash
uv run python -m novelai_image_mcp generate \
  --prompt "a cat sitting on a windowsill, masterpiece, best quality" \
  --width 832 \
  --height 1216
```

The CLI prints the path to the saved PNG:

```text
outputs/generate-YYYYMMDD-HHMMSS-NNN.png
```

Open the file — you should see your generated cat.

## 3. Generate via HTTP

To expose the server to remote clients over HTTP:

```bash
MCP_TRANSPORT=streamable-http uv run python -m novelai_image_mcp serve
```

The server listens at <http://127.0.0.1:8000/mcp> by default. Override the
host and port with `MCP_HOST` / `MCP_PORT`.

## 4. Connect Claude Desktop

Edit `claude_desktop_config.json` (macOS: `~/Library/Application Support/Claude/`,
Windows: `%APPDATA%\Claude\`):

```json
{
  "mcpServers": {
    "novelai-image": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "C:/dev/NovelAI-Image-MCP",
        "python",
        "-m",
        "novelai_image_mcp",
        "serve"
      ],
      "env": {
        "NOVELAI_TOKEN": "pst-..."
      }
    }
  }
}
```

Restart Claude Desktop. You'll see a `novelai-image` MCP server registered
with 11 tools. Ask Claude to *"generate a watercolor painting of a fox"*
and watch it call `generate_image`.

## 5. Verify your account balance

Before a long generation session, check your Anlas balance:

```bash
uv run python -m novelai_image_mcp info
```

```json
{
  "tier": 3,
  "active": true,
  "trainingStepsLeft": { "fixed": 10000, "perStepUsage": false },
  "subscriptionId": "..."
}
```

Or call the `get_subscription` MCP tool from your agent.

---

## Common next steps

- 📚 Read the [Tools reference](tools/index.md) for every parameter
- 🎨 Try [tutorials](tutorials/index.md) — img2img, inpaint, upscale, ControlNet
- 🔧 Tune [generation defaults](configuration.md) via env vars
- 🐳 [Dockerize](transports/http.md) for production

## Troubleshooting

:::{admonition} Credentials error
:class: warning

If you see:

```text
RuntimeError: NovelAI credentials are not configured: set NOVELAI_TOKEN or
NOVELAI_USERNAME + NOVELAI_PASSWORD (see .env.example).
```

Make sure your `.env` file exists and contains a valid `NOVELAI_TOKEN`
starting with `pst-`. The `info` subcommand is the cheapest way to verify
auth without spending Anlas.
:::

:::{admonition} Slow first run
:class: tip

The first `uv sync` downloads ~60 wheels. Subsequent runs reuse the cache
and complete in seconds. If you're behind a corporate proxy, set
`UV_HTTP_TIMEOUT=300` (seconds) to avoid timeouts on slow networks.
:::

:::{admonition} Image not saved
:class: warning

Check `NOVELAI_OUTPUT_DIR` (default: `outputs`). The directory must be
writable by the user running the server. In Docker, the directory is
`/app/outputs` and is backed by a named volume (`novelai-outputs`).
:::
