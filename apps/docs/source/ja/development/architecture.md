# アーキテクチャ

このサーバーは、NovelAI HTTP クライアントの上に載る薄いコンポジションルートです。
このページでは各レイヤーと、それらがどのように組み合わさるのかを順に説明します。

## レイヤー

```{mermaid}
graph TD
    A[Agent / MCP host] -->|JSON-RPC over stdio / HTTP| B[FastMCP]
    B -->|middleware| M[ToolCallLoggingMiddleware]
    B -->|optional bearer auth| N[mcp_auth.build_auth]
    B -->|lifespan| C[AppContext: NovelAIClient + NovelAISettings]
    C -->|Depends DI| D[tools/* · resources.py · prompts.py]
    D -->|calls| E[NovelAIClient nai/]
    E -->|httpx.AsyncClient| F[NovelAI API]
    D -->|saves| G[output.py → outputs/]
    D -->|ImageContent| A
    D -->|structured output| A
```

## `FastMCP` コンポジションルート

[`novelai_image_mcp.server`](../api/server.md) がコンポジションルートです。これは
次のことを行います:

1. MCP の `lifespan` が所有する単一の共有 `httpx.AsyncClient` (コネクションプール)
   を構築します。
2. 設定と httpx クライアントから `NovelAIClient` を構築します。
3. 両者を `AppContext` として yield し、依存性プロバイダーがそれをすべての
   ツール、リソース、プロンプトに公開します。
4. シャットダウン時に両者を破棄します (まず `NovelAIClient` を閉じ、次に基盤の
   httpx セッションを閉じます — クライアントのクローズが例外を送出しても、
   ソケットのリークを避けるため httpx セッションは必ず解放されます)。

インスタンス自体はインポート時に一度だけ設定されます:

```python
mcp = FastMCP(
    name="novelai-image",
    version=__version__,          # serves the package version, not the framework version
    instructions=INSTRUCTIONS,    # how an agent should use the server
    lifespan=lifespan,
    auth=build_auth(get_mcp_settings()),   # None unless MCP_AUTH_TOKEN is set
    mask_error_details=True,      # only ToolError messages reach the client
    middleware=[ToolCallLoggingMiddleware()],
)

from . import prompts, resources, tools  # decorators attach to `mcp`
```

ツール、リソース、プロンプトはモジュールレベルのデコレーターでアタッチされるため、
呼び出すべき `register(mcp)` 関数はありません: `tools/` (または `resources.py`、
`prompts.py`) をインポートすることが登録手順そのものであり、それは `mcp` が
存在した後に実行されます。

```python
@asynccontextmanager
async def lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
    settings = get_novelai_settings()
    if not settings.has_credentials():
        raise RuntimeError("NovelAI credentials are not configured...")
    http_client = create_http_client(timeout=settings.timeout)
    client = create_novelai_client(settings, http_client=http_client)
    try:
        yield AppContext(client=client, settings=settings)
    finally:
        try:
            await client.aclose()
        finally:
            if not http_client.is_closed:
                await http_client.aclose()
```

すべてのコンポーネントは自身が必要とするものを宣言し、FastMCP がリクエストごとに
それを解決して、依存関係を入力スキーマから除外します:

```python
@mcp.tool(title=..., tags={...}, annotations=IMAGE_WRITE_ANNOTATIONS)
@translate_errors
async def generate_image(
    prompt: str,
    model: Model | None = None,
    app: AppContext = Depends(get_app_context),   # hidden from the schema
) -> list[Any]: ...
```

`deps.py` がプロバイダー (`get_app_context`、`get_client`) を所有し、
`tools/_errors.py` が `NovelAIError`/`ValueError` → `ToolError` の変換を所有します。
この変換はツール本体の内部で行う必要があります: ミドルウェアのフックが呼び出しを
見るころには、FastMCP がすでに例外をマスクしているためです。

## `NovelAIClient` (`nai/` サブパッケージ)

`nai/` サブパッケージは NovelAI HTTP クライアントです。MCP とは **無関係** で —
任意の非同期 Python コードから単体で利用できます。

| モジュール | 責務 |
|---|---|
| `auth.py` | Argon2id によるアクセスキーの導出、リクエスト追跡ヘッダー。 |
| `client.py` | `NovelAIClient` — 高レベルな非同期 API (`generate`、`upscale`、`director`、`annotate`、`suggest_tags`、`encode_vibe`、`get_subscription`、`get_user_data`)。 |
| `constants.py` | Enum: `Action`、`Model`、`Sampler`、`DirectorTool`、`Emotion`、`EmotionLevel`、`ControlNetModel`、`Endpoint`、`NoiseSchedule`。加えて `is_v4_model`、`is_inpaint_model`。 |
| `exceptions.py` | ドメイン例外: `NovelAIAuthenticationError`、`NovelAIValidationError`、`NovelAIInsufficientCreditsError`、`NovelAIConcurrencyError`、`NovelAIImageError`、`NovelAIProviderError`。 |
| `models.py` | Pydantic モデル: `GenerationRequest`、`CharacterPrompt`、`NovelAIGenerationPlan`。 |
| `payload.py` | `build_generation_payload` — ワイヤーフォーマットのエンコーダー (MessagePack 互換)。 |
| `response.py` | `NovelAIImage`、`parse_messagepack_images`、`parse_zip_images`、`check_status`、`GenerationEvent`。 |
| `service.py` | `create_novelai_client` ファクトリー + `NovelAIConfigLike` プロトコル。 |

