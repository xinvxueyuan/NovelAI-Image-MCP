# 教程：文生图

用 `generate_image` 工具从一段文本提示词生成图像。这是最简单的工作流 ——
没有输入图像、没有蒙版、没有 vibe。

## 1. 生成你的第一张图像

```python
result = await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, fox ears, autumn leaves, masterpiece, best quality",
    "negative_prompt": "lowres, bad anatomy, watermark, signature",
    "width": 832,
    "height": 1216,
    "steps": 28,
    "scale": 5.0,
    "sampler": "k_euler_ancestral",
    "seed": 42,
})
```

结果是一个列表，其中包含一个 `Image` 块（智能体可以 "看到" 图像）和一个带有
保存路径的文本块：

```python
[
    Image(data=b"...png bytes...", format="png"),
    "Saved 1 image(s): ['outputs/generate-20260725-133702-001.png']"
]
```

## 2. 生成多个变体

传入 `n_samples` 可以在一次 API 调用中产出多张图像（比分开调用更便宜）：

```python
result = await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, fox ears, autumn leaves",
    "n_samples": 4,
    "seed": 42,
})
# 4 images saved; the first is returned inline.
```

## 3. 换一个模型

```python
# V3 model
await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, fox ears",
    "model": "nai-diffusion-3",
})

# V4.5 full (current default)
await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, fox ears",
    "model": "nai-diffusion-4-5-full",
})

# NovelAI Diffusion V5 — natural-language prompts, EN/JP, true alpha
await ctx.session.call_tool("generate_image", {
    "prompt": "a fox girl sitting in autumn leaves, soft watercolor",
    "model": "nai-diffusion-5-full",
    "straight_alpha": True,  # pair with "transparent background" in the prompt
})
```

## 4. 复现一次生成

要复现同一张图像，设置相同的 `seed` 与相同的参数：

```python
await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, fox ears, autumn leaves",
    "seed": 42,
    "width": 832, "height": 1216, "steps": 28,
    "scale": 5.0, "sampler": "k_euler_ancestral",
})
```

输出逐位相同（前提是 NovelAI 的模型权重没有变化）。

## 5. 等价的 CLI 命令

```bash
uv run python -m novelai_image_mcp generate \
  --prompt "1girl, fox ears, autumn leaves, masterpiece, best quality" \
  --negative "lowres, bad anatomy, watermark" \
  --width 832 --height 1216 --steps 28 --scale 5.0 \
  --seed 42
```

## 下一步

- [图生图](img2img.md) —— 变换一张已有图像
- [多角色构图](../tools/generate.md#多角色构图v4) —— V4+ 特性
- [Vibe transfer](vibe-transfer.md) —— 编码一种参考风格
- [工具参考](../tools/index.md) —— 完整参数列表
