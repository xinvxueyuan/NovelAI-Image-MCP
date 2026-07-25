# Tutorial: Vibe transfer

Encode a reference image's style or identity into a vibe token, then pass
it to a generation. Vibe transfer (V4+ only) is the cleanest way to
reproduce a style or character across multiple generations.

## When to use vibe transfer

| Goal | Tool |
|---|---|
| Reuse a **style** across many generations | `encode_vibe` (low `information_extracted`) |
| Reproduce a **character identity** in new scenes | `encode_vibe` (high `information_extracted`) |
| Match a **composition** | ControlNet ([tutorial](controlnet.md)) |
| Repaint an existing image | `image_to_image` ([tutorial](img2img.md)) |

## 1. Encode a reference

```python
import base64
from pathlib import Path

ref_b64 = base64.b64encode(Path("reference.png").read_bytes()).decode("ascii")

# Style-focused vibe: low information_extracted
style_vibe = await ctx.session.call_tool("encode_vibe", {
    "reference": ref_b64,
    "information_extracted": 0.3,
})
# Returns a base64 vibe token (string)
```

## 2. Use the vibe in a generation

```python
result = await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, sitting in a cafe, masterpiece",
    "references": [style_vibe],
})
```

The generated image inherits the reference's painterly style, lighting, and
palette — but uses a completely different subject and composition.

## 3. Blend multiple vibes

`references` accepts a list. Blend a style vibe and a character vibe:

```python
# Style vibe — captures the painterly look
style_vibe = await ctx.session.call_tool("encode_vibe", {
    "reference": style_ref_b64,
    "information_extracted": 0.2,
})

# Character vibe — captures identity
character_vibe = await ctx.session.call_tool("encode_vibe", {
    "reference": character_ref_b64,
    "information_extracted": 0.9,
})

result = await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, sitting in a cafe",
    "references": [style_vibe, character_vibe],
})
```

The result has the character's face/identity in the style's painterly look.

## 4. Tune `information_extracted`

| Value | Effect |
|---|---|
| `0.01`–`0.3` | Style transfer — lighting, palette, brushwork. Identity not preserved. |
| `0.4`–`0.7` | Balanced — style + approximate character archetype. |
| `0.8`–`1.0` | Identity transfer — same character in a new pose/scene. |

:::{tip}
Start at `0.3` for style transfer and `0.9` for identity transfer. Iterate
in steps of 0.1.
:::

## 5. Caching

The server caches vibe encodings in-memory (size:
`NOVELAI_VIBE_CACHE_ENTRIES`, default 64). Encoding the same reference with
the same parameters a second time hits the cache and returns instantly
without an API call.

```python
# First call: hits the API (~2 seconds)
vibe1 = await ctx.session.call_tool("encode_vibe", {
    "reference": ref_b64,
    "information_extracted": 0.3,
})

# Second call with the same args: cache hit, returns instantly
vibe2 = await ctx.session.call_tool("encode_vibe", {
    "reference": ref_b64,
    "information_extracted": 0.3,
})
# vibe1 == vibe2
```

## 6. Vibe transfer only (v0.1.0)

`generate_image` accepts vibe references but not ControlNet conditions in
v0.1.0. To combine a structural map with a style, extract the annotation
with `annotate_image` and apply it via `director_tool` for now; full
ControlNet conditioning is planned for v0.2.

```python
# Step 1: extract depth from a pose reference (saved to disk)
depth = await ctx.session.call_tool("annotate_image", {
    "image": pose_photo_b64,
    "model": "midas",
})

# Step 2: encode a style vibe from a painting reference
style_vibe = await ctx.session.call_tool("encode_vibe", {
    "reference": painting_ref_b64,
    "information_extracted": 0.2,
})

# Step 3: generate with the vibe (v0.1.0 supports references, not controlnet)
result = await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, standing in a meadow",
    "references": [style_vibe],
})
```

The result carries the painting's style; structural conditioning will
arrive in v0.2.

## 7. Pitfalls

:::{warning}
**V3 models do not support vibes.** `encode_vibe` with a V3 model id
raises `ValueError`. Check with `is_v4_model()` (takes a `Model` enum):

```python
from novelai_image_mcp.nai import is_v4_model, Model
is_v4_model(Model.V4_5)  # True
is_v4_model(Model.V3)    # False
```
:::

:::{tip}
**Reference quality matters.** A single high-quality, well-cropped
reference (close-up, neutral background) produces better vibes than a noisy
album of similar images.
:::

## What's next?

- [`encode_vibe` reference](../tools/vibe.md)
- [`generate_image` reference](../tools/generate.md#generate_image)
- [ControlNet tutorial](controlnet.md) — combine vibes with structural conditioning
