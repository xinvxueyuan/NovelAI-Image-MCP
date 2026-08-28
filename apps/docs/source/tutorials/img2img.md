# Tutorial: Image-to-image

Transform an existing image with a new prompt using the `image_to_image`
tool. Ideal for refining details, changing style, or iterating on a
composition without starting from scratch.

## 1. Read the input image

`image_to_image` expects the input as a base64-encoded PNG/JPEG string. If
you're scripting in Python:

```python
import base64
from pathlib import Path

image_b64 = base64.b64encode(Path("input.png").read_bytes()).decode("ascii")
```

The CLI accepts a file path directly — no manual base64 needed.

## 2. Run image-to-image

```python
result = await ctx.session.call_tool("image_to_image", {
    "prompt": "1girl, masterpiece, smiling, golden hour lighting",
    "image": image_b64,
    "strength": 0.4,
    "noise": 0.05,
    "seed": 42,
})
```

## 3. Tune `strength`

`strength` (0.01–0.99) is the most important parameter:

| `strength` | Effect |
|---|---|
| 0.1–0.3 | Subtle refinement — fixes small details, preserves composition. |
| 0.4–0.6 | Balanced — visible style/lighting changes, identity preserved. |
| 0.7–0.9 | Drastic — approaches fresh text-to-image, input barely visible. |

:::{tip}
Start at `0.5`. If the result looks too similar to the input, bump to `0.6`;
if it's lost the input's identity, drop to `0.4`.
:::

## 4. Add controlled noise

`noise` (0–0.99) injects extra randomness *on top of* the input image. Use
it to introduce variation without changing `strength`:

```python
result = await ctx.session.call_tool("image_to_image", {
    "prompt": "1girl, masterpiece",
    "image": image_b64,
    "strength": 0.5,
    "noise": 0.2,        # 20% noise
    "extra_noise_seed": 99,  # separate seed for the noise (defaults to `seed`)
})
```

## 5. Use the Python API

If you're scripting without an MCP host, call the underlying client directly:

:::{note}
The direct-API examples use `create_http_client()` — do **not** hand-roll
`httpx.AsyncClient()`. NovelAI's Cloudflare WAF fingerprints the TLS stack
(JA3/JA4) and silently resets non-browser connections;
`create_http_client()` impersonates Chrome and is the only supported
transport for `image.novelai.net`.
:::

```python
import asyncio
import base64
from pathlib import Path

from novelai_image_mcp.nai import (
    Action, GenerationRequest, Model, create_novelai_client,
)
from novelai_image_mcp.nai.http import create_http_client
from novelai_image_mcp.settings import NovelAISettings

async def main():
    settings = NovelAISettings(token="pst-...")
    image_b64 = base64.b64encode(Path("input.png").read_bytes()).decode("ascii")
    async with create_http_client(timeout=settings.timeout) as http_client:
        client = create_novelai_client(settings, http_client=http_client)
        try:
            request = GenerationRequest(
                prompt="1girl, masterpiece, smiling",
                action=Action.IMG2IMG,
                model=Model.V4_5,
                image=image_b64,
                strength=0.4, noise=0.05, seed=42,
            )
            images = await client.generate(request)
        finally:
            await client.aclose()

asyncio.run(main())
```

## What's next?

- [Inpainting](inpaint.md) — redraw a specific region
- [Upscaling](upscale.md) — increase resolution
- [`image_to_image` reference](../tools/generate.md#image_to_image)
