# 配置

所有运行时配置都通过环境变量完成（由
[`novelai_image_mcp.settings`](api/settings.md) 中的 `pydantic-settings` 读取）。权威参考是仓库根目录下的
[`.env.example`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.env.example)。

## 加载顺序

1. 进程环境（最高优先级）
2. 当前工作目录下的 `.env` 文件
3. 内置默认值（最低优先级）

`.env` 文件以 UTF-8 解析；未知键会被忽略；变量名
大小写不敏感（`NOVELAI_TOKEN` 与 `novelai_token`
等价）。

---

## NovelAI 凭据

| 变量 | 默认值 | 是否必需 | 说明 |
|---|---|---|---|
| `NOVELAI_TOKEN` | — | *二选一* | 持久 API token（推荐）。从 <https://novelai.net> → Account 获取。 |
| `NOVELAI_USERNAME` | — | *二选一* | 用于 access-key 登录的用户名（邮箱）。 |
| `NOVELAI_PASSWORD` | — | *二选一* | 账户密码。与 `NOVELAI_USERNAME` 组合后经 argon2id 派生 access key。 |

:::{important}
设置 `NOVELAI_TOKEN` **或者** `NOVELAI_USERNAME` + `NOVELAI_PASSWORD`
组合 **之一**。如果两者都未设置，服务器在启动时会抛出 `RuntimeError`
（见 [`NovelAISettings.has_credentials`](api/settings.md)）。
:::

## 端点

| 变量 | 默认值 | 说明 |
|---|---|---|
| `NOVELAI_IMAGE_BASE_URL` | `https://image.novelai.net` | 图像生成 / Director / encode-vibe / suggest-tags 端点。NovelAI 已将大部分第三方 API 访问收口到 `image.novelai.net`。 |
| `NOVELAI_ACCOUNT_BASE_URL` | `https://image.novelai.net` | 账户 / 订阅 / 用户数据端点。与 `NOVELAI_IMAGE_BASE_URL` 共用同一主机。 |
| `NOVELAI_LEGACY_IMAGE_BASE_URL` | `https://api.novelai.net` | `/ai/annotate-image` 的 Primary API 主机 —— 唯一从未迁移的端点（其他所有端点在这里都返回 404）。独立的 `/ai/upscale` 位于 `image.novelai.net`，且仅支持 V5。 |
| `NOVELAI_TIMEOUT` | `120`（秒） | 单次 NovelAI 请求的 HTTP 超时。 |

