# 教程

把一两个工具组合起来完成常见任务的端到端工作流。每篇教程都可以直接运行 ——
复制代码片段、设置好 `NOVELAI_TOKEN`，然后跟着做即可。

## 教程

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

| 教程 | 用到的工具 | 耗时 | Anlas |
|---|---|---|---|
| [文生图](txt2img.md) | `generate_image` | 2 分钟 | ~5 |
| [图生图](img2img.md) | `image_to_image` | 2 分钟 | ~3 |
| [局部重绘](inpaint.md) | `inpaint` | 5 分钟 | ~5 |
| [放大](upscale.md) | `upscale_image` | 1 分钟 | 视情况而定 |
| [ControlNet 工作流](controlnet.md) | `annotate_image` + `generate_image` | 5 分钟 | ~10 |
| [Vibe transfer](vibe-transfer.md) | `encode_vibe` + `generate_image` | 4 分钟 | ~8 |

:::{tip}
**`novelai-workflows`** agent 技能把这些多工具流水线打包成 AI 智能体在运行时
可以读取的可移植格式。用 `npx skills add xinvxueyuan/NovelAI-Image-MCP`
安装 —— 详见 [Agent 技能](../skills.md)。
:::

## 前置条件

- 一个配置好的 NovelAI 账户（见 [安装](../installation.md)）
- 在仓库根目录成功执行过 `uv sync`
- 整套教程约需 50 Anlas（Opus 档位的一次免费样本批量可能就够）

## 约定

教程使用 MCP 的 `Context.session.call_tool(...)` 模式 —— 与智能体使用的是同一种
形式。如果想改用 CLI 运行某篇教程，请参考各工具的
[CLI 示例](../tools/index.md)，把参数改写成 `--flag` 形式。
