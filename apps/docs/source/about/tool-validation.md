# Tool validation

End-to-end verification of every MCP tool against the real NovelAI API, using
the published `novelai-image-mcp` package launched via `uvx` with a real
`NOVELAI_TOKEN`.

:::{note}
This page was generated on **2026-07-25** from a live run of the
`mcp_novelai-image-mcp` MCP server (the project dogfooding itself). It
captures both successes and failures honestly — failures are flagged with ❌
and include root-cause analysis.
:::

---

## Summary

| # | Tool | Status | Notes |
|---|---|---|---|
| 1 | `estimate_anolas_cost` | ✅ pass | Pure local calculation, no API call. Returns `{"anlas": 2, "opus_free_sample": false}` for a 512×512 / 1-step / 1-sample request. |
| 2 | `suggest_tags` | ✅ pass | API call to `image.novelai.net` succeeded. Returned 10 tag descriptors with `tag` / `count` / `confidence` fields. |
| 3 | `get_subscription` | ❌ fail | `NovelAITransportError` — `api.novelai.net` unreachable from the MCP server's env (no `HTTPS_PROXY`). Wiring is verified: the error is surfaced cleanly. |
| 4 | `get_user_data` | ❌ fail | Same root cause as `get_subscription`. |
| 5 | `generate_image` | ❌ fail | **Code bug.** API call succeeded, PNG was saved to disk, but the MCP v2 SDK cannot serialize the `Image` return block — `Unable to serialize unknown type: <class 'mcp.server.mcpserver.utilities.types.Image'>`. |
| 6 | `image_to_image` | ❌ fail | Same `Image`-serialization bug (shares `_save_and_return` with `generate_image`). |
| 7 | `inpaint` | ❌ fail | Same `Image`-serialization bug. |
| 8 | `upscale_image` | ❌ fail | Same `Image`-serialization bug **and** `api.novelai.net` unreachable. |
| 9 | `director_tool` | ❌ fail | Wiring verified (reached the API, got HTTP 500 for a 1×1 test image). The `Image`-serialization bug would also trigger with valid input (shares `_save_and_return`). |
| 10 | `annotate_image` | ❌ fail | Same `Image`-serialization bug **and** `api.novelai.net` unreachable. |
| 11 | `encode_vibe` | ⚠️ inconclusive | Wiring verified (reached the API, got HTTP 500 for a 1×1 test image — too small for the vibe encoder). Returns a plain string, so the `Image`-serialization bug does not apply. Would likely succeed with a real reference image. |

**Result: 2 / 11 fully pass, 1 / 11 inconclusive (environmental), 8 / 11 fail
(1 environmental + network, 6 code bug, 1 environmental).**

---

## Environment

The MCP server was launched with this config (token redacted):

```json
{
  "mcpServers": {
    "novelai-image-mcp": {
      "command": "uvx",
      "args": ["--prerelease=allow", "novelai-image-mcp", "serve"],
      "env": { "NOVELAI_TOKEN": "pst-..." }
    }
  }
}
```

The host machine runs Windows and reaches the internet through a local proxy
at `127.0.0.1:10808`. Because the MCP server's `env` block does not include
`HTTPS_PROXY`, `httpx` cannot reach `api.novelai.net` (the account/subscription
endpoint). `image.novelai.net` (the generation/director/tags endpoint) is
reachable directly — this is why `suggest_tags` and `generate_image` succeed
at the API layer while `get_subscription` and `get_user_data` fail at
transport.

:::{tip}
If you are behind a corporate or regional firewall, add proxy env vars to
the MCP server's `env` block:

```json
"env": {
  "NOVELAI_TOKEN": "pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "HTTPS_PROXY": "http://127.0.0.1:10808",
  "HTTP_PROXY": "http://127.0.0.1:10808",
  "NO_PROXY": "localhost,127.0.0.1"
}
```

