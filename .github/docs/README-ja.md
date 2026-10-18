# NovelAI Image MCP

## 言語

| English | 简体中文 | 日本語 |
|---|---|---|
| [English](../../README.md) | [简体中文](README-zh.md) | [日本語](README-ja.md) |

[![CI][ci-badge]][ci-workflow]
[![Docs][docs-badge]][docs]
[![License: MIT][mit-badge]][license]
[![Python 3.13+][python-badge]][python]
[![uv][uv-badge]][uv]
[![REUSE status][reuse-badge]][reuse]
[![DeepWiki][deepwiki-badge]][deepwiki]
[![skills.sh][skills-badge]][skills-sh]

[![NovelAI Image MCP - MCP server for integrating NovelAI Image generation into AI | Product Hunt][product-hunt-badge]][product-hunt] [![Featured on Lifto][lifto-badge]][lifto]

**NovelAI の画像生成** を AI エージェント（Claude Desktop、Cline、カスタムエージェント、リモートクライアント）向けに公開する [MCP（Model Context Protocol）][mcp] サーバーです。同期 CLI と 3 つの [skills.sh][skills-site] パッケージも同梱し、エージェントがどちらの入口も扱えるようにします。

FastMCP 4（MCP SDK v2 `mcp>=2.3.0` 上の fastmcp フレームワーク）を基盤とし、txt2img / img2img / inpaint、4 倍アップスケール、Director ツール（線画、表情、背景削除など）、ControlNet による注釈付け、タグ候補の提案、vibe のエンコード、アカウントのサブスクリプション照会を、標準 MCP ツールインターフェース経由で提供します。

> 📖 **ドキュメント**：[xinvxueyuan.github.io/NovelAI-Image-MCP][docs]

## 3 つの利用方法

いずれも同じ非同期 `NovelAIClient` を包んでおり、違いは呼び出し方だけです。

- **MCP ツール** —— 対話的なエージェントセッション（Claude Desktop、Cline など）。
  エージェントは base64 の `Image` コンテンツブロックを認識できます。
- **CLI** —— シェルスクリプト、CI ジョブ、単発コマンド。PNG を保存してパスを出力し、
  画像ブロックは返しません。
- **エージェントスキル** —— エージェントに前の 2 つの使い方を教える可搬な手順。
  画像を認識するかはスキルが駆動する入口に依存します。

## 特徴

- **11 個の MCP ツール**で NovelAI 画像 API の全機能をカバー。
- **2 個の prompt + 3 個のリソース + 1 個のリソーステンプレート**：`novelai_prompt_writer` / `novelai_image_workflow` がプロンプト作成とツールの順序付けを担い、`novelai://models`、`novelai://samplers`、`novelai://defaults`、`novelai://outputs/{name}` がモデル／サンプラーの語彙と現在の既定値を公開し、生成済み PNG を読み戻せます。
- **3 つのエージェントスキル**（`novelai-cli`、`novelai-mcp-tools`、`novelai-workflows`）。CLI / MCP Tools / Workflows にグループ化され、`npx skills add` 1 コマンドで導入できます。
- **同期 `typer` CLI**：MCP ホストの外でスクリプト化するための 6 つのサブコマンド。
- **2 種類のトランスポート**：stdio（ローカルエージェント）+ HTTP（リモート／マルチクライアント）。後者はベアラートークン（`MCP_AUTH_TOKEN`）で任意に保護できます。
- **オプトインのルーティングと監査（HTTP）**：`X-MCP-Insiders` を送ったクライアントは、ルートごとの出力ディレクトリ、ルート名のロガー、追記専用の JSONL 監査ログを得られます（プロンプトと資格情報がそのまま書かれることはありません）。このヘッダーを送らなければ挙動は変わりません。詳しくは[インサイダーヘッダー・ルーティング・監査][insiders-docs]。
- **構造化された結果**：列挙型で検証されるツールスキーマ、MCP ツールアノテーション、想定される失敗に対する `ToolError`。
- **画像の二重返却**：base64 の `Image` コンテンツブロック（エージェントが画像を*見る*）と、ディスクに保存される PNG（パスをテキストで返却）。
- **モノレポ**：Turbo が uv workspace（Python）+ pnpm workspace（Node ツールチェーン）をオーケストレーション。MIT ライセンス、Docker 対応、GitHub Pages ドキュメント。

