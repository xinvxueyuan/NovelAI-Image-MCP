# 設定

ランタイムの設定はすべて環境変数経由で行います (`pydantic-settings` が
[`novelai_image_mcp.settings`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/docs/source/api/settings.md)
で読み取ります)。正の参照元はリポジトリルートの
[`.env.example`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.env.example)
です。

## 読み込み順序

1. プロセス環境 (最優先)
2. カレントワーキングディレクトリの `.env` ファイル
3. 組み込みデフォルト (最低優先)

`.env` ファイルは UTF-8 としてパースされます。不明なキーは無視され、
変数名は大文字小文字を区別しません (`NOVELAI_TOKEN` と `novelai_token` は
等価です)。

---

## NovelAI 認証情報

| 変数 | デフォルト | 必須 | 備考 |
|---|---|---|---|
| `NOVELAI_TOKEN` | — | *いずれか一つ* | 永続 API トークン (推奨)。<https://novelai.net> → Account から取得します。 |
| `NOVELAI_USERNAME` | — | *いずれか一つ* | アクスキーログイン用のユーザー名 (メールアドレス)。 |
| `NOVELAI_PASSWORD` | — | *いずれか一つ* | アカウントのパスワード。`NOVELAI_USERNAME` と組み合わせて argon2id に通し、アクセスキーを導出します。 |

:::{important}
`NOVELAI_TOKEN` **または** `NOVELAI_USERNAME` + `NOVELAI_PASSWORD` のペアの
**いずれか一方**を設定してください。どちらも存在しない場合、サーバーは起動時に
`RuntimeError` を送出します
([`NovelAISettings.has_credentials`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/docs/source/api/settings.md)
を参照)。
:::

## エンドポイント

