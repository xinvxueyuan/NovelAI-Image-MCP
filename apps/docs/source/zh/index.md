# NovelAI Image MCP

```{image} ../_static/logo.svg
:alt: NovelAI Image MCP
:width: 120px
:align: center
```

一个 [MCP（模型上下文协议）][mcp] 服务器，把 **NovelAI 图像生成** 暴露为 AI
智能体可调用的工具 —— Claude Desktop、Cline、自定义智能体以及远程客户端均可接入。

它基于 FastMCP 4（MCP SDK v2 `mcp>=2.0.0` 之上的 fastmcp 框架）构建，让智能体能够通过标准的
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

---

## 快速链接

- [快速开始](quickstart.md) —— 安装、配置并生成你的第一张图像
- [安装指南](installation.md) —— 从克隆仓库到验证凭据
- [配置参考](configuration.md) —— 环境变量与默认值

---

## 项目链接

- **源码**: <https://github.com/xinvxueyuan/NovelAI-Image-MCP>
- **Issues**: <https://github.com/xinvxueyuan/NovelAI-Image-MCP/issues>
- **License**: [MIT](https://xinvxueyuan.github.io/NovelAI-Image-MCP/about/license.html)
- **Changelog**: [Keep a Changelog](https://xinvxueyuan.github.io/NovelAI-Image-MCP/about/changelog.html)
- **NovelAI API 文档**: <https://image.novelai.net/docs/index.html>

---

## 其他章节（英文）

工具参考、教程、传输方式、开发指南、API 参考等章节目前仅提供英文版本，点击直达：

- [工具参考](https://xinvxueyuan.github.io/NovelAI-Image-MCP/tools/index.html) —— 全部 11 个 MCP 工具的参数与示例
- [教程](https://xinvxueyuan.github.io/NovelAI-Image-MCP/tutorials/index.html) —— 端到端工作流（txt2img、img2img、inpaint 等）
- [传输方式](https://xinvxueyuan.github.io/NovelAI-Image-MCP/transports/index.html) —— stdio 与 streamable-http 对比
- [Agent 技能](https://xinvxueyuan.github.io/NovelAI-Image-MCP/skills.html) —— 让 AI 智能体学会 CLI 与 MCP 工具
- [开发指南](https://xinvxueyuan.github.io/NovelAI-Image-MCP/development/index.html) —— 架构、贡献、测试与发布
- [API 参考](https://xinvxueyuan.github.io/NovelAI-Image-MCP/api/index.html) —— autodoc 生成的 Python API
- [许可证 / 更新日志 / 工具验证](https://xinvxueyuan.github.io/NovelAI-Image-MCP/about/license.html)
