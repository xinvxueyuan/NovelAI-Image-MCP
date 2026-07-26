# 配置

所有运行时配置都通过环境变量读取（由 `pydantic-settings` 在
`novelai_image_mcp.settings` 模块中解析）。权威参考是仓库根目录下的
[`.env.example`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.env.example)。

## 加载顺序

1. 进程环境（最高优先级）
2. 当前工作目录下的 `.env` 文件
3. 内置默认值（最低优先级）

`.env` 文件以 UTF-8 解析；未知键会被忽略；变量名大小写不敏感
（`NOVELAI_TOKEN` 和 `novelai_token` 等价）。

---

## NovelAI 凭据

| 变量 | 默认值 | 是否必需 | 说明 |
|---|---|---|---|
| `NOVELAI_TOKEN` | — | *二选一* | 持久 API token（推荐）。从 <https://novelai.net> → Account 获取。 |
| `NOVELAI_USERNAME` | — | *二选一* | 用于 access-key 登录的用户名（邮箱）。 |
| `NOVELAI_PASSWORD` | — | *二选一* | 账户密码。与 `NOVELAI_USERNAME` 组合后通过 argon2id 派生 access key。 |

:::{important}
设置 `NOVELAI_TOKEN` **或者** `NOVELAI_USERNAME` + `NOVELAI_PASSWORD`
组合 **之一**。如果两者都未设置，服务器在启动时会抛出 `RuntimeError`
（见 `NovelAISettings.has_credentials`）。
:::

## 端点

| 变量 | 默认值 | 说明 |
|---|---|---|
| `NOVELAI_IMAGE_BASE_URL` | `https://image.novelai.net` | 图像生成 / Director / 放大端点。 |
| `NOVELAI_ACCOUNT_BASE_URL` | `https://image.novelai.net` | 账户 / 订阅 / 标签推荐端点。NovelAI 已将所有第三方 API 访问收口到 `image.novelai.net`，因此该端点与 `NOVELAI_IMAGE_BASE_URL` 共用同一主机。 |
| `NOVELAI_TIMEOUT` | `120`（秒） | 单次 NovelAI 请求的 HTTP 超时。 |

:::{tip}
在集成测试期间，可以覆盖 `NOVELAI_IMAGE_BASE_URL` 指向本地 mock（例如
`http://localhost:9000`）。`apps/server/tests/` 中的测试使用
[`respx`](https://github.com/transportapp/respx) 替代，不需要这样做。
:::

## 生成默认值

这些变量调整 `generate_image`（以及任何接受相同参数的工具）使用的默认值。
它们可以在每次工具调用时被覆盖。

| 变量 | 默认值 | 范围 | 说明 |
|---|---|---|---|
| `NOVELAI_DEFAULT_MODEL` | `nai-diffusion-4-5-full` | 见 `Model` 枚举 | V3 / V4 / V4.5 模型 ID。 |
| `NOVELAI_DEFAULT_WIDTH` | `832` | 64–49152，64 的倍数 | 图像宽度（像素）。 |
| `NOVELAI_DEFAULT_HEIGHT` | `1216` | 64–49152，64 的倍数 | 图像高度（像素）。 |
| `NOVELAI_DEFAULT_STEPS` | `28` | 1–50 | 采样器迭代次数。 |
| `NOVELAI_DEFAULT_SCALE` | `5.0` | 0–20 | Classifier-free guidance 比例。 |
| `NOVELAI_DEFAULT_SAMPLER` | `k_euler_ancestral` | 见 `Sampler` 枚举 | 采样器 ID。 |

## 客户端

| 变量 | 默认值 | 范围 | 说明 |
|---|---|---|---|
| `NOVELAI_VIBE_CACHE_ENTRIES` | `64` | 1–1024 | Vibe-transfer 编码缓存大小。对同一参考图编码两次会命中缓存而不是重新调用 API。 |

## 输出

| 变量 | 默认值 | 说明 |
|---|---|---|
| `NOVELAI_OUTPUT_DIR` | `outputs` | 生成 PNG 的保存目录。相对路径相对于服务器工作目录解析。目录按需创建。 |

## MCP 传输方式

| 变量 | 默认值 | 范围 | 说明 |
|---|---|---|---|
| `MCP_TRANSPORT` | `stdio` | `stdio` \| `streamable-http` | 服务器暴露给客户端的方式。 |
| `MCP_HOST` | `127.0.0.1` | 任意绑定地址 | `streamable-http` 的绑定主机。 |
| `MCP_PORT` | `8000` | 1–65535 | `streamable-http` 的绑定端口。 |
| `MCP_PATH` | `/mcp` | 路径字符串 | streamable-http 端点的 HTTP 路径。完整 URL：`http://${MCP_HOST}:${MCP_PORT}${MCP_PATH}`。 |

:::{warning}
默认的 `MCP_HOST=127.0.0.1` **仅绑定到 localhost**。要将服务器暴露给局域网
中的其他机器，请设置 `MCP_HOST=0.0.0.0` —— 并将其放在 TLS 终止或经过认证
的反向代理后面。MCP streamable-http 传输方式 **不** 实现认证。
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
MCP_TRANSPORT=streamable-http
MCP_HOST=0.0.0.0
MCP_PORT=8000
MCP_PATH=/mcp

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

## 另请参见

- `novelai_image_mcp.settings` 模块（API 参考暂仅英文）
- [.env.example](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.env.example)
- 传输方式章节（stdio 与 streamable-http 的权衡，暂仅英文）
