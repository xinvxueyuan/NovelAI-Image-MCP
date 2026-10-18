# `novelai_image_mcp.server`

MCP サーバーのコンポジションルート。MCP の `lifespan` を通じて共有の `httpx.AsyncClient` と
`NovelAIClient` を所有し、11 個すべてのツールを登録し、起動時にトランスポートを選択します。

:::{admonition} 関連項目
:class: tip

[アーキテクチャ → FastMCP コンポジションルート](../development/architecture.md#fastmcp-コンポジションルート)
— ライフスパンとツールがどう配線されるかの解説
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
