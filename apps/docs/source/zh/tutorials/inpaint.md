# 教程：局部重绘

用 `inpaint` 工具重绘图像中的指定区域。适用场景：修正人体结构、移除物体、
更换背景、替换面部。

## 前置条件

- 一个 `*_inpainting` 模型。标准的 V4.5 局部重绘模型是
  `nai-diffusion-4-5-full-inpainting`。
- 一张**蒙版** —— 一张 PNG，其中非透明（alpha > 0）的像素标记需要重新生成的
  区域。

## 1. 制作蒙版

蒙版必须与输入图像尺寸相同。你可以用任何图像编辑器（例如 Photoshop、GIMP、
Krita）制作，也可以用代码生成：

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

## 2. 运行局部重绘

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

## 3. 调 `strength`

与 `image_to_image` 一样，`strength` 控制重绘区域偏离原图的程度：

- `0.2–0.3` —— 保留身份特征，修补小问题
- `0.5` —— 均衡，通常是最佳点
- `0.7+` —— 大幅改动，有与周围像素接缝的风险

## 4. 工作流：迭代细化

局部重绘最适合迭代进行。生成、查看、修蒙版、重复：

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

## 5. 使用 Python API

如果要在没有 MCP 宿主的情况下写脚本，可以直接调用底层客户端：

:::{note}
这些直连 API 的例子使用 `create_http_client()` —— **不要**自己手搓
`httpx.AsyncClient()`。NovelAI 的 Cloudflare WAF 会对 TLS 栈做指纹识别
（JA3/JA4）并静默重置非浏览器连接；`create_http_client()` 模拟 Chrome，是
`image.novelai.net` 唯一受支持的传输方式。
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
    mask_b64 = base64.b64encode(Path("mask.png").read_bytes()).decode("ascii")
    async with create_http_client(timeout=settings.timeout) as http_client:
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

## 常见坑

:::{warning}
**模型不匹配。** 局部重绘需要 inpaint 模型。用非 inpaint 模型调用 `inpaint`
会抛出 `NovelAIValidationError`。可以这样检查：

```python
from novelai_image_mcp.nai import is_inpaint_model, Model
is_inpaint_model(Model.V4_5_INPAINT)  # True
is_inpaint_model(Model.V4_5)           # False
```
:::

:::{warning}
**蒙版尺寸。** 蒙版必须与输入图像尺寸*完全*一致。832×1216 的图像需要
832×1216 的蒙版。尺寸不匹配的蒙版会抛出 `NovelAIValidationError`。
:::

:::{tip}
**给蒙版做羽化。** 硬边蒙版会产生可见接缝。用高斯模糊（半径 5–10 px）柔化
蒙版的 alpha，过渡会更自然。
:::

## 下一步

- [图生图](img2img.md) —— 整图变换
- [放大](upscale.md) —— 以更高分辨率收尾
- [`inpaint` 参考](../tools/generate.md#inpaint)
