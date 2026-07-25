# streamable-http transport

Exposes the MCP server over HTTP. Designed for remote deployments,
multi-client scenarios, and production environments where the server runs
as a long-lived service.

## Run

```bash
MCP_TRANSPORT=streamable-http uv run python -m novelai_image_mcp serve
# or via the CLI flag:
uv run python -m novelai_image_mcp serve --transport streamable-http
```

The server binds to `127.0.0.1:8000/mcp` by default. Override with
`MCP_HOST` / `MCP_PORT` / `MCP_PATH`:

```bash
MCP_TRANSPORT=streamable-http \
MCP_HOST=0.0.0.0 \
MCP_PORT=9000 \
MCP_PATH=/mcp \
uv run python -m novelai_image_mcp serve
```

## URL

The full endpoint URL is:

```text
http://${MCP_HOST}:${MCP_PORT}${MCP_PATH}
```

Default: <http://127.0.0.1:8000/mcp>.

## Agent configuration

### MCP client config (`mcpServers`)

After `docker compose up --build` (or any other `streamable-http` deployment),
point your MCP host at the URL with the `http` type:

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
MCP host (Claude Desktop, Cline, …) supports one.

### Custom Python agent

```python
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print([t.name for t in tools])

asyncio.run(main())
```

### Curl (debugging)

The streamable-http transport uses Server-Sent Events for server → client
messages. A raw HTTP request to inspect the server:

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl","version":"1.0"}}}'
```

## Docker deployment

The simplest production deployment:

```bash
docker compose up --build
```

The [`docker-compose.yml`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/docker-compose.yml)
at the repo root configures the streamable-http transport with sensible
defaults:

```yaml
services:
  mcp:
    build:
      context: .
      dockerfile: apps/server/Dockerfile
    ports:
      - "8000:8000"
    environment:
      MCP_TRANSPORT: streamable-http
      MCP_HOST: 0.0.0.0
      MCP_PORT: 8000
      NOVELAI_OUTPUT_DIR: /app/outputs
    volumes:
      - novelai-outputs:/app/outputs
```

The healthcheck probes the bind port (default `8000`) every 30 seconds.

## Production checklist

:::{warning}
**The MCP streamable-http transport does not implement authentication.**
Before exposing the server to the internet, put it behind:

- TLS termination (Caddy, nginx, Traefik, AWS ALB)
- An authentication layer (mTLS, OAuth proxy, API gateway)
- A rate limiter (to prevent Anlas abuse)
:::

:::{tip}
**Bind to localhost for local multi-client use.** If you only need
multiple agents on the same machine (e.g. a Python + a Node agent), set
`MCP_HOST=127.0.0.1` and skip TLS. Use a reverse proxy only when crossing
network boundaries.
:::

:::{admonition} Output directory
:class: note

In Docker, `NOVELAI_OUTPUT_DIR=/app/outputs` is backed by a named volume
(`novelai-outputs`). Generated images persist across container restarts.
For Kubernetes, replace the volume with a PersistentVolumeClaim.
:::

## Concurrency model

- The server uses a single shared `httpx.AsyncClient` (connection pool).
  Multiple concurrent tool calls share the pool — no per-request HTTP
  overhead.
- Each MCP request runs in its own asyncio task on the server's event
  loop.
- The server does not queue or rate-limit requests — that's the
  responsibility of the upstream proxy.

## See also

- [stdio transport](stdio.md)
- [Configuration](../configuration.md#mcp-transport)
- [Docker Compose file](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/docker-compose.yml)
