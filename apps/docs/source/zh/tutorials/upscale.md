# 教程：放大

用 NovelAI 的独立放大器把图像分辨率提高 4×。相比以更高分辨率重新生成，
放大器更快，结果也更干净。

## 1. 放大一张图像

```python
import base64
from pathlib import Path

image_b64 = base64.b64encode(Path("portrait.png").read_bytes()).decode("ascii")

result = await ctx.session.call_tool("upscale_image", {
    "image": image_b64,
    "factor": 4,
})
```

输出的 PNG 是源分辨率的 4×。832×1216 的输入会变成 3328×4864。

## 2. `factor` 固定为 4

NovelAI 的独立放大器只提供单一 4× 档位，所以 `factor` 只接受 `4` ——
没有 2× 模式。请以较低分辨率生成后放大一次，而不是寻找更小的倍率。

Anlas 消耗随源分辨率增长。如果要在批量场景下放大，先调用
[`estimate_anlas_cost`](../tools/account.md#estimate_anlas_cost)。

## 3. 等价的 CLI 命令

```bash
uv run python -m novelai_image_mcp upscale ./portrait.png --factor 4
```

## 4. 工作流：生成 → 放大

一个常见做法是先用低分辨率快速迭代，再放大最终留下的那张：

```python
# Step 1: iterate at 832×1216 (cheap, ~5 Anlas each)
result = await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, masterpiece",
    "width": 832, "height": 1216,
    "n_samples": 4,
})
# (you pick the best of the 4 — say, outputs/generate-...003.png)

# Step 2: upscale the keeper to 3328×4864
import base64
from pathlib import Path
keeper_b64 = base64.b64encode(
    Path("outputs/generate-...003.png").read_bytes()
).decode("ascii")

result = await ctx.session.call_tool("upscale_image", {
    "image": keeper_b64,
    "factor": 4,
})
```

这样一批约花 5 Anlas，加上放大约 10 Anlas，合计约 15 Anlas —— 比直接生成四张
4× 图像（约 80 Anlas）便宜得多。

## 5. 坑

:::{warning}
**内存占用。** 把 1024×1024 的图像放大 4× 会得到 4096×4096 的 PNG
（未压缩约 64 MB）。请据此规划磁盘空间。
:::

:::{tip}
**先放大再局部重绘。** 如果你需要修补小细节，先放大能让 inpaint 模型有更多
像素可用 —— 蒙版更精细，细节更好。
:::

## 下一步

- [`upscale_image` 参考](../tools/upscale.md)
- [账户余额](../tools/account.md#get_subscription) —— 先检查 Anlas
- [成本估算](../tools/account.md#estimate_anlas_cost) —— 预览账单
