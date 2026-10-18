# 設定

実行時の設定はすべて環境変数で行います（[`novelai_image_mcp.settings`](api/settings.md) の
`pydantic-settings` が読み取ります）。正典となるリファレンスはリポジトリルートの
[`.env.example`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.env.example) です。

## 読み込み順序

1. プロセスの環境変数（最優先）
2. カレントワーキングディレクトリの `.env` ファイル
3. 組み込みのデフォルト（最低優先）

`.env` ファイルは UTF-8 として解析されます。未知のキーは無視され、変数名は
大文字小文字を区別しません（`NOVELAI_TOKEN` と `novelai_token` は等価です）。

---

## NovelAI 認証情報

| 変数 | デフォルト | 必須 | 備考 |
|---|---|---|---|
| `NOVELAI_TOKEN` | — | *いずれか* | 永続 API トークン（推奨）。<https://novelai.net> → Account から取得します。 |
| `NOVELAI_USERNAME` | — | *いずれか* | アクセスキーログイン用のユーザー名（メールアドレス）。 |
| `NOVELAI_PASSWORD` | — | *いずれか* | アカウントのパスワード。`NOVELAI_USERNAME` と組み合わせ、argon2id を通してアクセスキーを導出します。 |

:::{important}
`NOVELAI_TOKEN` **または** `NOVELAI_USERNAME` + `NOVELAI_PASSWORD` の
ペアの **どちらか** を設定してください。どちらもない場合、サーバーは起動時に
`RuntimeError` を送出します（[`NovelAISettings.has_credentials`](api/settings.md) を参照）。
:::

## エンドポイント

| 変数 | デフォルト | 備考 |
|---|---|---|
| `NOVELAI_IMAGE_BASE_URL` | `https://image.novelai.net` | 画像生成 / Director / encode-vibe / suggest-tags の各エンドポイント。NovelAI は第三者による API アクセスの大半を `image.novelai.net` に集約しました。 |
| `NOVELAI_ACCOUNT_BASE_URL` | `https://image.novelai.net` | アカウント / サブスクリプション / ユーザーデータの各エンドポイント。`NOVELAI_IMAGE_BASE_URL` と同じホストを共有します。 |
| `NOVELAI_LEGACY_IMAGE_BASE_URL` | `https://api.novelai.net` | `/ai/annotate-image` 用の Primary API ホスト — 移行しなかった唯一のエンドポイントです（それ以外はそこでは 404 になります）。単体の `/ai/upscale` は `image.novelai.net` にあり、V5 専用です。 |
| `NOVELAI_TIMEOUT` | `120`（秒） | NovelAI への 1 リクエストあたりの HTTP タイムアウト。 |

