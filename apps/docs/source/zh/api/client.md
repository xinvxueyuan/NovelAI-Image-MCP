# `novelai_image_mcp.nai` —— NovelAI HTTP 客户端

`nai/` 子包是 NovelAI HTTP 客户端。它**与 MCP 无关** —— 可以在任何异步 Python
代码中独立使用，不依赖 MCP 服务器。

## 子模块

### `novelai_image_mcp.nai.client`

高层异步客户端。在共享的 `httpx.AsyncClient` 之上封装了线格式编码器
（`payload.build_generation_payload`）与响应解码器
（`response.parse_messagepack_images`）。

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.client
   :members:
   :undoc-members:
   :show-inheritance:
```

### `novelai_image_mcp.nai.constants`

NovelAI API 接口面的枚举：`Action`、`Model`、`Sampler`、
`DirectorTool`、`Emotion`、`EmotionLevel`、`ControlNetModel`、`Endpoint`、
`NoiseSchedule`。以及谓词函数 `is_v4_model`、`is_v5_model`、
`supports_vibe` 与 `is_inpaint_model`。

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.constants
   :members:
   :undoc-members:
   :show-inheritance:
```

### `novelai_image_mcp.nai.models`

线格式的 Pydantic 模型：`GenerationRequest`、
`CharacterPrompt`、`NovelAIGenerationPlan`。

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.models
   :members:
   :undoc-members:
   :show-inheritance:
```

### `novelai_image_mcp.nai.auth`

Argon2id access-key 派生 + 每请求的追踪头。

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.auth
   :members:
   :undoc-members:
   :show-inheritance:
```

### `novelai_image_mcp.nai.payload`

`build_generation_payload` —— 线格式编码器（兼容 MessagePack）。

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.payload
   :members:
   :undoc-members:
   :show-inheritance:
```

### `novelai_image_mcp.nai.response`

响应解析：`NovelAIImage`、`parse_messagepack_images`、
`parse_zip_images`、`check_status`、`GenerationEvent`。

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.response
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: NovelAIProviderError, NovelAIResponseError, NovelAIAuthenticationError, NovelAIConcurrencyError, NovelAIInsufficientCreditsError, NovelAIValidationError
```

:::{note}
上面列出的异常类被导入到 ``response`` 中，以便在 ``check_status`` 中抛出；
它们记录在定义它们的模块 `novelai_image_mcp.nai.exceptions` 下（见下一小节）。
:::

### `novelai_image_mcp.nai.exceptions`

领域异常层级：

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.exceptions
   :members:
   :undoc-members:
   :show-inheritance:
```

### `novelai_image_mcp.nai.errors`

错误体解析与官方错误码说明：`ErrorInfo`、
`OFFICIAL_CODE_EXPLANATIONS`、`explain`、`parse_error_body`。

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.errors
   :members:
   :undoc-members:
   :show-inheritance:
```

### `novelai_image_mcp.nai.service`

`create_novelai_client` 工厂 + `NovelAIConfigLike` 协议。该工厂接收一个
类 settings 对象与一个 `httpx.AsyncClient`，返回接线完整的 `NovelAIClient`。

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.service
   :members:
   :undoc-members:
   :show-inheritance:
```

## 官方错误码

该客户端抛出的每个 NovelAI 错误都带有错误 ``code``（HTTP 状态码，或 API 自身的
流式错误码），并且在有文档的情况下带有 NovelAI 的官方说明。两者都会追加到消息中，
并作为异常的属性暴露：

| 错误码 | 含义（官方） |
|---|---|
| `400` | 无效请求（校验失败） |
| `401` | 认证失败 |
| `402` | 需要有效订阅或 Anlas |
| `409` | 请求冲突 |
| `429` | 速率限制 / 并发限制 |
| `5xx` | NovelAI 上游错误 |

所有异常都派生自 ``NovelAIError``，并暴露 ``.code`` /
``.explanation``（对于传输、超时以及不带服务端错误码的本地校验失败，两者均为
``None``）。解析辅助函数见 `novelai_image_mcp.nai.errors` 模块。

## 参见

- [架构 → `NovelAIClient`](../development/architecture.md#novelaiclientnai-子包)
- [GitHub 源码](https://github.com/xinvxueyuan/NovelAI-Image-MCP/tree/main/apps/server/src/novelai_image_mcp/nai)
