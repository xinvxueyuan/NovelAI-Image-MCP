# チュートリアル: テキストから画像

`generate_image` ツールを使ってテキストプロンプトから画像を生成します。最も単純な
ワークフローです — 入力画像もマスクも vibe も不要です。

## 1. 最初の画像を生成する

```python
result = await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, fox ears, autumn leaves, masterpiece, best quality",
    "negative_prompt": "lowres, bad anatomy, watermark, signature",
    "width": 832,
    "height": 1216,
    "steps": 28,
    "scale": 5.0,
    "sampler": "k_euler_ancestral",
    "seed": 42,
})
```

結果は `Image` ブロック (エージェントが画像を「見る」ことができる) と、保存された
ファイルパスを含むテキストブロックからなるリストです:

```python
[
    Image(data=b"...png bytes...", format="png"),
    "Saved 1 image(s): ['outputs/generate-20260725-133702-001.png']"
]
```

## 2. 複数のバリエーションを生成する

`n_samples` を渡すと、1 回の API 呼び出しで複数の画像を生成できます (個別に呼ぶより
安価です):

```python
result = await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, fox ears, autumn leaves",
    "n_samples": 4,
    "seed": 42,
})
# 4 images saved; the first is returned inline.
```

## 3. 別のモデルを使う

```python
# V3 model
await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, fox ears",
    "model": "nai-diffusion-3",
})

# V4.5 full (current default)
await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, fox ears",
    "model": "nai-diffusion-4-5-full",
})

# NovelAI Diffusion V5 — natural-language prompts, EN/JP, true alpha
await ctx.session.call_tool("generate_image", {
    "prompt": "a fox girl sitting in autumn leaves, soft watercolor",
    "model": "nai-diffusion-5-full",
    "straight_alpha": True,  # pair with "transparent background" in the prompt
})
```

## 4. 生成を再現する

同じ画像を再現するには、同じ `seed` と同じパラメーターを設定します:

```python
await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, fox ears, autumn leaves",
    "seed": 42,
    "width": 832, "height": 1216, "steps": 28,
    "scale": 5.0, "sampler": "k_euler_ancestral",
})
```

出力はビット単位で同一になります (NovelAI のモデルの重みが変わっていない場合)。

## 5. CLI での同等の実行

```bash
uv run python -m novelai_image_mcp generate \
  --prompt "1girl, fox ears, autumn leaves, masterpiece, best quality" \
  --negative "lowres, bad anatomy, watermark" \
  --width 832 --height 1216 --steps 28 --scale 5.0 \
  --seed 42
```

## 次のステップ

- [画像から画像](img2img.md) — 既存の画像を変換する
- [複数キャラクターの構図](../tools/generate.md) — V4 以降の機能
- [vibe 転送](vibe-transfer.md) — 参照スタイルをエンコードする
- [ツールリファレンス](../tools/index.md) — パラメーターの完全な一覧
