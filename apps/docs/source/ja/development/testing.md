# テスト

サーバーのテストスイートは `apps/server/tests/` にあり、`pytest` +
`pytest-asyncio` + `respx` (HTTP モック) を使用します。

## スイートを実行する

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

## テストのレイアウト

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

## フィクスチャ

`conftest.py` は以下のフィクスチャを提供します:

| フィクスチャ | 型 | 目的 |
|---|---|---|
| `png_bytes` | `bytes` | 最小の 1×1 PNG (透明な黒)。 |
| `png_b64` | `str` | 同じ PNG の base64 (ワイヤーフォーマット)。 |
| `nai_image` | `NovelAIImage` | モック化されたクライアントメソッドが返す固定の画像。 |
| `settings` | `NovelAISettings` | トークンと一時出力ディレクトリを持つ設定。 |
| `fake_client` | `AsyncMock` | 既定で固定の画像を返す、モック化された `NovelAIClient`。 |
| `fake_app` | `AppContext` | ツールが `Depends(get_app_context)` 経由で受け取る lifespan の値。ツールを直接呼び出すときに渡します。 |
| `mcp_client` | `Client` | 本番の `server.mcp` に対するインメモリの `fastmcp.Client`。lifespan はモック化されたクライアントに差し替えられています。ネットワークアクセスなしでスキーマ検証、依存性注入、結果変換を実行します。 |

テストごとの挙動をカスタマイズするには、`fake_client` のメソッドの
`return_value` / `side_effect` を上書きします:

```python
from fastmcp.exceptions import ToolError


async def test_generate_image_handles_provider_error(fake_app, fake_client):
    fake_client.generate.side_effect = NovelAIProviderError("rate limited")
    with pytest.raises(ToolError, match="rate limited"):
        await generate.generate_image(prompt="1girl", app=fake_app)
```

想定される失敗は `ToolError` として表面化します (サーバーは
`mask_error_details=True` で動作するため、それ以外はマスクされます —
`tools/_errors.py` を参照)。

## HTTP のモック

`respx` がテストスイート内のすべての `httpx` リクエストをモックします —
実際の NovelAI API 呼び出しは行われません。パターン:

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

## 非同期の規約

- `asyncio_mode = "auto"` — 非同期テスト関数に `@pytest.mark.asyncio` は不要です。
- `asyncio_default_fixture_loop_scope = "session"` — セッション全体で 1 つの
  イベントループ (高速で、テストごとのループオーバーヘッドがありません)。
- 非同期フィクスチャは `async def` を直接使用します。

## カバレッジ

- 下限: 70% (`--cov-fail-under=70` で強制)。
- レポート: `term-missing` (ターミナル) + `xml:test-results/coverage.xml` (CI)。
- 除外: `pragma: no cover`、`if TYPE_CHECKING:`、
  `raise NotImplementedError`、`if __name__ == .__main__.:`。
- 対象: `apps/server/src/novelai_image_mcp/`。

## CI

GitHub Actions はすべての PR と `main`/`dev` への push で、3 つの OS
(Ubuntu、Windows、macOS) にわたってスイートを実行します。
[`ci.yml`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.github/workflows/ci.yml)
を参照してください。

`docker-build` ジョブは `SMOKE_TEST=true` で本番イメージをビルドし、その中で
`apps/server/docker/smoke-test.py` を実行します — コンテナが実際に起動し、
ツールが登録されることを検証します。

## 新しいテストを書く

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

FastMCP でしか証明できないもの — スキーマ検証、依存性注入、アノテーション、
`Image`→`ImageContent` 変換 — については、代わりにクライアント経由で実行してください:

```python
async def test_generate_image_serializes(mcp_client, fake_client, nai_image):
    from mcp_types import ImageContent

    fake_client.generate.return_value = (nai_image,)
    result = await mcp_client.call_tool("generate_image", {"prompt": "1girl"})

    assert any(isinstance(block, ImageContent) for block in result.content)
```

実行します:

```bash
uv run --directory apps/server pytest apps/server/tests/test_tools.py::test_generate_image_with_v4_model -v
```

## 関連項目

- [アーキテクチャ](architecture.md) — 何がテストされるか
- [コントリビュート](contributing.md) — ワークフローの中でテストがどこに位置するか
- [apps/server/pyproject.toml の `pytest` 設定](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/pyproject.toml)
