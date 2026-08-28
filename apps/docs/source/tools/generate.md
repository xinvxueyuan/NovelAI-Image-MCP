# Generation tools

Three tools that produce images from a text prompt — pure text-to-image,
image-conditioned (img2img), and mask-conditioned (inpaint). All three
return a base64 `Image` block plus the saved file path.

---

## `generate_image`

Text-to-image. The most common tool — produces one or more images from a
prompt string. Supports NovelAI V3 / V4 / V4.5 / V5 models, multi-character
composition, and vibe transfer (V5 rejects vibe transfer — not yet released
upstream). V5 additionally accepts English/Japanese natural-language prompts.

### Parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `prompt` | `str` | *required* | Positive prompt. Tags separated by commas. |
| `negative_prompt` | `str` | `""` | Negative prompt (UC). |
| `model` | `str \| None` | `NOVELAI_DEFAULT_MODEL` | Override model id. See `Model` enum. |
| `width` | `int \| None` | `NOVELAI_DEFAULT_WIDTH` | Image width (px). Multiple of 64. |
| `height` | `int \| None` | `NOVELAI_DEFAULT_HEIGHT` | Image height (px). Multiple of 64. |
| `steps` | `int \| None` | `NOVELAI_DEFAULT_STEPS` | Sampler steps (1–50). |
| `scale` | `float \| None` | `NOVELAI_DEFAULT_SCALE` | CFG scale (0–20). |
| `sampler` | `str \| None` | `NOVELAI_DEFAULT_SAMPLER` | Sampler id (see `Sampler` enum). |
| `seed` | `int` | `0` | RNG seed. `0` = random. |
| `n_samples` | `int` | `1` | Number of images (1–8). |
| `quality` | `bool` | `True` | Use the quality tags preset (V4+). |
| `uc_preset` | `int` | `0` | Negative-prompt preset (0=heavy, 1=light, 2=human focus). |
| `cfg_rescale` | `float` | `0.0` | CFG rescale (0–1, V4+). |
| `smea` | `bool \| None` | model-dependent | Enable SMEA. `None` = auto. |
| `smea_dynamic` | `bool \| None` | model-dependent | Enable dynamic SMEA. |
| `auto_smea` | `bool` | `False` | Auto-select SMEA based on resolution. |
| `straight_alpha` | `bool` | `False` | True alpha channel (V5 only; pair with `transparent background` / `has alpha`). |
| `prefer_brownian` | `bool` | `True` | Prefer Brownian noise schedule (V4+). |
| `noise_schedule` | `str` | `"karras"` | Noise schedule (`karras`, `exponential`, `polyexponential`). |
| `character_prompts` | `list[dict] \| None` | `None` | V4+ / V5 multi-character composition. |
| `references` | `list[str] \| None` | `None` | V4/V4.5 vibe tokens (base64 vibe strings from `encode_vibe`); rejected on V5. |

### Returns

`list[ContentBlock]` — base64 `Image` + saved-path text.

### Example

```python
# Simple text-to-image
await ctx.session.call_tool("generate_image", {
    "prompt": "a fox in a snowy forest, masterpiece, best quality",
    "negative_prompt": "lowres, bad anatomy, watermark",
    "width": 832,
    "height": 1216,
    "steps": 28,
    "scale": 5.0,
    "seed": 42,
})
```

### Multi-character composition (V4+ / V5)

```python
await ctx.session.call_tool("generate_image", {
    "prompt": "two characters talking in a cafe",
    "character_prompts": [
        {"prompt": "1girl, red hair, blue eyes", "x": 0.3, "y": 0.5, "negative_prompt": ""},
        {"prompt": "1boy, black hair, green eyes", "x": 0.7, "y": 0.5, "negative_prompt": ""},
    ],
})
```

`x` and `y` are normalized centers in the range `0.1`–`0.9`. The first
character is always the focal subject.

### Vibe transfer (V4 / V4.5)

```python
# 1. Encode a reference image
vibe = await ctx.session.call_tool("encode_vibe", {"reference": ref_b64})

# 2. Use the vibe as a reference
await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, watercolor style",
    "references": [vibe],
})
```

See [vibe transfer tutorial](../tutorials/vibe-transfer.md) for the full
workflow.

---

## `image_to_image`

Image-to-image. Produces a new image conditioned on an input image.

### Parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `prompt` | `str` | *required* | Positive prompt. |
| `image` | `str` | *required* | Base64-encoded input PNG/JPEG. |
| `negative_prompt` | `str` | `""` | Negative prompt. |
| `model` | `str \| None` | default | Model id. Must match the input image domain. |
| `strength` | `float` | `0.3` | 0.01–0.99. How far to deviate from the input. |
| `noise` | `float` | `0.0` | 0–0.99. Extra variation. |
| `width` / `height` / `steps` / `scale` / `sampler` / `seed` / `n_samples` / `quality` / `uc_preset` / `noise_schedule` / `cfg_rescale` | (see `generate_image`) | (same defaults) | |
| `extra_noise_seed` | `int \| None` | `None` | Separate seed for noise (defaults to `seed`). |

### Example

```python
await ctx.session.call_tool("image_to_image", {
    "prompt": "1girl, masterpiece, smile",
    "image": image_b64,
    "strength": 0.4,
    "noise": 0.05,
})
```

:::{tip}
`strength=0.5` is a good starting point. Below 0.3, the result looks like a
re-denoise of the input; above 0.7, it drifts toward a fresh text-to-image.
:::

---

## `inpaint`

Locally redraw a region of an image. The region is defined by a mask —
non-transparent pixels are regenerated.

### Parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `prompt` | `str` | *required* | Prompt for the regenerated region. |
| `image` | `str` | *required* | Base64-encoded input PNG/JPEG. |
| `mask` | `str` | *required* | Base64-encoded mask. Non-transparent = redraw. |
| `negative_prompt` | `str` | `""` | Negative prompt for the region. |
| `model` | `str \| None` | default | **Must** be an inpaint model (e.g. `nai-diffusion-4-5-full-inpainting` or `nai-diffusion-5-full-inpainting`). |
| `strength` / `noise` / `width` / `height` / `steps` / `scale` / `sampler` / `seed` / `n_samples` / `quality` / `uc_preset` / `noise_schedule` / `cfg_rescale` / `extra_noise_seed` | (see `image_to_image`) | (same defaults) | |

### Example

```python
await ctx.session.call_tool("inpaint", {
    "prompt": "1girl, masterpiece, smiling",
    "image": image_b64,
    "mask": mask_b64,
    "model": "nai-diffusion-4-5-full-inpainting",
    "strength": 0.5,
})
```

:::{warning}
Inpainting requires a dedicated inpaint model. Calling `inpaint` with a
non-inpaint model returns a `NovelAIValidationError`. Use
[`is_inpaint_model`](../api/client.md) (in the `nai.constants` submodule) to
check before calling.
:::

See [inpaint tutorial](../tutorials/inpaint.md) for a mask-creation
walkthrough.

---

## See also

- [Generation tutorial](../tutorials/txt2img.md)
- [img2img tutorial](../tutorials/img2img.md)
- [inpaint tutorial](../tutorials/inpaint.md)
- [`novelai_image_mcp.tools.generate` API reference](../api/tools.md)
- [Configuration](../configuration.md) — defaults applied when a parameter is omitted
