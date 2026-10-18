# HTTP トランスポート

MCP サーバーを HTTP 経由で公開します。リモートデプロイ、マルチクライアントの
シナリオ、サーバーを長時間稼働のサービスとして動かす本番環境向けに設計されています。

## 実行

```bash
MCP_TRANSPORT=http uv run python -m novelai_image_mcp serve
# or via the CLI flag:
uv run python -m novelai_image_mcp serve --transport http
```

サーバーはデフォルトで `127.0.0.1:8000/mcp` にバインドします。`MCP_HOST` /
`MCP_PORT` / `MCP_PATH` で上書きできます:

```bash
MCP_TRANSPORT=http \
MCP_HOST=0.0.0.0 \
MCP_PORT=9000 \
MCP_PATH=/mcp \
uv run python -m novelai_image_mcp serve
```

## URL

エンドポイントの完全な URL は次のとおりです:

```text
http://${MCP_HOST}:${MCP_PORT}${MCP_PATH}
```

デフォルト: <http://127.0.0.1:8000/mcp>。

## エージェントの設定

### MCP クライアント設定 (`mcpServers`)

`docker compose up --build` (または他の HTTP デプロイ) の後、MCP ホストを `http`
タイプでその URL に向けます:

```json
{
  "mcpServers": {
    "novelai-image-http": {
      "type": "http",
      "url": "http://127.0.0.1:8000/mcp",
      "headers": {
        "Authorization": "Bearer <MCP_AUTH_TOKEN>"
      }
    }
  }
}
```

`http://127.0.0.1:8000/mcp` は自前でデプロイしたエンドポイント (例: TLS 終端の
リバースプロキシの背後にある `https://mcp.example.com/mcp`) に置き換えてください。

`Authorization` ヘッダーは **NovelAI のトークンではありません**: サーバーは自身の
`NOVELAI_TOKEN` で NovelAI と通信します。このヘッダーが意味を持つのは、サーバー側で
`MCP_AUTH_TOKEN` が設定されている場合だけで、その場合は一致させる必要があります
(`Authorization: Bearer <MCP_AUTH_TOKEN>`)。`MCP_AUTH_TOKEN` (および `MCP_ROUTE_TOKENS`)
がない場合、エンドポイントは未認証のクライアントを受け付けます — TLS とリバース
プロキシの背後に置くか、`MCP_HOST` を localhost のままにしてください。

### 自作の Python エージェント

```python
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print([t.name for t in tools])

asyncio.run(main())
```

### Curl (デバッグ)

