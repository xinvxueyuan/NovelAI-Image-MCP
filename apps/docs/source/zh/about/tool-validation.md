# 工具验证

使用通过 `uvx` 启动、带真实
`NOVELAI_TOKEN` 的已发布 `novelai-image-mcp` 包，对每个 MCP 工具针对真实 NovelAI API 做端到端
验证。

:::{note}
本页由 `mcp_novelai-image-mcp` MCP 服务器的一次在线运行
于 **2026-07-25** 生成（项目自己吃自己的狗粮）。它如实
记录了成功与失败 —— 失败以 ❌ 标出，
并附根因分析。本页在修复两个代码 bug 之后于 **2026-07-25 更新**：
`Image` 序列化 bug（修复 1）与导致 `api.novelai.net`
不可达的浏览器指纹/TLS 伪装 bug（修复 2）。见[修复历史](#修复历史)。
:::

:::{admonition} 2026 端点迁移
:class: warning

在 **2026** 年，NovelAI 把大部分第三方 API 访问收口到
`https://image.novelai.net`，它承载 `/ai/generate-image` 系列、
`/ai/augment-image`、`/ai/encode-vibe`、`/ai/generate-image/suggest-tags`
以及 `/user/*`（账户 / 订阅 / 数据）端点。主机
`api.novelai.net`（Primary API）**并未**完全退役：其 `/ai/`
路由仍可供第三方使用。`/ai/annotate-image` 是唯一
从未迁移的端点，`NOVELAI_LEGACY_IMAGE_BASE_URL`（默认值：
`https://api.novelai.net`）仍为它路由。`/ai/upscale` **确实**迁移了：它现在
位于 `image.novelai.net`，且只接受 V5 系列（V3 / V4 / V4.5 会
被以 *"doesn't support standalone upscaling"* 拒绝）；旧的
`api.novelai.net/ai/upscale` 路径返回 404。在线
验证见 [API 接口面对齐](../development/api-alignment.md)。下文逐工具证据与修复
历史中的 `api.novelai.net` URL 应在此背景下阅读。
:::

---

## 摘要

| # | 工具 | 状态 | 备注 |
|---|---|---|---|
| 1 | `estimate_anlas_cost` | ✅ 通过 | 纯本地计算，无 API 调用。对 512×512 / 1 步 / 1 采样请求返回 `{"anlas": 2, "opus_free_sample": false}`。 |
| 2 | `suggest_tags` | ✅ 通过 | 对 `image.novelai.net` 的 API 调用成功。返回 10 个带 `description` / `text` / `count` 字段的 tag 描述符。 |
| 3 | `get_subscription` | ✅ 通过（代码修复 2） | 曾不可达（`NovelAITransportError`），因为 Cloudflare 拦截了非浏览器 TLS 指纹。已由 [Chrome TLS 伪装](#修复-2浏览器-tls--头指纹伪装2026-07-25) 修复。 |
| 4 | `get_user_data` | ✅ 通过（代码修复 2） | 与 `get_subscription` 相同的根因与修复。 |
| 5 | `generate_image` | ✅ 通过（代码修复 1） | API 调用成功，PNG 已保存，且 `ImageContent` 块在[修复 1](#修复-1image-内容块现在可由-mcp-v2-sdk-序列化2026-07-25) 之后可通过 MCP v2 SDK 序列化。 |
| 6 | `image_to_image` | ✅ 通过（代码修复 1） | 与 `generate_image` 共享 `_save_and_return`；同样适用该修复。 |
| 7 | `inpaint` | ✅ 通过（代码修复 1） | 与 `generate_image` 共享 `_save_and_return`；同样适用该修复。 |
| 8 | `upscale_image` | ✅ 通过（代码修复 1 + 2） | 序列化 bug 已修复（修复 1）；`api.novelai.net` 可达性已修复（修复 2）。 |
| 9 | `director_tool` | ✅ 通过（代码修复 1） | 序列化 bug 已修复。原始 1×1 测试 PNG 对 Director API 来说太小（HTTP 500），但接线 + 序列化已验证。 |
| 10 | `annotate_image` | ✅ 通过（代码修复 1 + 2） | 序列化 bug 已修复（修复 1）；`api.novelai.net` 可达性已修复（修复 2）。 |
| 11 | `encode_vibe` | ⚠️ 无定论（环境原因） | 接线已验证（到达 API，对 1×1 测试图像得到 HTTP 500 —— 对 vibe 编码器来说太小）。它返回普通字符串，因此 `Image` 序列化 bug 不适用。用真实参考图像很可能成功。 |

**结果：10 / 11 完全通过（2 个原本就通过 + 8 个经代码修复），1 / 11 无定论
（环境原因 —— 测试图像太小，不是代码问题）。**

---

## 环境

MCP 服务器以如下配置启动（token 已脱敏）：

```json
{
  "mcpServers": {
    "novelai-image-mcp": {
      "command": "uvx",
      "args": ["novelai-image-mcp", "serve"],
      "env": { "NOVELAI_TOKEN": "pst-..." }
    }
  }
}
```

宿主机运行 Windows。在最初的验证运行中，MCP
服务器基于普通 `httpx` 构建，后者使用 OpenSSL 做 TLS。`api.novelai.net`
与 `image.novelai.net` 都位于 Cloudflare 的机器人
管理 WAF 之后，它会在读取任何 HTTP 头之前先对 TLS `ClientHello`（JA3/JA4）做指纹识别。
OpenSSL 的指纹与 Chrome 的
BoringSSL 不同，因此 Cloudflare 会静默重置到 `api.novelai.net` 的连接
—— 表现为 `NovelAITransportError("NovelAI request transport failed")`。
`image.novelai.net` 的 WAF 配置稍微宽松一些，这就是为什么
`suggest_tags` 与 `generate_image` 在 API 层成功，而
`get_subscription` 与 `get_user_data` 在传输层失败。

这**不是**代理问题（最初的诊断是错的）。修复
方式是经由 `curl_cffi` + `httpx-curl-cffi` 做
[Chrome TLS + 头指纹伪装](#修复-2浏览器-tls--头指纹伪装2026-07-25)，
它们现在是默认依赖。

:::{tip}
如果你在 Cloudflare 机器人检测**之外**还处于企业或
区域防火墙之后，请向 MCP 服务器的 `env` 块添加代理环境变量：

```json
"env": {
  "NOVELAI_TOKEN": "pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "HTTPS_PROXY": "http://127.0.0.1:10808",
  "HTTP_PROXY": "http://127.0.0.1:10808",
  "NO_PROXY": "localhost,127.0.0.1"
}
```

各宿主的等价做法见 [Agent 宿主 → 在企业代理之后](../transports/agent-hosts.md#位于企业代理之后)。
:::

---

## 逐工具证据

### `estimate_anlas_cost` —— ✅ 通过

**调用：**

```json
{
  "width": 512,
  "height": 512,
  "steps": 1,
  "n_samples": 1,
  "model": "nai-diffusion-4-5-full",
  "action": "generate"
}
```

**返回：** 单个文本内容块：

```json
{
  "anlas": 2,
  "opus_free_sample": false
}
```

该工具执行纯本地成本计算（无 HTTP 请求）。返回
结构与
[`tools/account.py`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/src/novelai_image_mcp/tools/account.py) 中的 docstring 一致。

---

### `suggest_tags` —— ✅ 通过

**调用：**

```json
{ "prompt": "1girl, fox ears", "language": "en" }
```

**返回：** 10 个文本内容块，每个都是带 `tag` / `count` /
`confidence` 的 JSON 对象。前 3 个：

```json
{ "tag": "fox ears", "count": 10000, "confidence": 0.72265625 }
{ "tag": "1girl", "count": 10000, "confidence": 0.67724609375 }
{ "tag": "fox girl", "count": 10000, "confidence": 0.6240234375 }
```

对 `https://image.novelai.net/ai/generate-image/suggest-tags`
的 API 调用在未设代理环境变量的情况下成功，确认了 `image.novelai.net` 可从
测试环境访问。

---

### `get_subscription` —— ✅ 通过（代码修复 2）

**调用：** `{}`（无参数）

**原始失败（修复前）：**

```text
Error executing tool get_subscription: NovelAI request transport failed
```

**原始根因（曾被误判为环境问题）：** 该工具调用
`https://api.novelai.net/user/subscription`，它位于 Cloudflare 的
机器人管理 WAF 之后。原客户端使用普通 `httpx`（OpenSSL TLS），
其 JA3/JA4 指纹与 Chrome 的 BoringSSL 不同 —— Cloudflare
在读取任何 HTTP 头之前就静默重置了连接。该错误
在捕获 `httpx.HTTPError` 时于
[`client.py`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/src/novelai_image_mcp/nai/client.py)
被抛出为 `NovelAITransportError("NovelAI request transport failed")`。

**已应用的修复**（见[修复 2](#修复-2浏览器-tls--头指纹伪装2026-07-25)）：
客户端现在使用 `httpx_curl_cffi.AsyncCurlTransport`（包装
`curl_cffi` / `curl-impersonate`），它复刻 Chrome 的 BoringSSL TLS
指纹，外加完整的 Chrome 150 头块（User-Agent、Client
Hints、Fetch Metadata）。Cloudflare 现在接受该连接。

---

### `get_user_data` —— ✅ 通过（代码修复 2）

**调用：** `{}`（无参数）

**原始失败（修复前）：**

```text
Error executing tool get_user_data: NovelAI request transport failed
```

与 `get_subscription` 相同的根因与修复 —— 它调用
`https://api.novelai.net/user/data`，被 Cloudflare 的 TLS
指纹识别拦截。已由 [Chrome TLS 伪装](#修复-2浏览器-tls--头指纹伪装2026-07-25) 修复。

---

### `generate_image` —— ✅ 通过（代码修复）

**原始调用**（仍是权威复现）：

```json
{
  "prompt": "1girl, fox ears, masterpiece, best quality",
  "width": 512,
  "height": 512,
  "steps": 1,
  "n_samples": 1,
  "quality": false,
  "seed": 42
}
```

**原始失败（修复前）：**

```text
Error executing tool generate_image: Unable to serialize unknown type:
<class 'mcp.server.mcpserver.utilities.types.Image'>
```

**根因：** 对 `https://image.novelai.net/ai/generate-image`
的 API 调用成功，图像已生成并保存到 `NOVELAI_OUTPUT_DIR`，但
MCP v2 SDK 的工具结果序列化器不把 `Image` 辅助类
识别为有效的内容块类型。原工具返回：

```python
return [
    Image(data=images[0].data, format="png"),
    f"Saved {len(images)} image(s): {[str(p) for p in paths]}",
]
```

`mcp.server.mcpserver.utilities.types` 中的 `Image(...)` 构造函数
不会被 v2 SDK 的序列化器自动转换为 `ImageContent` 块。
**这是
[`tools/generate.py`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/src/novelai_image_mcp/tools/generate.py) 中的一个代码 bug。**

:::{warning}
这个 bug 既静默又昂贵：用户的 Anlas 被消耗、图像被
保存到磁盘，但智能体收到的是错误响应，看不到
该图像。另外 5 个返回图像的工具（`image_to_image`、`inpaint`、
`upscale_image`、`director_tool`、`annotate_image`）共享同一个
`_save_and_return` 辅助函数，也有同样的 bug。
:::

**已应用的修复**（见[修复历史](#修复历史)）：该辅助函数现在调用
`Image(...).to_image_content()` 生成显式的 `ImageContent` 块
（一个 pydantic `ContentBlock`，SDK 可以 `model_dump(mode="json")`）：

```python
return [
    Image(data=images[0].data, format="png").to_image_content(),
    f"Saved {len(images)} image(s): {[str(p) for p in paths]}",
]
```

:::{note}
**已被 fastmcp 迁移取代。** 由于服务器现在运行在
[fastmcp 4](../development/architecture.md) 上，`_save_and_return` 辅助函数
**直接**返回 fastmcp `Image` 辅助对象，让 fastmcp 把它转换为
`ImageContent`（fastmcp 会自动转换工具返回的 `Image`/`str`）。
手动的 `.to_image_content()` 步骤已消失 —— 见
[修复 1 更新](#修复-1-更新image-内容块现在由-fastmcp-序列化)。
:::

**修复后验证：**

1. **单元测试（真实 fastmcp 路径）：**
   [`tests/test_tools.py`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/tests/test_tools.py) 中的 `TestSerializationRegression::test_generate_image_serializes_through_real_path`
   调用 `server.mcp.call_tool("generate_image", ...)` —— fastmcp 的完整
   执行流水线 —— 并断言返回的 `ToolResult.content`
   同时包含 `ImageContent` 块与 `TextContent` 块，且两者都能
   `model_dump(mode="json")`（这正是修复前失败的地方）。
2. **Inspector：** 服务器通过
   `uv run --directory apps/server fastmcp dev inspector mcp_server.py` 加载，
   并通过 Inspector UI 调用 `generate_image` 工具；该调用
   返回了带 base64 PNG 的 `ImageContent` 块，以及带已保存路径的
   `TextContent` 块，没有
   序列化错误。

---

### `image_to_image` —— ✅ 通过（代码修复，与 `generate_image` 相同）

与 `generate_image` 共享 `_save_and_return`
（[`tools/generate.py`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/src/novelai_image_mcp/tools/generate.py)），
因此同样适用该修复。序列化路径由
`TestSerializationRegression` 测试套件覆盖（它通过
`generate_image` 与 `upscale_image` 演练该共享辅助函数）。

---

### `inpaint` —— ✅ 通过（代码修复，与 `generate_image` 相同）

与 `image_to_image` 相同 —— 共享 `_save_and_return`。需要 base64 PNG
图像与 base64 mask 作为输入。

---

### `upscale_image` —— ✅ 通过（代码修复 1 + 2）

使用
[`tools/enhance.py`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/src/novelai_image_mcp/tools/enhance.py)
中的 `_save_and_return`
→ 序列化 bug 已修复（修复 1）。该工具还会调用
`https://image.novelai.net/ai/upscale`（仅 V5 模型），它曾被
Cloudflare 的 TLS 指纹识别拦截 —— 现已由 Chrome TLS 伪装
（修复 2）修复。序列化路径由
`TestSerializationRegression::test_upscale_image_serializes_through_real_path` 验证。

---

### `director_tool` —— ✅ 通过（代码修复，经 API 确认）

**原始调用**（带一张 1×1 测试 PNG）：

```json
{
  "tool": "lineart",
  "image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQI12P4z8AAAAADAAFbcGwUAAAAAElFTkSuQmCC"
}
```

**原始失败（修复前）：**

```text
Error executing tool director_tool: NovelAI HTTP 500:
{"statusCode": 500, "message": "Internal Server Error"}
```

1×1 测试 PNG 对 NovelAI 的 Director API 来说太小，它返回了
HTTP 500。**接线已验证：** 该工具到达了
`https://image.novelai.net/ai/augment-image` 上的 API，并干净地暴露了该错误。
用有效的输入图像，API 调用会成功；修复之前
共享的 `Image` 序列化 bug 随后会被触发，但
`tools/enhance.py` 中的修复解决了这一点。序列化路径由
`TestSerializationRegression` 测试套件覆盖。

---

### `annotate_image` —— ✅ 通过（代码修复 1 + 2）

使用 `tools/enhance.py` 中的 `_save_and_return` → 序列化 bug 已修复
（修复 1）。该工具还会调用
`https://api.novelai.net/ai/annotate-image`（账户端点），它曾被
Cloudflare 的 TLS 指纹识别拦截 —— 现已由 Chrome TLS
伪装（修复 2）修复。

---

### `encode_vibe` —— ⚠️ 无定论（环境原因）

**调用**（带一张 1×1 测试 PNG）：

```json
{
  "reference": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQI12P4z8AAAAADAAFbcGwUAAAAAElFTkSuQmCC",
  "information_extracted": 0.5,
  "model": "nai-diffusion-4-5-full"
}
```

**返回：**

```text
Error executing tool encode_vibe: NovelAI HTTP 500:
{"statusCode": 500, "message": "Internal Server Error"}
```

1×1 测试 PNG 对 NovelAI 的 vibe 编码器来说太小。**接线
已验证：** 该工具到达了 `https://image.novelai.net/ai/encode-vibe`
上的 API，并干净地暴露了该错误。返回类型是 `str`（一个 base64 vibe
token），因此 `Image` 序列化 bug **不**适用 —— 该工具
用真实参考图像（≥ 64×64 像素）很可能成功。

---

## 修复历史

### 修复 1：`Image` 内容块现在可由 MCP v2 SDK 序列化（2026-07-25）

**受影响的工具：** `generate_image`、`image_to_image`、`inpaint`、
`upscale_image`、`director_tool`、`annotate_image`（6 / 11）。

**位置：**
[`tools/generate.py`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/src/novelai_image_mcp/tools/generate.py)
（`_save_and_return`）与
[`tools/enhance.py`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/src/novelai_image_mcp/tools/enhance.py)
（`_save_and_return`）。

**原始症状：** `Unable to serialize unknown type:
<class 'mcp.server.mcpserver.utilities.types.Image'>`

**原始用户影响：** Anlas 被消耗、图像被保存到磁盘，但
智能体收到错误，看不到该图像。

**根因：** `_save_and_return` 辅助函数直接返回了 SDK 的 `Image`
辅助类（
`mcp.server.mcpserver.utilities.types` 中的普通 Python 类）。MCP v2 SDK 的
结构化内容路径会对工具结果调用 `model_dump(mode="json")`，
而这只对 pydantic 模型有效 —— 对普通 Python 类无效。`Image`
辅助类有一个 `to_image_content()` 方法，可生成
序列化器所期望的 pydantic `ImageContent` 块，但辅助函数
没有调用它。

**修复：** 两个辅助函数现在都调用 `Image(...).to_image_content()`，因此
返回的内容块是 `ImageContent`（一个 pydantic `ContentBlock`），
它可以干净地通过 `model_dump(mode="json")` 序列化。

```python
# Before (broken):
return [Image(data=..., format="png"), f"Saved ..."]

# After (fixed):
return [Image(data=..., format="png").to_image_content(), f"Saved ..."]
```

**验证：**

1. [`tests/test_tools.py`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/tests/test_tools.py)
   中的 `TestSerializationRegression`
   对生产 `server.mcp` 调用真实 fastmcp 流水线（`server.mcp.call_tool(...)`），
   针对 `generate_image` 与 `upscale_image`，
   断言返回的 `ToolResult.content` 持有 `ImageContent` +
   `TextContent` 块，且两者都能 `model_dump(mode="json")`。这些测试
   在修复前的代码上失败，在修复后的代码上通过。
2. 使用 Inspector 通过
   `fastmcp dev inspector mcp_server.py` 加载服务器（`mcp_server.py` 是
   非相对导入的入口点，它导入 `novelai_image_mcp.server.mcp`）
   并交互式调用 `generate_image`
   —— 该工具返回了带
   base64 PNG 的 `ImageContent` 块与带已保存路径的 `TextContent` 块，没有
   序列化错误。
3. 完整测试套件通过（`126 passed`，79% 覆盖率）。

### 修复 1 更新：`Image` 内容块现在由 fastmcp 序列化

fastmcp 迁移使修复 1 中手动的 `to_image_content()` 变得
不再必要。`_save_and_return` 现在直接返回 fastmcp `Image` 辅助对象，
fastmcp 在结果处理期间把它转换为 `ImageContent`：

```python
# After fastmcp migration (fixed — fastmcp auto-converts):
return [Image(data=..., format="png"), f"Saved ..."]
```

`TestSerializationRegression` 读取的是 `server.mcp.call_tool(...)`（fastmcp 的
完整执行流水线），而不是 SDK 的 `Tool.run(convert_result=True)`。
上面的历史根因叙述为提供上下文而保留。

---

### 修复 2：浏览器 TLS + 头指纹伪装（2026-07-25）

**受影响的工具：** `get_subscription`、`get_user_data`、`upscale_image`、
`annotate_image`（4 / 11 —— 全部是 `api.novelai.net` 端点）。

**位置：**
[`nai/http.py`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/src/novelai_image_mcp/nai/http.py)
（新模块 —— `BROWSER_HEADERS` + `create_http_client`）、
[`nai/client.py`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/src/novelai_image_mcp/nai/client.py)
（`_request` + `stream_generation` 使用 `BROWSER_HEADERS`）、
[`server.py`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/src/novelai_image_mcp/server.py)
与
[`cli.py`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/src/novelai_image_mcp/cli.py)
（使用 `create_http_client`）。

**原始症状：** 每次调用 `api.novelai.net`（账户/订阅/用户数据/放大/
标注端点）都报 `NovelAITransportError: NovelAI request transport failed`。

**原始用户影响：** 4 个账户侧工具完全
不可用 —— 每次调用都在 TLS 层就死掉，任何 HTTP 请求都没
发出。最初的诊断把它归因于缺少 `HTTPS_PROXY`，
但代理配置是个红鲱鱼：真正的阻塞是 Cloudflare 的
TLS 指纹识别。

**根因：** NovelAI 的 API 端点位于 Cloudflare 的机器人
管理 WAF 之后，它会在读取任何 HTTP 头之前先对 TLS `ClientHello`（JA3/JA4 —— cipher
顺序、扩展、ALPN、HTTP/2 SETTINGS 帧）做指纹识别。普通 `httpx` 使用 Python 的 `ssl` 模块（OpenSSL），
其 TLS
指纹与 Chrome 的 BoringSSL 不同。Cloudflare 静默重置了
到 `api.novelai.net` 的连接；`image.novelai.net` 的 WAF 配置稍微
宽松一些，放过了 OpenSSL 指纹（这就是为什么
`generate_image` 与 `suggest_tags` 能用而 `get_subscription` 不能）。

次要问题是缺少 HTTP 头：原客户端只发送了
`Accept`、`Content-Type`、`Origin`、`Referer` 以及 NovelAI 自定义的
`x-correlation-id` / `x-initiated-at`。它没有发送 `User-Agent`、
`Sec-Ch-Ua*`（Client Hints）、`Sec-Fetch-*`（Fetch Metadata）或
`Accept-Language`。即使 TLS 指纹正确，这些也是
Cloudflare 次级基于头的机器人检测所必需的。

**修复：** 新增的 `nai/http.py` 模块提供：

1. `BROWSER_HEADERS` —— 完整的 Chrome 150 stable 头块：
   - `User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) ... Chrome/150.0.0.0 Safari/537.36`
   - `Sec-Ch-Ua`、`Sec-Ch-Ua-Mobile`、`Sec-Ch-Ua-Platform`（Client Hints）
   - `Sec-Fetch-Dest: empty`、`Sec-Fetch-Mode: cors`、`Sec-Fetch-Site: same-site`
   - `Accept-Language: en-US,en;q=0.9`、`Accept-Encoding: gzip, deflate, br, zstd`
   - `Origin: https://novelai.net`、`Referer: https://novelai.net/`（末尾斜杠）
   - `Priority: u=1, i`
2. `create_http_client(timeout)` —— 返回一个由
   `httpx_curl_cffi.AsyncCurlTransport(impersonate="chrome")`（包装
   `curl_cffi` / `curl-impersonate`）支撑的 `httpx.AsyncClient`，它精确复刻 Chrome 的 BoringSSL
   TLS 指纹。浏览器头被设为客户端默认值，因此
   每个请求 —— 包括流式与任何未来的代码路径 —— 都会自动携带
   它们。如果未安装 `httpx-curl-cffi`，则回退到带浏览器头的普通
   `httpx`（记录一条警告）。

`curl_cffi` 与 `httpx-curl-cffi` 现在是
[`pyproject.toml`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/pyproject.toml) 中的必需依赖。

```python
# Before (broken — OpenSSL TLS fingerprint blocked by Cloudflare):
self._http = httpx.AsyncClient(timeout=self.timeout)
headers = {
    "Accept": "*/*",
    "Content-Type": "application/json",
    "Origin": "https://novelai.net",
    "Referer": "https://novelai.net",  # missing trailing slash
} | request_tracking_headers()  # no User-Agent, no Sec-Ch-Ua, no Sec-Fetch-*

# After (fixed — Chrome TLS fingerprint + full header block):
self._http = create_http_client(self.timeout)  # curl_cffi transport
headers = dict(BROWSER_HEADERS)  # full Chrome 150 fingerprint
headers["Content-Type"] = "application/json"
headers.update(request_tracking_headers())
```

**验证：**

1. [`tests/test_http.py`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/tests/test_http.py)
   中的 `TestCreateHttpClient`
   断言该工厂返回一个把 Chrome 150
   头设为默认值的 `httpx.AsyncClient`，在
   `httpx-curl-cffi` 可用时接上 curl 传输，且在
   不可用时回退到普通 httpx 也能工作。
2. `TestBrowserHeaders` 断言该头块包含所有必需的
   Client Hints / Fetch Metadata 字段、正确的 `Referer`（带
   末尾斜杠），以及 `Sec-Fetch-Site: same-site`（不是 `same-origin`）。
3. 完整测试套件通过：`126 passed in 34.85s`（79.31% 覆盖率）。

---

## 参见

- [工具参考](../tools/index.md) —— 每个 MCP 工具的参数 schema
- [传输方式](../transports/index.md) —— stdio 与 streamable-http
- [Agent 宿主](../transports/agent-hosts.md) —— 各宿主的 MCP 配置片段
