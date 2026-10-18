# 开发

如何为 NovelAI Image MCP 服务器本身贡献代码。

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

## 快速开始

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

## 仓库布局

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

## 常用命令

| 操作 | 命令 |
|---|---|
| 同步全部依赖 | `uv sync` |
| 运行服务器（stdio） | `uv run python -m novelai_image_mcp serve` |
| 运行服务器（http） | `MCP_TRANSPORT=streamable-http uv run python -m novelai_image_mcp serve` |
| 运行测试 | `uv run --directory apps/server pytest` |
| Python lint | `uv run --directory apps/server ruff check src tests` |
| Python 格式化 | `uv run --directory apps/server ruff format src tests` |
| 类型检查 | `uv run --directory apps/server pyright` |
| 全部检查 | `uv run --directory apps/server poe check` |
| 构建文档 | `uv run --package novelai-image-mcp-docs sphinx-build -b html apps/docs/source apps/docs/_build/html` |
| 实时文档 | `uv run --package novelai-image-mcp-docs sphinx-autobuild apps/docs/source apps/docs/_build/html` |
| REUSE 合规 | `uv run reuse lint` |

`pnpm install` 执行过后，同样的命令也可以通过 turbo 运行：

| 操作 | Turbo 命令 |
|---|---|
| 构建全部 workspace | `pnpm build` |
| Lint 全部 workspace | `pnpm lint` |
| 类型检查 | `pnpm typecheck` |
| 测试全部 workspace | `pnpm test` |
| 格式化 | `pnpm format` |
| 仅构建文档 | `pnpm docs:build` |
| 实时文档 | `pnpm docs:serve` |
| 清理全部产物 | `pnpm clean` |

## 贡献

见 [贡献指南](contributing.md)。太长不看：

1. 开一个 issue 描述你的改动。
2. 从 `main` 拉出分支。
3. 实现 + 补测试。
4. `uv run --directory apps/server poe check` 必须通过。
5. 开一个描述清晰的 PR。

## 测试

见 [测试](testing.md) 了解测试布局、fixture 策略，以及如何
运行某个特定测试。

## 发布

见 [发布](releasing.md) 了解发版流程（PyPI + GHCR +
GitHub Release + cosign 签名）。

## 架构

见 [架构](architecture.md) 了解服务器的组合根、
`NovelAIClient` 设计，以及工具如何接入 MCP lifespan。
