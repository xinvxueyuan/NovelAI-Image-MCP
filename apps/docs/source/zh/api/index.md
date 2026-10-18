# API 参考

由 autodoc 生成的 `novelai_image_mcp` 公开 Python API 参考。这些页面通过
内省仓库源码
[`apps/server/src/novelai_image_mcp/`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/tree/main/apps/server/src/novelai_image_mcp)
生成，因此始终反映当前 `main` 分支的状态。

## 模块

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

| 模块 | 说明 |
|---|---|
| [`server`](server.md) | FastMCP 组合根 + lifespan + 传输方式选择 |
| [`deps`](deps.md) | `AppContext` 与 `Depends` 提供者 |
| [`mcp_auth`](mcp_auth.md) | 可选的 HTTP bearer-token 认证（`MCP_AUTH_TOKEN`） |
| [`middleware`](middleware.md) | 工具调用日志、分路审计与实验性工具门控 |
| [`routing`](routing.md) | 头驱动的路由：route 解析与净化 |
| [`insiders`](insiders.md) | `X-MCP-Insiders` opt-in 头解析器 |
| [`features`](features.md) | insiders 特性注册表及其解析规则 |
| [`prompts`](prompts.md) | 两个 prompt 模板 |
| [`resources`](resources.md) | `novelai://...` 资源 |
| [`schemas`](schemas.md) | 结构化输出模型 |
| [`settings`](settings.md) | `NovelAISettings` + `MCPServerSettings` |
| [`tools`](tools.md) | 11 个 MCP 工具函数 |
| [`nai` 客户端](client.md) | NovelAI HTTP 客户端（`NovelAIClient` + 枚举 + 模型） |

## 直接使用 API

`nai/` 子包与 MCP 无关 —— 你可以独立使用它：

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

## 类型检查

该 API 带有完整的类型注解，并在标准模式下通过 `pyright` 检查。IDE
（Pyright、Pylance、mypy）会给出与这些文档中相同的类型信息。

## 参见

- [架构](../development/architecture.md) —— 各模块如何组合在一起
- [工具参考](../tools/index.md) —— MCP 工具的叙述性文档
- [GitHub 源码](https://github.com/xinvxueyuan/NovelAI-Image-MCP/tree/main/apps/server/src/novelai_image_mcp)
