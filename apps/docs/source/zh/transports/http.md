# HTTP 传输方式

通过 HTTP 暴露 MCP 服务器。为远程部署、多客户端场景，以及服务器作为长期运行
服务运行的生产环境而设计。

## 运行

```bash
MCP_TRANSPORT=http uv run python -m novelai_image_mcp serve
# or via the CLI flag:
uv run python -m novelai_image_mcp serve --transport http
```

服务器默认绑定到 `127.0.0.1:8000/mcp`。可用 `MCP_HOST` / `MCP_PORT` /
`MCP_PATH` 覆盖：

```bash
MCP_TRANSPORT=http \
MCP_HOST=0.0.0.0 \
MCP_PORT=9000 \
MCP_PATH=/mcp \
uv run python -m novelai_image_mcp serve
```

## URL

完整的端点 URL 是：

```text
http://${MCP_HOST}:${MCP_PORT}${MCP_PATH}
```

默认：<http://127.0.0.1:8000/mcp>。

## 智能体配置

### MCP 客户端配置（`mcpServers`）

在 `docker compose up --build`（或任何其他 HTTP 部署）之后，用 `http` 类型
把你的 MCP 宿主指向该 URL：

```json
{
  "mcpServers": {
    "novelai-image-http": {
      "type": "http",
      "url": "http://127.0.0.1:8000/mcp",
      "headers": {
        "Authorization": "Bearer <MCP_AUTH_TOKEN>"
      }
    }
  }
}
```

把 `http://127.0.0.1:8000/mcp` 换成你自行部署的端点（例如置于 TLS 终止反向
代理之后的 `https://mcp.example.com/mcp`）。

`Authorization` 头**不是** NovelAI token：服务器用自己的 `NOVELAI_TOKEN` 与
NovelAI 通信。只有当服务器上设置了 `MCP_AUTH_TOKEN` 时这个头才有意义，此时
它必须与之匹配（`Authorization: Bearer <MCP_AUTH_TOKEN>`）。在没有
`MCP_AUTH_TOKEN`（也没有 `MCP_ROUTE_TOKENS`）时，端点会接受未认证的客户端
—— 请把它置于 TLS 与反向代理之后，或让 `MCP_HOST` 保持 localhost。

### 自定义 Python 智能体

```python
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print([t.name for t in tools])

asyncio.run(main())
```

### Curl（调试）

streamable-http 传输方式用 Server-Sent Events 承载服务器 → 客户端的消息。
用一条原始 HTTP 请求来查看服务器：

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl","version":"1.0"}}}'
```

## Insiders 头与路由

HTTP 是唯一能携带 opt-in 头的传输方式，所以路由相关的接口都放在这里。客户端
逐请求用 `X-MCP-Insiders` opt-in，并用路由头声明自己的 route：

```json
{
  "mcpServers": {
    "novelai-image-http": {
      "type": "http",
      "url": "http://127.0.0.1:8000/mcp",
      "headers": {
        "Authorization": "Bearer <MCP_AUTH_TOKEN>",
        "X-MCP-Insiders": "true",
        "X-MCP-Agent-ID": "team-a",
        "X-MCP-Model": "nai-diffusion-5-full"
      }
    }
  }
}
```

带上该头之后，服务器会解析出一个 route（这里是 `team-a`），把生成的图像写到
`<NOVELAI_OUTPUT_DIR>/team-a/`，向 `novelai_image_mcp.audit.team-a` logger
输出一行，并向审计 JSONL 追加一条记录。不带该头时什么都不变 —— 没有作用域
目录，也没有审计文件。

opt-in 同时门控 `director_tool` 的实验性 `emotion` / `emotion_level` 参数；
没有 opt-in 时，传入任意一个都会以 `ToolError` 失败。

头语法、候选头列表、审计记录字段、脱敏规则与扩展点见
[Insiders 头、路由与审计](../development/insiders-and-routing.md)。

### 按路由绑定的 token

`MCP_AUTH_TOKEN` 仍是单个静态 token。`MCP_ROUTE_TOKENS` 增加了绑定到 route 的
token，这样一个网关就能给不同团队发放不同的密钥：

```bash
MCP_AUTH_TOKEN=static-token
MCP_ROUTE_TOKENS='{"team-a":"token-for-team-a","team-b":"token-for-team-b"}'
```

路由 token 以其 route 的身份认证；当同一请求通过路由头声明了*另一个* route 时，
它会被以 `401` 拒绝。未声明任何可用 route 的请求会被接受，并归属到该 token 的
route；只有两个不同且都存在的 route 才会 fail closed。两者都未配置时，不会安装
任何认证中间件，端点行为与从前一致。

## Docker 部署

最简单的生产部署：

```bash
docker compose up --build
```

仓库根目录的
[`docker-compose.yml`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/docker-compose.yml)
用合理的默认值配置了 streamable-http 传输方式：

```yaml
services:
  mcp:
    build:
      context: .
      dockerfile: apps/server/Dockerfile
    ports:
      - "8000:8000"
    environment:
      MCP_TRANSPORT: streamable-http
      MCP_HOST: 0.0.0.0
      MCP_PORT: 8000
      NOVELAI_OUTPUT_DIR: /app/outputs
    volumes:
      - novelai-outputs:/app/outputs
```

healthcheck 每 30 秒探测一次绑定端口（默认 `8000`）。

## 生产环境检查清单

:::{warning}
**传输方式本身不带认证。** `MCP_AUTH_TOKEN`（与 `MCP_ROUTE_TOKENS`）在 MCP
端点前面加了一道 bearer 校验，但那只是一个共享密钥，不是身份提供方 —— 而且
路由头由客户端提供，可以被伪造。在把服务器暴露到互联网之前，请把它置于：

- TLS 终止（Caddy、nginx、Traefik、AWS ALB）之后
- 认证层（mTLS、OAuth 代理、API 网关）之后
- 限流器（防止 Anlas 被滥用）之后
:::

:::{tip}
**本地多客户端使用时绑定 localhost。** 如果你只需要同一台机器上的多个智能体
（例如一个 Python 智能体和一个 Node 智能体），设置 `MCP_HOST=127.0.0.1`
并跳过 TLS。只有跨网络边界时才需要反向代理。
:::

:::{admonition} 输出目录
:class: note

在 Docker 中，`NOVELAI_OUTPUT_DIR=/app/outputs` 由一个命名卷
（`novelai-outputs`）支撑。生成的图像在容器重启后仍然保留。在 Kubernetes 中，
请把该卷替换为 PersistentVolumeClaim。
:::

## 并发模型

- 服务器使用单个共享的 `httpx.AsyncClient`（连接池）。多个并发的工具调用共用
  该连接池 —— 没有逐请求的 HTTP 开销。
- 每个 MCP 请求都在服务器事件循环上运行于自己的 asyncio task 中。
- 服务器不对请求排队或限流 —— 那是上游代理的职责。

## 另请参见

- [stdio 传输方式](stdio.md)
- [Insiders 头、路由与审计](../development/insiders-and-routing.md)
- [配置](../configuration.md#mcp-传输方式)
- [Docker Compose 文件](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/docker-compose.yml)
