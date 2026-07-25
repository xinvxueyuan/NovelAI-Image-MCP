# stdio transport

The default and most common transport. The server reads JSON-RPC messages
from stdin and writes responses to stdout. Designed for tight integration
with a local MCP host (Claude Desktop, Cline, custom agents).

## Run

```bash
uv run python -m novelai_image_mcp serve
# or explicitly:
MCP_TRANSPORT=stdio uv run python -m novelai_image_mcp serve
```

The server runs in the foreground. Press `Ctrl+C` to exit.

## Agent configuration

### Claude Desktop

Edit `claude_desktop_config.json`:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

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

`${input:novelai_token}` resolves to a host-managed secret. For a one-off
test, inline a literal token (`"pst-..."`) instead.

#### Shorthand: uvx (installed package)

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

Set `NOVELAI_TOKEN` in the host shell — `uvx` inherits the parent env.

Restart Claude Desktop. You'll see a `novelai-image` MCP server registered
with 11 tools.

### Cline (VS Code)

Add to `cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "novelai-image": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run", "--directory", "/path/to/NovelAI-Image-MCP",
        "python", "-m", "novelai_image_mcp", "serve"
      ],
      "env": { "NOVELAI_TOKEN": "${input:novelai_token}" },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### Custom Python agent

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(
        command="uv",
        args=["run", "--directory", "/path/to/NovelAI-Image-MCP",
              "python", "-m", "novelai_image_mcp", "serve"],
        env={"NOVELAI_TOKEN": "pst-..."},
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print([t.name for t in tools])

asyncio.run(main())
```

## Why stdio?

- **No network overhead** — no TCP handshake, no HTTP framing.
- **No port conflicts** — the server doesn't bind to anything.
- **Process lifecycle is automatic** — the agent owns the process; when the
  agent exits, the server exits.
- **Stdin/stdout** are universally supported across MCP SDKs.

## Limitations

- **Single client only.** Two agents cannot share one stdio server.
- **The server's stderr is captured** by the agent as logs. Use `logging`
  (configured to stderr) for diagnostics; never print to stdout (it
  corrupts the JSON-RPC stream).

## Logging

The MCP runtime writes all logs to **stderr**. To see them in a separate
terminal:

```bash
uv run python -m novelai_image_mcp serve 2>server.log
```

To forward logs to the agent (e.g. for Claude Desktop's "MCP logs" panel),
configure the runtime's logging handler per the MCP SDK docs.

## See also

- [streamable-http transport](http.md)
- [Configuration](../configuration.md#mcp-transport)
- [Quick start](../quickstart.md)
