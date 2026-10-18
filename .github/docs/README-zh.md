# NovelAI Image MCP

## 语言

| English | 简体中文 | 日本語 |
|---|---|---|
| [English](../../README.md) | [简体中文](README-zh.md) | [日本語](README-ja.md) |

[![CI][ci-badge]][ci-workflow]
[![Docs][docs-badge]][docs]
[![License: MIT][mit-badge]][license]
[![Python 3.13+][python-badge]][python]
[![uv][uv-badge]][uv]
[![REUSE status][reuse-badge]][reuse]
[![DeepWiki][deepwiki-badge]][deepwiki]
[![skills.sh][skills-badge]][skills-sh]

[![NovelAI Image MCP - MCP server for integrating NovelAI Image generation into AI | Product Hunt][product-hunt-badge]][product-hunt] [![Featured on Lifto][lifto-badge]][lifto]

一个 [MCP（模型上下文协议）][mcp] 服务端，将 **NovelAI
图像生成** 能力以工具形式暴露给 AI 智能体（Claude Desktop、Cline、自定义 Agent、
远程客户端）。

基于 FastMCP 4（MCP SDK v2 `mcp>=2.3.0` 之上的 fastmcp 框架）构建。智能体可通过标准 MCP 工具接口完成
生图（文生图 / 图生图 / 局部重绘）、放大、Director 工具（线稿、表情、去背景……）、
ControlNet 标注、标签建议、Vibe 编码以及账户订阅查询。

> 📖 **在线文档**：[xinvxueyuan.github.io/NovelAI-Image-MCP][docs]

## 特性

- **11 个 MCP 工具**，覆盖 NovelAI 图像 API 全部能力。
- **2 个 prompt + 3 个资源 + 1 个资源模板**：`novelai_prompt_writer` / `novelai_image_workflow`
  提供提示词与工具编排范本；`novelai://models`、`novelai://samplers`、
  `novelai://defaults`、`novelai://outputs/{name}` 暴露模型与采样器词表、当前默认值，
  并可回读已生成的 PNG。
- **双传输**：stdio（本地 Agent）+ HTTP（远程 / 多客户端），HTTP 支持可选
  Bearer Token（`MCP_AUTH_TOKEN`）。
- **可选的路由与审计（HTTP）**：客户端发送 `X-MCP-Insiders` 后，可获得按路由划分的
  输出目录、按路由命名的 logger，以及 append-only 的 JSONL 审计流水（prompt 与凭证
  绝不落原文）。不发送该头时行为完全不变。详见[内测头、路由与审计][insiders-docs]。
- **结构化结果**：枚举校验的工具 schema、MCP 工具注解、预期失败统一抛 `ToolError`。
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
│   ├── server/                 # MCP server (the installable PyPI package)
│   │   ├── src/novelai_image_mcp/   # 11 MCP tools + NovelAI HTTP client
│   │   ├── tests/
│   │   ├── docker/              # smoke-test entrypoint
│   │   ├── Dockerfile           # built with repo root as context
│   │   └── pyproject.toml       # ruff / pyright / pytest config
│   └── docs/                    # Sphinx documentation site
│       ├── source/              # MyST Markdown + conf.py
│       ├── Makefile
│       └── pyproject.toml
├── .github/                     # workflows, CODEOWNERS, issue templates
├── pyproject.toml               # uv workspace root (virtual)
├── uv.lock                      # single shared lockfile
├── pnpm-workspace.yaml          # pnpm workspace declaration
├── pnpm-lock.yaml               # Node toolchain lockfile
├── turbo.json                   # cross-workspace task graph
├── package.json                 # root scripts + dev toolchain
└── docker-compose.yml           # local container orchestration
```

完整开发指南见 [`CONTRIBUTING.md`][contributing]，文档源码见
[`apps/docs/source/`][docs-source]。

## 快速开始

### 从源码安装（开发用）

```bash
# 1. Clone
git clone https://github.com/xinvxueyuan/NovelAI-Image-MCP.git
cd NovelAI-Image-MCP

# 2. Sync the uv workspace (installs server + docs + dev tools)
uv sync

# 3. Configure credentials
cp .env.example .env
#   set NOVELAI_TOKEN=...  (preferred)
#   or  NOVELAI_USERNAME + NOVELAI_PASSWORD

# 4. Run (stdio — for local agents)
uv run python -m novelai_image_mcp serve

