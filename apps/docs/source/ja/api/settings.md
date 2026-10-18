# `novelai_image_mcp.settings`

環境変数駆動の設定のための `pydantic-settings` モデル。2 つの
モデルがあります: `NovelAISettings`（認証情報 + 生成既定値、`NOVELAI_*`
環境変数）と `MCPServerSettings`（トランスポート選択、`MCP_*` 環境変数）。

:::{admonition} 関連項目
:class: tip

[設定](../configuration.md) — すべての環境変数、その既定値、効果を扱う解説リファレンス
:::

```{eval-rst}
.. automodule:: novelai_image_mcp.settings
   :members:
   :undoc-members:
   :show-inheritance:
```
