# `upscale_image`

用 NovelAI 的独立放大器把图像放大 4×。放大器运行在 `NOVELAI_UPSCALE_MODEL`
所配置的 V5 模型上，与生成输入图像时所用的模型无关。

## 参数

| 名称 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `image` | `str` | *必填* | base64 编码的待放大 PNG/JPEG。 |
| `factor` | `Literal[4]` | `4` | 只能是 `4` —— API 没有暴露其他倍率。 |

## 返回

`list[ContentBlock]` —— 放大后图像的 base64 `Image` + 保存路径文本。

## 行为

- 放大器是 NovelAI 的一个独立端点 —— 它**不**运行扩散循环，所以比直接以更高
  分辨率重新生成更快。
- Anlas 消耗随源分辨率增长（倍率固定为 4×）。在大批量运行*之前*先用
  [`estimate_anlas_cost`](account.md#estimate_anlas_cost) 估算。
- 输出保留输入的色彩配置与宽高比。放大过程中无法改变宽高比。

## 示例

```python
await ctx.session.call_tool("upscale_image", {
    "image": image_b64,
    "factor": 4,
})
```

### CLI

```bash
uv run python -m novelai_image_mcp upscale ./portrait.png --factor 4
```

## 提示

:::{tip}
**什么时候放大，什么时候重新生成？**

- 当你已经有一张接近完美的图像、只需要更高分辨率时，放大。
- 当你想改变构图、光照或细节时，重新生成。以原始分辨率的 2× 重新生成往往比
  放大得到更干净的结果，但会消耗更多 Anlas。
:::

:::{admonition} 内存占用
:class: warning

把 1024×1024 的图像放大 4× 会得到 4096×4096 的输出（未压缩 PNG 约 64 MB）。
确认你的 `NOVELAI_OUTPUT_DIR` 卷有足够空间。
:::

## 另请参见

- [放大教程](../tutorials/upscale.md)
- [`upscale_image` API 参考](../api/tools.md)
- [账户余额](account.md#get_subscription) —— 批量运行前检查 Anlas
