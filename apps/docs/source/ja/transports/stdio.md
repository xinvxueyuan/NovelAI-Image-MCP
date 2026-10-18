# stdio トランスポート

デフォルトで最も一般的なトランスポートです。サーバーは stdin から JSON-RPC メッセージを
読み取り、stdout にレスポンスを書き込みます。ローカルの MCP ホスト (Claude Desktop、
Cline、自作エージェント) との密接な統合のために設計されています。

## 実行

```bash
uv run python -m novelai_image_mcp serve
# or explicitly:
MCP_TRANSPORT=stdio uv run python -m novelai_image_mcp serve
```

サーバーはフォアグラウンドで動作します。終了するには `Ctrl+C` を押します。

## エージェントの設定

### Claude Desktop

`claude_desktop_config.json` を編集します:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

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

`${input:novelai_token}` はホストが管理するシークレットに解決されます。単発のテストでは、
代わりにリテラルのトークン (`"pst-..."`) を直接書いてください。

#### 省略形: uvx (インストール済みパッケージ)

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

ホストのシェルで `NOVELAI_TOKEN` を設定してください — `uvx` は親の環境を継承します。

Claude Desktop を再起動します。11 個のツールを持つ `novelai-image` MCP サーバーが
登録されているはずです。

### Cline (VS Code)

`cline_mcp_settings.json` に追加します:

```json
{
  "mcpServers": {
    "novelai-image": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run", "--directory", "/path/to/NovelAI-Image-MCP",
        "python", "-m", "novelai_image_mcp", "serve"
      ],
      "env": { "NOVELAI_TOKEN": "pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### 自作の Python エージェント

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(
        command="uv",
        args=["run", "--directory", "/path/to/NovelAI-Image-MCP",
              "python", "-m", "novelai_image_mcp", "serve"],
        env={"NOVELAI_TOKEN": "pst-..."},
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print([t.name for t in tools])

asyncio.run(main())
```

## なぜ stdio なのか

- **ネットワークのオーバーヘッドなし** — TCP ハンドシェイクも HTTP フレーミングもありません。
- **ポート競合なし** — サーバーは何もバインドしません。
- **プロセスのライフサイクルが自動** — プロセスはエージェントが所有し、エージェントが
  終了するとサーバーも終了します。
- **Stdin/stdout** は MCP SDK 全体で広くサポートされています。

## 制限

- **単一クライアントのみ。** 2 つのエージェントが 1 つの stdio サーバーを共有することは
  できません。
- **サーバーの stderr は** エージェントによってログとして取り込まれます。診断には
  `logging` (stderr 向けに設定) を使ってください。stdout に出力してはいけません
  (JSON-RPC ストリームが壊れます)。

## ログ

MCP ランタイムはすべてのログを **stderr** に書き込みます。別のターミナルで確認するには:

```bash
uv run python -m novelai_image_mcp serve 2>server.log
```

ログをエージェント側に転送する場合 (例: Claude Desktop の「MCP logs」パネル) は、
MCP SDK のドキュメントに従ってランタイムのログハンドラーを設定してください。

## 関連項目

- [streamable-http トランスポート](http.md)
- [設定](../configuration.md)
- [クイックスタート](../quickstart.md)
