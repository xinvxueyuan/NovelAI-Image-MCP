# NovelAI Image MCP

一个 [MCP（模型上下文协议）](https://modelcontextprotocol.io/) 服务端，将 **NovelAI
图像生成** 能力以工具形式暴露给 AI 智能体（Claude Desktop、Cline、自定义 Agent、
远程客户端）。

基于官方 MCP Python SDK v2（`MCPServer`）构建。智能体可通过标准 MCP 工具接口完成
生图（文生图 / 图生图 / 局部重绘）、放大、Director 工具（线稿、表情、去背景……）、
ControlNet 标注、标签建议、Vibe 编码以及账户订阅查询。

## 特性

- **11 个 MCP 工具**，覆盖 NovelAI 图像 API 全部能力。
- **双传输**：stdio（本地 Agent）+ streamable-http（远程 / 多客户端）。
- **图像返回**：base64 `Image` 内容块（Agent 能“看到”图）**同时** 保存 PNG 到磁盘
  （返回路径）。
- **异步 + 同步**：异步工具处理器 + `typer` CLI 直接调用。
- **uv 管理**，单一 Python 包，MIT 许可，开箱即用的 Docker。

## 快速开始

```bash
# 1. 安装（需要 uv ≥ 0.5）
uv sync

# 2. 配置凭证
cp .env.example .env
#   设置 NOVELAI_TOKEN=...  （推荐）
#   或   NOVELAI_USERNAME + NOVELAI_PASSWORD

# 3. 运行（stdio —— 用于本地 Agent）
uv run python -m novelai_image_mcp serve

# 4. 或通过 HTTP 运行
MCP_TRANSPORT=streamable-http uv run python -m novelai_image_mcp serve
#   → http://127.0.0.1:8000/mcp
```

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

```bash
uv sync --group dev      # 安装 lint + test 工具
uv run poe check         # ruff format-check + lint + pyright + 测试
uv run poe lint          # ruff check
uv run poe format        # ruff format（写入）
uv run poe test          # pytest
uv run poe typecheck     # pyright
```

### Docker

```bash
docker compose up --build      # 构建并运行服务端
```

## 项目结构

```
src/novelai_image_mcp/
├── server.py          # MCPServer（mcp v2）+ lifespan + 传输选择
├── settings.py        # pydantic-settings 环境配置
├── cli.py / __main__.py  # typer 同步 CLI
├── output.py          # 保存图像辅助
├── tools/             # 11 个 MCP 工具定义
└── nai/               # NovelAI HTTP 客户端（自 lingchu-bot 移植，已解耦）
    ├── auth.py  constants.py  models.py  payload.py
    ├── response.py  imaging.py  exceptions.py
    └── client.py  service.py    # 改造：NoneBot driver → httpx
```

## 许可证

MIT —— 见 [LICENSE](LICENSE)。

`src/novelai_image_mcp/nai/` 下的 NovelAI 客户端模块派生自
[lingchu-bot](https://github.com/xinvxueyuan/lingchu-bot) 项目
（LGPL-3.0-or-later）。仅当你拥有原作品权利时，才可将此衍生代码重新许可为 MIT。
详见 [LICENSE](LICENSE) 中的说明与 [REUSE.toml](REUSE.toml) 的逐文件 SPDX 标注。