| 変数 | デフォルト | 備考 |
|---|---|---|
| `NOVELAI_IMAGE_BASE_URL` | `https://image.novelai.net` | 画像生成 / Director / encode-vibe / タグ補完エンドポイント。NovelAI はサードパーティ API アクセスの大部分を `image.novelai.net` に統合しました。 |
| `NOVELAI_ACCOUNT_BASE_URL` | `https://image.novelai.net` | アカウント / サブスクリプション / ユーザーデータエンドポイント。`NOVELAI_IMAGE_BASE_URL` と同じホストを共有します。 |
| `NOVELAI_LEGACY_IMAGE_BASE_URL` | `https://api.novelai.net` | `/ai/upscale` と `/ai/annotate-image` をホストする Primary API。これら 2 つのエンドポイントは `image.novelai.net` に移行されず (404 を返します)、Primary API ドキュメント (<https://api.novelai.net/docs/>) はサードパーティユーザーがその `/ai/` ルートを使用できると明記しています。 |
| `NOVELAI_TIMEOUT` | `120` (秒) | 単一の NovelAI リクエストに対する HTTP タイムアウト。 |

:::{tip}
インテグレーションテスト中は `NOVELAI_IMAGE_BASE_URL` を上書きして
ローカルモック (例: `http://localhost:9000`) を向くようにできます。
`apps/server/tests/` のテストは代わりに
[`respx`](https://github.com/transportapp/respx) を使用するため、この設定は不要です。
:::

## 生成デフォルト

これらは `generate_image` (および同じパラメータを受け付ける他のツール) が
使用するデフォルト値を調整するものです。ツール呼び出しごとに上書き可能です。

| 変数 | デフォルト | 範囲 | 備考 |
|---|---|---|---|
| `NOVELAI_DEFAULT_MODEL` | `nai-diffusion-4-5-full` | `Model` enum 参照 | V3 / V4 / V4.5 / V5 モデル ID。 |
| `NOVELAI_DEFAULT_WIDTH` | `832` | 64–49152、64 の倍数 | 画像の幅 (ピクセル)。 |
| `NOVELAI_DEFAULT_HEIGHT` | `1216` | 64–49152、64 の倍数 | 画像の高さ (ピクセル)。 |
| `NOVELAI_DEFAULT_STEPS` | `28` | 1–50 | サンプラーの反復回数。 |
| `NOVELAI_DEFAULT_SCALE` | `5.0` | 0–20 | Classifier-free guidance スケール。 |
| `NOVELAI_DEFAULT_SAMPLER` | `k_euler_ancestral` | `Sampler` enum 参照 | サンプラー ID。 |

## クライアント

| 変数 | デフォルト | 範囲 | 備考 |
|---|---|---|---|
| `NOVELAI_VIBE_CACHE_ENTRIES` | `64` | 1–1024 | Vibe-transfer のエンコードキャッシュサイズ。同じ参照を 2 回エンコードすると、API を再呼び出しせずキャッシュヒットします。 |

## 出力

| 変数 | デフォルト | 備考 |
|---|---|---|
| `NOVELAI_OUTPUT_DIR` | `outputs` | 生成された PNG の保存先ディレクトリ。相対パスはサーバーのワーキングディレクトリを基準に解決されます。ディレクトリは必要に応じて作成されます。 |

## MCP トランスポート

| 変数 | デフォルト | 範囲 | 備考 |
|---|---|---|---|
| `MCP_TRANSPORT` | `stdio` | `stdio` \| `streamable-http` | サーバーがクライアントに自身を公開する方式。 |
| `MCP_HOST` | `127.0.0.1` | 任意のバインドアドレス | `streamable-http` のバインドホスト。 |
| `MCP_PORT` | `8000` | 1–65535 | `streamable-http` のバインドポート。 |
| `MCP_PATH` | `/mcp` | パス文字列 | streamable-http エンドポイントの HTTP パス。完全 URL: `http://${MCP_HOST}:${MCP_PORT}${MCP_PATH}`。 |

:::{warning}
デフォルトの `MCP_HOST=127.0.0.1` は **localhost のみ** にバインドします。
LAN 上の他のマシンにサーバーを公開するには `MCP_HOST=0.0.0.0` を設定
してください — ただし、TLS 終端または認証付きリバースプロキシの背後に
配置してください。MCP の streamable-http トランスポートは認証を
**実装していません**。
:::

---

## すべてを組み合わせる

リモートの streamable-http デプロイ向けの、本番運用グレードの `.env` 例:

```bash
# ── 認証 ──
NOVELAI_TOKEN=pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ── 生成デフォルト (Opus ティア、高品質) ──
NOVELAI_DEFAULT_MODEL=nai-diffusion-4-5-full
NOVELAI_DEFAULT_WIDTH=1024
NOVELAI_DEFAULT_HEIGHT=1024
NOVELAI_DEFAULT_STEPS=28
NOVELAI_DEFAULT_SCALE=5.0
NOVELAI_DEFAULT_SAMPLER=k_euler_ancestral

# ── 出力 (Docker ボリュームに永続化) ──
NOVELAI_OUTPUT_DIR=/app/outputs

# ── トランスポート ──
MCP_TRANSPORT=streamable-http
MCP_HOST=0.0.0.0
MCP_PORT=8000
MCP_PATH=/mcp

# ── クライアント ──
NOVELAI_VIBE_CACHE_ENTRIES=128
NOVELAI_TIMEOUT=180
```

## Docker 環境での環境変数

[`Dockerfile`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/Dockerfile)
は `docker-compose.yml` の `env_file:` ディレクティブ経由で `.env` を読み
ます。`.env` を編集せずに実行時に単一の変数を上書きするには、以下を実行
します。

```bash
docker compose run -e MCP_PORT=9000 mcp
```

Kubernetes の場合は、env ファイルを `Secret` としてマウントするか、
ConfigMap / Secret 対応の env プロバイダーを使用してください。

## 関連項目

- [`novelai_image_mcp.settings` API リファレンス](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/docs/source/api/settings.md) (英語版)
- [.env.example](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.env.example)
- [トランスポート](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/docs/source/transports/index.md) — stdio と streamable-http のトレードオフ (英語版)
