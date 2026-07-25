# NovelAI Image MCP

[![CI](https://github.com/xinvxueyuan/NovelAI-Image-MCP/actions/workflows/ci.yml/badge.svg)](https://github.com/xinvxueyuan/NovelAI-Image-MCP/actions/workflows/ci.yml)
[![Docs](https://github.com/xinvxueyuan/NovelAI-Image-MCP/actions/workflows/docs.yml/badge.svg)](https://xinvxueyuan.github.io/NovelAI-Image-MCP/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-managed-261230.svg)](https://docs.astral.sh/uv/)
[![REUSE status](https://api.reuse.software/badge/github.com/xinvxueyuan/NovelAI-Image-MCP)](https://api.reuse.software/info/github.com/xinvxueyuan/NovelAI-Image-MCP)

一个 [MCP（模型上下文协议）](https://modelcontextprotocol.io/) 服务端，将 **NovelAI
图像生成** 能力以工具形式暴露给 AI 智能体（Claude Desktop、Cline、自定义 Agent、
远程客户端）。

基于官方 MCP Python SDK v2（`MCPServer`）构建。智能体可通过标准 MCP 工具接口完成
生图（文生图 / 图生图 / 局部重绘）、放大、Director 工具（线稿、表情、去背景……）、
ControlNet 标注、标签建议、Vibe 编码以及账户订阅查询。

> 📖 **在线文档**：<https://xinvxueyuan.github.io/NovelAI-Image-MCP/>

## 特性

- **11 个 MCP 工具**，覆盖 NovelAI 图像 API 全部能力。
- **双传输**：stdio（本地 Agent）+ streamable-http（远程 / 多客户端）。
- **图像返回**：base64 `Image` 内容块（Agent 能“看到”图）**同时** 保存 PNG 到磁盘
  （返回路径）。
- **异步 + 同步**：异步工具处理器 + `typer` CLI 直接调用。
- **单体仓库**：uv workspace（Python）+ pnpm workspace（Node 工具链）由 Turbo 编排；
  MIT 许可，开箱即用的 Docker，GitHub Pages 文档。

## 仓库结构

这是一个 **uv + pnpm 单体仓库**：

```text
NovelAI-Image-MCP/
├── apps/
│   ├── server/                 # MCP 服务端（可发布的 PyPI 包）
│   │   ├── src/novelai_image_mcp/   # 11 个 MCP 工具 + NovelAI HTTP 客户端
│   │   ├── tests/
│   │   ├── docker/              # 烟雾测试入口
│   │   ├── Dockerfile           # 构建上下文为仓库根目录
│   │   └── pyproject.toml       # ruff / pyright / pytest 配置
│   └── docs/                    # Sphinx 文档站点
│       ├── source/              # MyST Markdown 源 + conf.py
│       ├── Makefile
│       └── pyproject.toml
├── .github/                     # workflows, CODEOWNERS, issue 模板
├── pyproject.toml               # uv workspace 根（虚拟）
├── uv.lock                      # 单一共享锁文件
├── pnpm-workspace.yaml          # pnpm workspace 声明
├── pnpm-lock.yaml               # Node 工具链锁文件
├── turbo.json                   # 跨 workspace 任务图
├── package.json                 # 根脚本 + 开发工具链
└── docker-compose.yml           # 本地容器编排
```

完整开发指南见 [`CONTRIBUTING.md`](CONTRIBUTING.md)，文档源码见
[`apps/docs/source/`](apps/docs/source/)。

## 快速开始

### 从源码安装（开发用）

```bash
# 1. 克隆
git clone https://github.com/xinvxueyuan/NovelAI-Image-MCP.git
cd NovelAI-Image-MCP

# 2. 同步 uv workspace（安装服务端 + 文档 + 开发工具）
uv sync

# 3. 配置凭证
cp .env.example .env
#   设置 NOVELAI_TOKEN=...  （推荐）
#   或   NOVELAI_USERNAME + NOVELAI_PASSWORD

# 4. 运行（stdio —— 用于本地 Agent）
uv run python -m novelai_image_mcp serve

# 5. 或通过 HTTP 运行
MCP_TRANSPORT=streamable-http uv run python -m novelai_image_mcp serve
#   → http://127.0.0.1:8000/mcp
```

### 从 PyPI 安装（仅运行时）

```bash
pip install novelai-image-mcp
export NOVELAI_TOKEN=pst-...
novelai-image-mcp serve
```

### 可选：Node 工具链（贡献者）

若要参与贡献，请通过 pnpm 安装横切 Node 工具链（turbo、husky、markdownlint）：

```bash
corepack enable pnpm      # 一次性
pnpm install --frozen-lockfile
```

该步骤会挂载 husky 的 pre-commit / commit-msg 钩子，并提供 `turbo` /
`markdownlint-cli2`。MCP 服务端 **不依赖** 任何 Node 运行时——此步骤仅面向贡献者。

## 接入 Agent（stdio）

Claude Desktop `claude_desktop_config.json`：

```jsonc
{
  "mcpServers": {
    "novelai-image": {
      "command": "uv",
      "args": ["run", "--directory", "C:/dev/NovelAI-Image-MCP",
               "python", "-m", "novelai_image_mcp", "serve"],
      "env": { "NOVELAI_TOKEN": "pst-..." }
    }
  }
}
```

## CLI（同步，用于脚本）

```bash
uv run python -m novelai_image_mcp generate --prompt "a cat, masterpiece" --width 832 --height 1216
uv run python -m novelai_image_mcp upscale --image ./in.png --factor 4
uv run python -m novelai_image_mcp info          # 订阅 / Anlas 余额
uv run python -m novelai_image_mcp --help
```

## 工具列表

| 工具 | 说明 |
|---|---|
| `generate_image` | 文生图（V3 / V4 / V4.5 模型，角色提示，Vibe） |
| `image_to_image` | 图生图（strength / noise） |
| `inpaint` | 局部重绘（需 inpaint 模型 + mask） |
| `upscale_image` | 2× / 4× 放大 |
| `director_tool` | 线稿 / 草图 / 去背景 / 去杂物 / 上色 / 表情 |
| `annotate_image` | ControlNet 标注（hed, midas, scribble, mlsd, uniformer） |
| `suggest_tags` | 标签建议 |
| `encode_vibe` | 将参考图编码为 vibe token |
| `get_subscription` | 账户订阅 + Anlas 余额 |
| `get_user_data` | 账户信息 |
| `estimate_anlas_cost` | 估算生图 Anlas 消耗（不调用 API） |

工具参数与示例见文档站
[工具参考](https://xinvxueyuan.github.io/NovelAI-Image-MCP/tools/index.html)。

## 配置

全部通过环境变量配置（见 `.env.example`）。关键项：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `NOVELAI_TOKEN` | — | 持久 API token（推荐认证方式） |
| `NOVELAI_USERNAME` / `NOVELAI_PASSWORD` | — | access-key 登录（argon2id） |
| `NOVELAI_OUTPUT_DIR` | `outputs` | 生成 PNG 的保存目录 |
| `MCP_TRANSPORT` | `stdio` | `stdio` 或 `streamable-http` |
| `MCP_HOST` / `MCP_PORT` | `127.0.0.1` / `8000` | streamable-http 用 |

NovelAI API 文档：<https://image.novelai.net/docs/index.html>

## 开发

本项目为 uv + pnpm 单体仓库，由 Turbo 编排。完整设置见
[`CONTRIBUTING.md`](CONTRIBUTING.md)，简版如下：

```bash
uv sync                              # Python workspace（server + docs + dev）
pnpm install --frozen-lockfile       # Node 工具链（turbo + husky + markdownlint）

pnpm check                           # 全 workspace 的 lint + typecheck + test
pnpm docs:build                       # 构建文档站点
pnpm server:serve                     # 运行 MCP 服务端
pnpm docs:serve                       # sphinx-autobuild 实时预览
```

单成员命令（通过 uv）：

```bash
uv run --directory apps/server ruff check src tests    # lint
uv run --directory apps/server -m pyright              # 类型检查
uv run --directory apps/server -m pytest               # 测试
```

### Docker

```bash
docker compose up --build      # 构建并运行服务端（HTTP 传输）
```

Dockerfile 位于 [`apps/server/Dockerfile`](apps/server/Dockerfile)，但构建上下文为
仓库根目录（这样 uv 能解析 workspace 图）。详见
[`docker-compose.yml`](docker-compose.yml)。

## 文档

Sphinx 文档站点使用 Furo + MyST Markdown 构建，每次推送到 `main` 时自动部署到
GitHub Pages：

- **在线站点**：<https://xinvxueyuan.github.io/NovelAI-Image-MCP/>
- **源码**：[`apps/docs/source/`](apps/docs/source/)
- **本地构建**：`pnpm docs:serve`

## 许可证

MIT —— 见 [LICENSE](LICENSE)。逐文件 SPDX 标注见
[REUSE.toml](REUSE.toml)。提交即表示你同意
[Developer Certificate of Origin](https://developercertificate.org/)（`commit-msg`
钩子会自动添加 `Signed-off-by`）。