# 5. Or over HTTP
MCP_TRANSPORT=http uv run python -m novelai_image_mcp serve
#   → http://127.0.0.1:8000/mcp
```

### 从 PyPI 安装（仅运行时）

```bash
pip install novelai-image-mcp
export NOVELAI_TOKEN=pst-...
novelai-image-mcp serve
```

### 标准 FastMCP 入口

仓库自带 [`fastmcp.json`](../../fastmcp.json)（source 指向 `apps/server/mcp_server.py`），
因此可以直接使用 FastMCP 官方命令（在仓库根执行，先 `uv sync`）：

```bash
uv run fastmcp run fastmcp.json                     # stdio server
uv run fastmcp inspect                              # list tools/prompts/resources
uv run --directory apps/server fastmcp dev inspector mcp_server.py   # Inspector
```

`fastmcp.json` 有意不写 `environment` 块：workspace 虚拟环境里已安装本包，
写了反而会让 FastMCP 每次额外建一个临时环境。

### 可选：Node 工具链（贡献者）

若要参与贡献，请通过 pnpm 安装横切 Node 工具链（turbo、husky、markdownlint）：

```bash
corepack enable pnpm      # one-time
pnpm install --frozen-lockfile
```

该步骤会挂载 husky 的 pre-commit / commit-msg 钩子，并提供 `turbo` /
`markdownlint-cli2`。MCP 服务端 **不依赖** 任何 Node 运行时——此步骤仅面向贡献者。

## 接入 Agent

MCP 服务端在 `mcpServers` 下支持两种传输（stdio + http）：

### stdio（本地 Agent —— Claude Desktop / Cline）

`claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "novelai-image": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/NovelAI-Image-MCP",
        "python",
        "-m",
        "novelai_image_mcp",
        "serve"
      ],
      "env": {
        "NOVELAI_TOKEN": "${input:novelai_token}"
      }
    }
  }
}
```

#### 备选：uvx（已发布的包）

```json
{
  "mcpServers": {
    "novelai-image": {
      "command": "uvx",
      "args": ["novelai-image-mcp", "serve"],
      "env": { "NOVELAI_TOKEN": "pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" }
    }
  }
}
```

请在宿主环境中预先设置 `NOVELAI_TOKEN`（或 `NOVELAI_USERNAME` +
`NOVELAI_PASSWORD`）—— `uvx` 会继承父 Shell 的环境变量。

### http（远程 / Docker 部署）

执行 `docker compose up --build` 后（服务端监听 `http://HOST:8000/mcp`）：

```json
{
  "mcpServers": {
    "novelai-image-http": {
      "type": "http",
      "url": "http://127.0.0.1:8000/mcp",
      "headers": {
        "Authorization": "Bearer pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

将 `http://127.0.0.1:8000/mcp` 替换为自部署的端点（例如
`https://mcp.example.com/mcp`，前置 TLS 终止的反向代理）。若宿主支持密钥
引用（Claude Desktop、Cline 等通过各自的密钥管理 UI 暴露），可将字面量
token 占位符替换为宿主定义的密钥引用。

## CLI（同步，用于脚本）

```bash
uv run python -m novelai_image_mcp generate --prompt "a cat, masterpiece" --width 832 --height 1216
uv run python -m novelai_image_mcp upscale --image ./in.png --factor 4
uv run python -m novelai_image_mcp info          # subscription / Anlas balance
uv run python -m novelai_image_mcp --help
```

## 技能（可移植的智能体指令）

本项目提供三个 [skills.sh][skills-site] 技能包，帮助 AI 智能体
（Claude Code、Codex、GitHub Copilot、Cursor 等）直接使用 CLI 和 MCP 工具，
无需手动粘贴文档：

```bash
npx skills add --yes --global xinvxueyuan/NovelAI-Image-MCP
```

| 技能 | 内容 |
|---|---|
| `novelai-cli` | 用于 Shell 脚本的 Typer CLI 命令（serve、generate、upscale、director、annotate、info） |
| `novelai-mcp-tools` | 11 个 MCP 工具：模型选择、参数、返回结构与 Anlas 消耗 |
| `novelai-workflows` | 多步骤创作流程（文生图→放大、标注→图生图、Director 编辑） |

技能与 CLI/MCP 工具互为补充。安装全部三个技能后，智能体会根据上下文选择合适的方式。
详见[智能体技能文档][skills-docs]。

