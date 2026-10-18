# `novelai_image_mcp.nai` — NovelAI HTTP クライアント

`nai/` サブパッケージは NovelAI の HTTP クライアントです。**MCP に依存しません** —
MCP サーバーとは独立して、任意の非同期 Python コードから単体で利用できます。

## サブモジュール

### `novelai_image_mcp.nai.client`

高レベルの非同期クライアント。ワイヤーフォーマットのエンコーダー
（`payload.build_generation_payload`）とレスポンスデコーダー
（`response.parse_messagepack_images`）を、共有の
`httpx.AsyncClient` 上でラップします。

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.client
   :members:
   :undoc-members:
   :show-inheritance:
```

### `novelai_image_mcp.nai.constants`

NovelAI API サーフェスの enum: `Action`、`Model`、`Sampler`、
`DirectorTool`、`Emotion`、`EmotionLevel`、`ControlNetModel`、`Endpoint`、
`NoiseSchedule`。さらに述語 `is_v4_model`、`is_v5_model`、
`supports_vibe`、`is_inpaint_model`。

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.constants
   :members:
   :undoc-members:
   :show-inheritance:
```

### `novelai_image_mcp.nai.models`

ワイヤーフォーマット用の Pydantic モデル: `GenerationRequest`、
`CharacterPrompt`、`NovelAIGenerationPlan`。

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.models
   :members:
   :undoc-members:
   :show-inheritance:
```

### `novelai_image_mcp.nai.auth`

Argon2id によるアクセスキー導出 + リクエストごとのトラッキングヘッダー。

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.auth
   :members:
   :undoc-members:
   :show-inheritance:
```

### `novelai_image_mcp.nai.payload`

`build_generation_payload` — ワイヤーフォーマットのエンコーダー（MessagePack 互換）。

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.payload
   :members:
   :undoc-members:
   :show-inheritance:
```

### `novelai_image_mcp.nai.response`

レスポンスのパース: `NovelAIImage`、`parse_messagepack_images`、
`parse_zip_images`、`check_status`、`GenerationEvent`。

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.response
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: NovelAIProviderError, NovelAIResponseError, NovelAIAuthenticationError, NovelAIConcurrencyError, NovelAIInsufficientCreditsError, NovelAIValidationError
```

:::{note}
上に挙げた例外クラスは `check_status` で送出するために `response` へインポートされている
だけです。ドキュメントは定義元のモジュール `novelai_image_mcp.nai.exceptions`（次の節）にあります。
:::

### `novelai_image_mcp.nai.exceptions`

ドメイン例外の階層:

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.exceptions
   :members:
   :undoc-members:
   :show-inheritance:
```

### `novelai_image_mcp.nai.errors`

エラーボディのパースと公式エラーコードの説明: `ErrorInfo`、
`OFFICIAL_CODE_EXPLANATIONS`、`explain`、`parse_error_body`。

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.errors
   :members:
   :undoc-members:
   :show-inheritance:
```

### `novelai_image_mcp.nai.service`

`create_novelai_client` ファクトリー + `NovelAIConfigLike` プロトコル。ファクトリーは
設定ライクなオブジェクトと `httpx.AsyncClient` を受け取り、完全に配線済みの
`NovelAIClient` を返します。

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.service
   :members:
   :undoc-members:
   :show-inheritance:
```

## 公式エラーコード

このクライアントが送出するすべての NovelAI エラーは、エラー ``code``（HTTP ステータス、または
API 自身のストリームコード）と、文書化されている場合は NovelAI の公式説明を保持します。どちらも
メッセージに追記され、例外の属性として公開されます:

| コード | 意味（公式） |
|---|---|
| `400` | リクエストが不正（バリデーション失敗） |
| `401` | 認証に失敗 |
| `402` | 有効なサブスクリプションまたは Anlas が必要 |
| `409` | リクエストの競合 |
| `429` | レート制限 / 同時実行数の上限 |
| `5xx` | NovelAI 上流のエラー |

すべての例外は ``NovelAIError`` を継承し、``.code`` /
``.explanation`` を公開します（サーバーコードを持たないトランスポート、タイムアウト、
ローカルバリデーションの失敗では両方とも ``None``）。パース用ヘルパーは
``novelai_image_mcp.nai.errors`` モジュールを参照してください。

## 関連項目

- [アーキテクチャ → `NovelAIClient`](../development/architecture.md#novelaiclient-nai-サブパッケージ)
- [GitHub のソース](https://github.com/xinvxueyuan/NovelAI-Image-MCP/tree/main/apps/server/src/novelai_image_mcp/nai)
