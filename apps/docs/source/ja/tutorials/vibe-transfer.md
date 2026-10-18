# チュートリアル: vibe 転送

参照画像のスタイルやアイデンティティを vibe トークンにエンコードし、それを生成に
渡します。vibe 転送 (V4 以降のみ) は、複数の生成にわたってスタイルやキャラクターを
再現する最もクリーンな方法です。

## vibe 転送を使う場面

| 目的 | ツール |
|---|---|
| 多くの生成で **スタイル** を再利用する | `encode_vibe` (`information_extracted` を低く) |
| 新しいシーンで **キャラクターのアイデンティティ** を再現する | `encode_vibe` (`information_extracted` を高く) |
| **構図** を合わせる | ControlNet ([チュートリアル](controlnet.md)) |
| 既存の画像を塗り直す | `image_to_image` ([チュートリアル](img2img.md)) |

## 1. 参照画像をエンコードする

```python
import base64
from pathlib import Path

ref_b64 = base64.b64encode(Path("reference.png").read_bytes()).decode("ascii")

# Style-focused vibe: low information_extracted
style_vibe = await ctx.session.call_tool("encode_vibe", {
    "reference": ref_b64,
    "information_extracted": 0.3,
})
# Returns a base64 vibe token (string)
```

## 2. 生成で vibe を使う

```python
result = await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, sitting in a cafe, masterpiece",
    "references": [style_vibe],
})
```

生成された画像は参照画像の絵画的スタイル、ライティング、配色を引き継ぎます — ただし
被写体と構図はまったく別のものになります。

## 3. 複数の vibe をブレンドする

`references` はリストを受け付けます。スタイルの vibe とキャラクターの vibe を
ブレンドします:

```python
# Style vibe — captures the painterly look
style_vibe = await ctx.session.call_tool("encode_vibe", {
    "reference": style_ref_b64,
    "information_extracted": 0.2,
})

# Character vibe — captures identity
character_vibe = await ctx.session.call_tool("encode_vibe", {
    "reference": character_ref_b64,
    "information_extracted": 0.9,
})

result = await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, sitting in a cafe",
    "references": [style_vibe, character_vibe],
})
```

結果は、スタイルの絵画的な見た目の中にキャラクターの顔 / アイデンティティを持ちます。

## 4. `information_extracted` を調整する

| 値 | 効果 |
|---|---|
| `0.01`–`0.3` | スタイル転送 — ライティング、配色、筆致。アイデンティティは保たれません。 |
| `0.4`–`0.7` | バランス型 — スタイル + おおよそのキャラクターの原型。 |
| `0.8`–`1.0` | アイデンティティ転送 — 同じキャラクターを新しいポーズ / シーンで。 |

:::{tip}
スタイル転送なら `0.3`、アイデンティティ転送なら `0.9` から始めます。0.1 刻みで
反復してください。
:::

## 5. キャッシュ

サーバーは vibe エンコード結果をメモリ上にキャッシュします (サイズ:
`NOVELAI_VIBE_CACHE_ENTRIES`、デフォルト 64)。同じ参照画像を同じパラメーターで
2 回エンコードするとキャッシュに当たり、API 呼び出しなしで即座に返ります。

```python
# First call: hits the API (~2 seconds)
vibe1 = await ctx.session.call_tool("encode_vibe", {
    "reference": ref_b64,
    "information_extracted": 0.3,
})

# Second call with the same args: cache hit, returns instantly
vibe2 = await ctx.session.call_tool("encode_vibe", {
    "reference": ref_b64,
    "information_extracted": 0.3,
})
# vibe1 == vibe2
```

## 6. vibe 転送のみ

`generate_image` は vibe 参照を受け付けますが、ControlNet の条件は受け付けません。
構造マップとスタイルを組み合わせるには、現時点では `annotate_image` でアノテーションを
抽出し、`director_tool` で適用してください。`generate_image` の ControlNet 条件付けは
まだ実装されていません。

```python
# Step 1: extract depth from a pose reference (saved to disk)
depth = await ctx.session.call_tool("annotate_image", {
    "image": pose_photo_b64,
    "model": "midas",
})

# Step 2: encode a style vibe from a painting reference
style_vibe = await ctx.session.call_tool("encode_vibe", {
    "reference": painting_ref_b64,
    "information_extracted": 0.2,
})

# Step 3: generate with the vibe (references are supported, controlnet is not)
result = await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, standing in a meadow",
    "references": [style_vibe],
})
```

結果は絵画のスタイルを帯びます。`generate_image` の構造的な条件付けはまだ
実装されていません。

## 7. 落とし穴

:::{warning}
**V5 モデルは vibe に対応していません。** V5 のモデル ID で `encode_vibe` を呼び出すと
`ToolError` が発生します。V3 / Furry モデルも対応範囲外ですが、拒否はローカルではなく
API によって強制されます — エラーに頼らず `supports_vibe()` (`Model` enum を受け取る)
で確認してください:

```python
from novelai_image_mcp.nai import supports_vibe, Model
supports_vibe(Model.V4_5)  # True
supports_vibe(Model.V3)    # False
supports_vibe(Model.V5)    # False
```
:::

:::{tip}
**参照画像の品質が重要です。** 高品質で適切にクロップされた 1 枚の参照画像
(クローズアップ、無地の背景) は、似た画像を大量に並べたノイズの多いセットよりも
良い vibe を生みます。
:::

## 次のステップ

- [`encode_vibe` リファレンス](../tools/vibe.md)
- [`generate_image` リファレンス](../tools/generate.md#generate_image)
- [ControlNet チュートリアル](controlnet.md) — vibe と構造的な条件付けを組み合わせる
