# `director_tool`

Apply a NovelAI **Director tool** to an image. Director tools transform an
existing image into a derivative form — line art, sketch, background
removal, declutter, colorize, or emotion transfer.

## Parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `tool` | `str` | *required* | One of: `lineart`, `sketch`, `bg-removal`, `declutter`, `colorize`, `emotion`. |
| `image` | `str` | *required* | Base64-encoded PNG/JPEG. |
| `prompt` | `str` | `""` | Guides `colorize` and `emotion`. |
| `defry` | `int` | `0` | 0–10. Sharpens line art (used by `lineart` / `sketch`). |
| `emotion` | `str \| None` | `None` | Emotion name (required for `emotion` tool). |
| `emotion_level` | `int` | `0` | 0–5. 0 = normal intensity, 5 = weakest. |

## Returns

`list[ContentBlock]` — base64 `Image` of the transformed image + saved-path text.

## Director tools

| `tool` value | Description |
|---|---|
| `lineart` | Convert the image to clean line art. Use `defry` (0–10) to sharpen lines. |
| `sketch` | Convert to a pencil-sketch style. Also accepts `defry`. |
| `bg-removal` | Remove the background, leaving the foreground subject on transparency. |
| `declutter` | Remove small clutter (text, watermarks, particles). |
| `colorize` | Colorize a monochrome / line-art image. `prompt` guides colors. |
| `emotion` | Transfer a facial emotion to the subject. Requires `emotion` name; `emotion_level` (0–5) scales intensity. |

## Emotion names

The `emotion` parameter accepts these values:

```text
happy, sad, angry, surprised, neutral, excited, nervous, thinking, wink,
pleased, smirk, awe, laughing, grumpy, embarrassed, screaming
```

Use `Emotion` enum introspection to list them at runtime:

```python
from novelai_image_mcp.nai import Emotion
print([e.value for e in Emotion])
```

## Examples

### Line art extraction

```python
await ctx.session.call_tool("director_tool", {
    "tool": "lineart",
    "image": image_b64,
    "defry": 5,
})
```

### Background removal

```python
await ctx.session.call_tool("director_tool", {
    "tool": "bg-removal",
    "image": image_b64,
})
```

### Colorize a sketch

```python
await ctx.session.call_tool("director_tool", {
    "tool": "colorize",
    "image": sketch_b64,
    "prompt": "1girl, red hair, blue dress, sunny day",
})
```

### Emotion transfer

```python
await ctx.session.call_tool("director_tool", {
    "tool": "emotion",
    "image": portrait_b64,
    "emotion": "happy",
    "emotion_level": 2,
})
```

### CLI

```bash
# Line art extraction
uv run python -m novelai_image_mcp director lineart ./portrait.png --defry 5

# Colorize a sketch
uv run python -m novelai_image_mcp director colorize ./sketch.png --prompt "1girl, red hair"

# Emotion transfer
uv run python -m novelai_image_mcp director emotion ./portrait.png --emotion happy --emotion-level 2
```

## Tips

:::{tip}
**Workflow idea**: extract line art from a photograph with `lineart`, then
use it as a ControlNet condition (see [`annotate_image`](annotate.md)) for a
fresh stylized generation.
:::

:::{admonition} `defry` semantics
:class: note

`defry` is NovelAI's "de-fry" parameter — it reduces the over-smoothed,
"wet" look that aggressive line-art extraction can produce. Higher values
sharpen lines but introduce jitter. `5` is a good middle ground.
:::

## See also

- [`director_tool` API reference](../api/tools.md)
- [`DirectorTool` enum](../api/client.md) — listed in the `nai.constants` submodule
- [ControlNet tutorial](../tutorials/controlnet.md) — combine `lineart` with `annotate_image`