## 工具列表

| 工具 | 说明 |
|---|---|
| `generate_image` | 文生图（V3 / V4 / V4.5 / V5 模型，角色提示；Vibe 仅 V4/V4.5） |
| `image_to_image` | 图生图（strength / noise） |
| `inpaint` | 局部重绘（需 inpaint 模型 + mask） |
| `upscale_image` | 4× 放大（V5 模型） |
| `director_tool` | 线稿 / 草图 / 去背景 / 去杂物 / 上色 / 表情 |
| `annotate_image` | ControlNet 标注（hed, midas, scribble, mlsd, uniformer） |
| `suggest_tags` | 标签建议 |
| `encode_vibe` | 将参考图编码为 vibe token |
| `get_subscription` | 账户订阅 + Anlas 余额 |
| `get_user_data` | 账户信息 |
| `estimate_anlas_cost` | 估算生图 Anlas 消耗（不调用 API） |

工具参数与示例见文档站
[工具参考][tools-docs]。

## 配置

全部通过环境变量配置（见 `.env.example`）。关键项：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `NOVELAI_TOKEN` | — | 持久 API token（推荐认证方式） |
| `NOVELAI_USERNAME` / `NOVELAI_PASSWORD` | — | access-key 登录（argon2id） |
| `NOVELAI_OUTPUT_DIR` | `outputs` | 生成 PNG 的保存目录 |
| `MCP_TRANSPORT` | `stdio` | `stdio` 或 `http`（`streamable-http` 为兼容别名） |
| `MCP_HOST` / `MCP_PORT` / `MCP_PATH` | `127.0.0.1` / `8000` / `/mcp` | HTTP 传输用 |
| `MCP_AUTH_TOKEN` | — | 设置后 HTTP 传输要求 `Authorization: Bearer <token>` |
| `MCP_ROUTE_TOKENS` | — | JSON `{"<route>": "<token>"}`，按路由绑定的 Bearer Token（路由不匹配返回 401） |
| `MCP_INSIDERS_HEADER` | `X-MCP-Insiders` | 客户端 opt-in 用的头名（仅 HTTP） |
| `MCP_MODEL_HEADERS` / `MCP_AGENT_HEADERS` / `MCP_CLIENT_HEADERS` | see below | JSON 列表，路由候选头，首个非空者生效 |
| `MCP_INSIDERS_DISABLED_FEATURES` | `[]` | 运维侧强制关闭开关（JSON 列表），优先级高于客户端 |
| `MCP_ROUTE_SCOPED_OUTPUT` | `true` | 路由生效时把图像写到 `<输出目录>/<route>/` |
| `MCP_AUDIT_LOG_PATH` | `<output>/audit.jsonl` | append-only JSONL 审计流水 |
| `MCP_LOG_LEVEL` | — | `DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL` |

list / dict 类型的配置按 **JSON** 读取：`MCP_MODEL_HEADERS='["X-MCP-Model"]'` 可用，
写成 `A,B` 会报配置错误，空值也不是合法 JSON。

### 内测头与路由

通过 HTTP，客户端可以逐请求 opt-in 实验性行为，并声明该请求属于哪条路由、哪个模型、
哪个 Agent 与哪个会话：

```text
X-MCP-Insiders: true
X-MCP-Agent-ID: team-a
X-MCP-Model: nai-diffusion-5-full
```

服务端随后把该请求的图像写到 `<NOVELAI_OUTPUT_DIR>/team-a/`，向
`novelai_image_mcp.audit.team-a` logger 输出一行，并向审计 JSONL 追加一条记录
（记录只保留 prompt 的长度与截断的 SHA-256，绝不保留 prompt 原文，也绝不写入凭证头或
图像载荷）。

**不发送该头时一切不变** —— 不产生路由子目录、不写审计文件、不增删任何工具 ——
只有一个刻意例外：`director_tool` 的 `emotion` 与 `emotion_level` 参数现在需要 opt-in，
否则抛 `ToolError`（见 CHANGELOG）。路由头由客户端提供、可以伪造，因此只在可信网关之后
才授予该 opt-in。

完整契约：[内测头、路由与审计][insiders-docs]。
NovelAI API 文档：[image.novelai.net/docs][nai-docs]

## 开发

本项目为 uv + pnpm 单体仓库，由 Turbo 编排。完整设置见
[`CONTRIBUTING.md`][contributing]，简版如下：

