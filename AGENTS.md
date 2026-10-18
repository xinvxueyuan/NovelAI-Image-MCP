# AGENTS.md

> 面向 AI agent 的仓库级上下文索引。完整开发者文档见
> [`CONTRIBUTING.md`](CONTRIBUTING.md) 与
> [docs 站](https://xinvxueyuan.github.io/NovelAI-Image-MCP/)。
> 本文件只沉淀"约束 + 指针"，避免与 docs 站重复。

## 项目是什么

NovelAI Image MCP —— 一个基于 [fastmcp](https://github.com/PrefectHQ/fastmcp) 4
（`fastmcp>=4.1.0,<5`，底层运行在 MCP SDK v2 `mcp>=2.3.0` 上）的模型上下文协议
服务器，把 NovelAI 图像生成 API 暴露为 11 个 MCP 工具、2 个 prompt、3 个资源 +
1 个资源模板，供 Claude Desktop / Cline / 自研 agent 调用。Python 3.13，MIT 协议。

## 仓库布局（uv + pnpm monorepo，Turbo 编排）

```text
apps/server/  → 可安装的 MCP 服务器包（PyPI: novelai-image-mcp）
  src/novelai_image_mcp/
    nai/         # NovelAI HTTP 客户端（必须走 create_http_client()）
    tools/       # 11 个 MCP 工具（模块级 @mcp.tool 装饰器）
    resources.py # novelai://models / samplers / defaults / outputs/{name}
    prompts.py   # novelai_prompt_writer / novelai_image_workflow
    middleware.py# 工具调用日志中间件
    mcp_auth.py  # 可选 HTTP Bearer Token（MCP_AUTH_TOKEN）
    deps.py      # AppContext + Depends 依赖提供者
    schemas.py   # 结构化输出模型（AnlasEstimate / TagSuggestion）
    server.py    # FastMCP 实例 + lifespan + 组件导入
    cli.py       # typer CLI（同步入口）
  tests/
  mcp_server.py  # fastmcp run/dev 入口（绕开相对导入问题）
  pyproject.toml # 版本号唯一权威源 + ruff/pyright/pytest 配置
fastmcp.json (根或 member) → fastmcp run 的声明式配置（source 指向 mcp_server.py）
apps/docs/    → Sphinx 文档站（Furo + MyST）
.github/      → workflows (ci/release/docs) + detect-changes composite action
pyproject.toml (根) → uv workspace 虚拟根（不可安装）
uv.lock       → 全仓库唯一锁文件
```

## 常用命令

```powershell
uv sync                                              # 同步 Python workspace
uv run --directory apps/server poe check             # format-check + lint + typecheck + test
uv run reuse lint                                    # REUSE 合规
uv run --directory apps/server poe serve             # 启动 stdio 服务器
uv run --directory apps/server poe serve-http        # 启动 HTTP 服务器
uv run fastmcp run fastmcp.json                      # 标准 FastMCP 入口（仓库根）
uv run --directory apps/server poe inspect           # 组件/版本一览（fastmcp inspect）
uv run --directory apps/server poe dev               # MCP Inspector（交互调试）
pnpm docs:serve                                      # sphinx-autobuild 实时预览
```

## 硬约束（不要触碰）

1. **版本号唯一源 = `apps/server/pyproject.toml` 的 `version` 字段**。
   不要手改 `package.json` / `apps/server/package.json` /
   `apps/docs/package.json` / `server.json` 的版本号——用
   `uv run --directory apps/server poe sync-versions` 生成，用
   `poe check-versions` 校验；release workflow 在被打标签的 commit 上跑的
   就是同一个 `--check`。
2. **NovelAI HTTP 客户端必须通过 `nai/http.py` 的 `create_http_client()`**
   构造。不要直接 `httpx.AsyncClient()`——`image.novelai.net` 后的 Cloudflare
   WAF 会按 JA3/JA4 TLS 指纹识别非浏览器客户端并静默重置连接。自 2026 年起
   NovelAI 已将大部分第三方 API 访问收口到 `image.novelai.net`：它承载
   `/ai/generate-image`、`/ai/generate-image-stream`、`/ai/augment-image`、
   `/ai/encode-vibe`、`/ai/generate-image/suggest-tags` 以及 `/user/*`（账户 /
   订阅 / 数据）端点。**例外**：只有 `/ai/annotate-image` 未迁移，仍在 Primary API
   `api.novelai.net` 上——`NovelAISettings.legacy_image_base_url`（默认
   `https://api.novelai.net`）只为它服务，`annotate()` 必须使用它。
   **`/ai/upscale` 已迁到 `image.novelai.net`**，请求体是
   `{image, model, declared_blur_sigma}`（没有 factor 字段），且**只有 V5 系列**
   支持独立放大（2026-10-10 实测：V3/V4/V4.5 全部报 "doesn't support
   standalone upscaling"，旧的 `api.novelai.net/ai/upscale` 返回 404）。`create_http_client()` 用
   `httpx_curl_cffi.AsyncCurlTransport(impersonate="chrome")` 复刻 Chrome 的
   BoringSSL 指纹 + 完整 Chrome 150 请求头块（`BROWSER_HEADERS`）。
3. **MCP 工具返回图像时返回 fastmcp 的 `Image` 辅助类（`from
   fastmcp.utilities.types import Image`），由 fastmcp 自动转为
   `ImageContent`**。`tools/generate.py` 与 `tools/enhance.py` 的
   `_save_and_return` 已封装此逻辑：直接
   `return [Image(data=..., format="png"), "saved ..."]`，fastmcp 在返回
   list 时会自动转换。不要手动拼 `ImageContent`，也不要返回裸 bytes。
   **资源不能返回 `Image`**（FastMCP 只接受 str/bytes/ResourceContent），
   `novelai://outputs/{name}` 因此返回 bytes + `mime_type="image/png"`。
4. **按文件路径加载的入口只能是 `apps/server/mcp_server.py`**（`fastmcp run`
   / `fastmcp dev inspector` / `fastmcp.json` 的 `source` 都指向它）。
   路径加载会把模块当成顶层模块执行，包内相对导入（`from .nai import ...`）
   无法解析，所以不要把这些命令指向 `server.py` 或包内文件；改了 server
   结构也不用改这个 shim（它只是 `from novelai_image_mcp.server import mcp`）。
5. **提交消息必须 gitmoji + Conventional Commits**，例：
   `🐛 fix(generate): handle zero-seed randomization`。`commit-msg`
   hook 自动追加 `Signed-off-by` 实现 DCO。不要 `--no-verify` 提交 PR。
6. **打标签前必须 `uv lock` + `poe sync-versions`**。release workflow 的
   `build` job 用 `uv build --package novelai-image-mcp`；`validate` job 还会
   校验 manifest、CHANGELOG 与发布说明，任何一处不一致都会在发布前失败。
7. **不要在 PyPI 重发同版本**——PyPI 不允许覆盖。失败的发布用 yank +
   patch 版本（`0.1.x` → `0.1.x+1`）补救。
8. **i18n 翻译页面放在 `apps/docs/source/<lang-code>/`**（如 `source/zh/`、
   `source/ja/`）。英文留在 `source/` 根。每个语言独立构建，共享同一份
   `conf.py`。**按语言的 toctree 只能引用该语言目录下实际存在的页面** ——
   不要在 `source/zh/index.md` 的 toctree 里链接未翻译的 `tools/` 或
   `tutorials/` 章节。未翻译的章节用户切换到英文查看即可。新增语言时同步
   更新 `conf.py` 的 `AVAILABLE_LANGUAGES` 与 `docs.yml` 的 matrix。

## README 多语言约定

主 README：根 `README.md`（英文）、`.github/docs/README-zh.md`（简体中文）、
`.github/docs/README-ja.md`（日文）。根 `README-zh.md` 仅保留旧链接入口。
所有 README 使用纯文本 Markdown 表格切换项目概览，列名为 `English` /
`简体中文` / `日本語`；包 README 不代表包指南已有翻译。完整译文同步所有章节、
工具表、配置表和代码块，迁移目录后修正相对链接。运行 `pnpm readme:check`、
`pnpm readme:test` 与 `pnpm exec markdownlint-cli2`；详见贡献指南的 Repository READMEs。

## 关键约定

- **新增 MCP 工具**：在 `tools/<name>.py` 用模块级
  ``@mcp.tool(title=..., tags=..., annotations=...)`` + ``@translate_errors``
  装饰函数（文件顶部 `from ..server import mcp`；参数用 `Depends(get_app_context)`
  取 `AppContext`，不要自己读 `ctx.lifespan_context`）→ 确保
  `tools/__init__.py` 导入该模块 → 在 `tests/test_tools.py` 扩展直接调用与
  schema 测试 → 在 `apps/docs/source/tools/<name>.md` 写文档 → 在
  根 `README.md` 与 `.github/docs/README-zh.md`、
  `.github/docs/README-ja.md` 工具表加行。**预期失败必须抛 `ToolError`**（用
  `translate_errors` 或显式 raise）：服务端开了 `mask_error_details=True`，
  其他异常的消息会被屏蔽，而且在工具内部翻译才有正确消息（中间件拿到的
  已经是屏蔽后的通用错误）。
- **新增资源 / prompt**：资源放 `resources.py`（静态 `mcp.resource("novelai://...")`，
  图像用 `novelai://outputs/{name}` 模板 + `mime_type="image/png"` 返回 bytes），
  prompt 放 `prompts.py`；两者都在 `server.py` 底部随 `tools` 一起被导入。
- **MCP Registry 发布**：`server.json` 是 registry 元数据唯一源。
  版本由 `poe sync-versions` 同步三处（顶层 `.version`、PyPI 包条目的
  `version`、OCI 包条目的 `identifier` 的 `:X.Y.Z` 后缀）——人只需要改
  `apps/server/pyproject.toml`，再用 `poe check-versions` 确认一致。
  自动发布内联在 release.yml 的 `publish-mcp` job
  （`needs: [validate, publish-pypi, publish-ghcr]`），依赖已发布的
  PyPI/GHCR 包做所有权验证。
  PyPI 验证靠 `apps/server/README.md` 的 `mcp-name:` 标记（注意：不是
  根 `README.md`！`apps/server/pyproject.toml` 的 `readme = "README.md"`
  解析为 `apps/server/README.md`，这才是 PyPI 包的 long description）；
  OCI 验证靠 Dockerfile 的 `io.modelcontextprotocol.server.name` 标签。
  两个标记都不能删，否则 registry 验证失败。**三个 `server.json`
  schema 陷阱**：(1) `description` 字段上限 100 字符；(2) OCI 包条目
  **不能有 `version` 字段** —— 版本必须嵌在 `identifier` 里
  （如 `ghcr.io/.../image:1.0.0`），PyPI 包条目则保留 `version` 字段；
  (3) registry v0 搜索 API 把服务器载荷嵌套在 `.server` 下
  （`{"servers":[{"server":{"name":"..."}, "_meta":{...}}]}`），
  verify 步骤的 jq 必须用 `.servers[] | select(.server.name == ...)`。
  **为什么内联而不是独立工作流**：一次 tag push 要原子地把所有产物发出去，
  独立的 tag 触发工作流只会重复同一套校验；`publish-mcp.yml` 仅保留
  `workflow_dispatch`，作为修复 server.json 后的手动补发工具——不要给它
  加回 `on: push: tags` 触发。
  **不再有 write-back（旧陷阱已消失）**：release workflow 只校验、不写仓库，
  因此 0.4.0 那个「sync-version 回写对下游 job 不可见」的陷阱随设计消失。
  若 registry 校验失败需要补发：在 `main` 上用 `poe sync-versions` 修好
  `server.json` 并提交，然后 `gh workflow run publish-mcp.yml -f version=X.Y.Z`。
- **测试用真实 FastMCP 管线**：conftest 的 `mcp_client` fixture 用
  `fastmcp.Client(server.mcp)`（内存传输，lifespan 用替身 `NovelAIClient`，
  不联网）驱动生产实例，覆盖 schema 校验、依赖注入、结果转换与
  `ImageContent` 序列化（`TestSerializationRegression`）。**该 fixture 必须
  与测试体跑在同一个事件循环上**（`pytest_asyncio.fixture(loop_scope="function")`），
  否则内存传输会挂死：`asyncio_default_fixture_loop_scope = "session"` 会让
  session 循环里建立的连接在 function 循环里被 await。
  新增图像返回工具时扩展 `TestSerializationRegression`。
- **`filterwarnings = ["error", ...]`**：pytest 把 warning 升级为 error。
  例外清单在 `apps/server/pyproject.toml`，目前只有
  `curl_cffi.utils.CurlCffiWarning`（Windows Proactor 事件循环缺
  `add_reader`，curl_cffi 注册 selector 线程补偿——信息性，无功能影响）。
- **REUSE 合规**：所有 `.md` 文件由 `REUSE.toml` 的 `**/*.md` glob 注解为
  MIT；新增根级 Markdown 文件无需手动加 SPDX 头。
- **Windows Proactor 事件循环**：本项目主要在 Windows 开发，curl_cffi
  与之兼容（见上条 warning），httpx 也兼容。不要为"跨平台一致性"切到
  Selector 事件循环——会破坏 curl_cffi 的 IOCP 路径。
- **Agent Skills（skills.sh）**：仓库根 `skills/` 目录包含可被
  `npx skills add xinvxueyuan/NovelAI-Image-MCP` 安装的 agent 技能。
  每个 skill 是一个子目录（`skills/<name>/SKILL.md`），遵循 skills.sh
  格式。`skills.sh.json` 在仓库根，按 section 分组技能
  （CLI / MCP Tools / Workflows）。**SKILL.md scaffold 规范**：
  (a) frontmatter 只含 `name` + `description`（不写 `metadata` 块）；
  `description` 不加引号（除非含 YAML 特殊字符），单行，< 200 字符，
  同时说明"做什么"和"何时调用"；
  (b) H1 = skill name（如 `# novelai-cli`），不用描述性标题；
  (c) 正文骨架：H1 后一行 intro → `## When to use`（小写 "use"）→
  `## Instructions`（编号步骤 + `###` 子段落）；现有详细内容作为
  `## Instructions` 下的 `###` 子段落，不丢弃。新增 skill 时：
  (1) 先运行 `npx skills init <name>` 生成骨架（或手动按 scaffold 模板
  创建），再填充内容，确保结构与官方 scaffold 一致；
  (2) 在 `skills.sh.json` 的 `groupings` 里加入对应 section；
  (3) 不要在 skill 里重复其他 skill 的主要内容——按需分发，不要都塞到
  一个文件里；(4) REUSE.toml 的 `**/*.md` glob 已覆盖 `skills/` 目录，
  无需手动加 SPDX 头。

## 发布流程

完整流程见 [`apps/docs/source/development/releasing.md`](apps/docs/source/development/releasing.md)。

**基线与发布策略（硬约束，2026-08-28 决策）**：

- 基线分支固定为 `main`：所有功能/修复分支从 `main` 创建，且仅作短期工作分支。
- **线性历史**：合入 `main` 只允许 fast-forward 或 rebase 后的线性提交；禁止 merge commit，禁止长期分叉分支（如长期存在的 `feat/*`）。
- **发版一律在 `main` 执行**：版本号（`apps/server/pyproject.toml`）、`CHANGELOG.md`、`release-notes/X.Y.Z.json` 与各 manifest 的修改都必须落在 `main` 上，发布由**标签**触发（`git push origin vX.Y.Z`）。tag 必须指向 `main` 上已有的 commit（workflow 校验祖先关系），不再使用发布分支。

要点：

1. 编辑 `apps/server/pyproject.toml`：`version = "X.Y.Z"`（唯一手改处）。
2. 编辑 `CHANGELOG.md`：把 `[Unreleased]` 改名为 `[X.Y.Z] — YYYY-MM-DD`，
   新建空 `[Unreleased]` 占位段。
3. 新写 `release-notes/X.Y.Z.json`（JSON 发布说明，格式见
   `release-notes/README.md`）；本地预览：
   `uv run --directory apps/server poe release-notes --version X.Y.Z`。
4. `uv run --directory apps/server poe sync-versions` 把版本写进
   `package.json` ×3 与 `server.json` ×3 处，然后 `uv lock`。
5. `poe check` + `uv run reuse lint` + `poe check-versions` 全绿。
6. `git commit -m "🏷️ chore(release): X.Y.Z"` → `git push` → 打标签并推送：
   `git tag -a vX.Y.Z -m "vX.Y.Z"` 与 `git push origin vX.Y.Z`。标签推送即
   触发 `.github/workflows/release.yml`：
   `validate → build → publish-pypi → publish-ghcr → github-release /
   publish-mcp`。手动重跑：`gh workflow run release.yml -f version=X.Y.Z`。
7. `gh run watch` 监控。GitHub Release 针对已存在的 tag 创建，正文来自
   `release-notes/X.Y.Z.json`（下方附 auto-generated commit 列表）。

## 项目记忆与历史决策

部分跨会话的硬约束与踩坑记录在
`c:\Users\admin\.trae-cn\memory\projects\-c-dev-NovelAI-Image-MCP\project_memory.md`
（仅当前 IDE 可读）。若需了解"为什么这样做"，先查该文件。

## 不要做的事（速查）

- ❌ 直接 `httpx.AsyncClient()` 调用 NovelAI API
- ❌ 工具返回裸 bytes / 手动拼 `ImageContent`（用 fastmcp 的 `Image` 辅助类，`_save_and_return` 已封装）
- ❌ 手改 `package.json` 版本号
- ❌ 把 `fastmcp run` / `fastmcp.json` 指向 `server.py`（用 `mcp_server.py`）
- ❌ 在工具里 `raise ValueError` 指望客户端看到消息（用 `ToolError`）
- ❌ 又开一个 `FastMCP` 实例来挂工具/资源/prompt（共享 `server.mcp`）
- ❌ 在 PyPI 重发同版本
- ❌ `git commit --no-verify` 提交 PR
- ❌ 引用 lingchu-bot / NoneBot（本项目无该历史关联）
- ❌ 在 LICENSE / 协议声明中加入 LGPL 衍生代码说明（纯 MIT）
- ❌ GitHub Actions 使用非 SHA pin 的外部 action（必须 pin 到
  `@<full-sha>`，与官方 tag commit 对应）
- ❌ 在翻译页面的 toctree 里链接未翻译的章节（用户会撞到 404）
- ❌ 为翻译页面创建"翻译中"占位 stub —— 要么完整翻译，要么不创建
- ❌ 在 SKILL.md frontmatter 中写 `metadata` 块（官方 scaffold 只有
  `name` + `description`）
- ❌ SKILL.md 的 H1 用描述性标题而非 skill name
