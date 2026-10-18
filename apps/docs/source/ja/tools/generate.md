# 生成ツール

テキストプロンプトから画像を生成する 3 つのツール — 純粋な text-to-image、
画像を条件とする img2img、マスクを条件とする inpaint です。3 つとも base64 の
`Image` ブロックと保存されたファイルパスを返します。

---

## `generate_image`

Text-to-image。最も一般的なツールで、プロンプト文字列から 1 枚以上の画像を生成します。
NovelAI V3 / V4 / V4.5 / V5 モデル、複数キャラクターの構図、vibe 転送に対応します
(V5 は vibe 転送を拒否します — 上流では未リリース)。V5 はさらに英語 / 日本語の
自然言語プロンプトを受け付けます。

### パラメーター

| 名前 | 型 | デフォルト | 備考 |
|---|---|---|---|
| `prompt` | `str` | *必須* | ポジティブプロンプト。タグはカンマ区切り。 |
| `negative_prompt` | `str` | `""` | ネガティブプロンプト (UC)。 |
| `model` | `str \| None` | `NOVELAI_DEFAULT_MODEL` | モデル ID を上書き。`Model` enum を参照。 |
| `width` | `int \| None` | `NOVELAI_DEFAULT_WIDTH` | 画像の幅 (px)。64 の倍数。 |
| `height` | `int \| None` | `NOVELAI_DEFAULT_HEIGHT` | 画像の高さ (px)。64 の倍数。 |
| `steps` | `int \| None` | `NOVELAI_DEFAULT_STEPS` | サンプラーのステップ数 (1–50)。 |
| `scale` | `float \| None` | `NOVELAI_DEFAULT_SCALE` | CFG スケール (0–20)。 |
| `sampler` | `str \| None` | `NOVELAI_DEFAULT_SAMPLER` | サンプラー ID (`Sampler` enum を参照)。 |
| `seed` | `int` | `0` | RNG シード。`0` = ランダム。 |
| `n_samples` | `int` | `1` | 画像の枚数 (1–8)。 |
| `quality` | `bool` | `True` | 品質タグのプリセットを使う (V4 以降)。 |
| `uc_preset` | `int` | `0` | ネガティブプロンプトのプリセット (0=heavy、1=light、2=human focus)。 |
| `cfg_rescale` | `float` | `0.0` | CFG リスケール (0–1、V4 以降)。 |
| `smea` | `bool \| None` | モデル依存 | SMEA を有効化。`None` = 自動。 |
| `smea_dynamic` | `bool \| None` | モデル依存 | 動的 SMEA を有効化。 |
| `auto_smea` | `bool` | `False` | 解像度に応じて SMEA を自動選択。 |
| `straight_alpha` | `bool` | `False` | 真のアルファチャンネル (V5 のみ。`transparent background` / `has alpha` と併用)。 |
| `prefer_brownian` | `bool` | `True` | ブラウン運動ノイズスケジュールを優先 (V4 以降)。 |
| `noise_schedule` | `str` | `"karras"` | ノイズスケジュール (`native`、`karras`、`exponential`、`polyexponential`)。 |
| `character_prompts` | `list[dict] \| None` | `None` | V4 以降 / V5 の複数キャラクター構図。 |
| `references` | `list[str] \| None` | `None` | V4/V4.5 の vibe トークン (`encode_vibe` が返す base64 の vibe 文字列)。V5 では拒否されます。 |

### 戻り値

`list[ContentBlock]` — base64 `Image` と、保存先パスのテキスト。

### 例

```python
# Simple text-to-image
await ctx.session.call_tool("generate_image", {
    "prompt": "a fox in a snowy forest, masterpiece, best quality",
    "negative_prompt": "lowres, bad anatomy, watermark",
    "width": 832,
    "height": 1216,
    "steps": 28,
    "scale": 5.0,
    "seed": 42,
})
```

### 複数キャラクターの構図 (V4 以降)

V5 も同じ複数キャラクターの仕組みに対応しているため (上流では最大 22 キャラクターまで
検証済み)、以下の挙動は V4 / V4.5 / V5 に当てはまります。

```python
await ctx.session.call_tool("generate_image", {
    "prompt": "two characters talking in a cafe",
    "character_prompts": [
        {"prompt": "1girl, red hair, blue eyes", "x": 0.3, "y": 0.5, "negative_prompt": ""},
        {"prompt": "1boy, black hair, green eyes", "x": 0.7, "y": 0.5, "negative_prompt": ""},
    ],
})
```

