# Configuration

All runtime configuration is via environment variables (read by
`pydantic-settings` in [`novelai_image_mcp.settings`](api/settings.md)). The
canonical reference is [`.env.example`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.env.example)
in the repository root.

## Loading order

1. Process environment (highest priority)
2. `.env` file in the current working directory
3. Built-in defaults (lowest priority)

The `.env` file is parsed as UTF-8; unknown keys are ignored; variable
names are case-insensitive (`NOVELAI_TOKEN` and `novelai_token` are
equivalent).

---

## NovelAI credentials

| Variable | Default | Required | Notes |
|---|---|---|---|
| `NOVELAI_TOKEN` | — | *one of* | Persistent API token (preferred). Get it from <https://novelai.net> → Account. |
| `NOVELAI_USERNAME` | — | *one of* | Username (email) for access-key login. |
| `NOVELAI_PASSWORD` | — | *one of* | Account password. Combined with `NOVELAI_USERNAME` and run through argon2id to derive the access key. |

:::{important}
Set **either** `NOVELAI_TOKEN` **or** the `NOVELAI_USERNAME` + `NOVELAI_PASSWORD`
pair. The server raises `RuntimeError` at startup if neither is present
(see [`NovelAISettings.has_credentials`](api/settings.md)).
:::

## Endpoints

| Variable | Default | Notes |
|---|---|---|
| `NOVELAI_IMAGE_BASE_URL` | `https://image.novelai.net` | Image generation / Director / upscale endpoint. |
| `NOVELAI_ACCOUNT_BASE_URL` | `https://image.novelai.net` | Account / subscription / tag-suggestion endpoint. NovelAI consolidated all third-party API access to `image.novelai.net`, so this now shares the same host as `NOVELAI_IMAGE_BASE_URL`. |
| `NOVELAI_TIMEOUT` | `120` (seconds) | HTTP timeout for any single NovelAI request. |

:::{tip}
Override `NOVELAI_IMAGE_BASE_URL` to point at a local mock (e.g.
`http://localhost:9000`) during integration testing. The tests in
`apps/server/tests/` use [`respx`](https://github.com/transportapp/respx)
instead and don't need this.
:::

## Generation defaults

These tune the defaults used by `generate_image` (and any other tool that
accepts the same parameters). They are overridable per tool call.

| Variable | Default | Range | Notes |
|---|---|---|---|
| `NOVELAI_DEFAULT_MODEL` | `nai-diffusion-4-5-full` | See `Model` enum | V3 / V4 / V4.5 model id. |
| `NOVELAI_DEFAULT_WIDTH` | `832` | 64–49152, multiple of 64 | Image width in pixels. |
| `NOVELAI_DEFAULT_HEIGHT` | `1216` | 64–49152, multiple of 64 | Image height in pixels. |
| `NOVELAI_DEFAULT_STEPS` | `28` | 1–50 | Sampler iterations. |
| `NOVELAI_DEFAULT_SCALE` | `5.0` | 0–20 | Classifier-free guidance scale. |
| `NOVELAI_DEFAULT_SAMPLER` | `k_euler_ancestral` | See `Sampler` enum | Sampler id. |

## Client

| Variable | Default | Range | Notes |
|---|---|---|---|
| `NOVELAI_VIBE_CACHE_ENTRIES` | `64` | 1–1024 | Vibe-transfer encoding cache size. Encoding the same reference twice hits the cache instead of re-calling the API. |

## Output

| Variable | Default | Notes |
|---|---|---|
| `NOVELAI_OUTPUT_DIR` | `outputs` | Directory where generated PNGs are saved. Relative paths resolve against the server's working directory. The directory is created on demand. |

## MCP transport

| Variable | Default | Range | Notes |
|---|---|---|---|
| `MCP_TRANSPORT` | `stdio` | `stdio` \| `streamable-http` | How the server exposes itself to clients. |
| `MCP_HOST` | `127.0.0.1` | any bind address | Bind host for `streamable-http`. |
| `MCP_PORT` | `8000` | 1–65535 | Bind port for `streamable-http`. |
| `MCP_PATH` | `/mcp` | path string | HTTP path for the streamable-http endpoint. Full URL: `http://${MCP_HOST}:${MCP_PORT}${MCP_PATH}`. |

:::{warning}
The default `MCP_HOST=127.0.0.1` binds to **localhost only**. To expose the
server to other machines on your LAN, set `MCP_HOST=0.0.0.0` — and put it
behind TLS termination or an authenticated reverse proxy. The MCP
streamable-http transport does **not** implement authentication.
:::

---

## Putting it all together

A production-grade `.env` for a remote streamable-http deployment:

```bash
# ── Auth ──
NOVELAI_TOKEN=pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ── Generation defaults (Opus tier, high quality) ──
NOVELAI_DEFAULT_MODEL=nai-diffusion-4-5-full
NOVELAI_DEFAULT_WIDTH=1024
NOVELAI_DEFAULT_HEIGHT=1024
NOVELAI_DEFAULT_STEPS=28
NOVELAI_DEFAULT_SCALE=5.0
NOVELAI_DEFAULT_SAMPLER=k_euler_ancestral

# ── Output (persist to a Docker volume) ──
NOVELAI_OUTPUT_DIR=/app/outputs

# ── Transport ──
MCP_TRANSPORT=streamable-http
MCP_HOST=0.0.0.0
MCP_PORT=8000
MCP_PATH=/mcp

# ── Client ──
NOVELAI_VIBE_CACHE_ENTRIES=128
NOVELAI_TIMEOUT=180
```

## Environment in Docker

The [`Dockerfile`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/Dockerfile)
reads from `.env` via `docker-compose.yml`'s `env_file:` directive. To
override a single variable at run time without editing `.env`:

```bash
docker compose run -e MCP_PORT=9000 mcp
```

For Kubernetes, mount the env file as a `Secret` or use a ConfigMap /
Secret-aware env provider.

## See also

- [`novelai_image_mcp.settings` API reference](api/settings.md)
- [.env.example](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.env.example)
- [Transports](transports/index.md) — stdio vs streamable-http trade-offs
