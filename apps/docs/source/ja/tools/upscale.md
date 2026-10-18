# `upscale_image`

NovelAI のスタンドアロンアップスケーラーで画像を 4 倍にアップスケールします。
アップスケーラーは入力画像を生成したモデルに関係なく、`NOVELAI_UPSCALE_MODEL` で
設定された V5 モデルで動作します。

## パラメーター

| 名前 | 型 | デフォルト | 備考 |
|---|---|---|---|
| `image` | `str` | *必須* | アップスケールする base64 エンコードの PNG/JPEG。 |
| `factor` | `Literal[4]` | `4` | `4` のみ — API は他の倍率を公開していません。 |

## 戻り値

`list[ContentBlock]` — アップスケール後の画像の base64 `Image` と、保存先パスのテキスト。

## 動作

- アップスケーラーは別個の NovelAI エンドポイントです — 拡散ループを実行 **しない** ため、
  より高解像度で再生成するよりも高速です。
- Anlas コストは元の解像度に比例します (倍率は 4 倍で固定)。大きなバッチの *前に*
  [`estimate_anlas_cost`](account.md#estimate_anlas_cost) を使ってください。
- 出力は入力のカラープロファイルとアスペクト比を保ちます。アップスケール中に
  アスペクト比を変更することはできません。

## 例

```python
await ctx.session.call_tool("upscale_image", {
    "image": image_b64,
    "factor": 4,
})
```

### CLI

```bash
uv run python -m novelai_image_mcp upscale ./portrait.png --factor 4
```

## ヒント

:::{tip}
**アップスケールと再生成のどちらを選ぶか?**

- ほぼ完璧な画像がすでにあり、より高い解像度だけが必要な場合はアップスケールします。
- 構図、ライティング、細部を変えたい場合は再生成します。元の 2 倍の解像度で
  再生成すると、アップスケールよりきれいな結果が得られることが多いですが、
  Anlas の消費は増えます。
:::

:::{admonition} メモリ使用量
:class: warning

1024×1024 の画像を 4 倍にアップスケールすると 4096×4096 の出力
(非圧縮 PNG で約 64 MB) になります。`NOVELAI_OUTPUT_DIR` のボリュームに
空きがあることを確認してください。
:::

## 関連項目

- [アップスケールのチュートリアル](../tutorials/upscale.md)
- [`upscale_image` API リファレンス](../api/tools.md)
- [アカウント残高](account.md#get_subscription) — バッチの前に Anlas を確認する
