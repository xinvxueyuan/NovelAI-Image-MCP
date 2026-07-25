# Tools reference

The server registers **11 MCP tools** against the [`MCPServer`](../api/server.md)
instance. Every tool is `async` and reads its dependencies (the
`NovelAIClient` and `NovelAISettings`) from the MCP request context's
lifespan state.

## Tool index

| Tool | Group | Description |
|---|---|---|
| [`generate_image`](generate.md#generate_image) | generation | Text-to-image (V3 / V4 / V4.5, character prompts, vibes) |
| [`image_to_image`](generate.md#image_to_image) | generation | Image-to-image with strength / noise |
| [`inpaint`](generate.md#inpaint) | generation | Local redraw (requires inpaint model + mask) |
| [`upscale_image`](enhance.md#upscale_image) | enhance | 2× / 4× upscaling |
| [`director_tool`](director.md#director_tool) | enhance | line art / sketch / bg-removal / declutter / colorize / emotion |
| [`annotate_image`](annotate.md#annotate_image) | enhance | ControlNet preprocessing (hed, midas, scribble, mlsd, uniformer) |
| [`suggest_tags`](tags.md#suggest_tags) | tags | Prompt tag suggestions |
| [`encode_vibe`](vibe.md#encode_vibe) | tags | Encode a reference image into a vibe token |
| [`get_subscription`](account.md#get_subscription) | account | Account subscription + Anlas balance |
| [`get_user_data`](account.md#get_user_data) | account | Account user data |
| [`estimate_anlas_cost`](account.md#estimate_anlas_cost) | account | Estimate Anlas cost without an API call |

## Common patterns

### Return shape

Every image-producing tool returns a list of MCP content blocks:

```python
[
    Image(data=b"...png bytes...", format="png"),  # agent sees the image
    f"Saved 1 image(s): ['outputs/generate-...png']"  # text path for follow-up
]
```

The agent can either inspect the image inline (base64 `Image` block) or read
the path from the text block to pass to a subsequent tool.

### Image parameters

Image parameters that take a `str` (`image`, `mask`, `reference`,
`references`) expect **base64-encoded PNG or JPEG** strings, not file paths.
To convert a local file:

```python
import base64
from pathlib import Path

image_b64 = base64.b64encode(Path("input.png").read_bytes()).decode("ascii")
```

The CLI handles this automatically — it accepts file paths via `--image ./input.png`.

### Validation

Tools validate inputs eagerly and raise `ValueError` with a list of valid
options when an enum-style parameter (`model`, `tool`, `emotion`,
`controlnet model`, `action`) doesn't match. The MCP runtime surfaces these
as tool-call errors that the agent can read and self-correct from.

## Per-tool pages

```{toctree}
:maxdepth: 1
:hidden:

generate
enhance
director
annotate
tags
vibe
account
```

## See also

- [Tutorials](../tutorials/index.md) — end-to-end workflows combining tools
- [API reference](../api/index.md) — autodoc for the underlying `NovelAIClient`
- [Configuration](../configuration.md) — defaults applied when a parameter is omitted
