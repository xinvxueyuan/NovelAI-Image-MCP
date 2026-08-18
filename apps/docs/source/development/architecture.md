# Architecture

The server is a thin composition root over a NovelAI HTTP client. This page
walks through the layers and how they fit together.

## Layers

```{mermaid}
graph TD
    A[Agent / MCP host] -->|JSON-RPC over stdio / HTTP| B[FastMCP]
    B -->|lifespan| C[AppContext: NovelAIClient + NovelAISettings]
    B -->|tool calls| D[tools/*]
    D -->|calls| E[NovelAIClient nai/]
    E -->|httpx.AsyncClient| F[NovelAI API]
    D -->|saves| G[output.py → outputs/]
```

## `FastMCP` composition root

[`novelai_image_mcp.server`](../api/server.md) is the composition root. It:

1. Builds a single shared `httpx.AsyncClient` (connection pool) owned by
   the MCP `lifespan`.
2. Builds a `NovelAIClient` from settings + the httpx client.
3. Yields both via `AppContext` to every tool invocation.
4. Tears down both on shutdown (closing `NovelAIClient` first, then the
   underlying httpx session — even if the client close raises, the httpx
   session is still released to avoid leaking sockets).

```python
@asynccontextmanager
async def lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
    settings = get_novelai_settings()
    if not settings.has_credentials():
        raise RuntimeError("NovelAI credentials are not configured...")
    http_client = httpx.AsyncClient(timeout=settings.timeout)
    client = create_novelai_client(settings, http_client=http_client)
    try:
        yield AppContext(client=client, settings=settings)
    finally:
        try:
            await client.aclose()
        finally:
            if not http_client.is_closed:
                await http_client.aclose()
```

Every tool reads the client + settings from the fastmcp request context:

```python
app = _app(ctx)  # extracts AppContext from ctx.lifespan_context
settings = app.settings
client = app.client
```

## `NovelAIClient` (the `nai/` subpackage)

The `nai/` subpackage is the NovelAI HTTP client. It is **agnostic** of
MCP — it can be used standalone from any async Python code.

| Module | Responsibility |
|---|---|
| `auth.py` | Argon2id access-key derivation; request tracking headers. |
| `client.py` | `NovelAIClient` — high-level async API (`generate`, `upscale`, `director`, `annotate`, `suggest_tags`, `encode_vibe`, `get_subscription`, `get_user_data`). |
| `constants.py` | Enums: `Action`, `Model`, `Sampler`, `DirectorTool`, `Emotion`, `EmotionLevel`, `ControlNetModel`, `Endpoint`, `NoiseSchedule`. Plus `is_v4_model`, `is_inpaint_model`. |
| `exceptions.py` | Domain exceptions: `NovelAIAuthenticationError`, `NovelAIValidationError`, `NovelAIInsufficientCreditsError`, `NovelAIConcurrencyError`, `NovelAIImageError`, `NovelAIProviderError`. |
| `models.py` | Pydantic models: `GenerationRequest`, `CharacterPrompt`, `NovelAIGenerationPlan`. |
| `payload.py` | `build_generation_payload` — wire-format encoder (MessagePack-compatible). |
| `response.py` | `NovelAIImage`, `parse_messagepack_images`, `parse_zip_images`, `check_status`, `GenerationEvent`. |
| `service.py` | `create_novelai_client` factory + `NovelAIConfigLike` protocol. |

## Tools layer

`novelai_image_mcp.tools` is a thin adapter between the fastmcp `FastMCP`
tool decorator and `NovelAIClient`. Each tool:

1. Extracts `AppContext` from the MCP context (`tools/_ctx.py`).
2. Builds a `GenerationRequest` (or equivalent) from tool parameters.
3. Calls the corresponding `NovelAIClient` method.
4. Persists the result via `output.save_image`.
5. Returns a list of MCP content blocks: `[Image, text_path]`.

Tools deliberately avoid business logic — validation and parameter
marshaling live in `nai/` so the same code path serves the MCP server, the
CLI, and direct client use.

## CLI

`novelai_image_mcp.cli` is a `typer` app that exposes a subset of the MCP
tools as direct subcommands (`generate`, `upscale`, `director`, `annotate`,
`info`, `serve`). It constructs a short-lived `httpx.AsyncClient` +
`NovelAIClient` per invocation — no shared session. For long-lived
multi-tool use, prefer the MCP server (which owns a pooled session via its
lifespan).

## Configuration

`novelai_image_mcp.settings` defines two `pydantic-settings` models:

- `NovelAISettings` — credentials, endpoints, generation defaults
  (`NOVELAI_*` env vars).
- `MCPServerSettings` — transport selection (`MCP_*` env vars).

Both load from process env + `.env` (in cwd), UTF-8, case-insensitive,
unknown keys ignored. `NovelAISettings` structurally satisfies
`NovelAIConfigLike`, so the client factory consumes it directly.

## Output

`novelai_image_mcp.output.save_image` writes a PNG to
`NOVELAI_OUTPUT_DIR`, returning the path. The directory is created on
demand. Filenames include the tool name + ISO timestamp + sample index
(`generate-20260725-133702-001.png`).

## Transports

The server supports stdio (default) and streamable-http, selected at
startup via `MCP_TRANSPORT`. Both share the same `lifespan`, the same
tools, and the same `NovelAIClient` — only the framing differs. See
[Transports](../transports/index.md).

## Containerization

[`apps/server/Dockerfile`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/Dockerfile)
is a multi-stage build:

1. **Builder stage**: installs uv, exports runtime deps (no dev groups),
   builds wheels.
2. **Project build stage**: builds the project wheel via `uv build`.
3. **Runtime stage**: slim Python 3.13, non-root `app` user, installs
   pre-built wheels only — no compiler toolchain in the runtime image.

The smoke test (`apps/server/docker/smoke-test.py`) is built into a
separate image (via the `SMOKE_TEST=true` build-arg) and verifies:

- The package imports cleanly.
- Settings instantiate from env (with `NOVELAI_TOKEN=pst-smoke-test`).
- Every tool registers against a recording FastMCP stub.
- The typer CLI constructs without runtime errors.

## See also

- [`server.py` API reference](../api/server.md)
- [`nai/` API reference](../api/client.md)
- [Testing](testing.md) — how the layers are tested in isolation
- [Releasing](releasing.md) — the Docker image build & sign process
