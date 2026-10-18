# `middleware`

`ToolCallLoggingMiddleware` —— 记录每次工具调用及其耗时，在 model routing 生效期间追加一条
按路由区分的审计记录，并对实验性工具面进行门控。它从不改变返回值，也从不吞掉异常。

:::{admonition} 参见
:class: tip

[架构](../development/architecture.md)
:::

```{eval-rst}
.. automodule:: novelai_image_mcp.middleware
   :members:
   :undoc-members:
   :show-inheritance:
```