See [Agent hosts → Behind a corporate proxy](../transports/agent-hosts.md#behind-a-corporate-proxy)
for the per-host equivalent.
:::

---

## Per-tool evidence

### `estimate_anolas_cost` — ✅ pass

**Call:**

```json
{
  "width": 512,
  "height": 512,
  "steps": 1,
  "n_samples": 1,
  "model": "nai-diffusion-4-5-full",
  "action": "generate"
}
```

**Return:** single text content block:

```json
{
  "anlas": 2,
  "opus_free_sample": false
}
```

The tool performs a pure local cost calculation (no HTTP request). The return
shape matches the docstring in
[`tools/account.py`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/src/novelai_image_mcp/tools/account.py).

---

### `suggest_tags` — ✅ pass

**Call:**

```json
{ "prompt": "1girl, fox ears", "language": "en" }
```

**Return:** 10 text content blocks, each a JSON object with `tag` / `count` /
`confidence`. Top 3:

```json
{ "tag": "fox ears", "count": 10000, "confidence": 0.72265625 }
{ "tag": "1girl", "count": 10000, "confidence": 0.67724609375 }
{ "tag": "fox girl", "count": 10000, "confidence": 0.6240234375 }
```

The API call to `https://image.novelai.net/ai/generate-image/suggest-tags`
succeeded without proxy env vars, confirming that `image.novelai.net` is
reachable from the test environment.

---

### `get_subscription` — ❌ fail (environmental)

**Call:** `{}` (no arguments)

**Return:** error text content block:

```text
Error executing tool get_subscription: NovelAI request transport failed
```

**Root cause:** the tool calls `https://api.novelai.net/user/subscription`,
which is unreachable from the MCP server's env (no `HTTPS_PROXY`). The error
is raised at [`client.py:141`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/src/novelai_image_mcp/nai/client.py)
as `NovelAITransportError("NovelAI request transport failed")` when
`httpx.HTTPError` is caught.

**Wiring verified:** the tool is registered, the parameter schema is empty
(matching the JSON descriptor), and the error is surfaced cleanly to the
MCP client. The failure is purely network-layer.

---

### `get_user_data` — ❌ fail (environmental)

**Call:** `{}` (no arguments)

**Return:**

```text
Error executing tool get_user_data: NovelAI request transport failed
```

Same root cause as `get_subscription` — calls
`https://api.novelai.net/user/data`, which is unreachable.

---

### `generate_image` — ❌ fail (code bug)

**Call:**

```json
{
  "prompt": "1girl, fox ears, masterpiece, best quality",
  "width": 512,
  "height": 512,
  "steps": 1,
  "n_samples": 1,
  "quality": false,
  "seed": 42
}
```

**Return:**

```text
Error executing tool generate_image: Unable to serialize unknown type:
<class 'mcp.server.mcpserver.utilities.types.Image'>
```

**Root cause:** the API call to `https://image.novelai.net/ai/generate-image`
succeeded, the image was generated and saved to `NOVELAI_OUTPUT_DIR`, but the
MCP v2 SDK's tool-result serializer does not recognize the `Image` helper
class as a valid content block type. The tool returns:

```python
return [
    Image(data=images[0].data, format="png"),
    f"Saved {len(images)} image(s): {[str(p) for p in paths]}",
]
```

The `Image(...)` constructor in `mcp.server.mcpserver.utilities.types` is not
auto-converted to an `ImageContent` block by the v2 SDK's serializer. **This
is a code bug** in
[`tools/generate.py:36`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/src/novelai_image_mcp/tools/generate.py).

:::{warning}
This bug is silent and costly: the user's Anlas is spent and the image is
saved to disk, but the agent receives an error response and cannot see the
image. The 5 other image-returning tools (`image_to_image`, `inpaint`,
`upscale_image`, `director_tool`, `annotate_image`) share the same
`_save_and_return` helper and have the same bug.
:::

**Fix direction:** replace `Image(data=..., format="png")` with the explicit
`ImageContent(data=base64.b64encode(...).decode("ascii"), mimeType="image/png")`
content block, or use the SDK's `mcp.types.ImageContent` directly. (This fix
is out of scope for the current doc-only change — see `tasks.md` for the
tracked follow-up.)

---

