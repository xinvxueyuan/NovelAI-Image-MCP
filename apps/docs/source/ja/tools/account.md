# アカウントツール

画像生成 API を呼び出さずにアカウントの状態を読み取り、コストを見積もる 3 つの
ツールです。Anlas を消費しないため、頻繁に呼び出しても安全です。

---

## `get_subscription`

アカウントのサブスクリプション情報と Anlas 残高を返します。

### パラメーター

なし。

### 戻り値

NovelAI の `/user/subscription` レスポンスを反映した `dict`:

| キー | 型 | 備考 |
|---|---|---|
| `tier` | `int` | 0 = free、1 = starter、2 = ...、3 = Opus。 |
| `active` | `bool` | サブスクリプションが現在有効かどうか。 |
| `trainingStepsLeft` | `dict` | `{fixed: int, perStepUsage: bool}` — 残りの Anlas 換算ステップ数。 |
| `fixedTrainingStepsLeft` | `int` | 使用ごとにカウントされない Anlas 換算ステップ数。 |
| `perStepUsage` | `bool` | 生成ごとにステップが差し引かれるかどうか。 |
| `subscriptionId` | `str` | 内部的なサブスクリプション ID。 |

### 例

```python
sub = await ctx.session.call_tool("get_subscription", {})
print(sub["tier"], sub["trainingStepsLeft"]["fixed"])
```

### CLI

```bash
uv run python -m novelai_image_mcp info
```

---

## `get_user_data`

認証済みアカウントのユーザーデータを返します。生成コマンドを発行する前に、
サーバーがどのアカウントで認証されているかを確認するのに便利です。

### パラメーター

なし。

### 戻り値

以下を含む `dict`:

| キー | 型 | 備考 |
|---|---|---|
| `email` | `str` | アカウントの登録メールアドレス。 |
| `accountChain` | `str` | 登録元 (例: `google`、`x`、`direct`)。 |
| `priority` | `int` | 内部的な epoch。 |

### 例

```python
user = await ctx.session.call_tool("get_user_data", {})
print(f"Authenticated as: {user['email']}")
```

---

## `estimate_anlas_cost`

API を呼び出さずに生成の Anlas コストを見積もります。NovelAI の公開 Web
クライアントのコスト計算式を反映しています。

### パラメーター

| 名前 | 型 | デフォルト | 備考 |
|---|---|---|---|
| `width` | `int` | *必須* | 画像の幅 (px)。 |
| `height` | `int` | *必須* | 画像の高さ (px)。 |
| `steps` | `int` | *必須* | サンプラーのステップ数。 |
| `n_samples` | `int` | `1` | 画像の枚数。 |
| `model` | `str` | `"nai-diffusion-4-5-full"` | 対象モデル。 |
| `action` | `str` | `"generate"` | `generate`、`img2img`、`infill` (inpaint) のいずれか。 |
| `strength` | `float \| None` | `None` | `img2img` / `infill` では必須 (0.01–0.99)。 |
| `smea` | `bool \| None` | `None` | SMEA を有効化。 |
| `smea_dynamic` | `bool \| None` | `None` | 動的 SMEA を有効化。 |
| `auto_smea` | `bool` | `False` | 自動 SMEA。 |
| `opus` | `bool` | `False` | Opus ティアの無料サンプルルールを適用。 |

### 戻り値

以下を含む `dict`:

| キー | 型 | 備考 |
|---|---|---|
| `anlas` | `int` | 見積もられた Anlas コスト。 |
| `opus_free_sample` | `bool` | Opus の無料サンプルが適用される場合 (Anlas は課金されない) は `True`。 |

### 例

```python
cost = await ctx.session.call_tool("estimate_anlas_cost", {
    "width": 832,
    "height": 1216,
    "steps": 28,
    "n_samples": 4,
    "model": "nai-diffusion-4-5-full",
})
# cost: {"anlas": 20, "opus_free_sample": False}
```

### コスト表 (目安)

参考値 — 1 サンプル、Opus ティア、`nai-diffusion-4-5-full`、28 ステップ:

| 解像度 | Anlas (txt2img) | Anlas (img2img、strength=0.5) |
|---|---|---|
| 512 × 768 | 2 | 1 |
| 832 × 1216 | 5 | 3 |
| 1024 × 1024 | 5 | 3 |
| 1536 × 1024 | 7 | 4 |

:::{note}
Opus ティアの加入者は、小規模な生成 (≤1024²、≤28 ステップ) で **無料サンプル** を
利用できます。無料サンプルを適用して見積もるには `opus=True` を設定します。
:::

:::{warning}
**V5 モデル** では、Opus の無料生成は NovelAI の補充可能な使用量上限で制限され、
上限を使い切ると API は **Anlas を無言で課金** します — コストの大きい V5 実行の前には
`get_subscription` の `usage` フィールドを確認してください。
:::

## 関連項目

- [`estimate_anlas_cost` API リファレンス](../api/tools.md)
- [NovelAI Anlas ドキュメント](https://docs.novelai.net/image/anlas.html)
- [設定](../configuration.md) — 生成デフォルトを設定してコストを制御する