`x` と `y` は `0.1`–`0.9` の範囲の正規化された中心座標です。最初のキャラクターが
常に焦点となる被写体になります。

### vibe 転送 (V4 / V4.5)

```python
# 1. Encode a reference image
vibe = await ctx.session.call_tool("encode_vibe", {"reference": ref_b64})

# 2. Use the vibe as a reference
await ctx.session.call_tool("generate_image", {
    "prompt": "1girl, watercolor style",
    "references": [vibe],
})
```

ワークフロー全体については [vibe 転送のチュートリアル](../tutorials/vibe-transfer.md) を
参照してください。

---

## `image_to_image`

Image-to-image。入力画像を条件として新しい画像を生成します。

### パラメーター

| 名前 | 型 | デフォルト | 備考 |
|---|---|---|---|
| `prompt` | `str` | *必須* | ポジティブプロンプト。 |
| `image` | `str` | *必須* | base64 でエンコードされた入力 PNG/JPEG。 |
| `negative_prompt` | `str` | `""` | ネガティブプロンプト。 |
| `model` | `str \| None` | デフォルト | モデル ID。入力画像のドメインと一致させる必要があります。 |
| `strength` | `float` | `0.3` | 0.01–0.99。入力からどれだけ離れるか。 |
| `noise` | `float` | `0.0` | 0–0.99。追加のばらつき。 |
| `width` / `height` / `steps` / `scale` / `sampler` / `seed` / `n_samples` / `quality` / `uc_preset` / `noise_schedule` / `cfg_rescale` | (`generate_image` を参照) | (同じデフォルト) | |
| `extra_noise_seed` | `int \| None` | `None` | ノイズ用の別シード (デフォルトは `seed`)。 |

### 例

```python
await ctx.session.call_tool("image_to_image", {
    "prompt": "1girl, masterpiece, smile",
    "image": image_b64,
    "strength": 0.4,
    "noise": 0.05,
})
```

:::{tip}
`strength=0.5` が出発点として適しています。0.3 を下回ると結果は入力の再デノイズの
ように見え、0.7 を超えると新規の text-to-image に近づいていきます。
:::

---

## `inpaint`

画像の一部を局所的に再描画します。領域はマスクで定義され、不透明なピクセルが
再生成されます。

### パラメーター

| 名前 | 型 | デフォルト | 備考 |
|---|---|---|---|
| `prompt` | `str` | *必須* | 再生成する領域のプロンプト。 |
| `image` | `str` | *必須* | base64 でエンコードされた入力 PNG/JPEG。 |
| `mask` | `str` | *必須* | base64 でエンコードされたマスク。不透明 = 再描画。 |
| `negative_prompt` | `str` | `""` | 領域に対するネガティブプロンプト。 |
| `model` | `str \| None` | デフォルト | inpaint モデル (例: `nai-diffusion-4-5-full-inpainting` または `nai-diffusion-5-full-inpainting`) で **なければなりません**。 |
| `strength` / `noise` / `width` / `height` / `steps` / `scale` / `sampler` / `seed` / `n_samples` / `quality` / `uc_preset` / `noise_schedule` / `cfg_rescale` / `extra_noise_seed` | (`image_to_image` を参照) | (同じデフォルト) | |

### 例

```python
await ctx.session.call_tool("inpaint", {
    "prompt": "1girl, masterpiece, smiling",
    "image": image_b64,
    "mask": mask_b64,
    "model": "nai-diffusion-4-5-full-inpainting",
    "strength": 0.5,
})
```

:::{warning}
Inpaint には専用の inpaint モデルが必要です。inpaint 以外のモデルで `inpaint` を
呼び出すと `NovelAIValidationError` が返されます。呼び出す前に
[`is_inpaint_model`](../api/client.md) (`nai.constants` サブモジュール内) で
確認してください。
:::

マスク作成の手順については [inpaint のチュートリアル](../tutorials/inpaint.md) を
参照してください。

---

## 関連項目

- [生成チュートリアル](../tutorials/txt2img.md)
- [img2img チュートリアル](../tutorials/img2img.md)
- [inpaint チュートリアル](../tutorials/inpaint.md)
- [`novelai_image_mcp.tools.generate` API リファレンス](../api/tools.md)
- [設定](../configuration.md) — パラメーターを省略したときに適用されるデフォルト
