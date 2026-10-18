# stdio 传输方式

默认且最常用的传输方式。服务器从 stdin 读取 JSON-RPC 消息，把响应写到
stdout。专为与本地 MCP 宿主（Claude Desktop、Cline、自定义智能体）紧密集成
而设计。

## 运行

```bash
uv run python -m novelai_image_mcp serve
# or explicitly:
MCP_TRANSPORT=stdio uv run python -m novelai_image_mcp serve
```

服务器在前台运行。按 `Ctrl+C` 退出。

## 智能体配置

### Claude Desktop

编辑 `claude_desktop_config.json`：

- **macOS**：`~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**：`%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**：`~/.config/Claude/claude_desktop_config.json`

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

`${input:novelai_token}` 会解析为宿主托管的密钥。做一次性测试时，改为直接内联
一个字面 token（`"pst-..."`）。

#### 简写：uvx（已安装的包）

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

在宿主 shell 中设置 `NOVELAI_TOKEN` —— `uvx` 会继承父进程环境。

重启 Claude Desktop。你会看到一个名为 `novelai-image` 的 MCP 服务器注册成功，
带 11 个工具。

### Cline（VS Code）

添加到 `cline_mcp_settings.json`：

```json
{
  "mcpServers": {
    "novelai-image": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run", "--directory", "/path/to/NovelAI-Image-MCP",
        "python", "-m", "novelai_image_mcp", "serve"
      ],
      "env": { "NOVELAI_TOKEN": "pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### 自定义 Python 智能体

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(
        command="uv",
        args=["run", "--directory", "/path/to/NovelAI-Image-MCP",
              "python", "-m", "novelai_image_mcp", "serve"],
        env={"NOVELAI_TOKEN": "pst-..."},
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print([t.name for t in tools])

asyncio.run(main())
```

## 为什么用 stdio？

- **没有网络开销** —— 没有 TCP 握手，没有 HTTP 分帧。
- **没有端口冲突** —— 服务器不绑定任何东西。
- **进程生命周期自动管理** —— 智能体拥有该进程；智能体退出时服务器随之退出。
- **stdin/stdout** 在所有 MCP SDK 中都受支持。

## 限制

- **只支持单客户端。** 两个智能体无法共用一个 stdio 服务器。
- **服务器的 stderr 会被智能体捕获**为日志。诊断信息请用 `logging`
  （配置到 stderr）；绝不要向 stdout 打印（会破坏 JSON-RPC 流）。

## 日志

MCP 运行时把所有日志写到 **stderr**。要在另一个终端查看它们：

```bash
uv run python -m novelai_image_mcp serve 2>server.log
```

要把日志转发给智能体（例如 Claude Desktop 的 "MCP logs" 面板），请按 MCP SDK
文档配置运行时的 logging handler。

## 另请参见

- [streamable-http 传输方式](http.md)
- [配置](../configuration.md#mcp-传输方式)
- [快速开始](../quickstart.md)
