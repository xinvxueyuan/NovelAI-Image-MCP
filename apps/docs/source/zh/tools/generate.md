# 生成工具

三个从文本提示词产出图像的工具 —— 纯文生图、图像条件（img2img）与蒙版条件
（inpaint）。三者都返回一个 base64 `Image` 块加上保存后的文件路径。

---

## `generate_image`

文生图。最常用的工具 —— 从一段提示词产出单张或多张图像。支持 NovelAI
V3 / V4 / V4.5 / V5 模型、多角色构图与 vibe transfer（V5 拒绝 vibe transfer
—— 上游尚未发布）。V5 还额外接受英文 / 日文自然语言提示词。

### 参数

| 名称 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `prompt` | `str` | *必填* | 正向提示词。标签之间用逗号分隔。 |
| `negative_prompt` | `str` | `""` | 负向提示词（UC）。 |
| `model` | `str \| None` | `NOVELAI_DEFAULT_MODEL` | 覆盖模型 id。见 `Model` 枚举。 |
| `width` | `int \| None` | `NOVELAI_DEFAULT_WIDTH` | 图像宽度（像素）。64 的倍数。 |
| `height` | `int \| None` | `NOVELAI_DEFAULT_HEIGHT` | 图像高度（像素）。64 的倍数。 |
| `steps` | `int \| None` | `NOVELAI_DEFAULT_STEPS` | 采样器步数（1–50）。 |
| `scale` | `float \| None` | `NOVELAI_DEFAULT_SCALE` | CFG 比例（0–20）。 |
| `sampler` | `str \| None` | `NOVELAI_DEFAULT_SAMPLER` | 采样器 id（见 `Sampler` 枚举）。 |
| `seed` | `int` | `0` | 随机数种子。`0` = 随机。 |
| `n_samples` | `int` | `1` | 图像数量（1–8）。 |
| `quality` | `bool` | `True` | 使用质量标签预设（V4+）。 |
| `uc_preset` | `int` | `0` | 负向提示词预设（0=heavy，1=light，2=human focus）。 |
| `cfg_rescale` | `float` | `0.0` | CFG rescale（0–1，V4+）。 |
| `smea` | `bool \| None` | 依模型而定 | 启用 SMEA。`None` = 自动。 |
| `smea_dynamic` | `bool \| None` | 依模型而定 | 启用动态 SMEA。 |
| `auto_smea` | `bool` | `False` | 按分辨率自动选择 SMEA。 |
| `straight_alpha` | `bool` | `False` | 真实 alpha 通道（仅 V5；配合 `transparent background` / `has alpha` 使用）。 |
| `prefer_brownian` | `bool` | `True` | 优先使用布朗噪声调度（V4+）。 |
| `noise_schedule` | `str` | `"karras"` | 噪声调度（`native`、`karras`、`exponential`、`polyexponential`）。 |
| `character_prompts` | `list[dict] \| None` | `None` | V4+ / V5 多角色构图。 |
| `references` | `list[str] \| None` | `None` | V4/V4.5 vibe token（`encode_vibe` 产出的 base64 vibe 字符串）；V5 上会被拒绝。 |

### 返回

`list[ContentBlock]` —— base64 `Image` + 保存路径文本。

### 示例

```python
# Simple text-to-image
await ctx.session.call_tool("generate_image", {
    "prompt": "a fox in a snowy forest, masterpiece, best quality",
    "negative_prompt": "lowres, bad anatomy, watermark",
    "width": 832,
    "height": 1216,
    "steps": 28,
    "scale": 5.0,
    "seed": 42,
})
```

### 多角色构图（V4+）

V5 支持同一套多角色机制（上游实测最多 22 个角色），所以下面的行为适用于
V4 / V4.5 / V5。

```python
await ctx.session.call_tool("generate_image", {
    "prompt": "two characters talking in a cafe",
    "character_prompts": [
        {"prompt": "1girl, red hair, blue eyes", "x": 0.3, "y": 0.5, "negative_prompt": ""},
        {"prompt": "1boy, black hair, green eyes", "x": 0.7, "y": 0.5, "negative_prompt": ""},
    ],
})
```

