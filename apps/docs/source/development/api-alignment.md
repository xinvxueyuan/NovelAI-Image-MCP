# API surface alignment

An audit of this server against NovelAI's published API documentation, with
**live verification** against the real endpoints. Re-run it whenever a
generation request starts failing with a validation error, when NovelAI
announces an API change, or before a release that touches `nai/`.

## What the official docs actually are

| URL | What it serves |
|---|---|
| `https://image.novelai.net/docs/index.html` | Swagger UI. Its inline config points at `doc.json`. |
| `https://image.novelai.net/docs/doc.json` | **The real spec**: Swagger 2.0, 27 paths, 57 definitions, titled "Omegalaser API". |
| `https://text.novelai.net/docs/doc.json` | Byte-identical copy of the same spec. |
| `https://api.novelai.net/docs/` | Swagger UI whose `swagger-initializer.js` still points at `https://petstore.swagger.io/v2/swagger.json` — **it is not a real spec**; do not use it as a source. |
| `https://text.novelai.net/openapi.json` | "Observability API" (error tracking), unrelated to image generation. |
| `https://docs.novelai.net/en/...` | Product guides (194 pages). They describe *features and UI settings*, not endpoints or field names; they never mention a `nai-diffusion-*` id or an `/ai/*` path. |

Fetch the spec with the project's own browser-fingerprinted client (Cloudflare
blocks plain clients):

```python
from novelai_image_mcp.nai.http import create_http_client

async with create_http_client(timeout=60) as client:
    spec = (await client.get("https://image.novelai.net/docs/doc.json")).json()
```

### The spec is not a field whitelist

`image.RequestParameters` omits fields this client sends and the API accepts —
`characterPrompts`, `autoSmea`, `ucPresetId`, `qualityPresetId` (V5),
`normalize_reference_strength_multiple`, `inpaintImg2ImgStrength`,
`legacy_uc`, parameter-level `use_coords` — and it types `model`,
`sampler` and `noise_schedule` as plain strings with no enumeration. Treat
the spec as authoritative for **which paths exist** and **response shapes**,
and treat the live API as authoritative for **which fields work**.

## Path inventory (27 documented)

Verified 2026-10-10 with a real account (Anlas before/after recorded).

| Documented path | This server | Live result |
|---|---|---|
| `POST /ai/generate-image` | V3 / Furry ZIP path (`Endpoint.IMAGE`) | 200 (ZIP) with `nai-diffusion-3` |
| `POST /ai/generate-image-stream` | V4 / V4.5 / V5 msgpack path | 200 (`application/msgpack`) |
| `POST /ai/generate-image/suggest-tags` | `suggest_tags` tool | 200, `{"tags": [{"tag", "count", "confidence"}]}` |
| `POST /ai/upscale` | `upscale_image` tool | 200 **only for V5 models** on this host; the old `api.novelai.net` path is 404 |
| `POST /ai/augment-image` | `director_tool` | 200 for `lineart`, `sketch`, `bg-removal`, `declutter`, `colorize` |
| `POST /ai/encode-vibe` | `encode_vibe` tool | 200 (binary vibe file, base64-encoded by the client) |
| `GET /user/subscription` | `get_subscription` tool | 200 |
| `GET /user/data` | `get_user_data` tool | 200 |
| `GET /user/information` | — | 200 (email/verification/ban status) |
| `GET /user/priority` | — | 200 (priority refill) |
| `GET /user/giftkeys` | — | **401** with a persistent token |
| `GET/PUT /user/clientsettings` | — | **401** with a persistent token |
| `POST /ai/generate`, `POST /ai/generate-stream` | — | text generation; out of scope for this image server |
| `/oa/v1/*` (completions, chat, token-count, models) | — | OpenAI-compatible text API; `GET /oa/v1/models` returns an empty `data` for this account |
| `/user/keystore`, `/user/consent`, `/user/create-persistent-token`, `/user/objects/*`, `/user/subscription/bind`, `/user/resend-email-verification` | — | account/product endpoints; mutations and private data are never called by this audit |
| `/ai/annotate-image` | `annotate_image` tool | **Not in this spec.** Live 200 on `api.novelai.net` for `hed`, `midas`, `fake_scribble`, `mlsd`, `uniformer` — the one endpoint that never moved |

## Findings that changed this codebase

1. **`/ai/upscale` moved and is V5-only.** The endpoint is on
   `image.novelai.net`, takes `{image, model, declared_blur_sigma}`, and
   rejects every V3/V4/V4.5 model with *"model ... doesn't support standalone
   upscaling"*. The previous implementation posted `{image, width, height,
   scale}` to `api.novelai.net/ai/upscale`, which now returns **404** — the
   tool was broken. Fixed by ``upscale()``: it posts to the image host,
   sends the documented body, defaults the model to
   `NOVELAI_UPSCALE_MODEL` (`nai-diffusion-5-full`), and refuses anything
   but a 4× step (the API exposes no factor).
2. **`suggest_tags` returns `{tag, count, confidence}`**, not the
   `{description, text, count}` shape the docs claimed. `schemas.TagSuggestion`
   now mirrors the wire fields (with `extra="allow"` so upstream additions
   survive).
3. **`/ai/generate-image` (ZIP) 500s for V4/V4.5 models** — those models must
   use `/ai/generate-image-stream`. The client already routes by model family
   (`is_v4_model()`), so no change was needed.

## Unverified on purpose

- `emotion` Director tool: the request 500s on a synthetic image with no face;
  the other five `req_type` values return 200. Needs a portrait to confirm.
- Anything that mutates account state (`/user/consent`, `subscription/bind`,
  `create-persistent-token`, `objects/*` deletes) — out of scope by design.
- `/user/giftkeys` and `/user/clientsettings` return 401 for persistent
  tokens; documenting the shape would require a session token.

## See also

- [Architecture](architecture.md) — how `nai/` maps to the API
- [Configuration](../configuration.md) — the endpoint and model settings
- [Transports](../transports/index.md)
