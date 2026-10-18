# 教程：Vibe transfer

把参考图的风格或身份编码为一个 vibe token，再把它传给一次生成。Vibe transfer
（仅 V4+）是在多次生成之间复现同一风格或角色的最干净的方式。

## 什么时候用 vibe transfer

| 目标 | 工具 |
|---|---|
| 在多次生成中复用同一种**风格** | `encode_vibe`（较低的 `information_extracted`） |
| 在新场景中复现**角色身份** | `encode_vibe`（较高的 `information_extracted`） |
| 匹配**构图** | ControlNet（[教程](controlnet.md)） |
| 重绘一张已有图像 | `image_to_image`（[教程](img2img.md)） |

## 1. 编码一张参考图

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

## 2. 在生成中使用这个 vibe

```python
result = await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, sitting in a cafe, masterpiece",
    "references": [style_vibe],
})
```

生成的图像会继承参考图的绘画风格、光照与配色 —— 但使用完全不同的主体与构图。

## 3. 混合多个 vibe

`references` 接受列表。可以把一个风格 vibe 和一个角色 vibe 混合起来：

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

结果会带着这个角色的面部 / 身份，并呈现该风格的绘画质感。

## 4. 调 `information_extracted`

| 取值 | 效果 |
|---|---|
| `0.01`–`0.3` | 风格迁移 —— 光照、配色、笔触。身份特征不保留。 |
| `0.4`–`0.7` | 均衡 —— 风格 + 大致相同的角色原型。 |
| `0.8`–`1.0` | 身份迁移 —— 同一个角色换个姿势 / 场景。 |

:::{tip}
风格迁移从 `0.3` 起调，身份迁移从 `0.9` 起调。以 0.1 为步长迭代。
:::

## 5. 缓存

服务器在内存中缓存 vibe 编码（大小由 `NOVELAI_VIBE_CACHE_ENTRIES` 控制，
默认 64）。用相同参数对同一张参考图再编码一次会命中缓存，立即返回而不调用 API。

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

## 6. 只有 vibe transfer

`generate_image` 接受 vibe 参考，但不接受 ControlNet 条件。要把结构图与风格
组合起来，目前的做法是用 `annotate_image` 提取标注，再通过 `director_tool`
应用；`generate_image` 上的 ControlNet 条件尚未实现。

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

# Step 3: generate with the vibe (references are supported, controlnet is not)
result = await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, standing in a meadow",
    "references": [style_vibe],
})
```

结果会带上这幅画的风格；`generate_image` 上的结构条件尚未实现。

## 7. 坑

:::{warning}
**V5 模型不支持 vibe。** 用 V5 模型 id 调用 `encode_vibe` 会抛出 `ToolError`。
V3 / Furry 模型同样不在支持集合内，但拒绝是由 API 而非本地强制执行的 ——
请用 `supports_vibe()`（接受一个 `Model` 枚举）检查，而不要依赖报错：

```python
from novelai_image_mcp.nai import supports_vibe, Model
supports_vibe(Model.V4_5)  # True
supports_vibe(Model.V3)    # False
supports_vibe(Model.V5)    # False
```
:::

:::{tip}
**参考图质量很重要。** 一张高质量、裁剪得当的参考图（特写、中性背景）比一堆
杂乱但相似的图能产出更好的 vibe。
:::

## 下一步

- [`encode_vibe` 参考](../tools/vibe.md)
- [`generate_image` 参考](../tools/generate.md#generate_image)
- [ControlNet 教程](controlnet.md) —— 把 vibe 与结构条件组合起来
