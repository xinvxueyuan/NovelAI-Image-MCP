# `director_tool`

对图像套用 NovelAI **Director 工具**。Director 工具把已有图像变换成派生形态
—— 线稿、素描、背景移除、declutter、上色或表情迁移。

## 参数

| 名称 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `tool` | `str` | *必填* | 以下之一：`lineart`、`sketch`、`bg-removal`、`declutter`、`colorize`、`emotion`。 |
| `image` | `str` | *必填* | base64 编码的 PNG/JPEG。 |
| `prompt` | `str` | `""` | 引导 `colorize` 与 `emotion`。 |
| `defry` | `int` | `0` | 0–10。锐化线稿（供 `lineart` / `sketch` 使用）。 |
| `emotion` | `str \| None` | `None` | 表情名称（`emotion` 工具必填）。 |
| `emotion_level` | `int` | `0` | 0–5。0 = 正常强度，5 = 最弱。 |

:::{warning}
`emotion` 与 `emotion_level` 属于**实验性**参数：只对通过 insiders 头
（`X-MCP-Insiders: experimental-tools=true`）显式 opt-in 的请求开放。没有该
opt-in 时，传入其中任意一个都会以 `ToolError` 失败；仅传入非默认的
`emotion_level` 也算作传参。无论哪种情况，这两个参数都仍然出现在工具 schema
中，因为 schema 在服务器启动时发布，无法按请求变化。见
[Insiders 头、路由与审计](../development/insiders-and-routing.md)。
:::

## 返回

`list[ContentBlock]` —— 变换后图像的 base64 `Image` + 保存路径文本。

## Director 工具

| `tool` 值 | 说明 |
|---|---|
| `lineart` | 把图像转换为干净的线稿。用 `defry`（0–10）锐化线条。 |
| `sketch` | 转换为铅笔素描风格。同样接受 `defry`。 |
| `bg-removal` | 移除背景，让前景主体留在透明底上。 |
| `declutter` | 移除细小的杂乱元素（文字、水印、颗粒）。 |
| `colorize` | 为单色 / 线稿图像上色。`prompt` 引导配色。 |
| `emotion` | 为对象迁移面部表情。需要 `emotion` 名称；`emotion_level`（0–5）调节强度。 |

## 表情名称

`emotion` 参数接受以下取值：

```text
neutral, happy, sad, angry, scared, surprised, tired, excited, nervous,
thinking, confused, shy, disgusted, smug, bored, laughing, irritated,
aroused, embarrassed, worried, love, determined, hurt, playful
```

用 `Emotion` 枚举在运行时列出它们：

```python
from novelai_image_mcp.nai import Emotion
print([e.value for e in Emotion])
```

## 示例

### 提取线稿

```python
await ctx.session.call_tool("director_tool", {
    "tool": "lineart",
    "image": image_b64,
    "defry": 5,
})
```

### 移除背景

```python
await ctx.session.call_tool("director_tool", {
    "tool": "bg-removal",
    "image": image_b64,
})
```

### 为草图上色

```python
await ctx.session.call_tool("director_tool", {
    "tool": "colorize",
    "image": sketch_b64,
    "prompt": "1girl, red hair, blue dress, sunny day",
})
```

### 表情迁移

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

## 提示

:::{tip}
**工作流思路**：用 `lineart` 从照片提取线稿，再把它作为 ControlNet 条件
（见 [`annotate_image`](annotate.md)）做一次全新的风格化生成。
:::

:::{admonition} `defry` 的语义
:class: note

`defry` 是 NovelAI 的 "de-fry" 参数 —— 它减轻激进线稿提取可能产生的过度平滑、
"湿" 的观感。值越大线条越锐利，但会引入抖动。`5` 是不错的折中。
:::

## 另请参见

- [`director_tool` API 参考](../api/tools.md)
- [`DirectorTool` 枚举](../api/client.md) —— 列于 `nai.constants` 子模块
- [ControlNet 教程](../tutorials/controlnet.md) —— 把 `lineart` 与 `annotate_image` 组合使用
