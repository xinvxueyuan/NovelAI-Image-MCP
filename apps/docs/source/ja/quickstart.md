# クイックスタート

このページでは、サーバーのインストール、認証情報の設定、5 分以内に最初の
画像を生成するまでの手順を説明します。

:::{note}
このガイドは、すでに [インストール](installation.md) を完了していることを
前提としています。
:::

---

## 1. サーバーを起動する (stdio)

デフォルトのトランスポートは **stdio** です — Claude Desktop や Cline のような
ローカルエージェント向けです。フォアグラウンドプロセスとして実行します。

```bash
uv run python -m novelai_image_mcp serve
```

サーバーは stdin から読み取り、JSON-RPC レスポンスを stdout に書き出します。
クライアントが接続するまで何も表示されません。終了するには `Ctrl+C` を
押してください。

## 2. 画像を生成する (CLI)

MCP ホストを立ち上げずに手軽に試すには、同期の `typer` CLI を使用します。

```bash
uv run python -m novelai_image_mcp generate \
  --prompt "a cat sitting on a windowsill, masterpiece, best quality" \
  --width 832 \
  --height 1216
```

CLI は保存された PNG のパスを出力します。

```text
outputs/generate-YYYYMMDD-HHMMSS-NNN.png
```

ファイルを開くと、生成された猫の画像が表示されます。

## 3. HTTP 経由で生成する

サーバーを HTTP 経由でリモートクライアントに公開するには、以下を実行します。

```bash
MCP_TRANSPORT=streamable-http uv run python -m novelai_image_mcp serve
```

サーバーはデフォルトで <http://127.0.0.1:8000/mcp> でリッスンします。
ホストとポートは `MCP_HOST` / `MCP_PORT` で上書きできます。

## 4. Claude Desktop を接続する

`claude_desktop_config.json` を編集します (macOS: `~/Library/Application Support/Claude/`、Windows: `%APPDATA%\Claude\`)。

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

`${input:novelai_token}` はホスト側で定義されたシークレット参照です —
お使いの MCP ホストのシークレット UI (Claude Desktop、Cline など) を
参照してください。1 回限りのテストでは、リテラルトークンを直接記述する
こともできます。

### 代替案: uvx (公開パッケージ)

PyPI からインストールした場合、以下の省略記法が使えます。

```json
{
  "mcpServers": {
    "novelai-image": {
      "command": "uvx",
      "args": ["--prerelease=allow", "novelai-image-mcp", "serve"],
      "env": { "NOVELAI_TOKEN": "pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" }
    }
  }
}
```

ホストのシェルで `NOVELAI_TOKEN` を設定してください — `uvx` は親環境を
引き継ぎます。

### 代替案: http (リモート / Docker)

サーバーを別の場所で実行している場合 (例: リモートホスト上で
`docker compose up`)、ホストから URL に直接アクセスします。

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

`http://127.0.0.1:8000/mcp` は、ご自身でデプロイしたエンドポイント
(例: TLS 終端リバースプロキシ背後の `https://mcp.example.com/mcp`) に
置き換えてください。

Claude Desktop を再起動すると、11 個のツールを備えた `novelai-image`
MCP サーバーが登録されます。Claude に *「水彩画でキツネを描いて」* と
頼んでみて、`generate_image` が呼び出される様子を観察してください。

その他のエージェントホスト (Cline、Cursor、Continue、Windsurf、Codex CLI)
については、[エージェントホスト](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/docs/source/transports/agent-hosts.md)
(英語版) を参照してください。

## 5. アカウント残高を確認する

長時間の生成セッションの前に、Anlas 残高を確認しましょう。

```bash
uv run python -m novelai_image_mcp info
```

```json
{
  "tier": 3,
  "active": true,
  "trainingStepsLeft": { "fixed": 10000, "perStepUsage": false },
  "subscriptionId": "..."
}
```

または、エージェントから `get_subscription` MCP ツールを呼び出します。

---

## 次のよくあるステップ

- 📚 各パラメータの詳細は [ツールリファレンス](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/docs/source/tools/index.md) (英語版) を参照
- 🎨 [チュートリアル](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/docs/source/tutorials/index.md) (英語版) を試す — img2img、inpaint、アップスケール、ControlNet
- 🔧 環境変数で [生成デフォルト](configuration.md) を調整する
- 🐳 本番運用向けに [Docker 化](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/docs/source/transports/http.md) する (英語版)

## トラブルシューティング

:::{admonition} 認証エラー
:class: warning

以下のようなエラーが表示された場合:

```text
RuntimeError: NovelAI credentials are not configured: set NOVELAI_TOKEN or
NOVELAI_USERNAME + NOVELAI_PASSWORD (see .env.example).
```

`.env` ファイルが存在し、`pst-` で始まる有効な `NOVELAI_TOKEN` が含まれて
いることを確認してください。`info` サブコマンドは、Anlas を消費せずに
認証を検証する最も手軽な方法です。
:::

:::{admonition} 初回実行が遅い
:class: tip

初回の `uv sync` は約 60 個の wheel をダウンロードします。2 回目以降は
キャッシュを再利用し、数秒で完了します。企業プロキシ環境下の場合は、
`UV_HTTP_TIMEOUT=300` (秒) を設定して、遅いネットワークでのタイムアウトを
回避してください。
:::

:::{admonition} 画像が保存されない
:class: warning

`NOVELAI_OUTPUT_DIR` (デフォルト: `outputs`) を確認してください。ディレクトリは
サーバーを実行するユーザーが書き込み可能である必要があります。Docker の場合、
ディレクトリは `/app/outputs` で、名前付きボリューム (`novelai-outputs`) に
裏打ちされています。
:::
