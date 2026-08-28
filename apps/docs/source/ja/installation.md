# インストール

NovelAI Image MCP は Python 3.13+ で動作し、[uv][uv] ≥ 0.5 で管理されます。
リポジトリは uv ワークスペース構成になっており、サーバーは `apps/server/`、
ドキュメントサイトは `apps/docs/` に配置されています。リポジトリルートに
単一の共有仮想環境が保持されます。

[uv]: https://docs.astral.sh/uv/

---

## 1. リポジトリをクローンする

```bash
git clone https://github.com/xinvxueyuan/NovelAI-Image-MCP.git
cd NovelAI-Image-MCP
```

## 2. uv をインストールする

まだ uv を導入していない場合は、以下の手順でインストールします。

=== "Unix / macOS"

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

=== "Windows (PowerShell)"

    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

=== "pip / pipx"

    ```bash
    pipx install uv
    ```

インストールを検証します。

```bash
uv --version
```

## 3. ワークスペースの仮想環境を同期する

リポジトリルートで以下を実行します。

```bash
uv sync
```

このコマンドは MCP サーバーのランタイム、Sphinx ドキュメントツールチェーン、
共有開発ツール (ruff、pyright、prek、reuse) を、リポジトリルートの単一の
`.venv/` にインストールします。初回実行時は約 60 パッケージの wheel を
ダウンロードしますが、2 回目以降は瞬時に完了します。

:::{tip}
開発用 / lint 用のグループをスキップし、サーバーを *実行* するために
必要なものだけをインストールするには、以下を実行します。

```bash
uv sync --no-dev --all-extras
```
:::

## 4. 認証情報を設定する

サンプルの環境ファイルをコピーし、NovelAI の認証情報を記入します。

```bash
cp .env.example .env
```

`.env` を編集し、2 つの認証方式のうち **いずれか一方** を設定します。

```bash
# 方式 A (推奨): https://novelai.net > Account で取得した永続 API トークン
NOVELAI_TOKEN=pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 方式 B: ユーザー名 + パスワード (アクセスキーは argon2id で導出)
# NOVELAI_USERNAME=your@email
# NOVELAI_PASSWORD=your-password
```

変数の完全なリストは [設定](configuration.md) を参照してください。

## 5. インストールを検証する

```bash
# サーバーが起動し CLI が公開されていることを確認:
uv run python -m novelai_image_mcp --help

# アカウント情報が往復し、トークンが有効であることを検証:
uv run python -m novelai_image_mcp info
```

`info` がアカウントの `tier` と Anlas 残高を含む JSON を返せば、
[最初の画像を生成](quickstart.md) する準備が整っています。

---

## 任意: Node 側のツール類

リポジトリはクロスカッティングな Node ツール (turbo タスクランナー、
husky git フック、markdownlint) にも pnpm を使用しています。コントリビュート
する予定がある場合はインストールしてください。

```bash
# corepack 経由で pnpm をインストール (Node ≥ 24):
corepack enable pnpm

# Node の依存関係をインストールし、husky フックを接続:
pnpm install --frozen-lockfile
```

このステップはランタイム利用には **任意** です — MCP サーバーは Node の
ランタイム依存関係を一切持ちません。

---

## 任意: Docker

自己完結型で再現性のあるデプロイを行うには、以下を実行します。

```bash
docker compose up --build
```

イメージは [`apps/server/Dockerfile`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/Dockerfile)
からビルドされ、デフォルトでポート `8000` 上に streamable-http トランスポート
を公開します。高度な設定については [トランスポート → streamable-http](https://xinvxueyuan.github.io/NovelAI-Image-MCP/transports/http.html)
を参照してください。

## 次のステップ

- [クイックスタート](quickstart.md) — 最初の画像を生成する
- [設定](configuration.md) — 環境変数による生成デフォルトの調整
- [Docker での運用](https://xinvxueyuan.github.io/NovelAI-Image-MCP/transports/index.html) — stdio と streamable-http の比較 (英語版)
