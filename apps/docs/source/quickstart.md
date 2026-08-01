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

:::{tip}
**Prefer an AI agent to drive the CLI?** Install the [agent skills](skills.md)
with `npx skills add --yes --global xinvxueyuan/NovelAI-Image-MCP` — your
coding agent (Claude Code, Codex, Copilot, …) will then know the CLI commands
and MCP tool parameters without you pasting docs.
:::

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

`${input:novelai_token}` is a host-defined secret reference — see your MCP
host's secrets UI (Claude Desktop, Cline, …). For a one-off test you can
inline the literal token instead.

### Alternative: uvx (published package)

If you installed from PyPI, the shorthand is:

```json
{
  "mcpServers": {
    "novelai-image": {
      "command": "uvx",
      "args": ["--prerelease=allow", "novelai-image-mcp", "serve"],
      "env": { "NOVELAI_TOKEN": "pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" }
    }
  }
}
```

Set `NOVELAI_TOKEN` in the host shell — `uvx` inherits the parent env.

### Alternative: http (remote / Docker)

If you're running the server elsewhere (e.g. `docker compose up` on a remote
host), point the host at the URL directly:

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
`https://mcp.example.com/mcp` behind a TLS-terminating reverse proxy).

Restart Claude Desktop. You'll see a `novelai-image` MCP server registered
with 11 tools. Ask Claude to *"generate a watercolor painting of a fox"*
and watch it call `generate_image`.

For other agent hosts (Cline, Cursor, Continue, Windsurf, Codex CLI), see
[Agent hosts](transports/agent-hosts.md).

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
- 🧠 Install [agent skills](skills.md) — teach your AI agent the CLI + MCP tools
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
