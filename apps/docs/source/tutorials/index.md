# Tutorials

End-to-end workflows that combine one or more tools to accomplish a common
task. Each tutorial is runnable as-is — copy the snippet, set
`NOVELAI_TOKEN`, and follow along.

## Tutorials

```{toctree}
:maxdepth: 1
:hidden:

txt2img
img2img
inpaint
upscale
controlnet
vibe-transfer
```

| Tutorial | Tools used | Time | Anlas |
|---|---|---|---|
| [Text-to-image](txt2img.md) | `generate_image` | 2 min | ~5 |
| [Image-to-image](img2img.md) | `image_to_image` | 2 min | ~3 |
| [Inpainting](inpaint.md) | `inpaint` | 5 min | ~5 |
| [Upscaling](upscale.md) | `upscale_image` | 1 min | varies |
| [ControlNet workflow](controlnet.md) | `annotate_image` + `generate_image` | 5 min | ~10 |
| [Vibe transfer](vibe-transfer.md) | `encode_vibe` + `generate_image` | 4 min | ~8 |

## Prerequisites

- A configured NovelAI account (see [Installation](../installation.md))
- A working `uv sync` from the repo root
- ~50 Anlas for the full set (a single Opus-tier free-sample batch may cover it)

## Conventions

Tutorials use the MCP `Context.session.call_tool(...)` pattern — the same
shape an agent uses. To run a tutorial from the CLI instead, see the per-tool
[CLI examples](../tools/index.md) and adapt the parameters to `--flag` form.
