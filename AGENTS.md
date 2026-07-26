# AGENTS.md

> 面向 AI agent 的仓库级上下文索引。完整开发者文档见
> [`CONTRIBUTING.md`](CONTRIBUTING.md) 与
> [docs 站](https://xinvxueyuan.github.io/NovelAI-Image-MCP/)。
> 本文件只沉淀"约束 + 指针"，避免与 docs 站重复。

## 项目是什么

NovelAI Image MCP —— 一个基于 MCP v2 SDK（`mcp>=2.0.0b2`，`MCPServer`）
的模型上下文协议服务器，把 NovelAI 图像生成 API 暴露为 11 个 MCP 工具，
供 Claude Desktop / Cline / 自研 agent 调用。Python 3.13，MIT 协议。

## 仓库布局（uv + pnpm monorepo，Turbo 编排）

```text
apps/server/  → 可安装的 MCP 服务器包（PyPI: novelai-image-mcp）
  src/novelai_image_mcp/
    nai/         # NovelAI HTTP 客户端（必须走 create_http_client()）
    tools/       # 11 个 MCP 工具的注册函数
    server.py    # MCPServer 实例 + lifespan AppContext
    cli.py       # typer CLI（同步入口）
  tests/
  dev_server.py  # mcp dev 入口（绕开相对导入问题）
  pyproject.toml # 版本号唯一权威源 + ruff/pyright/pytest 配置
apps/docs/    → Sphinx 文档站（Furo + MyST）
.github/      → workflows (ci/release/docs) + sync-version composite action
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
mcp dev apps/server/dev_server.py                    # MCP Inspector（交互调试）
pnpm docs:serve                                      # sphinx-autobuild 实时预览
```

## 硬约束（不要触碰）

1. **版本号唯一源 = `apps/server/pyproject.toml` 的 `version` 字段**。
   不要手改 `package.json` / `apps/server/package.json` /
   `apps/docs/package.json` 的版本号——release workflow 的
   `.github/actions/sync-version` 会自动同步并回写 commit。
2. **NovelAI HTTP 客户端必须通过 `nai/http.py` 的 `create_http_client()`**
   构造。不要直接 `httpx.AsyncClient()`——`image.novelai.net` 后的 Cloudflare
   WAF 会按 JA3/JA4 TLS 指纹识别非浏览器客户端并静默重置连接。自 2026 年起
   NovelAI 已将所有第三方 API 访问收口到 `image.novelai.net`：它同时承载
   `/ai/*`（图像生成与工具）与 `/user/*`（账户 / 订阅 / 数据）端点，是第三方
   工具的唯一可访问主机；旧 `api.novelai.net` 已保留给官方前端并显式拒绝第三方
   请求。`create_http_client()` 用 `httpx_curl_cffi.AsyncCurlTransport
   (impersonate="chrome")` 复刻 Chrome 的 BoringSSL 指纹 + 完整
   Chrome 150 请求头块（`BROWSER_HEADERS`）。
3. **MCP 工具返回图像时必须返回 `ImageContent`，不能返回 SDK 的 `Image`
   辅助类**。`tools/generate.py` 与 `tools/enhance.py` 的
   `_save_and_return` 已封装此逻辑：`Image(...).to_image_content()`。
   直接返回 `Image` 会触发 `PydanticSerializationError`。
4. **`mcp dev` 用 `apps/server/dev_server.py` 作为入口**，不要直接指向
   `server.py`——`mcp dev` 直接加载会破坏 `from ._mcp import MCPServer`
   相对导入。
5. **提交消息必须 gitmoji + Conventional Commits**，例：
   `🐛 fix(generate): handle zero-seed randomization`。`commit-msg`
   hook 自动追加 `Signed-off-by` 实现 DCO。不要 `--no-verify` 提交 PR。
6. **不要在 `releases/*` 分支推送前忘记 `uv lock`**。release workflow 的
   `build` job 用 `uv build --package novelai-image-mcp`，lock 与
   pyproject 不一致会触发警告。
7. **不要在 PyPI 重发同版本**——PyPI 不允许覆盖。失败的发布用 yank +
   patch 版本（`0.1.x` → `0.1.x+1`）补救。
8. **i18n 翻译页面放在 `apps/docs/source/<lang-code>/`**（如 `source/zh/`、
   `source/ja/`）。英文留在 `source/` 根。每个语言独立构建，共享同一份
   `conf.py`。**按语言的 toctree 只能引用该语言目录下实际存在的页面** ——
   不要在 `source/zh/index.md` 的 toctree 里链接未翻译的 `tools/` 或
   `tutorials/` 章节。未翻译的章节用户切换到英文查看即可。新增语言时同步
   更新 `conf.py` 的 `AVAILABLE_LANGUAGES` 与 `docs.yml` 的 matrix。

## 关键约定

- **新增 MCP 工具**：在 `tools/<name>.py` 写 `register(mcp: MCPServer)`
  函数 → 在 `tools/__init__.py` 接线 → 在 `tests/test_tools.py` 扩展参数化
  测试 → 在 `apps/docs/source/tools/<name>.md` 写文档 → 在 README/README-zh
  工具表加行。
- **回归测试覆盖 SDK 序列化路径**：`TestSerializationRegression` 通过
  `Tool.run(convert_result=True)` 直接调用生产 `server.mcp` 实例，确保
  ImageContent 块能被 `model_dump(mode="json")` 序列化。新增图像返回
  工具时务必扩展该测试类。
- **`filterwarnings = ["error", ...]`**：pytest 把 warning 升级为 error。
  例外清单在 `apps/server/pyproject.toml`，目前只有
  `curl_cffi.utils.CurlCffiWarning`（Windows Proactor 事件循环缺
  `add_reader`，curl_cffi 注册 selector 线程补偿——信息性，无功能影响）。
- **REUSE 合规**：所有 `.md` 文件由 `REUSE.toml` 的 `**/*.md` glob 注解为
  MIT；新增根级 Markdown 文件无需手动加 SPDX 头。
- **Windows Proactor 事件循环**：本项目主要在 Windows 开发，curl_cffi
  与之兼容（见上条 warning），httpx 也兼容。不要为"跨平台一致性"切到
  Selector 事件循环——会破坏 curl_cffi 的 IOCP 路径。

## 发布流程

完整流程见 [`apps/docs/source/development/releasing.md`](apps/docs/source/development/releasing.md)。
要点：

1. 编辑 `apps/server/pyproject.toml`：`version = "X.Y.Z"`（唯一手改处）。
2. 编辑 `CHANGELOG.md`：把 `[Unreleased]` 改名为 `[X.Y.Z] — YYYY-MM-DD`，
   新建空 `[Unreleased]` 占位段。
3. `uv lock` 刷新锁文件。
4. `uv run --directory apps/server poe check` + `uv run reuse lint` 通过。
5. `git commit -m "🏷️ chore(release): X.Y.Z"` 后创建并推送
   `releases/X.Y.Z` 分支，触发 `.github/workflows/release.yml`：
   `validate → build → publish-pypi → publish-ghcr → github-release`。
6. `gh run watch` 监控。`github-release` job 自动创建 `vX.Y.Z` tag 与
   GitHub Release（含 auto-generated notes + wheel/sdist 资产）。

## 项目记忆与历史决策

部分跨会话的硬约束与踩坑记录在
`c:\Users\admin\.trae-cn\memory\projects\-c-dev-NovelAI-Image-MCP\project_memory.md`
（仅当前 IDE 可读）。若需了解"为什么这样做"，先查该文件。

## 不要做的事（速查）

- ❌ 直接 `httpx.AsyncClient()` 调用 NovelAI API
- ❌ 工具返回 SDK 的 `Image` 类（必须 `to_image_content()`）
- ❌ 手改 `package.json` 版本号
- ❌ `mcp dev` 入口指向 `server.py`（用 `dev_server.py`）
- ❌ 在 PyPI 重发同版本
- ❌ `git commit --no-verify` 提交 PR
- ❌ 引用 lingchu-bot / NoneBot（本项目无该历史关联）
- ❌ 在 LICENSE / 协议声明中加入 LGPL 衍生代码说明（纯 MIT）
- ❌ GitHub Actions 使用非 SHA pin 的外部 action（必须 pin 到
  `@<full-sha>`，与官方 tag commit 对应）
- ❌ 在翻译页面的 toctree 里链接未翻译的章节（用户会撞到 404）
- ❌ 为翻译页面创建"翻译中"占位 stub —— 要么完整翻译，要么不创建