:::{tip}
在集成测试期间，可以覆盖 `NOVELAI_IMAGE_BASE_URL` 指向本地 mock（例如
`http://localhost:9000`）。`apps/server/tests/` 中的测试改用
[`respx`](https://github.com/lundberg/respx)，不需要这样做。
:::

## 生成默认值

这些变量调整 `generate_image`（以及任何接受相同参数的工具）使用的默认值。
它们可以在每次工具调用时被覆盖。

| 变量 | 默认值 | 范围 | 说明 |
|---|---|---|---|
| `NOVELAI_DEFAULT_MODEL` | `nai-diffusion-4-5-full` | 见 `Model` 枚举 | V3 / V4 / V4.5 / V5 模型 id。 |
| `NOVELAI_DEFAULT_WIDTH` | `832` | 64–49152，64 的倍数 | 图像宽度（像素）。 |
| `NOVELAI_DEFAULT_HEIGHT` | `1216` | 64–49152，64 的倍数 | 图像高度（像素）。 |
| `NOVELAI_DEFAULT_STEPS` | `28` | 1–50 | 采样器迭代次数。 |
| `NOVELAI_DEFAULT_SCALE` | `5.0` | 0–20 | Classifier-free guidance 比例。 |
| `NOVELAI_DEFAULT_SAMPLER` | `k_euler_ancestral` | 见 `Sampler` 枚举 | 采样器 id。 |

## 客户端

| 变量 | 默认值 | 范围 | 说明 |
|---|---|---|---|
| `NOVELAI_VIBE_CACHE_ENTRIES` | `64` | 1–1024 | Vibe-transfer 编码缓存大小。对同一参考图编码两次会命中缓存，而不是重新调用 API。 |

## 输出

| 变量 | 默认值 | 说明 |
|---|---|---|
| `NOVELAI_OUTPUT_DIR` | `outputs` | 生成 PNG 的保存目录。相对路径相对于服务器工作目录解析。目录按需创建。 |
| `NOVELAI_UPSCALE_MODEL` | `nai-diffusion-5-full` | 独立 4× 放大器运行的模型。只有 V5 系列支持独立放大（`nai-diffusion-5-full`、`nai-diffusion-5-curated`）。 |

## MCP 传输方式

| 变量 | 默认值 | 范围 | 说明 |
|---|---|---|---|
| `MCP_TRANSPORT` | `stdio` | `stdio` \| `http`（旧别名 `streamable-http`） | 服务器如何把自己暴露给客户端。 |
| `MCP_HOST` | `127.0.0.1` | 任意绑定地址 | HTTP 传输的绑定主机。 |
| `MCP_PORT` | `8000` | 1–65535 | HTTP 传输的绑定端口。 |
| `MCP_PATH` | `/mcp` | 路径字符串 | MCP 端点的 HTTP 路径。完整 URL：`http://${MCP_HOST}:${MCP_PORT}${MCP_PATH}`。 |
| `MCP_AUTH_TOKEN` | *（空）* | 任意 token 字符串 | 设置后，HTTP 传输要求 `Authorization: Bearer <token>`。留空则端点保持开放（见下方警告）。 |
| `MCP_LOG_LEVEL` | *（框架默认）* | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` \| `CRITICAL` | 启动时传给 FastMCP 的日志级别。 |

:::{note}
`http` 是规范的传输名；`streamable-http` 作为旧别名被接受，选择的是同一个传输。
`MCP_PATH` 会直接传给 FastMCP，因此改它会移动端点。
:::

:::{warning}
默认的 `MCP_HOST=127.0.0.1` **仅绑定到 localhost**。要把服务器暴露给局域网
中的其他机器，请设置 `MCP_HOST=0.0.0.0` —— 并且要么设置
`MCP_AUTH_TOKEN`，要么把它放在 TLS 终止 / 经过认证的反向
代理之后。当 `MCP_AUTH_TOKEN` 与 `MCP_ROUTE_TOKENS` 都未设置时，HTTP
传输根本不安装认证中间件 —— 端点会接受
未认证的客户端。
:::

## Insiders、分路与审计

除非请求发送该头，否则 `X-MCP-Insiders` opt-in 接口面是不生效的。
这些变量配置它读取的头名以及它会打开
的副作用；完整契约见
[Insiders 头、分路与审计](development/insiders-and-routing.md)。

| 变量 | 默认值 | 说明 |
|---|---|---|
| `MCP_INSIDERS_HEADER` | `X-MCP-Insiders` | 按请求 opt-in 头的名字。查找大小写不敏感。 |
| `MCP_MODEL_HEADERS` | `["X-MCP-Model", "X-MCP-Model-Name"]` | JSON 列表。声明 model 的有序候选；第一个非空头胜出。 |
| `MCP_AGENT_HEADERS` | `["X-MCP-Agent-ID", "X-MCP-Agent", "X-MCP-Agent-Source"]` | JSON 列表。agent 的有序候选，也是第一个 route 来源。 |
| `MCP_CLIENT_HEADERS` | `["X-MCP-Client", "X-MCP-Client-Session-Id"]` | JSON 列表。client 的有序候选；名字中含 `session` 的第一个提供 session。 |
| `MCP_INSIDERS_DISABLED_FEATURES` | `[]` | JSON 列表。运维侧强制关闭开关：此处列出的特性无论客户端发送什么都会保持关闭。 |
| `MCP_ROUTE_SCOPED_OUTPUT` | `true` | 路由生效期间，把图像写入 `<NOVELAI_OUTPUT_DIR>/<sanitised route>/`。 |
| `MCP_AUDIT_LOG_PATH` | *（未设置）* | 审计 JSONL 目标位置；未设置表示 `<NOVELAI_OUTPUT_DIR>/audit.jsonl`。 |
| `MCP_ROUTE_TOKENS` | *（未设置）* | JSON 对象 `{"<route>": "<token>"}`。按路由绑定的 bearer token；与请求声明的 route 不一致的 token 会以 `401` 被拒绝。 |

:::{warning}
上面五个列表/字典变量是 **JSON**：
`MCP_AGENT_HEADERS='["X-MCP-Agent-ID"]'` 可用，逗号分隔的值会
抛出 settings 错误，而空值不是合法 JSON —— 请把该行注释掉，而不是
留空。
:::

---

## 组合示例

以下是一个用于远程 streamable-http 部署的生产级 `.env`：

```bash
# ── Auth ──
NOVELAI_TOKEN=pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ── Generation defaults (Opus tier, high quality) ──
NOVELAI_DEFAULT_MODEL=nai-diffusion-4-5-full
NOVELAI_DEFAULT_WIDTH=1024
NOVELAI_DEFAULT_HEIGHT=1024
NOVELAI_DEFAULT_STEPS=28
NOVELAI_DEFAULT_SCALE=5.0
NOVELAI_DEFAULT_SAMPLER=k_euler_ancestral

# ── Output (persist to a Docker volume) ──
NOVELAI_OUTPUT_DIR=/app/outputs

# ── Transport ──
MCP_TRANSPORT=http
MCP_HOST=0.0.0.0
MCP_PORT=8000
MCP_PATH=/mcp
# Require "Authorization: Bearer <token>" on the HTTP endpoint. Without it
# the endpoint is open — front it with TLS + a reverse proxy instead.
MCP_AUTH_TOKEN=change-me

# ── Client ──
NOVELAI_VIBE_CACHE_ENTRIES=128
NOVELAI_TIMEOUT=180
```

## Docker 中的环境变量

[`Dockerfile`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/Dockerfile)
通过 `docker-compose.yml` 的 `env_file:` 指令读取 `.env`。要在运行时覆盖
单个变量而不编辑 `.env`：

```bash
docker compose run -e MCP_PORT=9000 mcp
```

对于 Kubernetes，将 env 文件挂载为 `Secret`，或使用支持 ConfigMap /
Secret 的 env provider。

## 参见

- [`novelai_image_mcp.settings` API 参考](api/settings.md)
- [.env.example](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.env.example)
- [传输方式](transports/index.md) —— stdio 与 HTTP 的取舍