```bash
uv sync                              # Python workspace (server + docs + dev)
pnpm install --frozen-lockfile       # Node toolchain (turbo + husky + markdownlint)

pnpm check                           # lint + typecheck + test (all workspaces)
pnpm docs:build                       # build the docs site
pnpm server:serve                     # run the MCP server
pnpm docs:serve                       # sphinx-autobuild with live reload
```

单成员命令（通过 uv）：

```bash
uv run --directory apps/server ruff check src tests    # lint
uv run --directory apps/server -m pyright              # typecheck
uv run --directory apps/server -m pytest               # tests
```

### Docker

```bash
docker compose up --build      # builds and runs the server (HTTP transport)
```

Dockerfile 位于 [`apps/server/Dockerfile`][dockerfile]，但构建上下文为
仓库根目录（这样 uv 能解析 workspace 图）。详见
[`docker-compose.yml`][docker-compose]。

## 文档

Sphinx 文档站点使用 Furo + MyST Markdown 构建，每次推送到 `main` 时自动部署到
GitHub Pages：

- **在线站点**：[xinvxueyuan.github.io/NovelAI-Image-MCP][docs]
- **源码**：[`apps/docs/source/`][docs-source]
- **本地构建**：`pnpm docs:serve`

## 许可证

MIT —— 见 [LICENSE][license]。逐文件 SPDX 标注见
[REUSE.toml][reuse-toml]。提交即表示你同意
[Developer Certificate of Origin][dco]（`commit-msg`
钩子会自动添加 `Signed-off-by`）。

## 链接

[ci-badge]: https://github.com/xinvxueyuan/NovelAI-Image-MCP/actions/workflows/ci.yml/badge.svg
[ci-workflow]: https://github.com/xinvxueyuan/NovelAI-Image-MCP/actions/workflows/ci.yml
[docs-badge]: https://github.com/xinvxueyuan/NovelAI-Image-MCP/actions/workflows/docs.yml/badge.svg
[mit-badge]: https://img.shields.io/badge/License-MIT-blue.svg
[python-badge]: https://img.shields.io/badge/python-3.13+-blue.svg
[uv-badge]: https://img.shields.io/badge/uv-managed-261230.svg
[reuse-badge]: https://api.reuse.software/badge/github.com/xinvxueyuan/NovelAI-Image-MCP
[deepwiki-badge]: https://img.shields.io/badge/DeepWiki-Ask%20DeepWiki-blue
[skills-badge]: https://skills.sh/b/xinvxueyuan/NovelAI-Image-MCP
[product-hunt-badge]: https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=1206099&theme=light&t=1784973837616
[lifto-badge]: https://liftoapp.com/badges/featured-light.svg

[docs]: https://xinvxueyuan.github.io/NovelAI-Image-MCP/
[reuse]: https://api.reuse.software/info/github.com/xinvxueyuan/NovelAI-Image-MCP
[python]: https://www.python.org/downloads/
[uv]: https://docs.astral.sh/uv/
[deepwiki]: https://deepwiki.com/xinvxueyuan/NovelAI-Image-MCP
[skills-sh]: https://skills.sh/xinvxueyuan/NovelAI-Image-MCP
[product-hunt]: https://www.producthunt.com/products/novelai-image-mcp?embed=true&utm_source=badge-featured&utm_medium=badge&utm_campaign=badge-novelai-image-mcp
[lifto]: https://liftoapp.com/product/novelai-image-mcp
[mcp]: https://modelcontextprotocol.io/
[contributing]: ../../CONTRIBUTING.md
[docs-source]: ../../apps/docs/source/
[skills-site]: https://skills.sh
[skills-docs]: https://xinvxueyuan.github.io/NovelAI-Image-MCP/skills.html
[tools-docs]: https://xinvxueyuan.github.io/NovelAI-Image-MCP/tools/index.html
[insiders-docs]: https://xinvxueyuan.github.io/NovelAI-Image-MCP/development/insiders-and-routing.html
[nai-docs]: https://image.novelai.net/docs/index.html
[dockerfile]: ../../apps/server/Dockerfile
[docker-compose]: ../../docker-compose.yml
[license]: ../../LICENSE
[reuse-toml]: ../../REUSE.toml
[dco]: https://developercertificate.org/

<!-- mcp-name: io.github.xinvxueyuan/novelai-image-mcp -->
