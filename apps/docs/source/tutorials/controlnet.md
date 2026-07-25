# Tutorial: ControlNet workflow

Use NovelAI's ControlNet preprocessors to drive a generation from a
structural map. The workflow: extract an annotation (depth, line art, etc.)
from a reference image, then generate a new image conditioned on that
annotation.

## Workflow overview

```{mermaid}
graph LR
    A[Reference image] --> B[annotate_image]
    B --> C[Annotation<br/>depth / line art]
    C --> D[generate_image<br/>with controlnet_condition]
    D --> E[Final image]
```

## 1. Extract a depth map

```python
import base64
from pathlib import Path

photo_b64 = base64.b64encode(Path("photo.png").read_bytes()).decode("ascii")

depth_result = await ctx.session.call_tool("annotate_image", {
    "image": photo_b64,
    "model": "midas",
})
# depth_result[0] is an Image block with the depth map.
```

## 2. Generate with the annotation as a condition

Pass the annotation back to `generate_image` via the
`controlnet_condition` parameter (V4+ models):

```python
# Extract the base64 image bytes from the previous result
depth_b64 = depth_result[0].data  # base64-encoded PNG

result = await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, oil painting, renaissance style",
    "controlnet_condition": depth_b64,
    "controlnet_model": "midas",
    "width": 832,
    "height": 1216,
})
```

The generated image inherits the depth structure of the photo but takes on
the style and subject of the prompt.

## 3. Try different preprocessors

| Preprocessor | Best for |
|---|---|
| `midas` (depth) | Preserves pose, volumetric composition. |
| `hed` (soft edges) | Anime, painterly line preservation. |
| `fake_scribble` | Loose sketch → coherent line art. |
| `mlsd` | Architecture, interiors, straight lines. |
| `uniformer` | Scene composition, palette transfer. |

```python
for model in ("midas", "hed", "fake_scribble"):
    annotation = await ctx.session.call_tool("annotate_image", {
        "image": photo_b64,
        "model": model,
    })
    # save annotation, then use in a generate call
```

## 4. Combine with Director tools

Extract line art from a photo with `director_tool`, then use it as a
ControlNet condition for a fresh stylized generation:

```python
# Step 1: extract clean line art
lineart = await ctx.session.call_tool("director_tool", {
    "tool": "lineart",
    "image": photo_b64,
    "defry": 5,
})

# Step 2: use the line art as a condition (use hed preprocessor
# semantics, since lineart is effectively an edge map)
result = await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, anime style, watercolor",
    "controlnet_condition": lineart[0].data,
    "controlnet_model": "hed",
})
```

## 5. Tips

:::{tip}
**Match the preprocessor to the source.** A depth map extracted from a
photograph works great for re-posing a 3D scene; it's noisy for anime
line art. Use `hed` or `fake_scribble` for drawn inputs.
:::

:::{warning}
**ControlNet conditioning requires V4+.** V3 models don't accept
`controlnet_condition` / `controlnet_model`. Use `is_v4_model()` to check:

```python
from novelai_image_mcp.nai import is_v4_model
is_v4_model("nai-diffusion-4-5-full")  # True
is_v4_model("nai-diffusion-3")          # False
```
:::

## What's next?

- [`annotate_image` reference](../tools/annotate.md)
- [`director_tool` reference](../tools/director.md)
- [Vibe transfer](vibe-transfer.md) — alternate style-transfer workflow
