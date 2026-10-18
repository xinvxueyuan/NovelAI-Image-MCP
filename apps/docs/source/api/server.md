# `novelai_image_mcp.server`

The MCP server composition root. Owns the shared `httpx.AsyncClient` and
`NovelAIClient` via an MCP `lifespan`, registers all 11 tools, and selects
the transport at startup.

:::{admonition} See also
:class: tip

[Architecture → FastMCP composition root](../development/architecture.md#fastmcp-composition-root)
for a narrative walkthrough of how the lifespan + tools wire together.
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