## ツールレイヤー

`novelai_image_mcp.tools` は、fastmcp の `FastMCP` ツールデコレーターと
`NovelAIClient` の間の薄いアダプターです。各ツールは次のことを行います:

1. `Depends(get_app_context)` パラメーター (`deps.py`) を通じて `AppContext` を
   受け取るため、入力スキーマには現れません。
2. ツールのパラメーターから `GenerationRequest` (または同等のもの) を構築します。
3. 対応する `NovelAIClient` のメソッドを呼び出します。
4. `output.save_image` で結果を永続化します。
5. MCP コンテンツブロックのリスト `[Image, text_path]` を返します。

ツールは意図的にビジネスロジックを避けています — 検証とパラメーターの
マーシャリングは `nai/` に置かれているため、同じコードパスが MCP サーバー、
CLI、クライアントの直接利用に共通して使われます。Enum 型のパラメーター
(`Model`、`Sampler`、`DirectorTool`、...) はツール本体の内部で変換されるため、
Python から直接呼び出す場合は素の文字列を渡せますが、MCP の呼び出し側は
スキーマ検証を受けます。

ツールに加えて、サーバーは読み取り専用のコンテキストを公開します:

| コンポーネント | 場所 | 目的 |
|---|---|---|
| `novelai://models` | `resources.py` | 機能フラグ付きのモデル ID。 |
| `novelai://samplers` | `resources.py` | サンプラー / ノイズスケジュール / UC プリセットの語彙。 |
| `novelai://defaults` | `resources.py` | 現在有効な生成デフォルト (認証情報なし)。 |
| `novelai://outputs/{name}` | `resources.py` | 生成された PNG を読み戻します (名前は出力ディレクトリに対して検証されます)。 |
| `novelai_prompt_writer`, `novelai_image_workflow` | `prompts.py` | ハウススタイルのプロンプト作成とツールの順序付け。 |

## CLI

`novelai_image_mcp.cli` は `typer` アプリで、MCP ツールの一部を直接のサブコマンド
(`generate`、`upscale`、`director`、`annotate`、`info`、`serve`) として公開します。
呼び出しごとに短命な `httpx.AsyncClient` + `NovelAIClient` を構築します —
共有セッションはありません。長期間にわたって複数のツールを使う場合は、
MCP サーバー (lifespan 経由でプールされたセッションを所有します) を推奨します。

## 設定

`novelai_image_mcp.settings` は 2 つの `pydantic-settings` モデルを定義します:

- `NovelAISettings` — 認証情報、エンドポイント、生成デフォルト
  (`NOVELAI_*` 環境変数)。
- `MCPServerSettings` — トランスポートの選択 (`MCP_*` 環境変数)。

どちらもプロセス環境 + (カレントディレクトリの) `.env` から読み込まれ、UTF-8、
大文字小文字を区別せず、不明なキーは無視されます。`NovelAISettings` は構造的に
`NovelAIConfigLike` を満たすため、クライアントファクトリーはそれをそのまま
利用します。

## 出力

`novelai_image_mcp.output.save_image` は PNG を `NOVELAI_OUTPUT_DIR` に書き込み、
パスを返します。ディレクトリは必要に応じて作成されます。ファイル名にはツール名 +
ISO タイムスタンプ + サンプルインデックスが含まれます
(`generate-20260725-133702-001.png`)。

## トランスポート

サーバーは stdio (既定) と HTTP をサポートし、起動時に `MCP_TRANSPORT` で選択します
(`http` が正規で、`streamable-http` は受け付けられる別名です)。どちらも同じ `lifespan`、
同じツール、同じ `NovelAIClient` を共有し — 異なるのはフレーミングだけです。
`MCP_AUTH_TOKEN` (または `MCP_ROUTE_TOKENS`) を設定すると、HTTP トランスポートは
ベアラートークンを要求します。stdio は影響を受けません。
[トランスポート](../transports/index.md) を参照してください。

## コンテナ化

[`apps/server/Dockerfile`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/Dockerfile)
はマルチステージビルドです:

1. **ビルダーステージ**: uv をインストールし、ランタイム依存関係 (dev グループを除く)
   をエクスポートし、wheel をビルドします。
2. **プロジェクトビルドステージ**: `uv build` でプロジェクトの wheel をビルドします。
3. **ランタイムステージ**: スリムな Python 3.13、非 root の `app` ユーザー、
   ビルド済み wheel のみをインストール — ランタイムイメージにコンパイラー
   ツールチェーンは含まれません。

スモークテスト (`apps/server/docker/smoke-test.py`) は別のイメージに組み込まれ
(`SMOKE_TEST=true` ビルド引数経由)、次のことを検証します:

- パッケージがクリーンにインポートされる。
- 設定が環境変数からインスタンス化される (`NOVELAI_TOKEN=pst-smoke-test` を使用)。
- すべてのツールが記録用の FastMCP スタブに登録される。
- typer CLI がランタイムエラーなく構築される。

## 関連項目

- [`server.py` API リファレンス](../api/server.md)
- [`nai/` API リファレンス](../api/client.md)
- [テスト](testing.md) — 各レイヤーがどのように分離してテストされるか
- [リリース](releasing.md) — Docker イメージのビルドと署名のプロセス
