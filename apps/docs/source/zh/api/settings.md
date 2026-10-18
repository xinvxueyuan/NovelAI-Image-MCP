# `novelai_image_mcp.settings`

用于环境变量驱动配置的 `pydantic-settings` 模型。共两个模型：`NovelAISettings`
（凭据 + 生成默认值，`NOVELAI_*` 环境变量）与 `MCPServerSettings`
（传输方式选择，`MCP_*` 环境变量）。

:::{admonition} 参见
:class: tip

[配置](../configuration.md) 中的叙述性参考，覆盖了每个环境变量、其默认值
以及作用。
:::

```{eval-rst}
.. automodule:: novelai_image_mcp.settings
   :members:
   :undoc-members:
   :show-inheritance:
```
