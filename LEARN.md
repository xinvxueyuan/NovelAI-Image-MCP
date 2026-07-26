# Learning NovelAI Image MCP

A guided learning path from "what is MCP?" to "I shipped a new tool to
PyPI." Each module lists **objectives**, an estimated time, and a hands-on
**checkpoint** — do the checkpoint before moving on. Existing reference docs
are linked rather than duplicated; this file is the syllabus that stitches
them together.

> Already comfortable with MCP and Python packaging? Skip to
> [Module 3](#module-3--first-tool-call) and treat the earlier modules as
> reference.

---

## Module 0 — Prerequisites

**Objectives**: Confirm you have the baseline knowledge to learn this project.

You should already be comfortable with:

- **Python 3.12+**: async/await, type hints, dataclasses / pydantic, virtual
  environments.
- **HTTP**: status codes, JSON, base64, multipart bodies, what a TLS
  handshake is (conceptually).
- **Git**: branches, commits, PRs, rebase.
- **Command line**: running scripts, setting environment variables.

You do **not** need prior experience with:

- MCP (we cover it in Module 1)
- NovelAI's API (covered in Module 4)
- Sphinx / pnpm / Turbo (only needed for docs or release engineering)

**Checkpoint**: Run `python -c "import asyncio; print(asyncio.__version__)"`.
If that errors, brush up on async Python first.

⏱️ _0–30 minutes depending on background_

---

## Module 1 — MCP Fundamentals

**Objectives**: Understand what MCP is, why it exists, and how
clients/servers communicate.

### Read

1. Skim the official
   [MCP Quickstart](https://modelcontextprotocol.io/quickstart/server) — focus
   on the "what is an MCP server" section.
2. Read this project's
   [Quickstart](https://xinvxueyuan.github.io/NovelAI-Image-MCP/quickstart/)
   — it's the same idea, applied to image generation.

### Key concepts to internalize

- **MCP server** = a process that exposes **tools** (callable functions),
  **resources** (readable data), and **prompts** (templates). This project
  exposes 11 tools only — no resources, no prompts.
- **Transport**: how bytes get between client and server. Two flavors:
  - **stdio**: client spawns the server as a subprocess, talks over stdin/stdout.
    Simplest, works everywhere, default for Claude Desktop / Cline.
  - **Streamable HTTP**: server runs as a long-lived HTTP service. Used for
    shared/multi-tenant deployments. This project supports both — see
    [transports/](https://xinvxueyuan.github.io/NovelAI-Image-MCP/transports/).
- **Tool**: a function with a JSON Schema for its arguments. The client
  (e.g. Claude) decides when to call it based on the schema + description.
  Return values are **content blocks**: text, image, audio, embedded
  resources.

### Checkpoint

In your own words, write down: _"An MCP server is a process that …"_. If you
can't fit it in two sentences, re-skim. Then list the 11 tools this project
exposes by reading the [tools table in the README](README.md#tools).

⏱️ _30–60 minutes_

---

## Module 2 — Project Architecture

**Objectives**: Navigate the codebase confidently. Know which file does what.

### Read

1. [AGENTS.md](AGENTS.md) — the agent-facing index. Read it fully; it's short
   and dense.
2. [Repository layout](CONTRIBUTING.md#repository-layout) in CONTRIBUTING.
3. [Architecture](https://xinvxueyuan.github.io/NovelAI-Image-MCP/development/architecture/)
   on the docs site.

### Mental model to build

```text
            ┌─────────────────────────────────────────────┐
            │  MCP client (Claude Desktop / Cline / etc.) │
            └───────────────────┬─────────────────────────┘
                                │ JSON-RPC over stdio or HTTP
                                ▼
            ┌─────────────────────────────────────────────┐
            │  MCPServer  (server.py)                      │
            │    └── lifespan → AppContext                 │
            │          ├── NovelAISettings                 │
            │          └── NovelAIClient                   │
            └───────────────────┬─────────────────────────┘
                                │ @mcp.tool() registrations
                                ▼
            ┌─────────────────────────────────────────────┐
            │  tools/  (11 tools across 4 modules)         │
            │    generate.py  enhance.py  account.py tags │
            └───────────────────┬─────────────────────────┘
                                │ await client.<method>(...)
                                ▼
            ┌─────────────────────────────────────────────┐
            │  nai/  (NovelAI HTTP client)                 │
            │    client.py    HTTP method wrappers         │
            │    http.py      create_http_client() factory │
            │    payload.py   request body builders        │
            │    response.py  ZIP / msgpack decoders       │
            │    models.py    enums + dataclasses          │
            │    constants.py Endpoint enum, model registry│
            └───────────────────┬─────────────────────────┘
                                │ curl_cffi transport
                                ▼
                       image.novelai.net
                       api.novelai.net (legacy)
```

### Key files by responsibility

| File | Responsibility |
|---|---|
| `apps/server/src/novelai_image_mcp/server.py` | `MCPServer` instance + `lifespan` that builds `AppContext` |
| `apps/server/src/novelai_image_mcp/cli.py` | `typer` CLI — `serve` / `serve-http` entry points |
| `apps/server/src/novelai_image_mcp/tools/*.py` | Tool registration functions, one file per domain |
| `apps/server/src/novelai_image_mcp/nai/client.py` | `NovelAIClient` — high-level NovelAI API methods |
| `apps/server/src/novelai_image_mcp/nai/http.py` | `create_http_client()` — Chrome-fingerprinted httpx factory |
| `apps/server/src/novelai_image_mcp/nai/constants.py` | `Endpoint` enum, model registry, route table |
| `apps/server/src/novelai_image_mcp/output.py` | `save_image()` — writes PNG to disk, returns path |

### Checkpoint

Without looking, answer:

1. Why must HTTP clients go through `create_http_client()` instead of
   `httpx.AsyncClient()` directly? _(Answer: Cloudflare WAF fingerprints TLS
   via JA3/JA4; OpenSSL's fingerprint doesn't match any browser, so the
   connection is silently reset. curl_cffi impersonates Chrome's BoringSSL
   fingerprint.)_
2. Why does `tools/generate.py` call `Image(...).to_image_content()`
   instead of returning the `Image` helper directly? _(Answer: MCP v2 SDK's
   structured-content serialization path calls `model_dump(mode="json")`,
   which fails on the plain `Image` class with `PydanticSerializationError`.)_
3. Which two endpoints still live on `api.novelai.net` rather than
   `image.novelai.net`? _(`/ai/upscale` and `/ai/annotate-image` — they
   weren't migrated. Use `legacy_image_base_url`.)_

⏱️ _1–2 hours_

---

## Module 3 — First Tool Call

**Objectives**: Run the server locally and invoke a tool end-to-end.

### Read

1. [Installation](https://xinvxueyuan.github.io/NovelAI-Image-MCP/installation/)
2. [Quickstart](https://xinvxueyuan.github.io/NovelAI-Image-MCP/quickstart/)

### Hands-on

1. **Set up credentials**:

   ```bash
   cp .env.example .env
   # edit .env → NOVELAI_TOKEN=pst-...  (get from https://novelai.net/account)
   ```

2. **Run the server under the MCP Inspector** (the easiest debugging surface):

   ```bash
   mcp dev apps/server/dev_server.py
   ```

   The Inspector opens in your browser. You can list tools, read their
   schemas, and call them with crafted JSON.

3. **Call `get_subscription`** — it's the cheapest tool (no Anlas spend):
   - Click the tool in the Inspector sidebar
   - Click **Run**
   - You should see your subscription tier, Anlas balance, and renewal date.

4. **Call `generate_image`** with a short prompt. Watch the logs in the
   terminal where you ran `mcp dev` — you'll see the curl_cffi HTTP request
   fly by.

### Why `dev_server.py` and not `server.py`?

`mcp dev` loads the entry point by file path, which breaks Python's relative
import machinery (`from ._mcp import MCPServer`). `dev_server.py` is a thin
shim that imports the package absolutely. This is a hard constraint — see
AGENTS.md rule #4.

### Checkpoint

Generate an image with prompt `"a serene mountain lake at dawn"` and save
the path. Confirm the file exists on disk. If you hit a `400 Bad Request`,
check that your prompt isn't empty and that your token has Anlas.

⏱️ _30–60 minutes_

---

## Module 4 — The NovelAI API Layer

**Objectives**: Understand the request/response flow from tool to NovelAI.

### Read

1. [API reference: client](https://xinvxueyuan.github.io/NovelAI-Image-MCP/api/client/)
2. [API reference: settings](https://xinvxueyuan.github.io/NovelAI-Image-MCP/api/settings/)
3. [Tool validation](https://xinvxueyuan.github.io/NovelAI-Image-MCP/about/tool-validation/)
   — explains the endpoint split.

### The two-response-shapes gotcha

NovelAI's image endpoints don't all return the same thing:

| Models | Endpoint | HTTP status | Response body |
|---|---|---|---|
| V3 (Anime v3), Furry v3 | `POST /ai/generate-image` | `201 Created` | ZIP archive containing one PNG |
| V4 / V4.5 | `POST /ai/generate-image-stream` | `200 OK` | MessagePack stream (chunked) |

`nai/response.py` has two decoders — `decode_zip_response()` and
`decode_stream_response()`. The client picks based on the model. This is why
you'll see `Accept: application/x-msgpack` headers on V4 requests but not
V3.

### The two-host split

| Host | Endpoints |
|---|---|
| `image.novelai.net` | All generation, augmentation, vibe encoding, tag suggestion, account/subscription/data |
| `api.novelai.net` (legacy) | `/ai/upscale`, `/ai/annotate-image` only |

The `legacy_image_base_url` setting exists specifically for the two
not-yet-migrated endpoints. Don't "fix" it by routing them to
`image.novelai.net` — they'll 404.

### Checkpoint

Open `apps/server/src/novelai_image_mcp/nai/client.py` and trace
`generate_image()` end-to-end:

1. Where is the model → endpoint decision made? _(In `client.py`, branching
   on `model.is_v4_family()`.)_
2. Where does the HTTP request actually fire? _(In
   `client._request()`, using `self._http` which was built by
   `create_http_client()`.)_
3. Where is the response decoded? _(Delegated to `response.py` based on
   `Content-Type`.)_

⏱️ _1–2 hours_

---

## Module 5 — Adding a New Tool

**Objectives**: Ship a new MCP tool end-to-end, following project
conventions.

### Read

1. AGENTS.md → "关键约定" → "新增 MCP 工具" (the 5-step recipe)
2. [Contributing — first PR](CONTRIBUTING.md)
3. Look at `tools/tags.py` — it's the simplest existing tool (one method,
   text-only return).

### Steps

1. **Implement** in `tools/<name>.py`:

   ```python
   from .._mcp import Context
   from ..nai import NovelAIClient  # or whatever you need
   from ._ctx import app_context as _app

   def register(mcp: MCPServer) -> None:
       @mcp.tool()
       async def my_new_tool(ctx: Context, /* args */) -> list[Any]:
           """One-line summary.

           Detailed description. Args are documented in the docstring;
           MCP uses it as the tool description shown to the LLM.
           """
           app = _app(ctx)
           client = app.client
           result = await client.my_method(...)
           return [/* text or ImageContent blocks */]
   ```

2. **Wire** it in `tools/__init__.py`:

   ```python
   from . import my_new_tool as _my_new_tool
   # ...
   _my_new_tool.register(mcp)
   ```

3. **Test** in `tests/test_tools.py` — it's parameterized; add your tool's
   name + sample args to the `ToolCallCase` list. The
   `TestSerializationRegression` class is a must-extend if your tool returns
   images — it runs `Tool.run(convert_result=True)` against the production
   `server.mcp` to catch `PydanticSerializationError`.

4. **Document** in `apps/docs/source/tools/<name>.md`.

5. **README** — add a row to the tools table in both `README.md` and
   `README-zh.md`.

### Hard rules to remember

- ❌ Don't return the `Image` helper directly — always
  `Image(...).to_image_content()`. Use the `_save_and_return` helper in
  `tools/generate.py` / `tools/enhance.py` as a template.
- ❌ Don't construct `httpx.AsyncClient()` directly — go through
  `app.client` (which was built by `create_novelai_client()` using
  `create_http_client()`).
- ❌ Don't add a tool that does work without a test in `test_tools.py`.

### Checkpoint

Add a trivial tool `get_server_time` that returns the current server time as
text. Run `uv run --directory apps/server poe check` — it should pass with
your new test. Run `mcp dev apps/server/dev_server.py` and call your new
tool from the Inspector.

⏱️ _2–4 hours for a real tool, 30 minutes for the trivial checkpoint_

---

## Module 6 — Image Return Path

**Objectives**: Understand why image tools need special handling and how to
do it correctly.

### Read

1. AGENTS.md → hard constraint #3 (ImageContent vs Image helper)
2. `tools/generate.py:_save_and_return` — read the full docstring

### The problem

MCP v2 SDK's structured-content path serializes tool return values via
`model_dump(mode="json")`. The SDK ships an `Image` helper class as a
convenience — but it's a plain Python class, not a pydantic model, so
`model_dump` blows up with:

```text
PydanticSerializationError: Unable to serialize unknown type: Image
```

### The solution

Convert to `ImageContent` (a pydantic `ContentBlock`) before returning:

```python
from .._mcp import Image
from ..output import save_image

def _save_and_return(image: NovelAIImage, *, name: str, output_dir: str) -> list[Any]:
    path = save_image(image.data, name=name, output_dir=output_dir)
    return [
        Image(data=image.data, format="png").to_image_content(),  # ← key call
        f"Saved image: {path}",
    ]
```

Returning a `list` of mixed `ImageContent` + `TextContent` blocks is the
canonical pattern — the client renders both (shows the image, then the path
as a caption).

### Checkpoint

In `tests/test_server.py`, find `TestSerializationRegression`. Read what it
does. Add a hypothetical tool that returns an `Image` directly (without
`to_image_content()`) and watch the test fail with the exact error above.
Revert.

⏱️ _1 hour_

---

## Module 7 — Release Engineering

**Objectives**: Understand how a change goes from PR to PyPI / GHCR / GitHub
Release / MCP Registry.

### Read

1. [Releasing](https://xinvxueyuan.github.io/NovelAI-Image-MCP/development/releasing/)
   on the docs site.
2. AGENTS.md → "发布流程" + "硬约束" (rules #1, #6, #7).
3. `.github/workflows/release.yml` — the actual workflow.
4. `.github/workflows/publish-mcp.yml` — the registry publishing workflow.

### The release pipeline

```text
Edit pyproject.toml version ─────┐
Edit CHANGELOG.md [Unreleased]   │
uv lock                          │
poe check + reuse lint           │
git commit -m "🏷️ chore(release): X.Y.Z"
git checkout -b releases/X.Y.Z   │
git push -u origin releases/X.Y.Z
                                 ▼
                .github/workflows/release.yml
                  ├─ validate   (checks version sync, CHANGELOG format)
                  ├─ build      (uv build --package novelai-image-mcp)
                  ├─ publish-pypi   (trusted publishing via OIDC)
                  ├─ publish-ghcr   (docker buildx + push)
                  └─ github-release (gh release create vX.Y.Z + assets)
                                 │
                                 ▼  creates vX.Y.Z tag
                .github/workflows/publish-mcp.yml  (tag-push triggered)
                  ├─ validate server.json against schema
                  ├─ mcp-publisher login github-oidc
                  └─ mcp-publisher publish
                                 │
                                 ▼
                registry.modelcontextprotocol.io
                  → synced to github.com/mcp directory
```

### Hard rules

- **Version source of truth** is `apps/server/pyproject.toml`. Don't edit
  `package.json` versions manually — `.github/actions/sync-version` does it
  and rewrites the commit.
- **PyPI doesn't allow republish** of the same version. If a release fails
  after PyPI upload, yank + bump patch (`0.1.x` → `0.1.x+1`).
- **Always `uv lock` before pushing** `releases/*` — the `build` job will
  warn if lockfile is stale.
- **Commit messages** must be gitmoji + Conventional Commits (e.g.
  `🐛 fix(generate): handle zero-seed randomization`). The `commit-msg`
  hook auto-appends `Signed-off-by` for DCO. Never `--no-verify`.

### Checkpoint

Read the latest release notes at
<https://github.com/xinvxueyuan/NovelAI-Image-MCP/releases>. Trace the
CHANGELOG entries back to the PRs that introduced them. You should be able
to explain the relationship between CHANGELOG, git tag, and GitHub Release.

⏱️ _1 hour_

---

## Module 8 — Deep Dives

Pick the topics relevant to your work.

### 8.1 — Cloudflare WAF and TLS Fingerprinting

Read `nai/http.py` and the `BROWSER_HEADERS` constant. Understand:

- What JA3/JA4 fingerprints are and why Cloudflare uses them.
- Why `httpx_curl_cffi.AsyncCurlTransport(impersonate="chrome")` mimics
  Chrome's BoringSSL fingerprint while plain `httpx` (OpenSSL) doesn't.
- Why the full Chrome 150 header block is sent alongside the TLS layer —
  fingerprinting also inspects header order.

### 8.2 — MessagePack Streaming for V4 Models

Read `nai/response.py:decode_stream_response`. V4 endpoints stream
MessagePack frames; the decoder must consume chunks as they arrive. Compare
with the V3 path which receives a complete ZIP.

### 8.3 — MCP Registry and `server.json`

Read `server.json` at the repo root and `.github/workflows/publish-mcp.yml`.
Understand:

- How the official MCP Registry validates package ownership (PyPI README
  marker, OCI image label).
- Why the workflow is triggered by tag push rather than running inside
  `release.yml`.
- How GitHub OIDC authentication works without storing secrets.

### 8.4 — Hybrid Transports (stdio + HTTP)

Read `transports/http.md` and `cli.py`. The same `MCPServer` instance can
run in either stdio or streamable-HTTP mode based on CLI subcommand. The
HTTP mode is useful for self-hosting a shared server behind a reverse proxy.

### 8.5 — i18n Documentation

Read `apps/docs/source/conf.py` and the `AVAILABLE_LANGUAGES` config. Each
language has its own directory (`source/zh/`, `source/ja/`) and toctree.
Translations are independent builds — untranslated sections fall back to
English. Never link to a not-yet-translated page from a translated toctree.

⏱️ _Varies; 2–4 hours per topic_

---

## Where to go next

- **"I want to ship a feature"** → Module 5, then
  [CONTRIBUTING.md](CONTRIBUTING.md).
- **"A tool is returning weird errors"** → Module 4 + the
  [tool-validation reference](https://xinvxueyuan.github.io/NovelAI-Image-MCP/about/tool-validation/).
- **"I want to integrate this server into my app"** →
  [transports/](https://xinvxueyuan.github.io/NovelAI-Image-MCP/transports/)
  for stdio vs HTTP tradeoffs.
- **"I want to publish a derivative MCP server"** → Module 7 + the
  [MCP Registry publishing guide](https://github.com/modelcontextprotocol/registry/blob/main/docs/guides/publishing/publish-server.md).

## Getting unstuck

- **Stuck on a tool call?** Run `mcp dev apps/server/dev_server.py` and use
  the Inspector — it shows the exact JSON-RPC traffic.
- **Cloudflare resetting connections?** You bypassed
  `create_http_client()`. Go through `app.client`.
- **`PydanticSerializationError`?** You returned `Image` instead of
  `ImageContent`. Call `.to_image_content()`.
- **404 on upscale/annotate?** The endpoint was routed to
  `image.novelai.net` by mistake. Use `legacy_image_base_url`.
- **CI failing on `uv lock`?** You edited `pyproject.toml` without running
  `uv lock` afterward.

## Contributing back

See [CONTRIBUTING.md](CONTRIBUTING.md) for the first-PR workflow. The
project follows gitmoji + Conventional Commits and enforces DCO via a
`commit-msg` hook — sign-off is automatic, just don't `--no-verify`.
