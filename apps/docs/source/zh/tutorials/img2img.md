# 教程：图生图

用 `image_to_image` 工具，以一段新提示词变换已有图像。适合细化细节、改变风格，
或者在不从头开始的前提下迭代一个构图。

## 1. 读取输入图像

`image_to_image` 期望输入是 base64 编码的 PNG/JPEG 字符串。如果你用 Python
写脚本：

```python
import base64
from pathlib import Path

image_b64 = base64.b64encode(Path("input.png").read_bytes()).decode("ascii")
```

CLI 直接接受文件路径 —— 不需要手动做 base64。

## 2. 运行图生图

```python
result = await ctx.session.call_tool("image_to_image", {
    "prompt": "1girl, masterpiece, smiling, golden hour lighting",
    "image": image_b64,
    "strength": 0.4,
    "noise": 0.05,
    "seed": 42,
})
```

## 3. 调 `strength`

`strength`（0.01–0.99）是最重要的参数：

| `strength` | 效果 |
|---|---|
| 0.1–0.3 | 细微修饰 —— 修补小细节，保留构图。 |
| 0.4–0.6 | 均衡 —— 风格 / 光照有可见变化，身份得以保留。 |
| 0.7–0.9 | 剧烈 —— 接近全新的文生图，输入几乎看不出来。 |

:::{tip}
从 `0.5` 开始。如果结果与输入过于相似，提到 `0.6`；如果输入的身份特征
丢失了，降到 `0.4`。
:::

## 4. 加入受控噪声

`noise`（0–0.99）在输入图像*之上*注入额外随机性。用它可以在不改变
`strength` 的前提下引入变化：

```python
result = await ctx.session.call_tool("image_to_image", {
    "prompt": "1girl, masterpiece",
    "image": image_b64,
    "strength": 0.5,
    "noise": 0.2,        # 20% noise
    "extra_noise_seed": 99,  # separate seed for the noise (defaults to `seed`)
})
```

## 5. 使用 Python API

如果你在没有 MCP 宿主的情况下写脚本，可以直接调用底层客户端：

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

## 下一步

- [局部重绘](inpaint.md) —— 重绘指定区域
- [放大](upscale.md) —— 提高分辨率
- [`image_to_image` 参考](../tools/generate.md#image_to_image)
