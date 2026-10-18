# NovelAI Image MCP

```{image} ../_static/logo.svg
:alt: NovelAI Image MCP
:width: 120px
:align: center
```

一个 [MCP（模型上下文协议）][mcp] 服务器，把 **NovelAI 图像生成**
暴露为 AI 智能体可调用的工具 —— Claude Desktop、Cline、
自定义智能体以及远程客户端均可接入。

它基于 FastMCP 4（MCP SDK v2 `mcp>=2.3.0` 之上的 fastmcp 框架）构建，让智能体能够通过标准的
MCP 工具接口生成图像（txt2img / img2img / inpaint）、放大、运行 Director
工具（线稿、表情、背景移除等）、使用 ControlNet 标注、推荐标签、编码 vibe、
查询账户订阅信息等。

[mcp]: https://modelcontextprotocol.io/

---

## 特性

- **11 个 MCP 工具**，覆盖完整的 NovelAI 图像 API 接口。
- **两种传输方式**：stdio（本地智能体）与 streamable-http（远程 / 多客户端）。
- **双重返回形式**：base64 `Image` 内容块（让智能体直接 *看到* 图像）**以及**
  保存到磁盘的 PNG 文件（路径以文本形式返回）。
- **异步 + 同步**：异步工具处理器 + 一个 `typer` CLI 用于直接调用。
- **Agent 技能**：三个 [skills.sh](https://skills.sh) 包（`novelai-cli`、
  `novelai-mcp-tools`、`novelai-workflows`），教会 AI 智能体如何驱动
  CLI 与 MCP 工具。
- **uv 管理的 monorepo**，MIT 协议，Docker-ready，文档站由 GitHub Pages 托管。

---

## 入门

```{toctree}
:maxdepth: 2
:caption: 入门
:hidden:

installation
quickstart
configuration
```

```{toctree}
:maxdepth: 1
:caption: 工具参考
:hidden:

tools/index
```

```{toctree}
:maxdepth: 1
:caption: 教程
:hidden:

tutorials/index
```

```{toctree}
:maxdepth: 1
:caption: 传输方式
:hidden:

transports/index
```

```{toctree}
:maxdepth: 1
:caption: 技能
:hidden:

skills
```

```{toctree}
:maxdepth: 1
:caption: 开发
:hidden:

development/index
```

```{toctree}
:maxdepth: 1
:caption: API 参考
:hidden:

api/index
```

```{toctree}
:maxdepth: 1
:caption: 关于
:hidden:

about/license
about/changelog
about/tool-validation
```

---

## 快速链接

- [快速开始](quickstart.md) —— 安装、配置并生成你的第一张图像
- [工具参考](tools/index.md) —— 每个 MCP 工具、参数与示例
- [传输方式](transports/index.md) —— stdio 与 streamable-http
- [Agent 技能](skills.md) —— 教会 AI 智能体 CLI + MCP 工具的 skills.sh 包
- [API 参考](api/index.md) —— autodoc 生成的 Python API
- [贡献指南](development/contributing.md) —— 如何为服务器贡献代码

---

## 项目链接

- **源码**: <https://github.com/xinvxueyuan/NovelAI-Image-MCP>
- **Issues**: <https://github.com/xinvxueyuan/NovelAI-Image-MCP/issues>
- **License**: [MIT](about/license.md)
- **Changelog**: [Keep a Changelog](about/changelog.md)
- **NovelAI API 文档**: <https://image.novelai.net/docs/index.html>
