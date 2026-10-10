# Architecture

The server is a thin composition root over a NovelAI HTTP client. This page
walks through the layers and how they fit together.

## Layers

```{mermaid}
graph TD
    A[Agent / MCP host] -->|JSON-RPC over stdio / HTTP| B[FastMCP]
    B -->|middleware| M[ToolCallLoggingMiddleware]
    B -->|optional bearer auth| N[mcp_auth.build_auth]
    B -->|lifespan| C[AppContext: NovelAIClient + NovelAISettings]
    C -->|Depends DI| D[tools/* · resources.py · prompts.py]
    D -->|calls| E[NovelAIClient nai/]
    E -->|httpx.AsyncClient| F[NovelAI API]
    D -->|saves| G[output.py → outputs/]
    D -->|ImageContent| A
    D -->|structured output| A
```

## `FastMCP` composition root

[`novelai_image_mcp.server`](../api/server.md) is the composition root. It:

1. Builds a single shared `httpx.AsyncClient` (connection pool) owned by
   the MCP `lifespan`.
2. Builds a `NovelAIClient` from settings + the httpx client.
3. Yields both as `AppContext`, which dependency providers expose to every
   tool, resource and prompt.
4. Tears down both on shutdown (closing `NovelAIClient` first, then the
   underlying httpx session — even if the client close raises, the httpx
   session is still released to avoid leaking sockets).

The instance itself is configured once, at import time:

```python
mcp = FastMCP(
    name="novelai-image",
    version=__version__,          # serves the package version, not the framework version
    instructions=INSTRUCTIONS,    # how an agent should use the server
    lifespan=lifespan,
    auth=build_auth(get_mcp_settings()),   # None unless MCP_AUTH_TOKEN is set
    mask_error_details=True,      # only ToolError messages reach the client
    middleware=[ToolCallLoggingMiddleware()],
)

from . import prompts, resources, tools  # decorators attach to `mcp`
```

Tools, resources and prompts are attached by module-level decorators, so
there is no `register(mcp)` function to call: importing `tools/` (or
`resources.py`, `prompts.py`) is the registration step, and it happens after
`mcp` exists.

```python
@asynccontextmanager
async def lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
    settings = get_novelai_settings()
    if not settings.has_credentials():
        raise RuntimeError("NovelAI credentials are not configured...")
    http_client = create_http_client(timeout=settings.timeout)
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

Every component declares what it needs; FastMCP resolves it per request and
keeps the dependency out of the input schema:

```python
@mcp.tool(title=..., tags={...}, annotations=IMAGE_WRITE_ANNOTATIONS)
@translate_errors
async def generate_image(
    prompt: str,
    model: Model | None = None,
    app: AppContext = Depends(get_app_context),   # hidden from the schema
) -> list[Any]: ...
```

`deps.py` owns the providers (`get_app_context`, `get_client`), and
`tools/_errors.py` owns the `NovelAIError`/`ValueError` → `ToolError`
translation. The translation has to happen inside the tool body: by the
time a middleware hook sees the call, FastMCP has already masked the
exception.

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
CLI, and direct client use. Enum-typed parameters (`Model`, `Sampler`,
`DirectorTool`, ...) are still coerced inside the tool body, so direct
Python callers may pass plain strings while MCP callers get schema
validation.

Alongside the tools the server exposes read-only context:

| Component | Where | Purpose |
|---|---|---|
| `novelai://models` | `resources.py` | Model ids with capability flags. |
| `novelai://samplers` | `resources.py` | Sampler / noise-schedule / UC-preset vocabulary. |
| `novelai://defaults` | `resources.py` | The active generation defaults (no credentials). |
| `novelai://outputs/{name}` | `resources.py` | Read a generated PNG back (name validated against the output directory). |
| `novelai_prompt_writer`, `novelai_image_workflow` | `prompts.py` | House-style prompt drafting and tool sequencing. |

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

The server supports stdio (default) and HTTP, selected at startup via
`MCP_TRANSPORT` (`http` is canonical, `streamable-http` is an accepted
alias). Both share the same `lifespan`, the same tools, and the same
`NovelAIClient` — only the framing differs. Setting `MCP_AUTH_TOKEN` makes
the HTTP transport require a bearer token; stdio is unaffected. See
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
