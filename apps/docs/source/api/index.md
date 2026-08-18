# API reference

Autodoc-generated reference for the public Python API of
`novelai_image_mcp`. These pages introspect the in-tree source under
[`apps/server/src/novelai_image_mcp/`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/tree/main/apps/server/src/novelai_image_mcp),
so they always reflect the current `main` branch.

## Modules

```{toctree}
:maxdepth: 1
:hidden:

server
settings
tools
client
```

| Module | Description |
|---|---|
| [`server`](server.md) | FastMCP composition root + lifespan |
| [`settings`](settings.md) | `NovelAISettings` + `MCPServerSettings` |
| [`tools`](tools.md) | The 11 MCP tool functions |
| [`nai` client](client.md) | The NovelAI HTTP client (`NovelAIClient` + enums + models) |

## Using the API directly

The `nai/` subpackage is MCP-agnostic — you can use it standalone:

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

## Type checking

The API is fully type-annotated and passes `pyright` in standard mode. IDEs
(Pyright, Pylance, mypy) will surface the same type information you see in
these docs.

## See also

- [Architecture](../development/architecture.md) — how the modules fit together
- [Tools reference](../tools/index.md) — narrative docs for the MCP tools
- [Source on GitHub](https://github.com/xinvxueyuan/NovelAI-Image-MCP/tree/main/apps/server/src/novelai_image_mcp)