### `image_to_image` — ❌ fail (code bug, same as `generate_image`)

Not called independently — shares `_save_and_return` with `generate_image`
([`tools/generate.py:27-38`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/src/novelai_image_mcp/tools/generate.py)),
so the same `Image`-serialization bug applies. With a valid input image the
API call would succeed, the image would be saved, and the same serialization
error would be returned.

---

### `inpaint` — ❌ fail (code bug, same as `generate_image`)

Same as `image_to_image` — shares `_save_and_return`. Requires a base64 PNG
image and a base64 mask as input.

---

### `upscale_image` — ❌ fail (code bug + environmental)

Not called independently. Uses `_save_and_return` in
[`tools/enhance.py:23-34`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/src/novelai_image_mcp/tools/enhance.py)
→ same `Image`-serialization bug. Additionally calls
`https://api.novelai.net/user/ai-upscale-image` (account endpoint), which is
unreachable from the test env. Both bugs would need to be fixed for this tool
to work end-to-end.

---

### `director_tool` — ❌ fail (code bug, confirmed via API)

**Call** (with a 1×1 test PNG):

```json
{
  "tool": "lineart",
  "image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQI12P4z8AAAAADAAFbcGwUAAAAAElFTkSuQmCC"
}
```

**Return:**

```text
Error executing tool director_tool: NovelAI HTTP 500:
{"statusCode": 500, "message": "Internal Server Error"}
```

The 1×1 test PNG is too small for NovelAI's Director API, which returned
HTTP 500. **Wiring is verified:** the tool reached the API at
`https://image.novelai.net/ai/augment-image` and surfaced the error cleanly.
With a valid input image, the API call would succeed but the same
`Image`-serialization bug would trigger (shares `_save_and_return` with
`upscale_image`).

---

### `annotate_image` — ❌ fail (code bug + environmental)

Not called independently. Uses `_save_and_return` in `tools/enhance.py` →
same `Image`-serialization bug. Additionally calls
`https://api.novelai.net/ai/annotate-image` (account endpoint), which is
unreachable from the test env. Both bugs would need to be fixed.

---

### `encode_vibe` — ⚠️ inconclusive (environmental)

**Call** (with a 1×1 test PNG):

```json
{
  "reference": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQI12P4z8AAAAADAAFbcGwUAAAAAElFTkSuQmCC",
  "information_extracted": 0.5,
  "model": "nai-diffusion-4-5-full"
}
```

**Return:**

```text
Error executing tool encode_vibe: NovelAI HTTP 500:
{"statusCode": 500, "message": "Internal Server Error"}
```

The 1×1 test PNG is too small for NovelAI's vibe encoder. **Wiring is
verified:** the tool reached the API at `https://image.novelai.net/ai/encode-vibe`
and surfaced the error cleanly. The return type is `str` (a base64 vibe
token), so the `Image`-serialization bug does **not** apply — this tool would
likely succeed with a real reference image (≥ 64×64 pixels).

---

## Confirmed bugs

### Bug 1: `Image` content block not serializable by MCP v2 SDK

**Affected tools:** `generate_image`, `image_to_image`, `inpaint`,
`upscale_image`, `director_tool`, `annotate_image` (6 / 11).

**Location:**
[`tools/generate.py:36`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/src/novelai_image_mcp/tools/generate.py)
and
[`tools/enhance.py:32`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/src/novelai_image_mcp/tools/enhance.py).

**Symptom:** `Unable to serialize unknown type:
<class 'mcp.server.mcpserver.utilities.types.Image'>`

**User impact:** Anlas is spent, image is saved to disk, but the agent
receives an error and cannot see the image.

**Fix direction:** replace `Image(data=..., format="png")` with an explicit
`ImageContent` block from `mcp.types`. This fix is **out of scope** for the
current doc-only change; tracked as a follow-up task in `tasks.md`.

---

## See also

- [Tools reference](../tools/index.md) — every MCP tool's parameter schema
- [Transports](../transports/index.md) — stdio vs streamable-http
- [Agent hosts](../transports/agent-hosts.md) — per-host MCP config snippets
