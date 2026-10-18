# 许可证

NovelAI Image MCP 以 **MIT 许可证** 授权 —— 完整文本见
[`LICENSE`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/LICENSE)。

## 逐文件 SPDX 注解

除了权威的 `LICENSE` 文件之外，每个源文件都带有通过
[`REUSE.toml`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/REUSE.toml)
声明的 SPDX `copyright` / `license` 头。
按文件类型划分的许可证是：

| 文件类型 | 许可证 |
|---|---|
| 软件代码（`*.py`、`conf.py`） | MIT |
| 文档（`*.md`、`*.mdx`） | MIT |
| 视觉元素（`*.png`、`*.svg`、`*.jpg` 等） | CC0-1.0 |
| 基础设施 / 配置（`*.toml`、`*.yml`、`*.json`、`Dockerfile` 等） | CC0-1.0 |
| 构建产物（`*.pyc`、`node_modules/`、缓存） | CC0-1.0 |

CC0-1.0（公有领域奉献）用于非创作性内容
（配置、基础设施、生成产物），因此它们对下游用户
不施加任何署名要求。

## 验证合规

本仓库符合 [REUSE 3.0](https://reuse.software/)。运行：

```bash
uv run reuse lint
```

CI 工作流会在每次 PR 上运行同一项检查。

## 第三方许可证

本项目依赖：

| 依赖 | 许可证 |
|---|---|
| [mcp](https://pypi.org/project/mcp/) | MIT |
| [httpx](https://www.python-httpx.org/) | BSD-3-Clause |
| [pydantic](https://docs.pydantic.dev/) | MIT |
| [pydantic-settings](https://docs.pydantic.dev/latest/usage/settings/) | MIT |
| [typer](https://typer.tiangolo.com/) | MIT |
| [argon2-cffi](https://argon2-cffi.readthedocs.io/) | MIT |
| [msgpack](https://msgpack-python.readthedocs.io/) | Apache-2.0 |
| [Sphinx](https://www.sphinx-doc.org/) | BSD-2-Clause |
| [Furo](https://pradyunsg.me/furo/) | MIT |
| [MyST Parser](https://myst-parser.readthedocs.io/) | MIT |

运行 `uv tree` 查看完整依赖树，包括传递
依赖。

## 参见

- [完整许可证文本](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/LICENSE)
- [REUSE.toml](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/REUSE.toml)
- [FSFE REUSE 规范](https://reuse.software/spec/)
