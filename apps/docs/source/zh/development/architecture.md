# 架构

服务器是一个薄薄的组合根，架在 NovelAI HTTP 客户端之上。本页
逐一说明各层以及它们如何拼装在一起。

## 分层

```{mermaid}
graph TD
    A[Agent / MCP host] -->|JSON-RPC over stdio / HTTP| B[FastMCP]
    B -->|middleware| M[ToolCallLoggingMiddleware]
    B -->|optional bearer auth| N[mcp_auth.build_auth]
    B -->|lifespan| C[AppContext: NovelAIClient + NovelAISettings]
    C -->|Depends DI| D[tools/* · resources.py · prompts.py]
    D -->|calls| E[NovelAIClient nai/]
    E -->|httpx.AsyncClient| F[NovelAI API]
    D -->|saves| G[output.py → outputs/]
    D -->|ImageContent| A
    D -->|structured output| A
```

## `FastMCP` 组合根

[`novelai_image_mcp.server`](../api/server.md) 是组合根。它：

1. 构建一个由 MCP `lifespan` 持有的、唯一的共享 `httpx.AsyncClient`
   （连接池）。
2. 用 settings + 该 httpx 客户端构建 `NovelAIClient`。
3. 把两者作为 `AppContext` 产出，依赖提供者再将其暴露给每个
   工具、资源与 prompt。
4. 在关闭时把两者都拆掉（先关闭 `NovelAIClient`，再关闭
   底层 httpx 会话 —— 即使客户端关闭抛错，httpx
   会话仍会被释放，以免泄漏 socket）。

该实例本身在导入时配置一次：

```python
mcp = FastMCP(
    name="novelai-image",
    version=__version__,          # serves the package version, not the framework version
    instructions=INSTRUCTIONS,    # how an agent should use the server
    lifespan=lifespan,
    auth=build_auth(get_mcp_settings()),   # None unless MCP_AUTH_TOKEN is set
    mask_error_details=True,      # only ToolError messages reach the client
    middleware=[ToolCallLoggingMiddleware()],
)

from . import prompts, resources, tools  # decorators attach to `mcp`
```

工具、资源与 prompt 通过模块级装饰器挂载，因此没有 `register(mcp)`
函数需要调用：导入 `tools/`（或 `resources.py`、`prompts.py`）就是注册步骤，
它发生在 `mcp` 已存在之后。

```python
@asynccontextmanager
async def lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
    settings = get_novelai_settings()
    if not settings.has_credentials():
        raise RuntimeError("NovelAI credentials are not configured...")
    http_client = create_http_client(timeout=settings.timeout)
    client = create_novelai_client(settings, http_client=http_client)
    try:
        yield AppContext(client=client, settings=settings)
    finally:
        try:
            await client.aclose()
        finally:
            if not http_client.is_closed:
                await http_client.aclose()
```

每个组件都声明自己需要什么；FastMCP 按请求解析它，并
让该依赖不出现在输入 schema 中：

```python
@mcp.tool(title=..., tags={...}, annotations=IMAGE_WRITE_ANNOTATIONS)
@translate_errors
async def generate_image(
    prompt: str,
    model: Model | None = None,
    app: AppContext = Depends(get_app_context),   # hidden from the schema
) -> list[Any]: ...
```

`deps.py` 持有提供者（`get_app_context`、`get_client`），
`tools/_errors.py` 持有 `NovelAIError`/`ValueError` → `ToolError`
的翻译。翻译必须发生在工具体内部：等到中间件钩子看到这次调用时，
FastMCP 已经把异常屏蔽掉了。

## `NovelAIClient`（`nai/` 子包）

`nai/` 子包是 NovelAI HTTP 客户端。它**不依赖** MCP —— 可以在
任何异步 Python 代码中独立使用。

| 模块 | 职责 |
|---|---|
| `auth.py` | Argon2id access-key 派生；请求追踪头。 |
| `client.py` | `NovelAIClient` —— 高层异步 API（`generate`、`upscale`、`director`、`annotate`、`suggest_tags`、`encode_vibe`、`get_subscription`、`get_user_data`）。 |
| `constants.py` | 枚举：`Action`、`Model`、`Sampler`、`DirectorTool`、`Emotion`、`EmotionLevel`、`ControlNetModel`、`Endpoint`、`NoiseSchedule`。以及 `is_v4_model`、`is_inpaint_model`。 |
| `exceptions.py` | 领域异常：`NovelAIAuthenticationError`、`NovelAIValidationError`、`NovelAIInsufficientCreditsError`、`NovelAIConcurrencyError`、`NovelAIImageError`、`NovelAIProviderError`。 |
| `models.py` | Pydantic 模型：`GenerationRequest`、`CharacterPrompt`、`NovelAIGenerationPlan`。 |
| `payload.py` | `build_generation_payload` —— 线格式编码器（兼容 MessagePack）。 |
| `response.py` | `NovelAIImage`、`parse_messagepack_images`、`parse_zip_images`、`check_status`、`GenerationEvent`。 |
| `service.py` | `create_novelai_client` 工厂 + `NovelAIConfigLike` 协议。 |

