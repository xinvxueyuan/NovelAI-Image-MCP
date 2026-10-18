# `suggest_tags`

推荐能够补全或细化一段不完整提示词的 NovelAI 提示词标签。推荐结果由
NovelAI 训练集标注器排序，并附带该标签在训练集中的出现次数。

## 参数

| 名称 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `prompt` | `str` | *必填* | 待补全的不完整提示词文本。 |
| `model` | `str` | `"nai-diffusion-4-5-full"` | 标注器词表（对应一个 `Model` 枚举值）。 |
| `language` | `str` | `"en"` | ISO 639-1 响应语言（例如 `en`、`ja`、`zh`）。 |

## 返回

`list[TagSuggestion]` —— 每条推荐都带有 NovelAI 返回的字段：

| 键 | 类型 | 说明 |
|---|---|---|
| `tag` | `str` | 标签字符串本身（把它用在你的提示词里）。 |
| `count` | `int` | 训练集出现次数（越大越常见）。 |
| `confidence` | `float` | 标注器对这次补全的置信度（0–1）。 |

线上结构已实测验证（见
[API 接口对齐](../development/api-alignment.md)）：

## 示例

```python
result = await ctx.session.call_tool("suggest_tags", {
    "prompt": "1girl, fox ears,",
    "model": "nai-diffusion-4-5-full",
    "language": "en",
})
# result: [
#   {"tag": "fox girl", "count": 10000, "confidence": 0.745},
#   {"tag": "fox tail", "count": 4321, "confidence": 0.612},
#   ...
# ]
```

## 提示

:::{tip}
**迭代式构建提示词**：让智能体在每次修改提示词后调用 `suggest_tags`，然后采纳
最贴合场景的那条推荐。这是发现你原本想不到的标签的快捷方式。
:::

:::{admonition} 标签计数与质量
:class: note

`count` 衡量的是该标签在 NovelAI 训练数据中出现的频率 —— 不是它对*你的*提示词
有多*有用*。一个冷门标签（`count` 低）同样可能正是你场景的完美描述词。
:::

## 另请参见

- [`suggest_tags` API 参考](../api/tools.md)
- [NovelAI 标签文档](https://docs.novelai.net/image/promptstags.html)
