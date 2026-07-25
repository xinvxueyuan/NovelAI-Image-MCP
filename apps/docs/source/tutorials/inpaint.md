# Tutorial: Inpainting

Redraw a specific region of an image with the `inpaint` tool. Use cases:
fix anatomy, remove an object, change a background, swap a face.

## Prerequisites

- A `*_inpainting` model. The standard V4.5 inpaint model is
  `nai-diffusion-4-5-full-inpainting`.
- A **mask** — a PNG where non-transparent (alpha > 0) pixels mark the
  region to regenerate.

## 1. Create the mask

The mask must be the same dimensions as the input image. You can create
one with any image editor (e.g. Photoshop, GIMP, Krita) or programmatically:

```python
from PIL import Image, ImageDraw

# Open the source image to get its dimensions
src = Image.open("input.png")
mask = Image.new("RGBA", src.size, (0, 0, 0, 0))  # fully transparent

# Draw a region to redraw (e.g. the face area)
draw = ImageDraw.Draw(mask)
draw.ellipse(
    (src.width // 3, src.height // 4, src.width * 2 // 3, src.height // 2),
    fill=(255, 255, 255, 255),  # opaque white = redraw
)
mask.save("mask.png")
```

## 2. Run inpaint

```python
import base64
from pathlib import Path

image_b64 = base64.b64encode(Path("input.png").read_bytes()).decode("ascii")
mask_b64 = base64.b64encode(Path("mask.png").read_bytes()).decode("ascii")

result = await ctx.session.call_tool("inpaint", {
    "prompt": "1girl, masterpiece, smiling",
    "image": image_b64,
    "mask": mask_b64,
    "model": "nai-diffusion-4-5-full-inpainting",
    "strength": 0.5,
    "seed": 42,
})
```

## 3. Tune `strength`

Like `image_to_image`, `strength` controls how far the redrawn region
diverges from the original:

- `0.2–0.3` — preserve identity, fix minor issues
- `0.5` — balanced, often the sweet spot
- `0.7+` — major changes, risk of seams with the surrounding pixels

## 4. Workflow: iterative refinement

Inpaint works best iteratively. Generate, inspect, refine the mask, repeat:

```python
# Step 1: coarse redraw with high strength
result = await ctx.session.call_tool("inpaint", {
    "prompt": "1girl, smiling",
    "image": image_b64,
    "mask": coarse_mask_b64,
    "strength": 0.7,
})

# Step 2: refine with a tighter mask and lower strength
result = await ctx.session.call_tool("inpaint", {
    "prompt": "1girl, smiling, perfect teeth",
    "image": result_image_b64,  # use the previous result
    "mask": fine_mask_b64,
    "strength": 0.3,
})
```

## 5. Use the Python API

For scripting without an MCP host, call the underlying client directly:

```python
import asyncio
import base64
from pathlib import Path

import httpx
from novelai_image_mcp.nai import (
    Action, GenerationRequest, Model, create_novelai_client,
)
from novelai_image_mcp.settings import NovelAISettings

async def main():
    settings = NovelAISettings(token="pst-...")
    image_b64 = base64.b64encode(Path("input.png").read_bytes()).decode("ascii")
    mask_b64 = base64.b64encode(Path("mask.png").read_bytes()).decode("ascii")
    async with httpx.AsyncClient(timeout=settings.timeout) as http_client:
        client = create_novelai_client(settings, http_client=http_client)
        try:
            request = GenerationRequest(
                prompt="1girl, masterpiece, smiling",
                action=Action.INPAINT,
                model=Model.V4_5_INPAINT,
                image=image_b64, mask=mask_b64,
                strength=0.5, seed=42,
            )
            images = await client.generate(request)
        finally:
            await client.aclose()

asyncio.run(main())
```

## Common pitfalls

:::{warning}
**Model mismatch.** Inpaint requires an inpaint model. Calling `inpaint`
with a non-inpaint model raises `NovelAIValidationError`. Check with:

```python
from novelai_image_mcp.nai import is_inpaint_model, Model
is_inpaint_model(Model.V4_5_INPAINT)  # True
is_inpaint_model(Model.V4_5)           # False
```
:::

:::{warning}
**Mask dimensions.** The mask must match the input image's dimensions
*exactly*. A 832×1216 image needs an 832×1216 mask. Mismatched masks raise
a `NovelAIValidationError`.
:::

:::{tip}
**Feather the mask.** Hard mask edges create visible seams. Soften the
mask's alpha with a Gaussian blur (5–10 px radius) for smoother transitions.
:::

## What's next?

- [Image-to-image](img2img.md) — full-image transformation
- [Upscaling](upscale.md) — finalize at higher resolution
- [`inpaint` reference](../tools/generate.md#inpaint)
