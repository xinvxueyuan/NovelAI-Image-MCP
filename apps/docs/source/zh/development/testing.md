# 测试

服务器的测试套件位于 `apps/server/tests/`，使用
`pytest` + `pytest-asyncio` + `respx`（HTTP mock）。

## 运行测试套件

```bash
# From repo root:
uv run --directory apps/server pytest

# With a specific reporter (e.g. short traceback):
uv run --directory apps/server pytest --tb=short

# Single file:
uv run --directory apps/server pytest apps/server/tests/test_tools.py

# Single test:
uv run --directory apps/server pytest apps/server/tests/test_tools.py::test_generate_image_calls_client

# With coverage report:
uv run --directory apps/server pytest --cov-report=term-missing

# With JUnit XML output (CI-style):
uv run --directory apps/server pytest --junitxml=test-results/pytest.xml
```

## 测试布局

```text
apps/server/tests/
├── conftest.py               # Shared fixtures (png_bytes, settings, fake_client, fake_app, mcp_client)
├── _helpers.py               # Constants + helpers (PNG_BYTES)
├── test_audit.py             # Append-only audit trail: record shape, redaction, header cap
├── test_cli.py               # CLI subcommands
├── test_client.py            # NovelAIClient HTTP layer (uses respx)
├── test_errors.py            # Error-body parsing + code/explanation propagation
├── test_features.py          # Insiders feature registry + resolution rules
├── test_http.py              # Chrome TLS + header fingerprint factory (create_http_client)
├── test_insiders.py          # X-MCP-Insiders header parser
├── test_insiders_http.py     # End-to-end HTTP: real server + real headers (routing, audit, scoped output, emotion gate)
├── test_mcp_auth.py          # Optional bearer-token auth (unit + live HTTP)
├── test_middleware.py        # Tool-call logging middleware
├── test_models.py            # Pydantic models
├── test_output.py            # save_image + resolve_output_path
├── test_payload.py           # build_generation_payload
├── test_prompts.py           # novelai_* prompt templates
├── test_release_tooling.py   # Release tooling in scripts/ (version sync, release notes)
├── test_resources.py         # novelai://... resources and templates
├── test_routing.py           # Header-driven routing context + route sanitisation
├── test_server.py            # FastMCP lifespan, metadata + transport selection
├── test_settings.py          # Settings surface + insiders/routing dependency providers
└── test_tools.py             # Each MCP tool's happy path + error cases
```

## Fixture

`conftest.py` 提供以下 fixture：

| Fixture | 类型 | 用途 |
|---|---|---|
| `png_bytes` | `bytes` | 最小的 1×1 PNG（透明黑）。 |
| `png_b64` | `str` | 同一张 PNG 的 base64 形式（线格式）。 |
| `nai_image` | `NovelAIImage` | mock 客户端方法返回的预置图像。 |
| `settings` | `NovelAISettings` | 带 token + 临时输出目录的 settings。 |
| `fake_client` | `AsyncMock` | 被 mock 的 `NovelAIClient`，默认返回预置图像。 |
| `fake_app` | `AppContext` | 工具通过 `Depends(get_app_context)` 收到的 lifespan 值；直接调用工具时传入它。 |
| `mcp_client` | `Client` | 基于生产 `server.mcp` 的内存 `fastmcp.Client`，其 lifespan 被替换为 mock 客户端。在无网络访问的情况下检验 schema 校验、依赖注入与结果转换。 |

覆写 `fake_client` 各方法上的 `return_value` / `side_effect`
即可定制单个测试的行为：

```python
from fastmcp.exceptions import ToolError


async def test_generate_image_handles_provider_error(fake_app, fake_client):
    fake_client.generate.side_effect = NovelAIProviderError("rate limited")
    with pytest.raises(ToolError, match="rate limited"):
        await generate.generate_image(prompt="1girl", app=fake_app)
```

预期失败会以 `ToolError` 的形式出现（服务器以
`mask_error_details=True` 运行，因此其他异常都会被屏蔽 —— 见
`tools/_errors.py`）。

## HTTP mock

`respx` 会 mock 测试套件中所有 `httpx` 请求 —— 不会发起真实的 NovelAI
API 调用。模式：

```python
import respx
from httpx import Response

@respx.mock
async def test_get_subscription():
    respx.get("https://image.novelai.net/user/subscription").mock(
        return_value=Response(200, json={"tier": 3, "active": True})
    )
    sub = await client.get_subscription()
    assert sub["tier"] == 3
```

## 异步约定

- `asyncio_mode = "auto"` —— 异步测试函数不需要 `@pytest.mark.asyncio`。
- `asyncio_default_fixture_loop_scope = "session"` —— 整个会话共用一个事件
  循环（更快，没有每测试的循环开销）。
- 异步 fixture 直接使用 `async def`。

## 覆盖率

- 下限：70%（由 `--cov-fail-under=70` 强制执行）。
- 报告：`term-missing`（终端）+ `xml:test-results/coverage.xml`（CI）。
- 排除：`pragma: no cover`、`if TYPE_CHECKING:`、
  `raise NotImplementedError`、`if __name__ == .__main__.:`。
- 源码范围：`apps/server/src/novelai_image_mcp/`。

## CI

GitHub Actions 在每次 PR 以及推送到 `main`/`dev` 时运行该测试套件，
覆盖三个操作系统（Ubuntu、Windows、macOS）。见
[`ci.yml`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.github/workflows/ci.yml)。

`docker-build` job 以 `SMOKE_TEST=true` 构建生产镜像，并在其中运行
`apps/server/docker/smoke-test.py` —— 验证容器确实能启动、且工具能注册。

## 编写新测试

```python
# apps/server/tests/test_tools.py

async def test_generate_image_with_v4_model(fake_app, fake_client):
    """generate_image should pass through V4 model ids."""
    from novelai_image_mcp.tools import generate

    fake_client.generate.return_value = (
        NovelAIImage(filename="test.png", data=PNG_BYTES),
    )

    # Direct call: asserts the request and the returned content blocks.
    result = await generate.generate_image(
        prompt="1girl",
        model=Model.V4,
        app=fake_app,
    )

    assert len(result) == 2
    assert result[0].data == PNG_BYTES  # fastmcp Image helper holds raw bytes
    assert "Saved 1 image" in result[1]
```

对于只有 FastMCP 才能证明的东西 —— schema 校验、依赖
注入、注解、`Image`→`ImageContent` 转换 —— 请改走
客户端：

```python
async def test_generate_image_serializes(mcp_client, fake_client, nai_image):
    from mcp_types import ImageContent

    fake_client.generate.return_value = (nai_image,)
    result = await mcp_client.call_tool("generate_image", {"prompt": "1girl"})

    assert any(isinstance(block, ImageContent) for block in result.content)
```

运行它：

```bash
uv run --directory apps/server pytest apps/server/tests/test_tools.py::test_generate_image_with_v4_model -v
```

## 参见

- [架构](architecture.md) —— 被测的是什么
- [贡献指南](contributing.md) —— 测试在工作流中的位置
- [`apps/server/pyproject.toml` 中的 `pytest` 配置](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/pyproject.toml)
