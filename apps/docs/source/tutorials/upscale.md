# Tutorial: Upscaling

Increase an image's resolution by 2× or 4× using NovelAI's dedicated
upscaler. The upscaler is faster and produces cleaner results than
re-generating at a higher resolution.

## 1. Upscale an image

```python
import base64
from pathlib import Path

image_b64 = base64.b64encode(Path("portrait.png").read_bytes()).decode("ascii")

result = await ctx.session.call_tool("upscale_image", {
    "image": image_b64,
    "factor": 4,
})
```

The output PNG is at 4× the source resolution. A 832×1216 input becomes
3328×4864.

## 2. Choose `factor`

| `factor` | Use case |
|---|---|
| `2` | Web display, quick preview, modest resolution bump. |
| `4` | Print, large-format display, archival storage. |

Higher factors cost more Anlas and produce much larger files. Use
[`estimate_anlas_cost`](../tools/account.md#estimate_anlas_cost) first if
you're upscaling a batch.

## 3. CLI equivalent

```bash
uv run python -m novelai_image_mcp upscale ./portrait.png --factor 4
```

## 4. Workflow: generate → upscale

A common pattern is to generate at low resolution for fast iteration, then
upscale the keeper:

```python
# Step 1: iterate at 832×1216 (cheap, ~5 Anlas each)
result = await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, masterpiece",
    "width": 832, "height": 1216,
    "n_samples": 4,
})
# (you pick the best of the 4 — say, outputs/generate-...003.png)

# Step 2: upscale the keeper to 3328×4864
import base64
from pathlib import Path
keeper_b64 = base64.b64encode(
    Path("outputs/generate-...003.png").read_bytes()
).decode("ascii")

result = await ctx.session.call_tool("upscale_image", {
    "image": keeper_b64,
    "factor": 4,
})
```

This costs ~5 Anlas for the batch + ~10 Anlas for the upscale = ~15 Anlas
total — much cheaper than generating four 4× images directly (~80 Anlas).

## 5. Pitfalls

:::{warning}
**Memory usage.** A 4× upscale of a 1024×1024 image produces a 4096×4096
PNG (~64 MB uncompressed). Plan disk space accordingly.
:::

:::{tip}
**Upscale before inpaint.** If you need to fix small details, upscaling
first gives the inpaint model more pixels to work with — finer masks and
better detail.
:::

## What's next?

- [`upscale_image` reference](../tools/enhance.md)
- [Account balance](../tools/account.md#get_subscription) — check Anlas first
- [Cost estimation](../tools/account.md#estimate_anlas_cost) — preview the bill
