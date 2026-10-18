# `annotate_image`

**ControlNet プリプロセッサー** で画像をアノテーションします。出力はアノテーション
そのもの — 派生画像 (例: ラインアートマップや深度マップ) で、ControlNet の条件として
生成にフィードバックできます。

## パラメーター

| 名前 | 型 | デフォルト | 備考 |
|---|---|---|---|
| `image` | `str` | *必須* | base64 でエンコードされた PNG/JPEG。 |
| `model` | `str` | *必須* | ControlNet プリプロセッサー ID (下記参照)。 |

## 戻り値

`list[ContentBlock]` — アノテーションの base64 `Image` と、保存先パスのテキスト。

## ControlNet モデル

| `model` の値 | NovelAI 名 | 出力 | 用途 |
|---|---|---|---|
| `hed` | Palette Swap | ソフトエッジマップ | アニメ / ペインターリーな線の保持 |
| `midas` | Form Lock / Depth | 深度マップ | ポーズ、奥行き、ボリュームの一貫性 |
| `fake_scribble` | Scribbler | 疑似スクリブル線画 | ラフスケッチ → 整合の取れた線画 |
| `mlsd` | Building Control | 直線検出 | 建築、インテリア |
| `uniformer` | Landscaper | セマンティックセグメンテーション | シーンの構図、配色 |

`ControlNetModel` enum をイントロスペクトして実行時に一覧表示できます:

```python
from novelai_image_mcp.nai import ControlNetModel
print([m.value for m in ControlNetModel])
```

## 例

### 深度マップの抽出

```python
depth = await ctx.session.call_tool("annotate_image", {
    "image": photo_b64,
    "model": "midas",
})
```

### アニメワークフロー向けの HED (ソフトエッジ)

```python
hed = await ctx.session.call_tool("annotate_image", {
    "image": illustration_b64,
    "model": "hed",
})
```

### CLI

```bash
uv run python -m novelai_image_mcp annotate ./photo.png --model midas
```

## ヒント

:::{tip}
**ワークフロー**: `midas` で写真から深度マップを抽出し、それを次の `generate_image`
呼び出しで ControlNet の条件として使うと、ポーズと構図を保ったまま別のスタイルで
シーンを再描画できます。
:::

:::{admonition} アノテーション ≠ Director
:class: note

`director_tool` は画像を *視覚的に* 変換します (ラインアート、カラー化など)。
`annotate_image` は *構造マップ* (深度、エッジ、セグメンテーション) を抽出するもので、
直接閲覧するためではなく下流の生成を駆動するためのものです。
:::

## 関連項目

- [ControlNet チュートリアル](../tutorials/controlnet.md) — annotate → generate の一連のワークフロー
- [`annotate_image` API リファレンス](../api/tools.md)
- [`ControlNetModel` enum](../api/client.md) — `nai.constants` サブモジュールに記載
