# HTTP transport

Exposes the MCP server over HTTP. Designed for remote deployments,
multi-client scenarios, and production environments where the server runs
as a long-lived service.

## Run

```bash
MCP_TRANSPORT=http uv run python -m novelai_image_mcp serve
# or via the CLI flag:
uv run python -m novelai_image_mcp serve --transport http
```

The server binds to `127.0.0.1:8000/mcp` by default. Override with
`MCP_HOST` / `MCP_PORT` / `MCP_PATH`:

```bash
MCP_TRANSPORT=http \
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

After `docker compose up --build` (or any other HTTP deployment),
point your MCP host at the URL with the `http` type:

```json
{
  "mcpServers": {
    "novelai-image-http": {
      "type": "http",
      "url": "http://127.0.0.1:8000/mcp",
      "headers": {
        "Authorization": "Bearer <MCP_AUTH_TOKEN>"
      }
    }
  }
}
```

Replace `http://127.0.0.1:8000/mcp` with your self-deployed endpoint (e.g.
`https://mcp.example.com/mcp` behind a TLS-terminating reverse proxy).

The `Authorization` header is **not** the NovelAI token: the server talks to
NovelAI with its own `NOVELAI_TOKEN`. The header matters only when
`MCP_AUTH_TOKEN` is set on the server, in which case it must match it
(`Authorization: Bearer <MCP_AUTH_TOKEN>`). Without `MCP_AUTH_TOKEN` the
endpoint accepts unauthenticated clients — put it behind TLS and a reverse
proxy, or keep `MCP_HOST` on localhost.

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

## Insiders header and routing

HTTP is the only transport that can carry the opt-in header, so the routing
surface lives here. A client opts in per request with `X-MCP-Insiders` and
declares its route with the routing headers:

```json
{
  "mcpServers": {
    "novelai-image-http": {
      "type": "http",
      "url": "http://127.0.0.1:8000/mcp",
      "headers": {
        "Authorization": "Bearer <MCP_AUTH_TOKEN>",
        "X-MCP-Insiders": "true",
        "X-MCP-Agent-ID": "team-a",
        "X-MCP-Model": "nai-diffusion-5-full"
      }
    }
  }
}
```

With the header, the server resolves a route (here `team-a`), writes generated
images under `<NOVELAI_OUTPUT_DIR>/team-a/`, emits one line to the
`novelai_image_mcp.audit.team-a` logger and appends one record to the audit
JSONL. Without it, nothing changes -- no scoped directory, no audit file.

The opt-in also gates the experimental `emotion` / `emotion_level` parameters
of `director_tool`; without it, passing either fails with a `ToolError`.

See [Insiders header, routing and audit](../development/insiders-and-routing.md)
for the header grammar, the candidate header lists, the audit record fields, the
redaction rules and the extension points.

### Route-bound tokens

`MCP_AUTH_TOKEN` stays a single static token. `MCP_ROUTE_TOKENS` adds tokens
bound to a route, so one gateway can hand different teams different secrets:

```bash
MCP_AUTH_TOKEN=static-token
MCP_ROUTE_TOKENS='{"team-a":"token-for-team-a","team-b":"token-for-team-b"}'
```

A route token authenticates as its route and is rejected with `401` when the
same request declares a *different* route through the routing headers. A request
that declares no usable route is accepted and attributed to the token's route;
only two different, both-present routes fail closed. When neither setting is
configured, no auth middleware is installed and the endpoint behaves as before.

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
**The transport itself ships no authentication.** `MCP_AUTH_TOKEN` (and
`MCP_ROUTE_TOKENS`) add a bearer check in front of the MCP endpoint, but that
is a single shared secret, not an identity provider -- and the routing headers
are client-supplied and forgeable. Before exposing the server to the internet,
put it behind:

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
- [Insiders header, routing and audit](../development/insiders-and-routing.md)
- [Configuration](../configuration.md#mcp-transport)
- [Docker Compose file](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/docker-compose.yml)
