# `middleware`

`ToolCallLoggingMiddleware` — logs every tool call with its duration, appends a per-route audit
record while model routing is active, and gates the experimental tool surface. It never alters the
result and never swallows an exception.

:::{admonition} See also
:class: tip

[Architecture](../development/architecture.md)
:::

```{eval-rst}
.. automodule:: novelai_image_mcp.middleware
   :members:
   :undoc-members:
   :show-inheritance:
```
