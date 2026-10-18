# ツールリファレンス

サーバーは [`FastMCP`](../api/server.md) インスタンスに対して
**11 個の MCP ツール** を登録します。すべてのツールは `async` であり、依存関係
(`NovelAIClient` と `NovelAISettings`) を MCP リクエストコンテキストの lifespan
状態から取得します。

## ツール一覧

| ツール | グループ | 説明 |
|---|---|---|
| [`generate_image`](generate.md#generate_image) | generation | テキストから画像を生成 (V3 / V4 / V4.5 / V5、キャラクタープロンプト、vibe) |
| [`image_to_image`](generate.md#image_to_image) | generation | strength / noise を指定した image-to-image |
| [`inpaint`](generate.md#inpaint) | generation | 部分的な再描画 (inpaint モデル + マスクが必要) |
| [`upscale_image`](upscale.md#upscale_image) | enhance | 4 倍アップスケール (V5 モデル) |
| [`director_tool`](director.md#director_tool) | enhance | line art / sketch / bg-removal / declutter / colorize / emotion |
| [`annotate_image`](annotate.md#annotate_image) | enhance | ControlNet の前処理 (hed、midas、fake_scribble、mlsd、uniformer) |
| [`suggest_tags`](tags.md#suggest_tags) | tags | プロンプト用タグの提案 |
| [`encode_vibe`](vibe.md#encode_vibe) | tags | 参照画像を vibe トークンにエンコード |
| [`get_subscription`](account.md#get_subscription) | account | アカウントのサブスクリプションと Anlas 残高 |
| [`get_user_data`](account.md#get_user_data) | account | アカウントのユーザーデータ |
| [`estimate_anlas_cost`](account.md#estimate_anlas_cost) | account | API を呼び出さずに Anlas コストを見積もる |

## 共通のパターン

### 戻り値の形

画像を生成するすべてのツールは、MCP コンテンツブロックのリストを返します。

```python
[
    Image(data=b"...png bytes...", format="png"),  # agent sees the image
    f"Saved 1 image(s): ['outputs/generate-...png']"  # text path for follow-up
]
```

エージェントは画像をインラインで確認する (base64 の `Image` ブロック) ことも、
テキストブロックからパスを読み取って後続のツールに渡すこともできます。

### 画像パラメーター

`str` を受け取る画像パラメーター (`image`、`mask`、`reference`、
`references`) は、ファイルパスではなく **base64 でエンコードされた PNG または
JPEG** の文字列を期待します。ローカルファイルを変換するには次のようにします。

```python
import base64
from pathlib import Path

image_b64 = base64.b64encode(Path("input.png").read_bytes()).decode("ascii")
```

CLI はこの変換を自動で行います — `upscale`、`director`、`annotate` は入力ファイルを
位置引数として受け取ります (例: `upscale ./input.png`)。

### バリデーション

ツールは入力を即座に検証し、enum 形式のパラメーター (`model`、`tool`、`emotion`、
`controlnet model`、`action`) が一致しない場合は、有効な選択肢の一覧を添えた
`ValueError` を送出します。MCP ランタイムはこれをツール呼び出しエラーとして
表面化するため、エージェントはそれを読んで自己修正できます。

## ツールごとのページ

```{toctree}
:maxdepth: 1
:hidden:

generate
upscale
director
annotate
tags
vibe
account
```

## 関連項目

- [チュートリアル](../tutorials/index.md) — ツールを組み合わせたエンドツーエンドのワークフロー
- [エージェントスキル](../skills.md) — このリファレンスを AI エージェント向けにまとめた `novelai-mcp-tools` スキル
- [API リファレンス](../api/index.md) — 基盤となる `NovelAIClient` の autodoc
- [設定](../configuration.md) — パラメーターを省略したときに適用されるデフォルト
