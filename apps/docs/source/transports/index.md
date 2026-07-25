# Transports

The MCP server supports two transports. Pick based on how you intend to use
it.

| Transport | Use case | Cost | Concurrency |
|---|---|---|---|
| [stdio](stdio.md) | Local agent integration (Claude Desktop, Cline) | Lowest — no network overhead | Single client |
| [streamable-http](http.md) | Remote / multi-client / production deployments | Slightly higher (HTTP framing) | Multiple clients |

## Quick selection guide

```{mermaid}
graph TD
    Q{How will you use the server?}
    Q -->|Local agent on the same machine| A[stdio]
    Q -->|Remote / multi-client / production| B[streamable-http]
    Q -->|Scripting — direct CLI use| C[CLI: novelai-image-mcp generate<br/>uv run python -m ...]
```

## Transport-agnostic design

The server's `lifespan` owns a single shared `httpx.AsyncClient` (connection
pool) and one `NovelAIClient`. Every tool reads those from the request
context's lifespan state — neither tool code nor tool signatures change
between transports.

Transport selection happens at server startup via `MCP_TRANSPORT` (or the
CLI `--transport` flag):

```bash
# stdio (default)
MCP_TRANSPORT=stdio uv run python -m novelai_image_mcp serve

# streamable-http
MCP_TRANSPORT=streamable-http uv run python -m novelai_image_mcp serve
```

See [Configuration](../configuration.md#mcp-transport) for the full list of
`MCP_*` variables.

```{toctree}
:maxdepth: 1
:hidden:

stdio
http
```
