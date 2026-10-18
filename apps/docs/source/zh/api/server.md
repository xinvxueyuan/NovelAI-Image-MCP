# `novelai_image_mcp.server`

MCP 服务器的组合根。通过 MCP `lifespan` 持有共享的 `httpx.AsyncClient` 与
`NovelAIClient`，注册全部 11 个工具，并在启动时选择传输方式。

:::{admonition} 参见
:class: tip

[架构 → FastMCP 组合根](../development/architecture.md#fastmcp-组合根)
了解 lifespan 与工具如何接线在一起的叙述性说明。
:::

```{eval-rst}
.. ``AppContext`` is defined in ``deps`` and re-exported here. Documenting the
   re-export as well would make every bare ``AppContext`` cross-reference ambiguous, so
   it is excluded from this page; its reference entry lives with ``deps``.
.. automodule:: novelai_image_mcp.server
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: AppContext
   :no-value:
```
