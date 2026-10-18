# 贡献指南

感谢你有兴趣改进 NovelAI Image MCP！本页介绍实际的工作流程。项目的
行为准则见
[`CODE_OF_CONDUCT.md`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/CODE_OF_CONDUCT.md)。

## 开始之前

1. **开一个 issue** 描述你打算做的改动。对于新功能或 API 变更尤其
   重要 —— 我们会在你花时间写代码之前先讨论范围与
   设计。
2. **查看 [issue tracker](https://github.com/xinvxueyuan/NovelAI-Image-MCP/issues)**
   了解是否有相关的工作正在进行。

## 开发环境搭建

```bash
git clone https://github.com/xinvxueyuan/NovelAI-Image-MCP.git
cd NovelAI-Image-MCP

# Sync the workspace virtualenv (server + docs + dev tools)
uv sync

# (Optional) Install Node-side tooling for husky + markdownlint + turbo
corepack enable pnpm
pnpm install --frozen-lockfile
```

首次 `uv sync` 会下载所有传递依赖；后续运行是瞬时的。

## 工作流

```bash
# 1. Branch off main
git checkout -b feat/my-feature

# 2. Implement your change.
#    - Source under apps/server/src/
#    - Tests under apps/server/tests/
#    - Docs under apps/docs/source/ (if user-facing)

# 3. Run all checks locally before pushing.
uv run --directory apps/server poe check
# Equivalent to: ruff format-check + ruff check + pyright + pytest

# 4. (If you touched docs) verify the build:
uv run --package novelai-image-mcp-docs sphinx-build -b html apps/docs/source apps/docs/_build/html -W --keep-going

# 5. (If you touched markdown) verify markdownlint:
pnpm exec markdownlint-cli2

# 6. (If you touched licensing) verify REUSE compliance:
uv run reuse lint

# 7. Commit using Conventional Commits + gitmoji:
git commit -m "✨ feat: add support for V5 model ids"

# 8. Push and open a PR:
git push -u origin feat/my-feature
gh pr create --title "..." --body "..."
```

## Pre-commit 钩子

如果你安装了 pnpm 依赖，`.husky/pre-commit` 钩子会在每次 `git commit`
时自动运行：

1. **prek** —— ruff `--fix`、ruff-format 以及通用钩子
   （trailing-whitespace、end-of-file-fixer 等）。
2. **markdownlint** —— 仅当有 `.md` 文件被 staged 时。
3. **pyright** —— 仅当有 `.py` 文件被 staged 时。
4. **pytest** —— 仅当有 `.py` 文件被 staged 时（最慢的阶段）。

如果 prek 修改了文件，钩子会重新 stage 它们并重试一次。如果任何
阶段失败，提交会以清晰的消息中止。

要为 WIP 提交绕过它（请节制使用）：

```bash
git commit --no-verify -m "wip: ..."
```

:::{warning}
CI 会运行与钩子相同的检查。`--no-verify` 提交仍然会在
CI 上失败 —— 只对确实处于 WIP、并且你会在
开 PR 前 rebase 的工作绕过它。
:::

## 编码规范

### Python

- **风格**：由 `ruff`（preview 模式）强制执行。规则集见 `apps/server/pyproject.toml`。
  运行 `uv run --directory apps/server ruff format` 自动
  格式化。
- **类型**：由 `pyright`（standard 模式）强制执行。类型检查必须通过。
- **Docstring**：Google 风格（本项目的 pydocstyle 约定）。
  公开 API 上必需；私有辅助函数上可选。
- **导入**：每个模块顶部都必须有 `from __future__ import annotations`
  （PEP 563 + Ruff `TC` 规则）。
- **异步**：工具是异步的。HTTP 用 `httpx.AsyncClient`，
  测试用 `pytest-asyncio`（`asyncio_mode=auto`）。

### Markdown

- 使用 MyST Markdown（文档站的解析器）。
- 行长不受限制（`MD013` 已禁用）。
- 标题不得以 `.,;:!` 结尾（`MD026`）。
- 允许内联 HTML（`MD033` 已禁用），用于 callout / details。
- 运行 `pnpm exec markdownlint-cli2 --fix` 自动修复大多数问题。

### 许可

- 所有文件都必须带有 SPDX 许可证头。`REUSE.toml` 按 glob 声明它们 ——
  通常你不需要手动添加任何东西。
- 运行 `uv run reuse lint` 验证合规。
- 软件代码：MIT。文档：MIT。视觉元素 + 基础设施：
  CC0-1.0。

## 测试覆盖率

- 覆盖率下限：**70%**（由 `--cov-fail-under=70` 强制执行）。
- 测试位于 `apps/server/tests/`，使用 `pytest-asyncio` +
  `respx`（HTTP mock）。
- 每个新的公开函数至少应有一个测试。
- Bug 修复应包含一个回归测试。

测试布局与 fixture 策略见 [测试](testing.md)。

## 文档

面向用户的改动（新工具、新参数、行为变更）必须
更新文档：

- 工具 → `apps/docs/source/tools/<tool>.md`
- 教程 → `apps/docs/source/tutorials/<tutorial>.md`
- 配置 → `apps/docs/source/configuration.md`
- API → 由 `sphinx.ext.autodoc` 从 docstring 自动生成

在本地预览文档：

```bash
uv run --package novelai-image-mcp-docs sphinx-autobuild apps/docs/source apps/docs/_build/html --open-browser
```

### 贡献技能

Agent 技能位于 `skills/<name>/SKILL.md`，并在仓库根目录的
`skills.sh.json` 中注册。要新增一个技能：

1. 运行 `npx skills init <name>` 生成 `SKILL.md` frontmatter 的脚手架
   （只含 `name` + `description`，不要 `metadata` 块）以及
   `## When to use` → `## Instructions` 的正文结构。
2. 填写内容 —— 按需分发指引，不要重复其他技能
   已经覆盖的内容。
3. 把该技能加入 `skills.sh.json` 中合适的分组
   （CLI / MCP Tools / Workflows）。
4. 如果该技能面向用户，更新 [Agent 技能](../skills.md) 文档页与 README
   技能表。

完整的脚手架约定（frontmatter 规则、H1 = 技能名、description < 200 字符、
YAML 特殊字符的引号规则）见 `AGENTS.md` → "Agent Skills (skills.sh)"。

## 翻译文档

文档站通过按语言划分的源码树支持多语言。
英文位于 `apps/docs/source/` 根目录；每种额外语言
位于 `apps/docs/source/<lang-code>/`（例如 `source/zh/`、
`source/ja/`）。所有语言共享同一份 `conf.py`。

### 规则

1. **只做完整翻译 —— 不要 stub。** 翻译页必须覆盖
   完整英文源。代码块保持不变；只翻译散文。
   不要创建"翻译中"占位页 —— 它们会破坏构建的 `-W` 告警门禁，
   并让用户困惑。

2. **toctree 范围 = 仅限已翻译页面。** 每个语言目录下的
   `index.md` toctree 只能引用该语言目录下实际存在的页面。
   如果某个章节（例如 `tools/`、
   `tutorials/`）未翻译，就不要把它放进已翻译的
   toctree —— 用户可切换到英文查看未翻译的章节。

3. **保留 MyST 指令。** 保持所有 MyST 语法（`:::tip`、
   `=== "Unix"` 标签页、`{toctree}`、`{image}` 等）不变。只
   翻译其中的散文。

4. **标题中的 CJK 标点。** `MD026` 禁止标题以 `.,;:!` 结尾 ——
   请改用 `。、！？`。（`MD013` 行长限制已禁用，
   因此很长的 CJK 行没问题。）

### 新增语言

1. 创建 `apps/docs/source/<code>/`，至少包含 `index.md`。
2. 在 `apps/docs/source/conf.py` 的 `AVAILABLE_LANGUAGES` 中加入该语言
   （`(code, label, base_path)` 元组）。
3. 在 `.github/workflows/docs.yml` 的 matrix 中加入该语言。
4. 在本地构建并确认零告警：

   ```bash
   uv run --package novelai-image-mcp-docs sphinx-build -b html \
     apps/docs/source/<code> apps/docs/_build/<code>/html \
     -c apps/docs/source -D language=<code> -W --keep-going
   ```

### 仓库 README

项目的权威概览是 `README.md`（英文）。它的完整
翻译位于 `.github/docs/README-zh.md`（简体中文）与
`.github/docs/README-ja.md`（日文），与 Sphinx 源码树
分开存放。根 `README-zh.md` 是兼容性入口，不是需要维护的
第二份翻译。

每个 README 都包含一个纯文本 Markdown 表格，链接到全部三份
项目概览，列名为 `English`、`简体中文` 与 `日本語`。
请使用适合该文件所在目录的相对链接；已发布的
`apps/server/README.md` 使用绝对 GitHub URL，因此链接在
PyPI 上也能用。包与发布说明的 README 把这些标注为项目概览
链接，而不是包或发布说明指南本身的翻译。

保持三份完整概览中的所有章节、工具/配置表格与围栏示例
同步。翻译散文，不要翻译可执行示例；
为 `.github/docs/` 调整本地文件链接。保留服务器包的
`mcp-name:` 标记。提交前运行 `pnpm readme:check`、`pnpm readme:test` 与
`pnpm exec markdownlint-cli2`；CI 与本地
pre-commit 钩子会运行同一套 README 检查器。

### 保持翻译同步

当英文源变更时，如果可行，请在同一个 PR 中更新对应的翻译页。
严重失去同步的翻译页应当删除，而不是留着过期 ——
缺少翻译好过误导性的翻译。

## 提交消息

遵循 [Conventional Commits](https://www.conventionalcommits.org/) +
[gitmoji](https://gitmoji.dev/)：

```text
<emoji> <type>: <subject>

<body>
```

| 类型 | 用途 |
|---|---|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 仅文档 |
| `style` | 格式化、空白，无代码变更 |
| `refactor` | 代码重构，无行为变更 |
| `perf` | 性能改进 |
| `test` | 新增 / 修复测试 |
| `build` | 构建系统、依赖、CI |
| `ci` | CI 配置变更 |
| `chore` | 杂项维护 |

常用 emoji：

| Emoji | 类型 |
|---|---|
| ✨ | feat |
| 🐛 | fix |
| 📝 | docs |
| 🎨 | style |
| ♻️ | refactor |
| ⚡️ | perf |
| ✅ | test |
| 🏗️ | build |
| 🔧 | chore |

## Pull request

- 每个逻辑变更一个 PR。
- 标题：Conventional Commit 格式（`feat:`、`fix:` 等）。
- 描述：关联 issue，概述改动，列出任何破坏性
  变更。
- 合并前所有 CI 检查必须通过。
- Squash-and-merge 进 `main`（默认分支）。

## 报告 bug

开一个 [bug report issue](https://github.com/xinvxueyuan/NovelAI-Image-MCP/issues/new?template=bug_report.md)。
请包含：

- 你运行的确切命令。
- 完整的错误输出（如果是 Python，请附 stack trace）。
- 服务器版本（通过 `uv run python -c "import novelai_image_mcp; print(novelai_image_mcp.__version__)"`）。
- 你的操作系统、Python 版本与 uv 版本。
- 一个最小复现（脚本或步骤）。

## 报告安全问题

**不要为安全漏洞开公开 issue。** 私有披露流程见
[`SECURITY.md`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/SECURITY.md)。

## 参见

- [测试](testing.md)
- [架构](architecture.md)
- [发布](releasing.md)
