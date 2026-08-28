# 快速开始

本页将带你完成服务器安装、凭据配置，并在五分钟内生成你的第一张图像。

:::{note}
本指南假设你已经完成了 [安装](installation.md)。
:::

---

## 1. 启动服务器（stdio）

默认传输方式是 **stdio** —— 适用于 Claude Desktop 或 Cline 等本地智能体。
以前台进程方式运行：

```bash
uv run python -m novelai_image_mcp serve
```

服务器从 stdin 读取输入，并将 JSON-RPC 响应写入 stdout。在有客户端连接之前，
你不会看到任何输出。要退出，请按 `Ctrl+C`。

## 2. 生成图像（CLI）

如果不想启动 MCP host，只想快速试验，可以使用同步 `typer` CLI：

```bash
uv run python -m novelai_image_mcp generate \
  --prompt "a cat sitting on a windowsill, masterpiece, best quality" \
  --width 832 \
  --height 1216
```

CLI 会打印保存的 PNG 路径：

```text
outputs/generate-YYYYMMDD-HHMMSS-NNN.png
```

打开文件 —— 你应该能看到生成的猫。

## 3. 通过 HTTP 生成

要通过 HTTP 将服务器暴露给远程客户端：

```bash
MCP_TRANSPORT=streamable-http uv run python -m novelai_image_mcp serve
```

服务器默认监听 <http://127.0.0.1:8000/mcp>。通过 `MCP_HOST` / `MCP_PORT`
覆盖主机和端口。

## 4. 连接 Claude Desktop

编辑 `claude_desktop_config.json`（macOS：`~/Library/Application Support/Claude/`，
Windows：`%APPDATA%\Claude\`）：

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

`${input:novelai_token}` 是由 host 定义的秘密引用 —— 详见你的 MCP host 的
secrets UI（Claude Desktop、Cline 等）。如果只是做一次性测试，可以直接内联
字面量 token。

### 替代方案：uvx（已发布包）

如果你从 PyPI 安装，简写形式是：

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

在 host shell 中设置 `NOVELAI_TOKEN` —— `uvx` 会继承父环境。

### 替代方案：http（远程 / Docker）

如果你在其他机器上运行服务器（例如在远程主机上 `docker compose up`），直接
将 host 指向该 URL：

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

将 `http://127.0.0.1:8000/mcp` 替换为你自部署的端点（例如位于 TLS 终止反向
代理后面的 `https://mcp.example.com/mcp`）。

重启 Claude Desktop。你会看到一个名为 `novelai-image` 的 MCP 服务器注册
进来，带有 11 个工具。让 Claude *"生成一幅狐狸的水彩画"*，看着它调用
`generate_image`。

其他智能体 host（Cline、Cursor、Continue、Windsurf、Codex CLI）的配置方式
类似，具体示例请参考英文文档的 Agent hosts 章节。

## 5. 验证你的账户余额

在长时间生成会话之前，检查你的 Anlas 余额：

```bash
uv run python -m novelai_image_mcp info
```

```json
{
  "tier": 3,
  "active": true,
  "trainingStepsLeft": { "fixed": 10000, "perStepUsage": false },
  "subscriptionId": "..."
}
```

或者从你的智能体调用 `get_subscription` MCP 工具。

---

## 常见的后续步骤

- 通过环境变量调整 [生成默认值](configuration.md)
- 工具参考、教程、传输方式等章节暂仅提供英文版本，可通过页面左下角的语言切换器切换到 English 查看。

## 故障排查

:::{admonition} 凭据错误
:class: warning

如果你看到：

```text
RuntimeError: NovelAI credentials are not configured: set NOVELAI_TOKEN or
NOVELAI_USERNAME + NOVELAI_PASSWORD (see .env.example).
```

请确保你的 `.env` 文件存在，并包含以 `pst-` 开头的有效 `NOVELAI_TOKEN`。
`info` 子命令是验证认证而不消耗 Anlas 的最廉价方式。
:::

:::{admonition} 首次运行缓慢
:class: tip

首次 `uv sync` 会下载约 60 个 wheel。后续运行会复用缓存并在几秒内完成。
如果你在公司代理后面，请设置 `UV_HTTP_TIMEOUT=300`（秒）以避免在慢速网络上
超时。
:::

:::{admonition} 图像未保存
:class: warning

检查 `NOVELAI_OUTPUT_DIR`（默认：`outputs`）。该目录必须可被运行服务器的
用户写入。在 Docker 中，目录是 `/app/outputs`，由一个命名卷
（`novelai-outputs`）支持。
:::
