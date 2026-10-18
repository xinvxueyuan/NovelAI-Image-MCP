# 智能体宿主

覆盖所有主流智能体宿主的、可直接复制粘贴的 MCP 配置片段。所有片段都使用标准
stdio 形态 —— `command` + `args` + `env` —— 因为 `uvx` 是一个*命令*（Astral 的
`uv` 包运行器），而不是传输方式。MCP 规范只定义两种传输方式，`stdio` 与
`Streamable HTTP`；当 `command` 存在时，宿主会隐式选择 stdio。

## 概览

| 宿主 | 配置文件 | 格式 | 密钥注入 |
|---|---|---|---|
| [Claude Desktop](#claude-desktop) | `claude_desktop_config.json` | JSON | `env` 字面量、`${input:…}` |
| [Cline](#cline) | `cline_mcp_settings.json` / `~/.cline/mcp.json` | JSON | `env` 字面量 |
| [Cursor](#cursor) | `mcp.json`（全局或项目级） | JSON | `env` 字面量、`auth`（OAuth） |
| [Continue](#continue) | `config.yaml` / `config.json` | YAML 或 JSON | `env` 字面量、`${{ secrets.X }}` |
| [Windsurf](#windsurf) | `mcp_config.json` | JSON | `${env:VAR}`、`${file:/path}` |
| [Codex CLI](#codex-cli) | `config.toml` | TOML | `env_vars`、`bearer_token_env_var` |
| [Generic stdio](#generic-stdio) | （依宿主而定） | JSON | `env` 字面量 |

## Claude Desktop

### 配置文件路径

| 操作系统 | 路径 |
|---|---|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux（非官方构建） | `~/.config/Claude/claude_desktop_config.json` |

macOS 路径也可以通过 Settings → Developer → **Edit Config** 到达，该操作会在
文件不存在时创建它。

### 片段

```json
{
  "mcpServers": {
    "novelai-image": {
      "command": "uvx",
      "args": ["novelai-image-mcp", "serve"],
      "env": { "NOVELAI_TOKEN": "${input:novelai_token}" }
    }
  }
}
```

做一次性测试时，改为直接内联一个字面 token
（`"pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"`），而不是 `${input:…}` 引用。

### 密钥注入

Claude Desktop 把 `env` 对象中的密钥当作字面字符串读取，或者通过它自己的宿主
托管密钥 UI 解析 `${input:…}` 引用。官方 schema 中没有 `${env:VAR}` shell
插值。

### 宿主特有字段

Claude Desktop 使用最朴素的 MCP 规范 stdio 形态 —— 没有 `type`、没有
`disabled`、没有 `autoApprove`。远程服务器改用 `url` + `headers`，而不是
`command` + `args`。

### 参考

- [docs.open.cx/mcp/clients/claude-desktop](https://docs.open.cx/mcp/clients/claude-desktop)
- [github.com/mcp-finder/claude-mcp-config-examples](https://github.com/mcp-finder/claude-mcp-config-examples)
- [modelcontextprotocol.io/docs/develop/connect-local-servers](https://modelcontextprotocol.io/docs/develop/connect-local-servers)

## Cline

### 配置文件路径

| 范围 | 路径 |
|---|---|
| VS Code 扩展 | 通过 MCP Servers 图标 → Configure 标签页 → **Configure MCP Servers** 打开 |
| Cline CLI | `~/.cline/mcp.json` |

扩展设置文件在磁盘上的位置在版本之间变动过；**Configure MCP Servers** 按钮是
可靠的入口。较旧的安装把它放在 VS Code 的
`globalStorage/saoudrizwan.claude-dev/settings/` 下 —— ⚠ 当前扩展版本是否仍
写入该处未经核实。

### 片段

```json
{
  "mcpServers": {
    "novelai-image": {
      "command": "uvx",
      "args": ["novelai-image-mcp", "serve"],
      "env": { "NOVELAI_TOKEN": "pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### 密钥注入

Cline 把密钥当作 `env` 对象中的字面字符串读取（远程服务器则读 `headers`）。
官方 schema 中没有任何 `${env:VAR}` 插值的文档。

### 宿主特有字段

- `disabled`（布尔）—— 在不删除配置的前提下停用某个服务器。
- `autoApprove`（字符串数组）—— 每个服务器的工具白名单。**不是**
  `alwaysAllow`（那是 Roo Code 分支的拼法）。
- 远程服务器的 `type` —— 接受 `streamableHttp`（驼峰）或 `sse`；省略
  `type` 会默认回退到旧的 `sse`，所以想用推荐的传输方式就要显式设置它。

### 参考

- [docs.cline.bot/mcp/mcp-overview](https://docs.cline.bot/mcp/mcp-overview)
- [policylayer.com/integrations/cline](https://policylayer.com/integrations/cline)

## Cursor

### 配置文件路径

| 范围 | 路径 |
|---|---|
| 全局 | `~/.cursor/mcp.json`（macOS/Linux）；`%USERPROFILE%\.cursor\mcp.json`（Windows） |
| 项目级 | 项目根目录下的 `.cursor/mcp.json` |

项目级配置会与全局文件合并（⚠ 合并语义未对照官方文档核实）。

### 片段

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

### 密钥注入

stdio 的密钥是 `env` 中的字面字符串；远程服务器的密钥放在 `headers` 里
（例如 `"Authorization": "Bearer …"`），或者通过 `auth` 对象走 OAuth 获取。
JSON schema 中没有任何 `${env:VAR}` 替换的文档。

### 宿主特有字段

- `auth` —— 用于静态 OAuth 远程服务器的对象，含 `CLIENT_ID`（必填）、
  `CLIENT_SECRET`、`scopes`。
- `envFile` —— 部分第三方指南提到用它从文件加载环境变量；⚠ 未对照官方文档
  核实。
- 没有 `type`/`transport` 字段 —— Cursor 会从字段形态自动判断传输方式
  （`command` → stdio；`url` → SSE 或 Streamable HTTP）。

### 参考

- [cursor.com/docs/mcp](https://cursor.com/docs/mcp)

## Continue

### 配置文件路径

| 操作系统 | 路径 |
|---|---|
| macOS / Linux | `~/.continue/config.yaml`（或 `config.json`） |
| Windows | `%USERPROFILE%\.continue\config.yaml`（或 `config.json`） |
| 项目级 | 工作区中的 `.continue/config.yaml` |
| 独立 MCP 块 | `.continue/mcpServers/<name>.yaml` 或 `.json` |

### 片段

```yaml
mcpServers:
  - name: novelai-image
    command: uvx
    args:
      - "novelai-image-mcp"
      - "serve"
    env:
      NOVELAI_TOKEN: "pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

:::{warning}
Continue 的 `mcpServers` 是一个对象**数组**，每个对象带有显式的 `name` 字段
—— 而不是以服务器名为键的对象。把 Claude Desktop / Cursor / Cline 的 JSON
配置原样复制过来不会生效。（Continue 确实接受丢进 `.continue/mcpServers/` 的
Claude Desktop 形态 JSON，用于迁移。）
:::

### 密钥注入

三种机制：`env` 中的字面值；从 Continue Mission Control 托管密钥库取值的
`${{ secrets.NAME }}` 占位符；以及 OAuth（Continue 会打开浏览器标签页让用户
授权）。

### 宿主特有字段

- `name`（必填）—— 服务器的显示名（取代其他宿主所用的对象键约定）。
- `type` —— `stdio`（默认）、`sse` 或 `streamable-http`（kebab-case，与
  Cline 的 `streamableHttp` 驼峰写法相反）。
- `env` / `args` 中的 `${{ secrets.X }}` 替换。

:::{note}
MCP 只在 Continue 的 **agent 模式**下可用 —— 聊天或自动补全模式下不行。
:::

### 参考

- [docs.continue.dev/customize/deep-dives/mcp](https://docs.continue.dev/customize/deep-dives/mcp)
- [docs.continue.dev/reference](https://docs.continue.dev/reference)

## Windsurf

### 配置文件路径

| 操作系统 | 路径 |
|---|---|
| macOS / Linux | `~/.codeium/windsurf/mcp_config.json` |
| Windows | `%USERPROFILE%\.codeium\windsurf\mcp_config.json` |

⚠ **存在分歧：** Windsurf 官方文档
[docs.windsurf.com/windsurf/cascade/mcp](https://docs.windsurf.com/windsurf/cascade/mcp)
仍写着 `~/.codeium/mcp_config.json`，*不含* `windsurf/` 这一段。六个独立的
第三方来源（open.cx、policylayer、quadratichq、toolcog、GitHub MCP Server 安装
指南，以及 mcp.directory 的 Windsurf 校验器）都引用了 `windsurf/` 子目录 ——
官方文档页面在这一点上似乎已经过期。配置只有全局一份；没有项目级文件。

### 片段

```json
{
  "mcpServers": {
    "novelai-image": {
      "command": "uvx",
      "args": ["novelai-image-mcp", "serve"],
      "env": { "NOVELAI_TOKEN": "${env:NOVELAI_TOKEN}" }
    }
  }
}
```

在启动 Windsurf 之前先在 shell 中导出 `NOVELAI_TOKEN` —— `${env:VAR}` 形式
可以让字面 token 不出现在配置文件里。

### 密钥注入

三种有文档的机制：`env`/`headers` 中的字面字符串；从用户 shell 环境取值的
`${env:VAR}` 插值；以及读取文件第一行的 `${file:/absolute/path}`。三者都
可用于 `command`、`args`、`env`、`serverUrl`、`url` 与 `headers`。

### 宿主特有字段

- `serverUrl` —— Windsurf 特有的 `url` 别名（也接受普通的 `url`）。
- 任意字符串字段中的 `${env:VAR}` 与 `${file:/path}` 插值。
- `disabledTools` —— 按服务器屏蔽的工具名数组（⚠ 未对照官方文档核实）。
- 没有 `type` 字段 —— 传输方式自动判断。

:::{warning}
Windsurf 只在启动时读取 `mcp_config.json`。编辑了文件却不重启 Cascade，是最
常见的静默失败。
:::

### 参考

- [docs.windsurf.com/windsurf/cascade/mcp](https://docs.windsurf.com/windsurf/cascade/mcp)
- [docs.codeium.com/plugins/cascade/mcp](https://docs.codeium.com/plugins/cascade/mcp)

## Codex CLI

### 配置文件路径

| 范围 | 路径 |
|---|---|
| 全局 | `$CODEX_HOME/config.toml`（默认 `~/.codex/config.toml`；Windows 上是 `%USERPROFILE%\.codex\config.toml`） |
| 项目级 | `.codex/config.toml`（只对受信任的项目加载） |

### 片段

```toml
[mcp_servers.novelai-image]
command = "uvx"
args = ["novelai-image-mcp", "serve"]
env_vars = ["NOVELAI_TOKEN"]
startup_timeout_sec = 10.0

[mcp_servers.novelai-image.env]
NOVELAI_OUTPUT_DIR = "/tmp/novelai-outputs"
```

在你的 shell 中导出 `NOVELAI_TOKEN`（例如写进 `~/.zshrc` 或 PowerShell
profile）。`env_vars = ["NOVELAI_TOKEN"]` 会在运行时从父进程转发它，让字面
token 不出现在配置文件里。

:::{note}
TOML 的顺序很重要：`command`、`args`、`env_vars`、`startup_timeout_sec`
必须出现在 `[mcp_servers.<name>.env]` 子表头*之上* —— 位于其下的内容都属于
`env`。这是本列表中唯一使用 TOML 的宿主；从 Claude Desktop / Cursor / Cline
复制 JSON 配置过来不会生效。
:::

### 密钥注入

Codex 是这七个宿主中最注重安全的 —— token 从不应该以字面形式写在配置文件里。
用 `env_vars` 从父进程转发指定名称的环境变量（支持 `source = "local"` 或
`source = "remote"`）；对 HTTP 服务器，用 `bearer_token_env_var` 指定一个
环境变量名，Codex 会在运行时读取它并注入为
`Authorization: Bearer <token>`。OAuth 也受支持，通过
`codex mcp login`。

### 宿主特有字段

- `env_vars` —— 从父环境转发的变量名列表（字符串，或
  `{ name = "X", source = "local"|"remote" }`）。
- `bearer_token_env_var` —— 指定承载 HTTP 服务器 bearer token 的环境变量名。
- `env_http_headers` —— 在运行时用环境变量填充 HTTP 头。
- `enabled_tools` / `disabled_tools` —— 按服务器的工具允许 / 拒绝列表。
- `startup_timeout_sec`（默认 `10.0`）/ `tool_timeout_sec`（默认 `60.0`）。
- `experimental_environment = "remote"` —— 把 stdio 服务器启动路由到远程
  执行器。
- 顶层 `mcp_oauth_credentials_store`（`auto` | `file` | `keyring`）。

### 参考

- [developers.openai.com/codex/mcp](https://developers.openai.com/codex/mcp)
- [developers.openai.com/codex/config-reference](https://developers.openai.com/codex/config-reference)
- [github.com/openai/codex](https://github.com/openai/codex)

## Generic stdio

MCP 规范只定义线协议与两种传输方式 —— 它并不标准化客户端配置文件的格式。下面
这种事实上的 "generic stdio" 形态，是 Claude Desktop、Cursor 与 Windsurf 都能
直接接受的（Cline 接受它并允许可选扩展；Continue 与 Codex CLI 不接受 —— 见
上文各自的小节）。

### 配置文件路径

依宿主而定 —— 见各宿主小节。

### 片段

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

### 密钥注入

最朴素的 `env` 字面量。在可用的地方升级为宿主特有机制（Claude Desktop 的
`${input:…}`、Windsurf 的 `${env:VAR}`、Codex CLI 的 `env_vars`）。

### 宿主特有字段

无 —— 这就是 MCP 规范 stdio 的规范形态。

### 参考

- [modelcontextprotocol.io/docs/develop/connect-local-servers](https://modelcontextprotocol.io/docs/develop/connect-local-servers)

## 常见坑

- **把 `uvx` 放进 `type`/`transport` 字段。** `uvx` 是一个命令 —— 它属于
  `command`。MCP 规范只有 `stdio` 与 `Streamable HTTP` 两种传输方式（外加
  旧的 `sse`）；当 `command` 存在时，宿主会隐式选择 stdio。
- **把 Claude Desktop 的 JSON 配置复制到 Codex CLI。** Codex 读取的是
  `~/.codex/config.toml`（TOML，不是 JSON），使用
  `[mcp_servers.<name>]` 表；JSON 配置无法解析。
- **把以对象为键的配置复制到 Continue。** Continue 把 `mcpServers` 读作带
  显式 `name` 字段的对象数组 —— 而不是以服务器名为键的对象。
- **在 Cline 中用 `alwaysAllow` 而不是 `autoApprove`。** `alwaysAllow` 是
  Roo Code 分支的拼法，出现在过期的校验器里；当前权威名称是 `autoApprove`。
- **混淆 `streamableHttp` 与 `streamable-http`。** Cline 用驼峰
  （`streamableHttp`）；Continue 用 kebab-case（`streamable-http`）。
- **编辑配置文件后忘记重启宿主。** Claude Desktop 与 Windsurf 只在启动时读取
  配置 —— 仅关闭窗口不够（macOS：`Cmd+Q`；Windsurf：完整重启 Cascade）。

## 位于企业代理之后

如果你位于企业或地区防火墙之后（例如无法直连 `novelai.net` 的中国大陆），
请在 `env` 块中加入标准代理环境变量：

```json
"env": {
  "NOVELAI_TOKEN": "pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "HTTPS_PROXY": "http://127.0.0.1:10808",
  "HTTP_PROXY": "http://127.0.0.1:10808",
  "NO_PROXY": "localhost,127.0.0.1"
}
```

服务器使用 `httpx`，它遵循标准的 `HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY`
环境变量。没有这些变量时，任何调用 NovelAI API 的工具（`get_subscription`、
`generate_image`、`upscale_image`……）都会以
`NovelAI request transport failed` 错误失败。

## 另请参见

- [stdio 传输方式](stdio.md)
- [streamable-http 传输方式](http.md)
- [配置](../configuration.md)
