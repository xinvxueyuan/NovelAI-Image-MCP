# 传输方式

MCP 服务器支持两种传输方式。请按你打算如何使用它来选择。

| 传输方式 | 使用场景 | 成本 | 并发 |
|---|---|---|---|
| [stdio](stdio.md) | 本地智能体集成（Claude Desktop、Cline） | 最低 —— 没有网络开销 | 单客户端 |
| [streamable-http](http.md) | 远程 / 多客户端 / 生产部署 | 略高（HTTP 分帧） | 多客户端 |

## 快速选择指南

```{mermaid}
graph TD
    Q{How will you use the server?}
    Q -->|Local agent on the same machine| A[stdio]
    Q -->|Remote / multi-client / production| B[streamable-http]
    Q -->|Scripting — direct CLI use| C[CLI: novelai-image-mcp generate<br/>uv run python -m ...]
    Q -->|Portable agent instructions| D[Agent skills<br/>npx skills add …]
```

技能不是传输方式 —— 它们是 [skills.sh](https://skills.sh) 包，用来教 AI 智能体
*如何*使用 CLI 或 MCP 工具。当你希望自己的编码智能体（Claude Code、Codex、
Copilot……）无需人工提示就了解本项目的命令与参数时，就安装它们。详见
[Agent 技能](../skills.md)。

## 与传输方式无关的设计

服务器的 `lifespan` 持有一个共享的 `httpx.AsyncClient`（连接池）和一个
`NovelAIClient`。每个工具都从请求上下文的 lifespan 状态中读取它们 ——
工具代码与工具签名都不随传输方式变化。

传输方式在服务器启动时通过 `MCP_TRANSPORT`（或 CLI 的 `--transport` 标志）
选定：

```bash
# stdio (default)
MCP_TRANSPORT=stdio uv run python -m novelai_image_mcp serve

# streamable-http
MCP_TRANSPORT=streamable-http uv run python -m novelai_image_mcp serve
```

`MCP_*` 变量的完整清单见 [配置](../configuration.md#mcp-传输方式)。

```{toctree}
:maxdepth: 1
:hidden:

stdio
http
agent-hosts
```
