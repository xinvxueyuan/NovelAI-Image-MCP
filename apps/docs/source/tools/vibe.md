# `encode_vibe`

Encode a reference image into a **NovelAI vibe token**. Vibe tokens are
compact representations of a reference image's style/identity that can be
passed to `generate_image` via the `references` parameter (V4+ models only).

## Parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `reference` | `str` | *required* | Base64-encoded reference PNG/JPEG. |
| `information_extracted` | `float` | `1.0` | 0.01–1.0. How strongly the vibe captures the reference's identity. |
| `model` | `str` | `"nai-diffusion-4-5-full"` | Target model id (must be V4+). |

## Returns

`str` — base64 vibe token. Pass it to `generate_image`'s `references` list.

## `information_extracted` semantics

| Value | Effect |
|---|---|
| `0.01`–`0.3` | Captures **style** only. Generated images inherit the reference's painterly look, lighting, palette — not its subject. |
| `0.4`–`0.7` | Balanced. Captures style + approximate identity (same character archetype). |
| `0.8`–`1.0` | Captures **identity**. Generated images reproduce the reference's subject closely (e.g. the same character in a new pose). |

## Example

```python
# Encode a reference style
vibe_token = await ctx.session.call_tool("encode_vibe", {
    "reference": ref_b64,
    "information_extracted": 0.3,  # style only
})

# Use it in a generation
await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, watercolor style, peaceful meadow",
    "references": [vibe_token],
})
```

## Multiple vibes

`references` accepts a list — you can blend multiple vibes:

```python
style_vibe = await ctx.session.call_tool("encode_vibe", {
    "reference": style_ref_b64,
    "information_extracted": 0.2,
})
character_vibe = await ctx.session.call_tool("encode_vibe", {
    "reference": character_ref_b64,
    "information_extracted": 0.9,
})

await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, sitting in a cafe",
    "references": [style_vibe, character_vibe],
})
```

## Caching

The server caches vibe encodings in-memory keyed by `(reference_hash,
information_extracted, model)`. Cache size is bounded by
`NOVELAI_VIBE_CACHE_ENTRIES` (default 64). Encoding the same reference
twice with the same parameters hits the cache and returns instantly
without an API call.

## Tips

:::{warning}
**V3 models do not support vibes.** Calling `encode_vibe` with a V3 model
id raises `ValueError`. Use `Model.is_v4_model()` to check before encoding.
:::

:::{tip}
**Reference image quality matters more than quantity.** A single
high-quality, well-cropped reference (close-up, neutral background) produces
better vibes than a noisy album of similar images.
:::

## See also

- [Vibe transfer tutorial](../tutorials/vibe-transfer.md) — full encode → generate workflow
- [`encode_vibe` API reference](../api/tools.md)
- [Vibe encoding reference in NovelAI docs](https://docs.novelai.net/image/vibe.html)
