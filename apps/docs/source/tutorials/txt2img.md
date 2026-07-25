# Tutorial: Text-to-image

Generate an image from a text prompt using the `generate_image` tool. This
is the simplest workflow — no input images, no masks, no vibes.

## 1. Generate your first image

```python
result = await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, fox ears, autumn leaves, masterpiece, best quality",
    "negative_prompt": "lowres, bad anatomy, watermark, signature",
    "width": 832,
    "height": 1216,
    "steps": 28,
    "scale": 5.0,
    "sampler": "k_euler_ancestral",
    "seed": 42,
})
```

The result is a list with an `Image` block (the agent can "see" the image)
and a text block with the saved file path:

```python
[
    Image(data=b"...png bytes...", format="png"),
    "Saved 1 image(s): ['outputs/generate-20260725-133702-001.png']"
]
```

## 2. Generate multiple variants

Pass `n_samples` to produce several images in one API call (cheaper than
separate calls):

```python
result = await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, fox ears, autumn leaves",
    "n_samples": 4,
    "seed": 42,
})
# 4 images saved; the first is returned inline.
```

## 3. Use a different model

```python
# V3 model
await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, fox ears",
    "model": "nai-diffusion-3",
})

# V4.5 full (current default)
await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, fox ears",
    "model": "nai-diffusion-4-5-full",
})
```

## 4. Reproduce a generation

To reproduce the same image, set the same `seed` and the same parameters:

```python
await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, fox ears, autumn leaves",
    "seed": 42,
    "width": 832, "height": 1216, "steps": 28,
    "scale": 5.0, "sampler": "k_euler_ancestral",
})
```

The output is bit-identical (assuming NovelAI's model weights haven't
changed).

## 5. CLI equivalent

```bash
uv run python -m novelai_image_mcp generate \
  --prompt "1girl, fox ears, autumn leaves, masterpiece, best quality" \
  --negative "lowres, bad anatomy, watermark" \
  --width 832 --height 1216 --steps 28 --scale 5.0 \
  --seed 42
```

## What's next?

- [Image-to-image](img2img.md) — transform an existing image
- [Multi-character composition](../tools/generate.md#multi-character-composition-v4) — V4+ feature
- [Vibe transfer](vibe-transfer.md) — encode a reference style
- [Tools reference](../tools/index.md) — full parameter list