:::{tip}
統合テスト中は `NOVELAI_IMAGE_BASE_URL` をローカルのモック（例:
`http://localhost:9000`）に向けて上書きできます。`apps/server/tests/` のテストは
代わりに [`respx`](https://github.com/lundberg/respx) を使うため、この設定は不要です。
:::

## 生成デフォルト

`generate_image`（および同じパラメータを受け付ける他のツール）が使うデフォルトを調整します。
ツール呼び出しごとに上書きできます。

| 変数 | デフォルト | 範囲 | 備考 |
|---|---|---|---|
| `NOVELAI_DEFAULT_MODEL` | `nai-diffusion-4-5-full` | `Model` enum を参照 | V3 / V4 / V4.5 / V5 のモデル id。 |
| `NOVELAI_DEFAULT_WIDTH` | `832` | 64–49152、64 の倍数 | 画像の幅（ピクセル）。 |
| `NOVELAI_DEFAULT_HEIGHT` | `1216` | 64–49152、64 の倍数 | 画像の高さ（ピクセル）。 |
| `NOVELAI_DEFAULT_STEPS` | `28` | 1–50 | サンプラーの反復回数。 |
| `NOVELAI_DEFAULT_SCALE` | `5.0` | 0–20 | Classifier-free guidance のスケール。 |
| `NOVELAI_DEFAULT_SAMPLER` | `k_euler_ancestral` | `Sampler` enum を参照 | サンプラー id。 |

## クライアント

| 変数 | デフォルト | 範囲 | 備考 |
|---|---|---|---|
| `NOVELAI_VIBE_CACHE_ENTRIES` | `64` | 1–1024 | Vibe 転送エンコードのキャッシュサイズ。同じ参照画像を 2 回エンコードすると、API を再度呼ばずにキャッシュに当たります。 |

## 出力

| 変数 | デフォルト | 備考 |
|---|---|---|
| `NOVELAI_OUTPUT_DIR` | `outputs` | 生成された PNG の保存先ディレクトリ。相対パスはサーバーのワーキングディレクトリを基準に解決されます。ディレクトリは必要に応じて作成されます。 |
| `NOVELAI_UPSCALE_MODEL` | `nai-diffusion-5-full` | 単体の 4× アップスケーラーが使用するモデル。単体アップスケールに対応するのは V5 系のみです（`nai-diffusion-5-full`、`nai-diffusion-5-curated`）。 |

## MCP トランスポート

| 変数 | デフォルト | 範囲 | 備考 |
|---|---|---|---|
| `MCP_TRANSPORT` | `stdio` | `stdio` \| `http`（旧称エイリアス `streamable-http`） | サーバーがクライアントに自身を公開する方式。 |
| `MCP_HOST` | `127.0.0.1` | 任意のバインドアドレス | HTTP トランスポートのバインドホスト。 |
| `MCP_PORT` | `8000` | 1–65535 | HTTP トランスポートのバインドポート。 |
| `MCP_PATH` | `/mcp` | パス文字列 | MCP エンドポイントの HTTP パス。完全 URL: `http://${MCP_HOST}:${MCP_PORT}${MCP_PATH}`。 |
| `MCP_AUTH_TOKEN` | *（空）* | 任意のトークン文字列 | 設定すると、HTTP トランスポートは `Authorization: Bearer <token>` を要求します。エンドポイントを開いたままにする場合は空にしてください（下の警告を参照）。 |
| `MCP_LOG_LEVEL` | *（フレームワークのデフォルト）* | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` \| `CRITICAL` | 起動時に FastMCP へ渡すログレベル。 |

:::{note}
`http` が正規のトランスポート名です。`streamable-http` は旧称エイリアスとして
受け付けられ、同じトランスポートを選択します。`MCP_PATH` はそのまま FastMCP に渡されるため、
変更するとエンドポイントが移動します。
:::

:::{warning}
デフォルトの `MCP_HOST=127.0.0.1` は **localhost のみ** にバインドします。
LAN 上の他のマシンにサーバーを公開するには `MCP_HOST=0.0.0.0` を設定し、
さらに `MCP_AUTH_TOKEN` を設定するか、TLS 終端 / 認証付きリバースプロキシの背後に
配置してください。`MCP_AUTH_TOKEN` と `MCP_ROUTE_TOKENS` のどちらも未設定の場合、
HTTP トランスポートは認証ミドルウェアをまったく導入しません — エンドポイントは
未認証のクライアントを受け付けます。
:::

## Insiders ヘッダー、ルーティング、監査

`X-MCP-Insiders` オプトインサーフェスは、リクエストがヘッダーを送らない限り何もしません。
以下の変数は、それが読み取るヘッダー名と、それが有効化する副作用を設定します。完全な契約は
[Insiders ヘッダー、ルーティング、監査](development/insiders-and-routing.md) にあります。

| 変数 | デフォルト | 備考 |
|---|---|---|
| `MCP_INSIDERS_HEADER` | `X-MCP-Insiders` | リクエスト単位のオプトインヘッダー名。検索は大文字小文字を区別しません。 |
| `MCP_MODEL_HEADERS` | `["X-MCP-Model", "X-MCP-Model-Name"]` | JSON リスト。宣言されたモデルの順序付き候補。空でない最初のヘッダーが採用されます。 |
| `MCP_AGENT_HEADERS` | `["X-MCP-Agent-ID", "X-MCP-Agent", "X-MCP-Agent-Source"]` | JSON リスト。エージェントの順序付き候補であり、最初のルート供給元でもあります。 |
| `MCP_CLIENT_HEADERS` | `["X-MCP-Client", "X-MCP-Client-Session-Id"]` | JSON リスト。クライアントの順序付き候補。`session` を含む最初の名前がセッションを供給します。 |
| `MCP_INSIDERS_DISABLED_FEATURES` | `[]` | JSON リスト。運用者向けキルスイッチ: ここに挙げた機能は、クライアントが何を送ってもオフのままです。 |
| `MCP_ROUTE_SCOPED_OUTPUT` | `true` | ルーティングが有効な間、画像を `<NOVELAI_OUTPUT_DIR>/<サニタイズ済みルート>/` に書き込みます。 |
| `MCP_AUDIT_LOG_PATH` | *（未設定）* | 監査 JSONL の出力先。未設定なら `<NOVELAI_OUTPUT_DIR>/audit.jsonl` です。 |
| `MCP_ROUTE_TOKENS` | *（未設定）* | JSON オブジェクト `{"<route>": "<token>"}`。ルート束縛ベアラートークン。リクエストが宣言したルートと一致しないトークンは `401` で拒否されます。 |

:::{warning}
上の 5 つのリスト / 辞書変数は **JSON** です:
`MCP_AGENT_HEADERS='["X-MCP-Agent-ID"]'` は動作しますが、カンマ区切りの値は
設定エラーになり、空の値は有効な JSON ではありません — 空にするのではなく行ごと
コメントアウトしてください。
:::

---

## すべてを組み合わせる

リモートの streamable-http デプロイ向けの、本番運用グレードの `.env`:

```bash
# ── Auth ──
NOVELAI_TOKEN=pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ── Generation defaults (Opus tier, high quality) ──
NOVELAI_DEFAULT_MODEL=nai-diffusion-4-5-full
NOVELAI_DEFAULT_WIDTH=1024
NOVELAI_DEFAULT_HEIGHT=1024
NOVELAI_DEFAULT_STEPS=28
NOVELAI_DEFAULT_SCALE=5.0
NOVELAI_DEFAULT_SAMPLER=k_euler_ancestral

# ── Output (persist to a Docker volume) ──
NOVELAI_OUTPUT_DIR=/app/outputs

# ── Transport ──
MCP_TRANSPORT=http
MCP_HOST=0.0.0.0
MCP_PORT=8000
MCP_PATH=/mcp
# Require "Authorization: Bearer <token>" on the HTTP endpoint. Without it
# the endpoint is open — front it with TLS + a reverse proxy instead.
MCP_AUTH_TOKEN=change-me

# ── Client ──
NOVELAI_VIBE_CACHE_ENTRIES=128
NOVELAI_TIMEOUT=180
```

## Docker 環境での環境変数

[`Dockerfile`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/Dockerfile)
は `docker-compose.yml` の `env_file:` ディレクティブを通じて `.env` を読み取ります。
`.env` を編集せずに実行時に 1 つの変数だけを上書きするには:

```bash
docker compose run -e MCP_PORT=9000 mcp
```

Kubernetes では、env ファイルを `Secret` としてマウントするか、ConfigMap /
Secret 対応の env プロバイダーを使用してください。

## 関連項目

- [`novelai_image_mcp.settings` API リファレンス](api/settings.md)
- [.env.example](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.env.example)
- [トランスポート](transports/index.md) — stdio と HTTP のトレードオフ
