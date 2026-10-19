# アカウントツール

画像生成 API を呼び出さずにアカウントの状態を読み取り、コストを見積もる 3 つの
ツールです。Anlas を消費しないため、頻繁に呼び出しても安全です。

---

## `get_subscription`

アカウントのサブスクリプション情報と Anlas 残高を返します。

### パラメーター

なし。

### 戻り値

NovelAI の `/user/subscription` レスポンスを反映した `dict` です。以下のキーと型は
実アカウントで観測したものです:

| キー | 型 | 備考 |
|---|---|---|
| `tier` | `int` | 0 = free、1 = starter、2 = ...、3 = Opus。 |
| `active` | `bool` | サブスクリプションが現在有効かどうか。 |
| `accountType` | `int` | NovelAI が報告するアカウント種別。 |
| `expiresAt` | `int` | サブスクリプションの有効期限 (API が返す値)。 |
| `isGracePeriod` | `bool` | サブスクリプションが猶予期間中かどうか。 |
| `isNewCustomer` | `bool` | 初回契約のアカウントかどうか。 |
| `isPaypal` | `bool` | PayPal で支払っているアカウントかどうか。 |
| `paymentProcessor` | `str` | 決済プロセッサーの ID。 |
| `paymentProcessorData` | `null` | 検証したアカウントでは `null` でした。実際の型は確定していないため、依存しないでください。 |
| `perks` | `object` | ティアの機能フラグ。 |
| `perks.maxPriorityActions` | `int` | ティアに含まれる最大優先度アクション数。 |
| `perks.startPriority` | `int` | ティアが開始するキューの優先度。 |
| `perks.contextTokens` | `int` | コンテキストトークンの許容量。 |
| `perks.unlimitedMaxPriority` | `bool` | 最大優先度が無制限かどうか。 |
| `perks.moduleTrainingSteps` | `int` | 含まれるモジュール学習ステップ数。 |
| `trainingStepsLeft` | `object` | 残りの Anlas 換算ステップ数。 |
| `trainingStepsLeft.fixedTrainingStepsLeft` | `int` | 残っている固定 (未購入) ステップ数。 |
| `trainingStepsLeft.purchasedTrainingSteps` | `int` | 残っている購入済みステップ数。 |

### 例

```python
sub = await ctx.session.call_tool("get_subscription", {})
print(sub["tier"], sub["trainingStepsLeft"]["fixedTrainingStepsLeft"])
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
# cost: {"anlas": 80, "opus_free_sample": False}
```

### コスト表 (目安)

参考値 — 1 サンプル、`nai-diffusion-4-5-full`、28 ステップ。このツールで実測したものです。

**txt2img** (`action="generate"`)

| 解像度 | `opus=False` | `opus=True` |
|---|---|---|
| 512 × 768 | 8 | 0 |
| 832 × 1216 | 20 | 0 |
| 1024 × 1024 | 20 | 0 |
| 1536 × 1024 | 30 | 30 |

**img2img** (`action="img2img"`, `strength=0.5`)

| 解像度 | `opus=False` | `opus=True` |
|---|---|---|
| 512 × 768 | 4 | 0 |
| 832 × 1216 | 10 | 0 |
| 1024 × 1024 | 10 | 0 |
| 1536 × 1024 | 15 | 15 |

:::{note}
Opus ティアの加入者は、小規模な生成 (≤1024²、≤28 ステップ) で **無料サンプル** を
利用できます: その範囲では `opus=True` が `anlas: 0` と `opus_free_sample: true` を
返します。範囲外では `opus` は見積もりを変えません。
:::

`infill` (inpaint) は `generate` と同じ価格です: 832 × 1216、28 ステップ、
`strength=0.5` で 20 Anlas です。

コストは `n_samples` に比例して増えます — 上記の例 (832 × 1216 で 4 サンプル) は
`4 × 20 = 80` です。

:::{warning}
**V5 モデル** では、Opus の無料生成は NovelAI の補充可能な使用量上限で制限され、
上限を使い切ると API は **Anlas を無言で課金** します。コストの大きい V5 実行の前には
`get_subscription` の `trainingStepsLeft` を確認してください — サブスクリプションの
レスポンスに独立した `usage` フィールドはありません。
:::

## 関連項目

- [`estimate_anlas_cost` API リファレンス](../api/tools.md)
- [NovelAI Anlas ドキュメント](https://docs.novelai.net/image/anlas.html)
- [設定](../configuration.md) — 生成デフォルトを設定してコストを制御する
