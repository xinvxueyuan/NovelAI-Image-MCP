# チュートリアル: ControlNet プリプロセッサー

NovelAI の ControlNet プリプロセッサーを使って、参照画像から構造マップ — 深度、
ラインアート、セマンティックセグメンテーション — を抽出します。抽出された
アノテーションは単体の画像として返され、保存したり確認したりできます。
`generate_image` はまだこれを ControlNet の条件として消費できません。

## ワークフローの概要

```{mermaid}
graph LR
    A[Reference image] --> B[annotate_image]
    B --> C[Annotation<br/>depth / line art]
    C --> D[Save or display]
```

## 1. 深度マップを抽出する

```python
import base64
from pathlib import Path

photo_b64 = base64.b64encode(Path("photo.png").read_bytes()).decode("ascii")

depth_result = await ctx.session.call_tool("annotate_image", {
    "image": photo_b64,
    "model": "midas",
})
# depth_result[0] is an Image content block with the depth map;
# depth_result[1] is the saved file path.
```

## 2. 別のプリプロセッサーを試す

| プリプロセッサー | 最適な用途 |
|---|---|
| `midas` (depth) | ポーズ、ボリュームのある構図。 |
| `hed` (soft edges) | アニメ、ペインターリーな線の保持。 |
| `fake_scribble` | ラフスケッチ → 整合の取れた線画。 |
| `mlsd` | 建築、インテリア、直線。 |
| `uniformer` | シーンの構図、配色の転送。 |

```python
for model in ("midas", "hed", "fake_scribble"):
    annotation = await ctx.session.call_tool("annotate_image", {
        "image": photo_b64,
        "model": model,
    })
    # Save each annotation for inspection
```

## 3. CLI での同等の実行

```bash
# Extract a depth map
uv run python -m novelai_image_mcp annotate ./photo.png --model midas
```

## 4. 現時点の制限

:::{warning}
**生成はまだアノテーションを消費しません。** `generate_image` はテキスト
プロンプト、キャラクタープロンプト、vibe 参照を受け付けますが、ControlNet の条件は
受け付けません。`generate_image` にはまだ `controlnet_condition` / `controlnet_model`
パラメーターがないため、抽出したアノテーションで生成を駆動することはできません。
:::

:::{tip}
**回避策:** 現時点では `annotate_image` と `director_tool` を組み合わせて写真から
様式化されたラインアート出力を作り、必要に応じて `image_to_image` で仕上げます。
[Director ツール](../tools/director.md) を参照してください。
:::

## 次のステップ

- [`annotate_image` リファレンス](../tools/annotate.md)
- [`director_tool` リファレンス](../tools/director.md)
- [vibe 転送](vibe-transfer.md) — 別のスタイル転送ワークフロー
