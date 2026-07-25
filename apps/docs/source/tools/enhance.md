# `upscale_image`

Upscale an image by 2× or 4× using NovelAI's dedicated upscaler. The
upscaler is model-independent — it works on any source image, regardless of
how it was produced.

## Parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `image` | `str` | *required* | Base64-encoded PNG/JPEG to upscale. |
| `factor` | `int` | `4` | `2` or `4`. |

## Returns

`list[ContentBlock]` — base64 `Image` of the upscaled image + saved-path text.

## Behavior

- The upscaler is a separate NovelAI endpoint — it does **not** run a
  diffusion loop, so it's faster than re-generating at a higher resolution.
- Anlas cost scales with source resolution and `factor`. Use
  [`estimate_anlas_cost`](account.md#estimate_anlas_cost) *before* a big
  batch.
- The output preserves the input's color profile and aspect ratio. You
  cannot change aspect ratio during upscale.

## Example

```python
await ctx.session.call_tool("upscale_image", {
    "image": image_b64,
    "factor": 4,
})
```

### CLI

```bash
uv run python -m novelai_image_mcp upscale ./portrait.png --factor 4
```

## Tips

:::{tip}
**When to upscale vs re-generate?**

- Upscale when you already have a near-perfect image and just need higher
  resolution.
- Re-generate when you want to change composition, lighting, or details.
  Re-generating at 2× the original resolution often produces cleaner
  results than upscaling, but costs more Anlas.
:::

:::{admonition} Memory usage
:class: warning

A 4× upscale of a 1024×1024 image produces a 4096×4096 output (~64 MB
uncompressed PNG). Make sure your `NOVELAI_OUTPUT_DIR` volume has space.
:::

## See also

- [Upscale tutorial](../tutorials/upscale.md)
- [`upscale_image` API reference](../api/tools.md)
- [Account balance](account.md#get_subscription) — check Anlas before a batch
