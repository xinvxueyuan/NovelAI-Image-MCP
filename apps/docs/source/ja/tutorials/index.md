# チュートリアル

よくあるタスクを達成するために 1 つ以上のツールを組み合わせたエンドツーエンドの
ワークフローです。各チュートリアルはそのまま実行できます — スニペットをコピーし、
`NOVELAI_TOKEN` を設定して、順に進めてください。

## チュートリアル

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

| チュートリアル | 使用するツール | 所要時間 | Anlas |
|---|---|---|---|
| [テキストから画像](txt2img.md) | `generate_image` | 2 分 | ~5 |
| [画像から画像](img2img.md) | `image_to_image` | 2 分 | ~3 |
| [Inpainting](inpaint.md) | `inpaint` | 5 分 | ~5 |
| [アップスケール](upscale.md) | `upscale_image` | 1 分 | 変動 |
| [ControlNet ワークフロー](controlnet.md) | `annotate_image` + `generate_image` | 5 分 | ~10 |
| [vibe 転送](vibe-transfer.md) | `encode_vibe` + `generate_image` | 4 分 | ~8 |

:::{tip}
**`novelai-workflows`** エージェントスキルは、これらの複数ツールのパイプラインを、
AI エージェントが実行時に読める可搬な形式にまとめたものです。
`npx skills add xinvxueyuan/NovelAI-Image-MCP` でインストールできます — 詳細は
[エージェントスキル](../skills.md) を参照してください。
:::

## 前提条件

- 設定済みの NovelAI アカウント ([インストール](../installation.md) を参照)
- リポジトリルートで `uv sync` が成功していること
- 一連のチュートリアル全体で約 50 Anlas (Opus ティアの無料サンプル 1 バッチで
  まかなえる場合もあります)

## 規約

チュートリアルは MCP の `Context.session.call_tool(...)` パターンを使います —
エージェントが使うのと同じ形です。代わりに CLI から実行する場合は、ツールごとの
[CLI の例](../tools/index.md) を参照し、パラメーターを `--flag` 形式に読み替えてください。
