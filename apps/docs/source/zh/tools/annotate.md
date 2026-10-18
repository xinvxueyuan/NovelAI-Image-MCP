# `annotate_image`

用 **ControlNet 预处理器**为图像做标注。输出就是标注本身 —— 一张派生图像
（例如线稿图或深度图），你可以把它作为 ControlNet 条件喂回生成流程。

## 参数

| 名称 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `image` | `str` | *必填* | base64 编码的 PNG/JPEG。 |
| `model` | `str` | *必填* | ControlNet 预处理器 id（见下表）。 |

## 返回

`list[ContentBlock]` —— 标注的 base64 `Image` + 保存路径文本。

## ControlNet 模型

| `model` 值 | NovelAI 名称 | 输出 | 用途 |
|---|---|---|---|
| `hed` | Palette Swap | 柔和边缘图 | 动漫 / 绘画风格的线条保留 |
| `midas` | Form Lock / Depth | 深度图 | 姿态、深度、体积一致性 |
| `fake_scribble` | Scribbler | 伪涂鸦线稿 | 松散草图 → 连贯线稿 |
| `mlsd` | Building Control | 直线检测 | 建筑、室内 |
| `uniformer` | Landscaper | 语义分割 | 场景构图、配色 |

用 `ControlNetModel` 枚举在运行时列出它们：

```python
from novelai_image_mcp.nai import ControlNetModel
print([m.value for m in ControlNetModel])
```

## 示例

### 提取深度图

```python
depth = await ctx.session.call_tool("annotate_image", {
    "image": photo_b64,
    "model": "midas",
})
```

### 面向动漫工作流的 HED（柔和边缘）

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

## 提示

:::{tip}
**工作流**：用 `midas` 从照片提取深度图，再把它作为 ControlNet 条件传给后续的
`generate_image` 调用，就能在保留姿态与构图的前提下，用另一种风格重新渲染
这个场景。
:::

:::{admonition} 标注 ≠ Director
:class: note

`director_tool` 对图像做的是*视觉*变换（线稿、上色等）。`annotate_image` 提取的
是*结构图*（深度、边缘、分割），用来驱动下游生成，而不是直接观看。
:::

## 另请参见

- [ControlNet 教程](../tutorials/controlnet.md) —— 完整的 annotate → generate 工作流
- [`annotate_image` API 参考](../api/tools.md)
- [`ControlNetModel` 枚举](../api/client.md) —— 列于 `nai.constants` 子模块
