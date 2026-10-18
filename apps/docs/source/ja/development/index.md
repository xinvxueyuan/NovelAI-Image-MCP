# 開発

NovelAI Image MCP サーバー自体をハックする方法を説明します。

```{toctree}
:maxdepth: 1
:hidden:

architecture
api-alignment
insiders-and-routing
contributing
testing
releasing
```

## クイックスタート

```bash
# 1. Clone + sync the workspace virtualenv
git clone https://github.com/xinvxueyuan/NovelAI-Image-MCP.git
cd NovelAI-Image-MCP
uv sync

# 2. Install Node tooling (turbo, husky, markdownlint) — optional but recommended
corepack enable pnpm
pnpm install --frozen-lockfile

# 3. Run all checks
uv run --directory apps/server poe check
# or via turbo:
pnpm check  # (runs: pnpm lint, pnpm typecheck, pnpm test via turbo)
```

## リポジトリのレイアウト

```text
NovelAI-Image-MCP/
├── apps/
│   ├── server/                     # ← MCP server (Python package)
│   │   ├── src/novelai_image_mcp/
│   │   │   ├── server.py           # FastMCP server + lifespan
│   │   │   ├── settings.py         # pydantic-settings env config
│   │   │   ├── cli.py / __main__.py  # typer sync CLI
│   │   │   ├── output.py           # save-image helper
│   │   │   ├── tools/              # 11 MCP tool definitions
│   │   │   │   ├── generate.py     # generate_image / image_to_image / inpaint
│   │   │   │   ├── enhance.py      # upscale / director / annotate
│   │   │   │   ├── tags.py         # suggest_tags / encode_vibe
│   │   │   │   └── account.py      # subscription / user_data / cost
│   │   │   └── nai/                # NovelAI HTTP client (httpx transport)
│   │   ├── tests/                  # pytest + respx
│   │   ├── docker/smoke-test.py    # container entrypoint smoke test
│   │   ├── Dockerfile              # multi-stage production image
│   │   ├── pyproject.toml          # server project + tool config (ruff/pyright/pytest/poe)
│   │   └── package.json            # turbo-script wrappers (no Node deps)
│   └── docs/                       # ← Sphinx documentation site
│       ├── source/                # MyST markdown sources
│       │   ├── conf.py             # Sphinx configuration
│       │   ├── *.md                # narrative docs
│       │   └── api/                # autodoc API reference
│       ├── Makefile                # sphinx-build / live / linkcheck targets
│       ├── pyproject.toml          # docs deps (sphinx, myst, furo)
│       └── package.json            # turbo-script wrappers
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                  # ruff / pyright / pytest / docker smoke
│   │   ├── docs.yml                # GitHub Pages deploy
│   │   └── release.yml             # PyPI + GHCR + GitHub Release
│   └── actions/detect-changes/     # composite change-detection action
├── docker-compose.yml              # orchestrates the server image
├── pyproject.toml                  # uv workspace root (virtual)
├── uv.lock                         # unified Python lockfile
├── pnpm-workspace.yaml             # pnpm workspace declaration
├── package.json                    # root workspace + turbo + husky + markdownlint
├── pnpm-lock.yaml                  # unified Node lockfile
├── turbo.json                      # cross-workspace task definition
├── prek.toml                       # pre-commit hook config
├── .husky/pre-commit               # husky pre-commit hook (4 phases)
├── REUSE.toml                      # SPDX license declarations
└── .markdownlint-cli2.jsonc        # markdown lint config
```

## よく使うコマンド

| 操作 | コマンド |
|---|---|
| すべての依存関係を同期 | `uv sync` |
| サーバーを実行 (stdio) | `uv run python -m novelai_image_mcp serve` |
| サーバーを実行 (http) | `MCP_TRANSPORT=streamable-http uv run python -m novelai_image_mcp serve` |
| テストを実行 | `uv run --directory apps/server pytest` |
| Python を lint | `uv run --directory apps/server ruff check src tests` |
| Python をフォーマット | `uv run --directory apps/server ruff format src tests` |
| 型チェック | `uv run --directory apps/server pyright` |
| すべてのチェック | `uv run --directory apps/server poe check` |
| ドキュメントをビルド | `uv run --package novelai-image-mcp-docs sphinx-build -b html apps/docs/source apps/docs/_build/html` |
| ドキュメントをライブ表示 | `uv run --package novelai-image-mcp-docs sphinx-autobuild apps/docs/source apps/docs/_build/html` |
| REUSE 準拠 | `uv run reuse lint` |

`pnpm install` を実行済みであれば、同じコマンドを turbo 経由でも実行できます:

| 操作 | Turbo コマンド |
|---|---|
| すべてのワークスペースをビルド | `pnpm build` |
| すべてのワークスペースを lint | `pnpm lint` |
| 型チェック | `pnpm typecheck` |
| すべてのワークスペースをテスト | `pnpm test` |
| フォーマット | `pnpm format` |
| ドキュメントのみビルド | `pnpm docs:build` |
| ドキュメントをライブ表示 | `pnpm docs:serve` |
| すべての成果物をクリーン | `pnpm clean` |

## コントリビュート

[コントリビュート](contributing.md) を参照してください。要点は次のとおりです:

1. 変更内容を説明する Issue を作成します。
2. `main` からブランチを作成します。
3. 実装とテストを追加します。
4. `uv run --directory apps/server poe check` がパスする必要があります。
5. 明確な説明を付けて PR を作成します。

## テスト

テストのレイアウト、フィクスチャ戦略、特定のテストの実行方法については
[テスト](testing.md) を参照してください。

## リリース

リリースを切る手順 (PyPI + GHCR + GitHub Release + cosign 署名) については
[リリース](releasing.md) を参照してください。

## アーキテクチャ

サーバーのコンポジションルート、`NovelAIClient` の設計、ツールが MCP の
ライフスパンにどのように接続されるかについては
[アーキテクチャ](architecture.md) を参照してください。
