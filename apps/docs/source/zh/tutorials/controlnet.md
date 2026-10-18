# 教程：ControlNet 预处理器

用 NovelAI 的 ControlNet 预处理器从参考图提取结构图 —— 深度、线稿、语义分割。
提取出的标注会作为一张独立图像返回，你可以保存或查看；`generate_image` 目前
还无法把它当作 ControlNet 条件消费。

## 工作流概览

```{mermaid}
graph LR
    A[Reference image] --> B[annotate_image]
    B --> C[Annotation<br/>depth / line art]
    C --> D[Save or display]
```

## 1. 提取深度图

```python
import base64
from pathlib import Path

photo_b64 = base64.b64encode(Path("photo.png").read_bytes()).decode("ascii")

depth_result = await ctx.session.call_tool("annotate_image", {
    "image": photo_b64,
    "model": "midas",
})
# depth_result[0] is an Image content block with the depth map;
# depth_result[1] is the saved file path.
```

## 2. 试试不同的预处理器

| 预处理器 | 最适合 |
|---|---|
| `midas`（深度） | 姿态、体积构图。 |
| `hed`（柔和边缘） | 动漫、绘画风格的线条保留。 |
| `fake_scribble` | 松散草图 → 连贯线稿。 |
| `mlsd` | 建筑、室内、直线。 |
| `uniformer` | 场景构图、配色迁移。 |

```python
for model in ("midas", "hed", "fake_scribble"):
    annotation = await ctx.session.call_tool("annotate_image", {
        "image": photo_b64,
        "model": model,
    })
    # Save each annotation for inspection
```

## 3. 等价的 CLI 命令

```bash
# Extract a depth map
uv run python -m novelai_image_mcp annotate ./photo.png --model midas
```

## 4. 当前限制

:::{warning}
**生成流程目前还不会消费标注。** `generate_image` 接受文本提示词、角色提示词与
vibe 参考 —— 但不接受 ControlNet 条件。`generate_image` 上还没有
`controlnet_condition` / `controlnet_model` 参数，所以提取出的标注无法驱动
一次生成。
:::

:::{tip}
**变通办法：** 目前可以先用 `annotate_image` 配合 `director_tool`，从照片产出
风格化的线稿结果，再用 `image_to_image` 可选地细化。见
[Director 工具](../tools/director.md)。
:::

## 下一步

- [`annotate_image` 参考](../tools/annotate.md)
- [`director_tool` 参考](../tools/director.md)
- [Vibe transfer](vibe-transfer.md) —— 另一种风格迁移工作流
