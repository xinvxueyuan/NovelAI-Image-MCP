# `novelai_image_mcp.tools`

11 个 MCP 工具函数。每个工具都是 `async` 的，并返回 MCP 内容块的 `list`
（`Image` + 文本路径）。依赖 —— `NovelAIClient`、
`NovelAISettings` 以及每请求的路由上下文 —— 以
`Depends(...)` 提供者（`deps.py`）的形式传入，因此它们按请求解析，
从不出现在工具的输入 schema 中。

:::{admonition} 参见
:class: tip

[工具参考](../tools/index.md) 中的叙述性文档，覆盖每个工具的
每个参数、默认值与示例。
:::

## `novelai_image_mcp.tools.generate`

```{eval-rst}
.. automodule:: novelai_image_mcp.tools.generate
   :members:
   :undoc-members:
   :show-inheritance:
```

## `novelai_image_mcp.tools.enhance`

```{eval-rst}
.. automodule:: novelai_image_mcp.tools.enhance
   :members:
   :undoc-members:
   :show-inheritance:
```

## `novelai_image_mcp.tools.tags`

```{eval-rst}
.. automodule:: novelai_image_mcp.tools.tags
   :members:
   :undoc-members:
   :show-inheritance:
```

## `novelai_image_mcp.tools.account`

```{eval-rst}
.. automodule:: novelai_image_mcp.tools.account
   :members:
   :undoc-members:
   :show-inheritance:
```

## `novelai_image_mcp.tools`（注册入口）

```{eval-rst}
.. automodule:: novelai_image_mcp.tools
   :members:
   :undoc-members:
   :show-inheritance:
```
