# チュートリアル: アップスケール

NovelAI のスタンドアロンアップスケーラーを使って画像の解像度を 4 倍にします。
アップスケーラーは、より高い解像度で再生成するよりも高速で、きれいな結果を
生み出します。

## 1. 画像をアップスケールする

```python
import base64
from pathlib import Path

image_b64 = base64.b64encode(Path("portrait.png").read_bytes()).decode("ascii")

result = await ctx.session.call_tool("upscale_image", {
    "image": image_b64,
    "factor": 4,
})
```

出力 PNG は元の解像度の 4 倍になります。832×1216 の入力は 3328×4864 になります。

## 2. `factor` は 4 で固定

NovelAI のスタンドアロンアップスケーラーは 4 倍の 1 段階のみを公開しているため、
`factor` は `4` だけを受け付けます — 2 倍モードはありません。より小さい倍率を
探すのではなく、低い解像度で生成して 1 回アップスケールしてください。

Anlas コストは元の解像度に比例します。バッチでアップスケールする場合は、先に
[`estimate_anlas_cost`](../tools/account.md#estimate_anlas_cost) を使ってください。

## 3. CLI での同等の実行

```bash
uv run python -m novelai_image_mcp upscale ./portrait.png --factor 4
```

## 4. ワークフロー: 生成 → アップスケール

よくあるパターンは、高速な反復のために低い解像度で生成し、採用する 1 枚を
アップスケールするというものです:

```python
# Step 1: iterate at 832×1216 (cheap, ~5 Anlas each)
result = await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, masterpiece",
    "width": 832, "height": 1216,
    "n_samples": 4,
})
# (you pick the best of the 4 — say, outputs/generate-...003.png)

# Step 2: upscale the keeper to 3328×4864
import base64
from pathlib import Path
keeper_b64 = base64.b64encode(
    Path("outputs/generate-...003.png").read_bytes()
).decode("ascii")

result = await ctx.session.call_tool("upscale_image", {
    "image": keeper_b64,
    "factor": 4,
})
```

これにかかるコストはバッチで約 5 Anlas + アップスケールで約 10 Anlas = 合計約 15 Anlas
です — 4 倍の画像を 4 枚直接生成する (約 80 Anlas) よりもはるかに安価です。

## 5. 落とし穴

:::{warning}
**メモリ使用量。** 1024×1024 の画像を 4 倍にアップスケールすると 4096×4096 の
PNG (非圧縮で約 64 MB) になります。ディスク容量をそれに合わせて計画してください。
:::

:::{tip}
**Inpaint の前にアップスケール。** 細部を修正する必要がある場合、先にアップスケール
すると inpaint モデルが扱えるピクセルが増え、より細かいマスクと良好なディテールが
得られます。
:::

## 次のステップ

- [`upscale_image` リファレンス](../tools/upscale.md)
- [アカウント残高](../tools/account.md#get_subscription) — 先に Anlas を確認する
- [コスト見積もり](../tools/account.md#estimate_anlas_cost) — 請求額を事前に確認する
