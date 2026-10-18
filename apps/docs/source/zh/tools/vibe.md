# `encode_vibe`

把参考图编码为一个 **NovelAI vibe token**。Vibe token 是参考图风格 / 身份的紧凑
表示，可以通过 `references` 参数传给 `generate_image`（仅 V4/V4.5 模型 ——
V5 尚不支持 vibe transfer）。

## 参数

| 名称 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `reference` | `str` | *必填* | base64 编码的参考 PNG/JPEG。 |
| `information_extracted` | `float` | `1.0` | 0.01–1.0。vibe 捕捉参考图身份特征的强度。 |
| `model` | `str` | `"nai-diffusion-4-5-full"` | 目标模型 id（必须是 V4/V4.5；V5 会被拒绝）。 |

## 返回

`str` —— base64 vibe token。把它传给 `generate_image` 的 `references` 列表。

## `information_extracted` 的语义

| 取值 | 效果 |
|---|---|
| `0.01`–`0.3` | 只捕捉**风格**。生成的图像继承参考图的绘画质感、光照与配色 —— 而不是它的主体。 |
| `0.4`–`0.7` | 均衡。同时捕捉风格与大致身份（同一类角色原型）。 |
| `0.8`–`1.0` | 捕捉**身份**。生成的图像会相当贴近参考图的主体（例如同一个角色换个姿势）。 |

## 示例

```python
# Encode a reference style
vibe_token = await ctx.session.call_tool("encode_vibe", {
    "reference": ref_b64,
    "information_extracted": 0.3,  # style only
})

# Use it in a generation
await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, watercolor style, peaceful meadow",
    "references": [vibe_token],
})
```

## 多个 vibe

`references` 接受列表 —— 你可以混合多个 vibe：

```python
style_vibe = await ctx.session.call_tool("encode_vibe", {
    "reference": style_ref_b64,
    "information_extracted": 0.2,
})
character_vibe = await ctx.session.call_tool("encode_vibe", {
    "reference": character_ref_b64,
    "information_extracted": 0.9,
})

await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, sitting in a cafe",
    "references": [style_vibe, character_vibe],
})
```

## 缓存

服务器在内存中缓存 vibe 编码，键为
`(reference_hash, information_extracted, model)`。缓存大小由
`NOVELAI_VIBE_CACHE_ENTRIES` 限制（默认 64）。用相同参数对同一张参考图编码
两次会命中缓存，立即返回而不调用 API。

## 提示

:::{warning}
**V5 不支持 vibe。** 用 V5 模型 id 调用 `encode_vibe` 会抛出 `ToolError`。
V3 / Furry 模型同样不在支持范围内 —— `novelai_image_mcp.nai` 的
`supports_vibe()` 对它们返回 `False` —— 但拒绝是由 API 而非本地强制执行的，
所以请在编码前检查这个判定函数，而不要依赖报错。
:::

:::{tip}
**参考图的质量比数量更重要。** 一张高质量、裁剪得当的参考图（特写、中性背景）
比一堆杂乱但相似的图能产出更好的 vibe。
:::

## 另请参见

- [Vibe transfer 教程](../tutorials/vibe-transfer.md) —— 完整的 encode → generate 工作流
- [`encode_vibe` API 参考](../api/tools.md)
- [NovelAI 文档中的 vibe 编码参考](https://docs.novelai.net/image/vibe.html)
