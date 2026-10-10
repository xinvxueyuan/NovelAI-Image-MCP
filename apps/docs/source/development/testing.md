# Testing

The server's test suite lives at `apps/server/tests/` and uses
`pytest` + `pytest-asyncio` + `respx` (HTTP mocking).

## Run the suite

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

## Test layout

```text
apps/server/tests/
├── conftest.py             # Shared fixtures (png_bytes, settings, fake_client, fake_app, mcp_client)
├── _helpers.py             # Constants + helpers (PNG_BYTES)
├── test_cli.py             # CLI subcommands
├── test_client.py          # NovelAIClient HTTP layer (uses respx)
├── test_mcp_auth.py        # Optional bearer-token auth (unit + live HTTP)
├── test_middleware.py      # Tool-call logging middleware
├── test_models.py          # Pydantic models
├── test_output.py          # save_image + resolve_output_path
├── test_payload.py         # build_generation_payload
├── test_prompts.py         # novelai_* prompt templates
├── test_resources.py       # novelai://... resources and templates
├── test_server.py          # FastMCP lifespan, metadata + transport selection
└── test_tools.py           # Each MCP tool's happy path + error cases
```

## Fixtures

`conftest.py` provides the following fixtures:

| Fixture | Type | Purpose |
|---|---|---|
| `png_bytes` | `bytes` | Minimal 1×1 PNG (transparent black). |
| `png_b64` | `str` | Same PNG as base64 (the wire format). |
| `nai_image` | `NovelAIImage` | Canned image returned by mocked client methods. |
| `settings` | `NovelAISettings` | Settings with a token + tmp output dir. |
| `fake_client` | `AsyncMock` | Mocked `NovelAIClient` that returns canned images by default. |
| `fake_app` | `AppContext` | The lifespan value tools receive via `Depends(get_app_context)`; pass it when calling a tool directly. |
| `mcp_client` | `Client` | In-memory `fastmcp.Client` over the production `server.mcp`, with the lifespan patched to the mocked client. Exercises schema validation, dependency injection and result conversion without network access. |

Override any `return_value` / `side_effect` on `fake_client`'s methods to
customize per-test behavior:

```python
from fastmcp.exceptions import ToolError


async def test_generate_image_handles_provider_error(fake_app, fake_client):
    fake_client.generate.side_effect = NovelAIProviderError("rate limited")
    with pytest.raises(ToolError, match="rate limited"):
        await generate.generate_image(prompt="1girl", app=fake_app)
```

Expected failures surface as `ToolError` (the server runs with
`mask_error_details=True`, so anything else is masked — see
`tools/_errors.py`).

## HTTP mocking

`respx` mocks all `httpx` requests in the test suite — no real NovelAI
API calls are made. Patterns:

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

## Async conventions

- `asyncio_mode = "auto"` — async test functions don't need `@pytest.mark.asyncio`.
- `asyncio_default_fixture_loop_scope = "session"` — one event loop for the
  whole session (faster, no per-test loop overhead).
- Async fixtures use `async def` directly.

## Coverage

- Floor: 70% (enforced by `--cov-fail-under=70`).
- Reports: `term-missing` (terminal) + `xml:test-results/coverage.xml` (CI).
- Excluded: `pragma: no cover`, `if TYPE_CHECKING:`,
  `raise NotImplementedError`, `if __name__ == .__main__.:`.
- Source: `apps/server/src/novelai_image_mcp/`.

## CI

GitHub Actions runs the suite on every PR and on push to `main`/`dev`,
across three operating systems (Ubuntu, Windows, macOS). See
[`ci.yml`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.github/workflows/ci.yml).

The `docker-build` job builds the production image with
`SMOKE_TEST=true` and runs `apps/server/docker/smoke-test.py` inside it —
verifying the container actually boots and the tools register.

## Writing a new test

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

For anything that only FastMCP can prove — schema validation, dependency
injection, annotations, `Image`→`ImageContent` conversion — go through the
client instead:

```python
async def test_generate_image_serializes(mcp_client, fake_client, nai_image):
    from mcp_types import ImageContent

    fake_client.generate.return_value = (nai_image,)
    result = await mcp_client.call_tool("generate_image", {"prompt": "1girl"})

    assert any(isinstance(block, ImageContent) for block in result.content)
```

Run it:

```bash
uv run --directory apps/server pytest apps/server/tests/test_tools.py::test_generate_image_with_v4_model -v
```

## See also

- [Architecture](architecture.md) — what's being tested
- [Contributing](contributing.md) — where tests fit in the workflow
- [`pytest` configuration in apps/server/pyproject.toml](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/pyproject.toml)