## クイックスタート

### 1. エージェントスキルをインストール

```bash
npx skills add --yes --global xinvxueyuan/NovelAI-Image-MCP
```

`--yes` は対話的な選択をスキップし、`--global` は `~/.agents/skills/` に導入してマシン上の全プロジェクトで使えるようにします。`--global` を外すと現在のプロジェクトの `.agents/skills/` に入ります。各スキルの内容は[エージェントスキル](#エージェントスキル)を参照してください。

### 2. サーバーをインストール（ソースから、開発用）

```bash
# 1. Clone
git clone https://github.com/xinvxueyuan/NovelAI-Image-MCP.git
cd NovelAI-Image-MCP

# 2. Sync the uv workspace (installs server + docs + dev tools)
uv sync

# 3. Configure credentials
cp .env.example .env
#   set NOVELAI_TOKEN=...  (preferred)
#   or  NOVELAI_USERNAME + NOVELAI_PASSWORD

# 4. Run (stdio — for local agents)
uv run python -m novelai_image_mcp serve

# 5. Or over HTTP
MCP_TRANSPORT=http uv run python -m novelai_image_mcp serve
#   → http://127.0.0.1:8000/mcp
```

### 3. サーバーをインストール（PyPI、ランタイムのみ）

```bash
pip install novelai-image-mcp
export NOVELAI_TOKEN=pst-...
novelai-image-mcp serve
```

### オプション：Node ツールチェーン（コントリビューター向け）

コントリビューションを予定している場合は、pnpm で共通 Node ツールチェーン（turbo、husky、markdownlint）をインストールしてください。

```bash
corepack enable pnpm      # one-time
pnpm install --frozen-lockfile
```

これにより husky の pre-commit + commit-msg フックが設定され、ローカル開発用の `turbo` / `markdownlint-cli2` が利用できるようになります。MCP サーバーには **Node のランタイム依存関係がありません**。この手順はコントリビューター専用です。

## エージェントを接続する

MCP サーバーは、`mcpServers` の下で設定する 2 種類のトランスポート（stdio + http）に対応しています。

### stdio（ローカルエージェント — Claude Desktop / Cline）

`claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "novelai-image": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/NovelAI-Image-MCP",
        "python",
        "-m",
        "novelai_image_mcp",
        "serve"
      ],
      "env": {
        "NOVELAI_TOKEN": "${input:novelai_token}"
      }
    }
  }
}
```

#### 代替：uvx（公開済みパッケージ）

```json
{
  "mcpServers": {
    "novelai-image": {
      "command": "uvx",
      "args": ["novelai-image-mcp", "serve"],
      "env": { "NOVELAI_TOKEN": "pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" }
    }
  }
}
```

起動前にホスト環境で `NOVELAI_TOKEN`（または `NOVELAI_USERNAME` + `NOVELAI_PASSWORD`）を設定してください。`uvx` は親シェルの環境変数を継承します。

### http（リモート／Docker デプロイ）

`docker compose up --build` の後（サーバーは `http://HOST:8000/mcp` でリッスンします）：

```json
{
  "mcpServers": {
    "novelai-image-http": {
      "type": "http",
      "url": "http://127.0.0.1:8000/mcp",
      "headers": {
        "Authorization": "Bearer pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

`http://127.0.0.1:8000/mcp` を自分でデプロイしたエンドポイント（例：TLS 終端リバースプロキシの背後にある `https://mcp.example.com/mcp`）に置き換えてください。MCP ホストが対応している場合（Claude Desktop、Cline などでは各自のシークレット UI から利用可能）、リテラルのトークンプレースホルダーをホスト管理のシークレット参照に置き換えます。

### 標準 FastMCP エントリーポイント

リポジトリには、source が `apps/server/mcp_server.py` を指す [`fastmcp.json`](../../fastmcp.json) が含まれているため、標準の FastMCP ツールも利用できます（`uv sync` の後、リポジトリのルートから実行してください）：

```bash
uv run fastmcp run fastmcp.json                     # stdio server
uv run fastmcp inspect                              # list tools/prompts/resources
uv run --directory apps/server fastmcp dev inspector mcp_server.py   # Inspector
```

`fastmcp.json` に `environment` ブロックがないのは意図的です。workspace の仮想環境にはすでにパッケージがインストールされており、`environment` エントリがあると FastMCP は実行のたびに別の使い捨て環境を構築するためです。

## CLI（同期、スクリプト用）

CLI には 6 つのサブコマンドがあります：`serve`、`generate`、`upscale`、`director`、`annotate`、`info`。

```bash
# Run the MCP server (stdio by default; -t http for the HTTP transport)
novelai-image-mcp serve

# Text-to-image — prints one absolute PNG path per generated image
novelai-image-mcp generate --prompt "a cat, masterpiece" --width 832 --height 1216

# 4x upscale (V5 model only)
novelai-image-mcp upscale --image ./in.png --factor 4

# Director tools: lineart | sketch | bg-removal | declutter | colorize | emotion
novelai-image-mcp director lineart ./photo.png --defry 5

# ControlNet annotation: hed | midas | fake_scribble | mlsd | uniformer
novelai-image-mcp annotate ./photo.png --model hed

# Subscription / Anlas balance
novelai-image-mcp info

novelai-image-mcp --help
```

導入は `pip install novelai-image-mcp`、一時的な実行は `uvx novelai-image-mcp <command>`、モノレポ内では `uv run --directory apps/server novelai-image-mcp <command>` です。画像を生成するコマンドはすべて PNG を `NOVELAI_OUTPUT_DIR`（既定 `outputs`）に保存し、そのパスを出力します。`-o` / `--output-dir` は 1 回の呼び出しだけディレクトリを上書きします。フラグの全一覧は [`novelai-cli` スキル][skills-docs] にあります。

## エージェントスキル

`skills/` に 3 つの [skills.sh][skills-site] パッケージが同梱されています。AI エージェント（Claude Code、Codex、GitHub Copilot、Cursor など）に CLI と MCP ツールの扱い方を教えるので、ドキュメントを会話に貼り付ける必要はありません。

```bash
npx skills add --yes --global xinvxueyuan/NovelAI-Image-MCP
```

```mermaid
graph TD
    Q{How will you drive NovelAI?}
    Q -->|"Interactive session with an MCP host"| MCP["MCP tools<br/>11 tools over stdio / http"]
    Q -->|"Shell script, CI job, one-off command"| CLI["CLI<br/>novelai-image-mcp generate ..."]
    Q -->|"Let an agent pick the right one"| SK["Agent skills<br/>novelai-cli / novelai-mcp-tools / novelai-workflows"]
    SK --> MCP
    SK --> CLI
```

| スキル | グループ | 内容 |
|---|---|---|
| `novelai-cli` | CLI | シェルスクリプト用の Typer CLI コマンド（serve、generate、upscale、director、annotate、info） |
| `novelai-mcp-tools` | MCP Tools | 11 個の MCP ツール — モデル選択、パラメーター、返却形式、Anlas コスト |
| `novelai-workflows` | Workflows | 複数ステップのクリエイティブパイプライン（txt2img→upscale、annotate→img2img、Director 編集） |

スキルと CLI／MCP ツールは二者択一ではなく相互補完です。3 つすべてを導入すると、エージェントがタスクに合うモードを選びます。各スキルは他の 2 つを指すだけで、内容を重複させません。グループの説明と入口の比較表は [エージェントスキルのドキュメント][skills-docs] を参照してください。

## リポジトリ構成

これは **uv + pnpm モノレポ**です。

```text
NovelAI-Image-MCP/
├── apps/
│   ├── server/                 # MCP server (the installable PyPI package)
│   │   ├── src/novelai_image_mcp/   # 11 MCP tools + NovelAI HTTP client
│   │   ├── tests/
│   │   ├── docker/              # smoke-test entrypoint
│   │   ├── Dockerfile           # built with repo root as context
│   │   └── pyproject.toml       # ruff / pyright / pytest config
│   └── docs/                    # Sphinx documentation site
│       ├── source/              # MyST Markdown + conf.py
│       ├── Makefile
│       └── pyproject.toml
├── skills/                      # skills.sh packages (novelai-cli, ...)
├── skills.sh.json               # skill groupings for skills.sh
├── .github/                     # workflows, CODEOWNERS, issue templates
├── pyproject.toml               # uv workspace root (virtual)
├── uv.lock                      # single shared lockfile
├── pnpm-workspace.yaml          # pnpm workspace declaration
├── pnpm-lock.yaml               # Node toolchain lockfile
├── turbo.json                   # cross-workspace task graph
├── package.json                 # root scripts + dev toolchain
└── docker-compose.yml           # local container orchestration
```

開発者ガイドは [`CONTRIBUTING.md`][contributing]、完全なドキュメントのソースは [`apps/docs/source/`][docs-source] を参照してください。

## ツール

| ツール | 説明 |
|---|---|
| `generate_image` | テキストから画像生成（V3 / V4 / V4.5 / V5 モデル、キャラクタープロンプト；vibe は V4/V4.5 のみ） |
| `image_to_image` | 強度／ノイズを指定した画像から画像への変換 |
| `inpaint` | インペイント（インペイントモデル + マスクが必要） |
| `upscale_image` | 4 倍アップスケール（V5 モデル） |
| `director_tool` | 線画／スケッチ／背景削除／不要物除去／カラー化／表情 |
| `annotate_image` | ControlNet による注釈付け（hed、midas、scribble、mlsd、uniformer） |
| `suggest_tags` | プロンプトタグの提案 |
| `encode_vibe` | 参照画像を vibe トークンにエンコード |
| `get_subscription` | アカウントのサブスクリプション + Anlas 残高 |
| `get_user_data` | アカウントのユーザーデータ |
| `estimate_anlas_cost` | 生成に必要な Anlas コストを推定（API 呼び出しなし） |

パラメーターと例については、ドキュメントサイトの [ツールリファレンス][tools-docs] を参照してください。

## 設定

すべての設定は環境変数で行います（`.env.example` を参照）。主な項目：

| 変数 | デフォルト | 備考 |
|---|---|---|
| `NOVELAI_TOKEN` | — | 永続 API トークン（推奨認証） |
| `NOVELAI_USERNAME` / `NOVELAI_PASSWORD` | — | access-key ログイン（argon2id） |
| `NOVELAI_OUTPUT_DIR` | `outputs` | 生成した PNG の保存先 |
| `NOVELAI_DEFAULT_MODEL` | `nai-diffusion-4-5-full` | ツール呼び出しでモデルを省略したときのモデル id |
| `NOVELAI_DEFAULT_WIDTH` / `NOVELAI_DEFAULT_HEIGHT` | `832` / `1216` | 既定の画像サイズ |
| `NOVELAI_DEFAULT_STEPS` | `28` | 既定のサンプリングステップ数（1–50） |
| `NOVELAI_DEFAULT_SCALE` | `5.0` | 既定の CFG スケール（≤20） |
| `NOVELAI_DEFAULT_SAMPLER` | `k_euler_ancestral` | 既定のサンプラー |
| `NOVELAI_UPSCALE_MODEL` | `nai-diffusion-5-full` | 単体 4 倍アップスケーラーが使うモデル（V5 系のみ） |
| `NOVELAI_TIMEOUT` | `120` | HTTP タイムアウト（秒） |
| `NOVELAI_IMAGE_BASE_URL` | `https://image.novelai.net` | 生成とアカウントのエンドポイントを担う統合 API ホスト |
| `NOVELAI_LEGACY_IMAGE_BASE_URL` | `https://api.novelai.net` | Primary API ホスト。`/ai/annotate-image` だけが今も使用 |
| `MCP_TRANSPORT` | `stdio` | `stdio` または `http`（`streamable-http` は旧来の別名） |
| `MCP_HOST` / `MCP_PORT` / `MCP_PATH` | `127.0.0.1` / `8000` / `/mcp` | HTTP トランスポート用 |
| `MCP_AUTH_TOKEN` | — | 設定すると HTTP トランスポートに `Authorization: Bearer <token>` が必要 |
| `MCP_ROUTE_TOKENS` | — | JSON `{"<route>": "<token>"}`、ルートに紐づくベアラートークン（ルート不一致は 401） |
| `MCP_INSIDERS_HEADER` | `X-MCP-Insiders` | クライアントがオプトインに使うヘッダー名（HTTP のみ） |
| `MCP_MODEL_HEADERS` / `MCP_AGENT_HEADERS` / `MCP_CLIENT_HEADERS` | see below | JSON リスト。ルーティング候補ヘッダーで、最初の非空値が採用されます |
| `MCP_INSIDERS_DISABLED_FEATURES` | `[]` | 運用側の強制オフスイッチ（JSON リスト）。クライアントより優先されます |
| `MCP_ROUTE_SCOPED_OUTPUT` | `true` | ルーティング有効時、画像を `<output>/<route>/` に書き出します |
| `MCP_AUDIT_LOG_PATH` | `<output>/audit.jsonl` | 追記専用 JSONL 監査ログ |
| `MCP_LOG_LEVEL` | — | `DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL` |

list / dict 型の設定は **JSON** として読み込まれます：`MCP_MODEL_HEADERS='["X-MCP-Model"]'` は有効ですが、`A,B` は設定エラーになり、空値も有効な JSON ではありません。

ルーティング候補ヘッダーの既定値（JSON リスト、最初の非空ヘッダーが採用）：

- `MCP_MODEL_HEADERS` — `["X-MCP-Model", "X-MCP-Model-Name"]`
- `MCP_AGENT_HEADERS` — `["X-MCP-Agent-ID", "X-MCP-Agent", "X-MCP-Agent-Source"]`
- `MCP_CLIENT_HEADERS` — `["X-MCP-Client", "X-MCP-Client-Session-Id"]`

### インサイダーヘッダーとルーティング

HTTP では、クライアントがリクエスト単位で実験的な挙動をオプトインし、そのリクエストがどのルート・モデル・エージェント・セッションに属するかを宣言できます：

```text
X-MCP-Insiders: true
X-MCP-Agent-ID: team-a
X-MCP-Model: nai-diffusion-5-full
```

サーバーはそのリクエストの画像を `<NOVELAI_OUTPUT_DIR>/team-a/` に書き出し、`novelai_image_mcp.audit.team-a` ロガーに 1 行を出力し、監査 JSONL に 1 件を追記します（レコードにはプロンプトの長さと切り詰めた SHA-256 のみが残り、プロンプト本文・資格情報ヘッダー・画像ペイロードが書かれることはありません）。

**このヘッダーを送らなければ何も変わりません** —— ルート別ディレクトリも監査ファイルも作られず、ツールが増減することもありません —— ただし意図的な例外が 1 つあります：`director_tool` の `emotion` と `emotion_level` はオプトインが必要になり、なければ `ToolError` になります（CHANGELOG 参照）。ルーティングヘッダーはクライアントが送るもので偽装できるため、信頼できるゲートウェイの背後でのみオプトインを許可してください。

完全な契約：[インサイダーヘッダー・ルーティング・監査][insiders-docs]。

NovelAI API リファレンス：[image.novelai.net/docs][nai-docs]

## 開発

このプロジェクトは Turbo がオーケストレーションする uv + pnpm モノレポです。完全なセットアップは [`CONTRIBUTING.md`][contributing] を参照してください。概要は次のとおりです。

```bash
uv sync                              # Python workspace (server + docs + dev)
pnpm install --frozen-lockfile       # Node toolchain (turbo + husky + markdownlint)

pnpm check                           # lint + typecheck + test (all workspaces)
pnpm docs:build                       # build the docs site
pnpm server:serve                     # run the MCP server
pnpm docs:serve                       # sphinx-autobuild with live reload
```

メンバー単位のコマンド（uv 経由）：

```bash
uv run --directory apps/server ruff check src tests    # lint
uv run --directory apps/server -m pyright              # typecheck
uv run --directory apps/server -m pytest               # tests
```

### Docker

```bash
docker compose up --build      # builds and runs the server (HTTP transport)
```

Dockerfile は [`apps/server/Dockerfile`][dockerfile] にありますが、ビルドコンテキストはリポジトリのルートです（uv が workspace グラフを解決できるようにするため）。[`docker-compose.yml`][docker-compose] を参照してください。

## ドキュメント

Sphinx ドキュメントサイトは Furo + MyST Markdown で構築され、`main` への push ごとに GitHub Pages へ自動デプロイされます。

- **ライブサイト**：[xinvxueyuan.github.io/NovelAI-Image-MCP][docs]
- **ソース**：[`apps/docs/source/`][docs-source]
- **ローカルでビルド**：`pnpm docs:serve`

## ライセンス

MIT — [LICENSE][license] を参照してください。ファイルごとの SPDX アノテーションは [REUSE.toml][reuse-toml] にあります。コントリビューションは [Developer Certificate of Origin][dco] の対象です（`commit-msg` フックがコミットに `Signed-off-by` を自動で付与します）。

## リンク

[ci-badge]: https://github.com/xinvxueyuan/NovelAI-Image-MCP/actions/workflows/ci.yml/badge.svg
[ci-workflow]: https://github.com/xinvxueyuan/NovelAI-Image-MCP/actions/workflows/ci.yml
[docs-badge]: https://github.com/xinvxueyuan/NovelAI-Image-MCP/actions/workflows/docs.yml/badge.svg
[mit-badge]: https://img.shields.io/badge/License-MIT-blue.svg
[python-badge]: https://img.shields.io/badge/python-3.13+-blue.svg
[uv-badge]: https://img.shields.io/badge/uv-managed-261230.svg
[reuse-badge]: https://api.reuse.software/badge/github.com/xinvxueyuan/NovelAI-Image-MCP
[deepwiki-badge]: https://img.shields.io/badge/DeepWiki-Ask%20DeepWiki-blue
[skills-badge]: https://skills.sh/b/xinvxueyuan/NovelAI-Image-MCP
[product-hunt-badge]: https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=1206099&theme=light&t=1784973837616
[lifto-badge]: https://liftoapp.com/badges/featured-light.svg

[docs]: https://xinvxueyuan.github.io/NovelAI-Image-MCP/
[reuse]: https://api.reuse.software/info/github.com/xinvxueyuan/NovelAI-Image-MCP
[python]: https://www.python.org/downloads/
[uv]: https://docs.astral.sh/uv/
[deepwiki]: https://deepwiki.com/xinvxueyuan/NovelAI-Image-MCP
[skills-sh]: https://skills.sh/xinvxueyuan/NovelAI-Image-MCP
[product-hunt]: https://www.producthunt.com/products/novelai-image-mcp?embed=true&utm_source=badge-featured&utm_medium=badge&utm_campaign=badge-novelai-image-mcp
[lifto]: https://liftoapp.com/product/novelai-image-mcp
[mcp]: https://modelcontextprotocol.io/
[contributing]: ../../CONTRIBUTING.md
[docs-source]: ../../apps/docs/source/
[skills-site]: https://skills.sh
[skills-docs]: https://xinvxueyuan.github.io/NovelAI-Image-MCP/skills.html
[tools-docs]: https://xinvxueyuan.github.io/NovelAI-Image-MCP/tools/index.html
[insiders-docs]: https://xinvxueyuan.github.io/NovelAI-Image-MCP/development/insiders-and-routing.html
[nai-docs]: https://image.novelai.net/docs/index.html
[dockerfile]: ../../apps/server/Dockerfile
[docker-compose]: ../../docker-compose.yml
[license]: ../../LICENSE
[reuse-toml]: ../../REUSE.toml
[dco]: https://developercertificate.org/

<!-- mcp-name: io.github.xinvxueyuan/novelai-image-mcp -->
