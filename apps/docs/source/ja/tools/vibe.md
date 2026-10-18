# `encode_vibe`

参照画像を **NovelAI の vibe トークン** にエンコードします。vibe トークンは参照画像の
スタイル / アイデンティティをコンパクトに表現したもので、`generate_image` の
`references` パラメーターに渡せます (V4/V4.5 モデルのみ — V5 はまだ vibe 転送に
対応していません)。

## パラメーター

| 名前 | 型 | デフォルト | 備考 |
|---|---|---|---|
| `reference` | `str` | *必須* | base64 でエンコードされた参照 PNG/JPEG。 |
| `information_extracted` | `float` | `1.0` | 0.01–1.0。vibe が参照画像のアイデンティティをどれだけ強く取り込むか。 |
| `model` | `str` | `"nai-diffusion-4-5-full"` | 対象モデル ID (V4/V4.5 である必要があり、V5 は拒否されます)。 |

## 戻り値

`str` — base64 の vibe トークン。`generate_image` の `references` リストに渡します。

## `information_extracted` の意味

| 値 | 効果 |
|---|---|
| `0.01`–`0.3` | **スタイル** のみを取り込みます。生成画像は参照画像の絵画的表現、ライティング、配色を引き継ぎ、被写体は引き継ぎません。 |
| `0.4`–`0.7` | バランス型。スタイル + おおよそのアイデンティティ (同じキャラクターの原型) を取り込みます。 |
| `0.8`–`1.0` | **アイデンティティ** を取り込みます。生成画像は参照画像の被写体を忠実に再現します (例: 同じキャラクターを新しいポーズで)。 |

## 例

```python
# Encode a reference style
vibe_token = await ctx.session.call_tool("encode_vibe", {
    "reference": ref_b64,
    "information_extracted": 0.3,  # style only
})

# Use it in a generation
await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, watercolor style, peaceful meadow",
    "references": [vibe_token],
})
```

## 複数の vibe

`references` はリストを受け付けるため、複数の vibe をブレンドできます:

```python
style_vibe = await ctx.session.call_tool("encode_vibe", {
    "reference": style_ref_b64,
    "information_extracted": 0.2,
})
character_vibe = await ctx.session.call_tool("encode_vibe", {
    "reference": character_ref_b64,
    "information_extracted": 0.9,
})

await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, sitting in a cafe",
    "references": [style_vibe, character_vibe],
})
```

## キャッシュ

サーバーは vibe エンコード結果を `(reference_hash, information_extracted, model)` を
キーとしてメモリ上にキャッシュします。キャッシュサイズは `NOVELAI_VIBE_CACHE_ENTRIES`
(デフォルト 64) で上限が決まります。同じ参照画像を同じパラメーターで 2 回
エンコードするとキャッシュに当たり、API 呼び出しなしで即座に返ります。

## ヒント

:::{warning}
**V5 は vibe に対応していません。** V5 のモデル ID で `encode_vibe` を呼び出すと
`ToolError` が発生します。V3 / Furry モデルも対応範囲外です — `novelai_image_mcp.nai`
の `supports_vibe()` はそれらに対して `False` を返します — ただし拒否はローカルではなく
API によって強制されるため、エラーに頼らずエンコード前に述語で確認してください。
:::

:::{tip}
**参照画像は数より品質が重要です。** 高品質で適切にクロップされた 1 枚の参照画像
(クローズアップ、無地の背景) は、似た画像を大量に並べたノイズの多いセットよりも
良い vibe を生みます。
:::

## 関連項目

- [vibe 転送のチュートリアル](../tutorials/vibe-transfer.md) — encode → generate の一連のワークフロー
- [`encode_vibe` API リファレンス](../api/tools.md)
- [NovelAI ドキュメントの vibe エンコード解説](https://docs.novelai.net/image/vibe.html)
