# `novelai_image_mcp.tools`

The 11 MCP tool functions. Each tool is `async` and returns a `list` of MCP
content blocks (`Image` + text path). Dependencies — the `NovelAIClient`, the
`NovelAISettings` and the per-request routing context — arrive as
`Depends(...)` providers (`deps.py`), so they are resolved per request and
never appear in the tool's input schema.

:::{admonition} See also
:class: tip

[Tools reference](../tools/index.md) for narrative docs covering every
parameter, default, and example for each tool.
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

## `novelai_image_mcp.tools` (registration entry point)

```{eval-rst}
.. automodule:: novelai_image_mcp.tools
   :members:
   :undoc-members:
   :show-inheritance:
```