`x` 与 `y` 是归一化后的中心坐标，取值范围 `0.1`–`0.9`。第一个角色始终是
画面焦点。

### Vibe transfer（V4 / V4.5）

```python
# 1. Encode a reference image
vibe = await ctx.session.call_tool("encode_vibe", {"reference": ref_b64})

# 2. Use the vibe as a reference
await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, watercolor style",
    "references": [vibe],
})
```

完整工作流见 [vibe transfer 教程](../tutorials/vibe-transfer.md)。

---

## `image_to_image`

图生图。以一张输入图像为条件产出新图像。

### 参数

| 名称 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `prompt` | `str` | *必填* | 正向提示词。 |
| `image` | `str` | *必填* | base64 编码的输入 PNG/JPEG。 |
| `negative_prompt` | `str` | `""` | 负向提示词。 |
| `model` | `str \| None` | 默认值 | 模型 id。必须与输入图像的领域匹配。 |
| `strength` | `float` | `0.3` | 0.01–0.99。偏离输入图像的程度。 |
| `noise` | `float` | `0.0` | 0–0.99。额外的变化量。 |
| `width` / `height` / `steps` / `scale` / `sampler` / `seed` / `n_samples` / `quality` / `uc_preset` / `noise_schedule` / `cfg_rescale` | （见 `generate_image`） | （相同默认值） | |
| `extra_noise_seed` | `int \| None` | `None` | 噪声的独立种子（默认为 `seed`）。 |

### 示例

```python
await ctx.session.call_tool("image_to_image", {
    "prompt": "1girl, masterpiece, smile",
    "image": image_b64,
    "strength": 0.4,
    "noise": 0.05,
})
```

:::{tip}
`strength=0.5` 是不错的起点。低于 0.3 时结果看起来像对输入图像重新去噪；
高于 0.7 时它会向全新的文生图漂移。
:::

---

## `inpaint`

对图像的某个区域做局部重绘。区域由蒙版定义 —— 非透明像素会被重新生成。

### 参数

| 名称 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `prompt` | `str` | *必填* | 针对被重绘区域的提示词。 |
| `image` | `str` | *必填* | base64 编码的输入 PNG/JPEG。 |
| `mask` | `str` | *必填* | base64 编码的蒙版。非透明 = 重绘。 |
| `negative_prompt` | `str` | `""` | 针对该区域的负向提示词。 |
| `model` | `str \| None` | 默认值 | **必须**是 inpaint 模型（例如 `nai-diffusion-4-5-full-inpainting` 或 `nai-diffusion-5-full-inpainting`）。 |
| `strength` / `noise` / `width` / `height` / `steps` / `scale` / `sampler` / `seed` / `n_samples` / `quality` / `uc_preset` / `noise_schedule` / `cfg_rescale` / `extra_noise_seed` | （见 `image_to_image`） | （相同默认值） | |

### 示例

```python
await ctx.session.call_tool("inpaint", {
    "prompt": "1girl, masterpiece, smiling",
    "image": image_b64,
    "mask": mask_b64,
    "model": "nai-diffusion-4-5-full-inpainting",
    "strength": 0.5,
})
```

:::{warning}
局部重绘需要专用的 inpaint 模型。用非 inpaint 模型调用 `inpaint` 会返回
`NovelAIValidationError`。调用前可以用
[`is_inpaint_model`](../api/client.md)（位于 `nai.constants` 子模块）检查。
:::

蒙版制作的分步说明见 [inpaint 教程](../tutorials/inpaint.md)。

---

## 另请参见

- [文生图教程](../tutorials/txt2img.md)
- [img2img 教程](../tutorials/img2img.md)
- [inpaint 教程](../tutorials/inpaint.md)
- [`novelai_image_mcp.tools.generate` API 参考](../api/tools.md)
- [配置](../configuration.md) —— 省略参数时套用的默认值