## 工具层

`novelai_image_mcp.tools` 是 fastmcp `FastMCP`
工具装饰器与 `NovelAIClient` 之间的一层薄适配器。每个工具：

1. 通过 `Depends(get_app_context)` 参数（`deps.py`）接收 `AppContext`，
   因此它不出现在输入 schema 中。
2. 由工具参数构建 `GenerationRequest`（或等价物）。
3. 调用对应的 `NovelAIClient` 方法。
4. 通过 `output.save_image` 持久化结果。
5. 返回 MCP 内容块列表：`[Image, text_path]`。

工具刻意不承载业务逻辑 —— 校验与参数
编组都在 `nai/` 中，因此同一条代码路径同时服务 MCP 服务器、
CLI 与直接客户端调用。枚举类型的参数（`Model`、`Sampler`、
`DirectorTool`、……）仍会在工具体内被强制转换，因此直接的
Python 调用方可以传普通字符串，而 MCP 调用方会得到 schema
校验。

除了工具之外，服务器还暴露只读上下文：

| 组件 | 位置 | 用途 |
|---|---|---|
| `novelai://models` | `resources.py` | 模型 id 及其能力标志。 |
| `novelai://samplers` | `resources.py` | 采样器 / noise-schedule / UC-preset 词表。 |
| `novelai://defaults` | `resources.py` | 当前生效的生成默认值（不需要凭据）。 |
| `novelai://outputs/{name}` | `resources.py` | 读回一张生成的 PNG（name 会针对输出目录做校验）。 |
| `novelai_prompt_writer`、`novelai_image_workflow` | `prompts.py` | 本仓库风格的 prompt 起草与工具编排。 |

## CLI

`novelai_image_mcp.cli` 是一个 `typer` 应用，把 MCP
工具的一个子集暴露为直接子命令（`generate`、`upscale`、`director`、`annotate`、
`info`、`serve`）。它每次调用都构造一个短生命周期的 `httpx.AsyncClient` +
`NovelAIClient` —— 没有共享会话。对于长时间的多工具
使用，请优先用 MCP 服务器（它通过 lifespan 持有池化会话）。

## 配置

`novelai_image_mcp.settings` 定义了两个 `pydantic-settings` 模型：

- `NovelAISettings` —— 凭据、端点、生成默认值
  （`NOVELAI_*` 环境变量）。
- `MCPServerSettings` —— 传输方式选择（`MCP_*` 环境变量）。

两者都从进程环境 + `.env`（位于 cwd）加载，UTF-8、大小写不敏感、
忽略未知键。`NovelAISettings` 在结构上满足
`NovelAIConfigLike`，因此客户端工厂直接消费它。

## 输出

`novelai_image_mcp.output.save_image` 把 PNG 写入
`NOVELAI_OUTPUT_DIR`，并返回路径。该目录按需创建。
文件名包含工具名 + ISO 时间戳 + 采样序号
（`generate-20260725-133702-001.png`）。

## 传输方式

服务器支持 stdio（默认）与 HTTP，在启动时通过
`MCP_TRANSPORT` 选择（`http` 是规范写法，`streamable-http` 是
被接受的别名）。两者共享同一个 `lifespan`、同一批工具与同一个
`NovelAIClient` —— 只有分帧方式不同。设置 `MCP_AUTH_TOKEN`（或
`MCP_ROUTE_TOKENS`）会让 HTTP 传输要求 bearer token；stdio 不受
影响。见 [传输方式](../transports/index.md)。

## 容器化

[`apps/server/Dockerfile`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/Dockerfile)
是一个多阶段构建：

1. **Builder 阶段**：安装 uv，导出运行时依赖（不含 dev 组），
   构建 wheel。
2. **项目构建阶段**：通过 `uv build` 构建项目 wheel。
3. **运行时阶段**：精简的 Python 3.13，非 root 的 `app` 用户，只安装
   预构建的 wheel —— 运行时镜像中没有编译器工具链。

冒烟测试（`apps/server/docker/smoke-test.py`）被构建进一个
单独的镜像（通过 `SMOKE_TEST=true` build-arg），并验证：

- 包可以干净地导入。
- Settings 可以从环境变量实例化（使用 `NOVELAI_TOKEN=pst-smoke-test`）。
- 每个工具都能注册到一个记录型的 FastMCP stub 上。
- typer CLI 可以构造且无运行时错误。

## 参见

- [`server.py` API 参考](../api/server.md)
- [`nai/` API 参考](../api/client.md)
- [测试](testing.md) —— 各层如何被隔离测试
- [发布](releasing.md) —— Docker 镜像构建与签名流程
