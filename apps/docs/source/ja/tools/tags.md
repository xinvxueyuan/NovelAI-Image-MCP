# `suggest_tags`

部分的なプロンプトを補完または洗練する NovelAI プロンプトタグを提案します。
提案は NovelAI の学習セットタガーによって順位付けされ、学習データでの出現回数と
ともに返されます。

## パラメーター

| 名前 | 型 | デフォルト | 備考 |
|---|---|---|---|
| `prompt` | `str` | *必須* | 補完する部分的なプロンプトテキスト。 |
| `model` | `str` | `"nai-diffusion-4-5-full"` | タガーの語彙 (`Model` enum の値と一致)。 |
| `language` | `str` | `"en"` | ISO 639-1 のレスポンス言語 (例: `en`、`ja`、`zh`)。 |

## 戻り値

`list[TagSuggestion]` — 各提案は NovelAI が返すフィールドを持ちます:

| キー | 型 | 備考 |
|---|---|---|
| `tag` | `str` | タグ文字列そのもの (プロンプトでこれを使います)。 |
| `count` | `int` | 学習セットでの出現回数 (大きいほど一般的)。 |
| `confidence` | `float` | この補完に対するタガーの信頼度 (0–1)。 |

ワイヤー上の形は実際に検証済みです (
[API サーフェスの整合](../development/api-alignment.md) を参照):

## 例

```python
result = await ctx.session.call_tool("suggest_tags", {
    "prompt": "1girl, fox ears,",
    "model": "nai-diffusion-4-5-full",
    "language": "en",
})
# result: [
#   {"tag": "fox girl", "count": 10000, "confidence": 0.745},
#   {"tag": "fox tail", "count": 4321, "confidence": 0.612},
#   ...
# ]
```

## ヒント

:::{tip}
**反復的なプロンプト構築**: プロンプトを編集するたびにエージェントへ `suggest_tags` を
呼ばせ、シーンに合う最上位の提案を採用します。思い付かなかったタグを素早く
見つける方法です。
:::

:::{admonition} タグの count と品質
:class: note

`count` はそのタグが NovelAI の学習データにどれだけ頻繁に現れるかを示すもので、
あなたのプロンプトにとってどれだけ *有用* かではありません。珍しいタグ (`count` が小さい)
でも、シーンの完璧な記述子になり得ます。
:::

## 関連項目

- [`suggest_tags` API リファレンス](../api/tools.md)
- [NovelAI タグのドキュメント](https://docs.novelai.net/image/promptstags.html)
