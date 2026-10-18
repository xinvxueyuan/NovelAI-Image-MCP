# `director_tool`

NovelAI の **Director ツール** を画像に適用します。Director ツールは既存の画像を
派生的な形 — ラインアート、スケッチ、背景除去、declutter、カラー化、感情転送 — に
変換します。

## パラメーター

| 名前 | 型 | デフォルト | 備考 |
|---|---|---|---|
| `tool` | `str` | *必須* | `lineart`、`sketch`、`bg-removal`、`declutter`、`colorize`、`emotion` のいずれか。 |
| `image` | `str` | *必須* | base64 でエンコードされた PNG/JPEG。 |
| `prompt` | `str` | `""` | `colorize` と `emotion` を誘導します。 |
| `defry` | `int` | `0` | 0–10。ラインアートを強調します (`lineart` / `sketch` で使用)。 |
| `emotion` | `str \| None` | `None` | 感情名 (`emotion` ツールでは必須)。 |
| `emotion_level` | `int` | `0` | 0–5。0 = 通常の強度、5 = 最も弱い。 |

:::{warning}
`emotion` と `emotion_level` は **実験的** です: insiders ヘッダー
(`X-MCP-Insiders: experimental-tools=true`) で opt-in したリクエストにのみ提供されます。
opt-in がない状態でどちらかを渡すと `ToolError` で失敗します。デフォルト以外の
`emotion_level` だけでも「渡した」とみなされます。どちらのパラメーターもツール
スキーマには表示されたままです — スキーマはサーバー起動時に公開されるため、
リクエストごとに変化させられないからです。
[Insiders ヘッダー、ルーティング、監査](../development/insiders-and-routing.md) を参照してください。
:::

## 戻り値

`list[ContentBlock]` — 変換後の画像の base64 `Image` と、保存先パスのテキスト。

## Director ツール

| `tool` の値 | 説明 |
|---|---|
| `lineart` | 画像をクリーンなラインアートに変換します。`defry` (0–10) で線を強調できます。 |
| `sketch` | 鉛筆スケッチ風に変換します。`defry` も受け付けます。 |
| `bg-removal` | 背景を除去し、前景の被写体を透明の上に残します。 |
| `declutter` | 小さな不要物 (文字、ウォーターマーク、粒子) を除去します。 |
| `colorize` | モノクロ / ラインアートの画像に着色します。`prompt` が色を誘導します。 |
| `emotion` | 被写体に顔の感情を転送します。`emotion` 名が必要で、`emotion_level` (0–5) が強度を調整します。 |

## 感情名

`emotion` パラメーターは以下の値を受け付けます:

```text
neutral, happy, sad, angry, scared, surprised, tired, excited, nervous,
thinking, confused, shy, disgusted, smug, bored, laughing, irritated,
aroused, embarrassed, worried, love, determined, hurt, playful
```

`Emotion` enum をイントロスペクトして実行時に一覧表示できます:

```python
from novelai_image_mcp.nai import Emotion
print([e.value for e in Emotion])
```

## 例

### ラインアートの抽出

```python
await ctx.session.call_tool("director_tool", {
    "tool": "lineart",
    "image": image_b64,
    "defry": 5,
})
```

### 背景の除去

```python
await ctx.session.call_tool("director_tool", {
    "tool": "bg-removal",
    "image": image_b64,
})
```

### スケッチの着色

```python
await ctx.session.call_tool("director_tool", {
    "tool": "colorize",
    "image": sketch_b64,
    "prompt": "1girl, red hair, blue dress, sunny day",
})
```

### 感情の転送

```python
await ctx.session.call_tool("director_tool", {
    "tool": "emotion",
    "image": portrait_b64,
    "emotion": "happy",
    "emotion_level": 2,
})
```

### CLI

```bash
# Line art extraction
uv run python -m novelai_image_mcp director lineart ./portrait.png --defry 5

# Colorize a sketch
uv run python -m novelai_image_mcp director colorize ./sketch.png --prompt "1girl, red hair"

# Emotion transfer
uv run python -m novelai_image_mcp director emotion ./portrait.png --emotion happy --emotion-level 2
```

## ヒント

:::{tip}
**ワークフローの例**: `lineart` で写真からラインアートを抽出し、それを ControlNet の
条件として使う ([`annotate_image`](annotate.md) を参照) ことで、新たに様式化した
生成を行えます。
:::

:::{admonition} `defry` の意味
:class: note

`defry` は NovelAI の「de-fry」パラメーターです — 強引なラインアート抽出が生む、
平滑化されすぎた「濡れた」見た目を軽減します。値が大きいほど線は強調されますが
ジャギーが増えます。`5` が良い中間点です。
:::

## 関連項目

- [`director_tool` API リファレンス](../api/tools.md)
- [`DirectorTool` enum](../api/client.md) — `nai.constants` サブモジュールに記載
- [ControlNet チュートリアル](../tutorials/controlnet.md) — `lineart` と `annotate_image` を組み合わせる
