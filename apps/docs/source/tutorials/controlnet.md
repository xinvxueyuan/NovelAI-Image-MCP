# Tutorial: ControlNet preprocessors

Use NovelAI's ControlNet preprocessors to extract a structural map from a
reference image — depth, line art, semantic segmentation. In v0.1.0 the
extracted annotation is returned as a standalone image you can save or
inspect; feeding it back into a generation is a v0.2 feature.

## Workflow overview

```{mermaid}
graph LR
    A[Reference image] --> B[annotate_image]
    B --> C[Annotation<br/>depth / line art]
    C --> D[Save or display]
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
# depth_result[0] is an Image content block with the depth map;
# depth_result[1] is the saved file path.
```

## 2. Try different preprocessors

| Preprocessor | Best for |
|---|---|
| `midas` (depth) | Pose, volumetric composition. |
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
    # Save each annotation for inspection
```

## 3. CLI equivalent

```bash
# Extract a depth map
uv run python -m novelai_image_mcp annotate ./photo.png --model midas
```

## 4. Limitations in v0.1.0

:::{warning}
**Generation does not consume annotations yet.** `generate_image` accepts
text prompts, character prompts, and vibe references — but not a
ControlNet condition. The `controlnet_condition` / `controlnet_model`
parameters planned for v0.2 will let `generate_image` use an extracted
annotation as a structural condition.
:::

:::{tip}
**Workaround:** For now, combine `annotate_image` with `director_tool` to
produce a stylized line-art output from a photo, then optionally use
`image_to_image` to refine. See [Director tools](../tools/director.md).
:::

## What's next?

- [`annotate_image` reference](../tools/annotate.md)
- [`director_tool` reference](../tools/director.md)
- [Vibe transfer](vibe-transfer.md) — alternate style-transfer workflow
