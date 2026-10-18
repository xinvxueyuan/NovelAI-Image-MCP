# `novelai_image_mcp.tools`

11 個の MCP ツール関数。各ツールは `async` で、MCP コンテンツブロックの `list`
（`Image` + テキストのパス）を返します。依存関係 — `NovelAIClient`、
`NovelAISettings`、リクエストごとのルーティングコンテキスト — は
`Depends(...)` プロバイダー（`deps.py`）として渡されるため、リクエストごとに解決され、
ツールの入力スキーマには決して現れません。

:::{admonition} 関連項目
:class: tip

各ツールのすべてのパラメータ、既定値、例を扱う解説ドキュメントは
[ツールリファレンス](../tools/index.md) を参照してください。
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

## `novelai_image_mcp.tools`（登録エントリポイント）

```{eval-rst}
.. automodule:: novelai_image_mcp.tools
   :members:
   :undoc-members:
   :show-inheritance:
```
