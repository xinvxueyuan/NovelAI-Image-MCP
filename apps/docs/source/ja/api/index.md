# API リファレンス

`novelai_image_mcp` の公開 Python API に対する autodoc 生成のリファレンスです。
各ページは
[`apps/server/src/novelai_image_mcp/`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/tree/main/apps/server/src/novelai_image_mcp)
配下のソースを直接イントロスペクトするため、常に現在の `main` ブランチを反映します。

## モジュール

```{toctree}
:maxdepth: 1
:hidden:

server
deps
mcp_auth
middleware
routing
insiders
features
prompts
resources
schemas
settings
tools
client
```

| モジュール | 説明 |
|---|---|
| [`server`](server.md) | FastMCP のコンポジションルート + ライフスパン + トランスポート選択 |
| [`deps`](deps.md) | `AppContext` と `Depends` プロバイダー |
| [`mcp_auth`](mcp_auth.md) | オプションの HTTP ベアラートークン認証（`MCP_AUTH_TOKEN`） |
| [`middleware`](middleware.md) | ツール呼び出しのログ、ルーティング監査、実験的ツールのゲート |
| [`routing`](routing.md) | ヘッダー駆動のルーティング: ルート解決とサニタイズ |
| [`insiders`](insiders.md) | `X-MCP-Insiders` オプトインヘッダーのパーサー |
| [`features`](features.md) | insiders の機能レジストリとその解決規則 |
| [`prompts`](prompts.md) | 2 つのプロンプトテンプレート |
| [`resources`](resources.md) | `novelai://...` リソース |
| [`schemas`](schemas.md) | 構造化出力モデル |
| [`settings`](settings.md) | `NovelAISettings` + `MCPServerSettings` |
| [`tools`](tools.md) | 11 個の MCP ツール関数 |
| [`nai` クライアント](client.md) | NovelAI HTTP クライアント（`NovelAIClient` + enum + モデル） |

## API を直接使う

`nai/` サブパッケージは MCP に依存しません — 単体で利用できます:

```python
import asyncio
import httpx
from novelai_image_mcp.nai import create_novelai_client, GenerationRequest, Action, Model
from novelai_image_mcp.settings import NovelAISettings

async def main():
    settings = NovelAISettings(token="pst-...")
    async with httpx.AsyncClient(timeout=settings.timeout) as http_client:
        client = create_novelai_client(settings, http_client=http_client)
        request = GenerationRequest(
            prompt="1girl, masterpiece",
            action=Action.GENERATE,
            model=Model.V4_5,
            width=832, height=1216,
        )
        images = await client.generate(request)
        await client.aclose()

asyncio.run(main())
```

## 型チェック

API は完全に型注釈されており、standard モードの `pyright` を通過します。IDE
（Pyright、Pylance、mypy）は、このドキュメントに表示されるのと同じ型情報を提示します。

## 関連項目

- [アーキテクチャ](../development/architecture.md) — モジュール同士がどう組み合わさるか
- [ツールリファレンス](../tools/index.md) — MCP ツールの解説ドキュメント
- [GitHub のソース](https://github.com/xinvxueyuan/NovelAI-Image-MCP/tree/main/apps/server/src/novelai_image_mcp)
