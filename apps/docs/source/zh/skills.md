# Agent 技能

NovelAI Image MCP 可以用三种互补的方式驱动。三者封装的是同一个异步
`NovelAIClient` —— 区别只在于你如何调用它。

| 方式 | 最适合 | 智能体可见 | 并发 |
|---|---|---|---|
| **MCP 工具** —— [工具参考](tools/index.md) | 交互式智能体会话（Claude Desktop、Cline……） | 是 —— base64 `Image` 内容块 | 每种传输方式单客户端 |
| **CLI** —— `novelai-image-mcp generate …` | Shell 脚本、CI 任务、一次性命令 | 否 —— 把 PNG 存到磁盘并打印路径 | 每次调用一个进程 |
| **Agent 技能** —— 本页 | 教 AI 智能体*如何*使用 CLI 或 MCP 工具的可移植指令 | 继承底层方式 | 继承底层方式 |

Agent 技能是 [skills.sh][skills-sh] 包 —— 一种 markdown 指令文件，AI 智能体
（Claude Code、Codex、GitHub Copilot、Cursor……）在运行时读取它来学习项目特有的
工作流。它们不取代 CLI 或 MCP 工具；它们*指导*智能体在何时、如何用它们。

[skills-sh]: https://skills.sh

---

## 安装技能

```bash
# Install all three skills globally (Claude Code, Codex, Copilot, …)
npx skills add --yes --global xinvxueyuan/NovelAI-Image-MCP
```

`--yes` 标志跳过交互式选择提示；`--global` 安装到 `~/.agents/skills/`，
这样你机器上的每个项目都能受益。省略 `--global` 则改为安装到当前项目的
`.agents/skills/`。

验证安装：

```bash
ls ~/.agents/skills/
# novelai-cli  novelai-mcp-tools  novelai-workflows
```

---

## 三个技能

### novelai-cli

**分组**：CLI

Typer CLI 的 shell 层用法 —— `serve`、`generate`、`upscale`、`director`、
`annotate`、`info`。涵盖安装（`pip install` / `uvx`）、凭据配置与输出行为。
适合在 MCP 宿主之外编写图像工作流脚本，或批量生成图像时使用。

### novelai-mcp-tools

**分组**：MCP Tools

服务器暴露的 11 个 MCP 工具的参考。涵盖模型选择（V3 / V4 / V4.5 / Furry）、
参数调优（steps、scale、sampler、seed）、`ImageContent` 返回形态，以及 Anlas
成本意识。适合通过 MCP 宿主（而非 CLI）生成或变换图像时使用。

### novelai-workflows

**分组**：Workflows

把多个工具串起来的端到端创作流水线：txt2img → upscale、annotate → img2img、
Director 编辑，以及完整的生产流程。适合被要求构建多步骤图像工作流配方或流水线
时使用。

---

## 什么时候用哪一个

```{mermaid}
graph TD
    Q{How will you use NovelAI?}
    Q -->|"Interactive session with Claude Desktop / Cline"| A[MCP tools<br/>see Tools reference]
    Q -->|"Shell script, CI job, one-off command"| B[CLI<br/>novelai-image-mcp generate …]
    Q -->|"Want an AI agent to drive either of the above"| C[Agent skills<br/>npx skills add …]
    C -->|"Agent picks CLI or MCP based on context"| A
    C --> B
```

技能与 CLI/MCP 工具**不是二选一**：

- **CLI + 技能**：安装 `novelai-cli` 技能，让你的 AI 编码智能体
  （Claude Code、Codex……）无需你粘贴文档就知道 CLI 命令。
- **MCP + 技能**：安装 `novelai-mcp-tools` 技能，让你的智能体理解 11 个 MCP
  工具的参数与模型选择经验。
- **工作流**：安装 `novelai-workflows`，让你的智能体能把工具串成多步骤流水线
  （txt2img → upscale → Director 编辑……）。

三个都可以装 —— 它们按需分发指导，彼此不重复核心内容。

---

## 另请参见

- [工具参考](tools/index.md) —— 11 个 MCP 工具、参数与示例
- [教程](tutorials/index.md) —— 端到端工作流
- [传输方式](transports/index.md) —— stdio 与 streamable-http
- [skills.sh 页面](https://skills.sh/xinvxueyuan/NovelAI-Image-MCP) —— 安装 / 安全性评估
- [智能体宿主配置](transports/agent-hosts.md) —— Claude Desktop、Cline、Cursor……
