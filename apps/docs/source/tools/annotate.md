# `annotate_image`

Annotate an image with a **ControlNet preprocessor**. The output is the
annotation itself — a derived image (e.g. a line-art map or depth map) you
can feed back into a generation as a ControlNet condition.

## Parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `image` | `str` | *required* | Base64-encoded PNG/JPEG. |
| `model` | `str` | *required* | ControlNet preprocessor id (see below). |

## Returns

`list[ContentBlock]` — base64 `Image` of the annotation + saved-path text.

## ControlNet models

| `model` value | NovelAI name | Output | Use case |
|---|---|---|---|
| `hed` | Palette Swap | Soft edge map | Anime / painterly line preservation |
| `midas` | Form Lock / Depth | Depth map | Pose, depth, volumetric consistency |
| `fake_scribble` | Scribbler | Pseudo-scribble line art | Loose sketch → coherent line art |
| `mlsd` | Building Control | Straight-line detection | Architecture, interiors |
| `uniformer` | Landscaper | Semantic segmentation | Scene composition, palette |

Use `ControlNetModel` enum introspection to list them at runtime:

```python
from novelai_image_mcp.nai import ControlNetModel
print([m.value for m in ControlNetModel])
```

## Examples

### Depth map extraction

```python
depth = await ctx.session.call_tool("annotate_image", {
    "image": photo_b64,
    "model": "midas",
})
```

### HED (soft edges) for anime workflows

```python
hed = await ctx.session.call_tool("annotate_image", {
    "image": illustration_b64,
    "model": "hed",
})
```

### CLI

```bash
uv run python -m novelai_image_mcp annotate ./photo.png --model midas
```

## Tips

:::{tip}
**Workflow**: extract a depth map from a photograph with `midas`, then use
it as a ControlNet condition in a subsequent `generate_image` call to
re-render the scene with a different style while preserving the pose and
composition.
:::

:::{admonition} Annotation ≠ Director
:class: note

`director_tool` transforms an image *visually* (line art, colorize, etc.).
`annotate_image` extracts a *structural map* (depth, edges, segmentation)
that's intended to drive a downstream generation, not to be viewed directly.
:::

## See also

- [ControlNet tutorial](../tutorials/controlnet.md) — full annotate → generate workflow
- [`annotate_image` API reference](../api/tools.md)
- [`ControlNetModel` enum](../api/client.md) — listed in the `nai.constants` submodule