streamable-http トランスポートはサーバー → クライアントのメッセージに Server-Sent
Events を使います。サーバーを確認するための生の HTTP リクエスト:

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl","version":"1.0"}}}'
```

## Insiders ヘッダーとルーティング

opt-in ヘッダーを運べるのは HTTP だけなので、ルーティングのサーフェスはここにあります。
クライアントは `X-MCP-Insiders` でリクエストごとに opt-in し、ルーティングヘッダーで
自身のルートを宣言します:

```json
{
  "mcpServers": {
    "novelai-image-http": {
      "type": "http",
      "url": "http://127.0.0.1:8000/mcp",
      "headers": {
        "Authorization": "Bearer <MCP_AUTH_TOKEN>",
        "X-MCP-Insiders": "true",
        "X-MCP-Agent-ID": "team-a",
        "X-MCP-Model": "nai-diffusion-5-full"
      }
    }
  }
}
```

このヘッダーがあると、サーバーはルート (ここでは `team-a`) を解決し、生成画像を
`<NOVELAI_OUTPUT_DIR>/team-a/` に書き込み、`novelai_image_mcp.audit.team-a` ロガーに
1 行を出力し、監査 JSONL に 1 レコードを追記します。ヘッダーがなければ何も変わりません
— スコープ付きディレクトリも監査ファイルもありません。

この opt-in は `director_tool` の実験的な `emotion` / `emotion_level` パラメーターも
ゲートします。opt-in がない状態でどちらかを渡すと `ToolError` で失敗します。

ヘッダーの文法、候補ヘッダーの一覧、監査レコードのフィールド、秘匿化のルール、
拡張ポイントについては
[Insiders ヘッダー、ルーティング、監査](../development/insiders-and-routing.md) を参照してください。

### ルートに束縛されたトークン

`MCP_AUTH_TOKEN` は単一の静的トークンのままです。`MCP_ROUTE_TOKENS` はルートに
束縛されたトークンを追加するため、1 つのゲートウェイがチームごとに異なるシークレットを
渡せます:

```bash
MCP_AUTH_TOKEN=static-token
MCP_ROUTE_TOKENS='{"team-a":"token-for-team-a","team-b":"token-for-team-b"}'
```

ルートトークンはそのルートとして認証され、同じリクエストがルーティングヘッダーで
*異なる* ルートを宣言した場合は `401` で拒否されます。使用可能なルートを宣言しない
リクエストは受け入れられ、トークンのルートに帰属されます。fail-closed になるのは、
2 つの異なるルートが両方とも提示された場合だけです。どちらの設定もない場合、認証
ミドルウェアはインストールされず、エンドポイントは以前と同じように動作します。

## Docker デプロイ

最も単純な本番デプロイ:

```bash
docker compose up --build
```

リポジトリルートの [`docker-compose.yml`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/docker-compose.yml)
が、streamable-http トランスポートを妥当なデフォルトで構成します:

```yaml
services:
  mcp:
    build:
      context: .
      dockerfile: apps/server/Dockerfile
    ports:
      - "8000:8000"
    environment:
      MCP_TRANSPORT: streamable-http
      MCP_HOST: 0.0.0.0
      MCP_PORT: 8000
      NOVELAI_OUTPUT_DIR: /app/outputs
    volumes:
      - novelai-outputs:/app/outputs
```

ヘルスチェックはバインドポート (デフォルト `8000`) を 30 秒ごとに確認します。

## 本番チェックリスト

:::{warning}
**トランスポート自体は認証を提供しません。** `MCP_AUTH_TOKEN` (および
`MCP_ROUTE_TOKENS`) は MCP エンドポイントの手前にベアラー検証を追加しますが、
それは単一の共有シークレットであり、ID プロバイダーではありません — さらに
ルーティングヘッダーはクライアントが送るもので偽装可能です。サーバーをインターネットに
公開する前に、以下を前に置いてください:

- TLS 終端 (Caddy、nginx、Traefik、AWS ALB)
- 認証レイヤー (mTLS、OAuth プロキシ、API ゲートウェイ)
- レートリミッター (Anlas の濫用を防ぐため)
:::

:::{tip}
**ローカルでのマルチクライアント利用なら localhost にバインドします。** 同じマシン上の
複数のエージェント (例: Python と Node のエージェント) だけが必要なら、
`MCP_HOST=127.0.0.1` を設定して TLS を省略します。リバースプロキシはネットワーク境界を
越える場合にのみ使ってください。
:::

:::{admonition} 出力ディレクトリ
:class: note

Docker では `NOVELAI_OUTPUT_DIR=/app/outputs` が名前付きボリューム
(`novelai-outputs`) で裏付けられています。生成画像はコンテナの再起動をまたいで
保持されます。Kubernetes では、ボリュームを PersistentVolumeClaim に置き換えてください。
:::

## 同時実行モデル

- サーバーは単一の共有 `httpx.AsyncClient` (コネクションプール) を使います。
  複数の同時ツール呼び出しがプールを共有するため、リクエストごとの HTTP オーバーヘッドは
  ありません。
- 各 MCP リクエストはサーバーのイベントループ上の独自の asyncio タスクで実行されます。
- サーバーはリクエストをキューに入れたりレート制限したりしません — それは上流の
  プロキシの責務です。

## 関連項目

- [stdio トランスポート](stdio.md)
- [Insiders ヘッダー、ルーティング、監査](../development/insiders-and-routing.md)
- [設定](../configuration.md)
- [Docker Compose ファイル](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/docker-compose.yml)
