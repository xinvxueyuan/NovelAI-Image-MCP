# `suggest_tags`

Suggest NovelAI prompt tags that complete or refine a partial prompt. The
suggestions are ranked by NovelAI's training-set tagger and returned with
their training occurrence count.

## Parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `prompt` | `str` | *required* | Partial prompt text to complete. |
| `model` | `str` | `"nai-diffusion-4-5-full"` | Tagger vocabulary (matches a `Model` enum value). |
| `language` | `str` | `"en"` | ISO 639-1 response language (e.g. `en`, `ja`, `zh`). |

## Returns

`list[dict]` — list of tag descriptors, each with:

| Key | Type | Notes |
|---|---|---|
| `description` | `str` | Human-readable description (localized to `language`). |
| `text` | `str` | The tag string itself (use this in your prompt). |
| `count` | `int` | Training-set occurrence count (higher = more reliable). |

## Example

```python
result = await ctx.session.call_tool("suggest_tags", {
    "prompt": "1girl, fox ears,",
    "model": "nai-diffusion-4-5-full",
    "language": "en",
})
# result: [
#   {"description": "fox tail", "text": "fox tail", "count": 12450},
#   {"description": "autumn leaves", "text": "autumn leaves", "count": 8230},
#   ...
# ]
```

## Tips

:::{tip}
**Iterative prompt building**: ask an agent to call `suggest_tags` after
each prompt edit, then accept the top suggestion that fits the scene. This
is a fast way to discover tags you wouldn't have thought of.
:::

:::{admonition} Tag count vs quality
:class: note

`count` measures how often the tag appears in NovelAI's training data — not
how often it's *useful* for your prompt. A rare tag (low `count`) can still
be the perfect descriptor for your scene.
:::

## See also

- [`suggest_tags` API reference](../api/tools.md)
- [NovelAI tag documentation](https://docs.novelai.net/image/promptstags.html)
