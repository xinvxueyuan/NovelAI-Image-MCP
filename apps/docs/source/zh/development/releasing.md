# 发布

本页描述发布流程：升级版本号、撰写发布说明，并发布到
PyPI + GHCR + GitHub Releases + MCP
Registry。推送一个版本标签就会运行整条流水线；标签是唯一的
触发方式。

## 版本号

项目遵循[语义化版本](https://semver.org/spec/v2.0.0.html)：

- `MAJOR.MINOR.PATCH`
- `MAJOR`：破坏性 API 变更
- `MINOR`：新功能，向后兼容
- `PATCH`：bug 修复，向后兼容

### 唯一真源

权威版本号位于
[`apps/server/pyproject.toml`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/pyproject.toml) 的
`[project] version` 字段。其他所有携带版本号的地方都
**派生**自它，一条命令即可全部写入：

```bash
uv run --directory apps/server poe sync-versions    # write
uv run --directory apps/server poe check-versions   # verify only (what CI runs)
```

| 位置 | 如何保持同步 |
|---|---|
| `apps/server/pyproject.toml` | **改这里**（权威源）。 |
| `package.json`、`apps/server/package.json`、`apps/docs/package.json` | `poe sync-versions` 写入顶层 `version`。 |
| `server.json`（MCP registry manifest） | `poe sync-versions` 写入顶层 `.version`、PyPI 条目的 `version` 与 OCI 条目的 `identifier` tag。 |
| `apps/server/src/novelai_image_mcp/__init__.py`（`__version__`） | 导入时从已安装 wheel 的 METADATA 解析，而 METADATA 由 `pyproject.toml` 生成。无需编辑。 |
| `apps/docs/source/conf.py`（`release`） | 在 Sphinx 构建时从已安装包的元数据解析，未同步的 checkout 回退为 `0.0.0`。 |
| `apps/server/Dockerfile`（`ARG VERSION`） | 构建时由 `validate.outputs.version` 注入。 |
| Docker 镜像标签（`org.opencontainers.image.version`） | 通过 `docker/metadata-action` 由 `validate.outputs.version` 注入。 |
| Git tag、PyPI 版本、GitHub Release | 全部来自触发本次运行的标签。 |

:::{important}
发布工作流会**校验**这些文件，但从不写入它们。发布运行期间
不会有任何内容被推回仓库，因此已发布的
产物永远不会与它所构建自的 commit 不一致。请在打标签*之前*
运行 `poe sync-versions` 并提交 —— 否则 `poe check-versions` 会让
本次运行失败。
:::

## 发布说明以 JSON 撰写

每次发布都带有一份公告，位于
[`release-notes/<version>.json`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/tree/main/release-notes)：

```json
{
  "version": "0.5.2",
  "date": "2026-10-13",
  "summary": "One paragraph summarising the release.",
  "highlights": [{ "title": "Headline", "body": "Markdown body" }],
  "sections": [{ "title": "🛡️ Security", "items": ["Bullet one"] }],
  "upgrade_notes": "Anything an operator must do.",
  "contributors": ["@someone"],
  "footer": "Optional closing Markdown."
}
```

`version`、`date` 与 `summary` 是必填项；其余键为可选，
并且**未知键会报错**，因此一个笔误不会悄悄丢掉公告的
某一部分。`🚀 Release` 工作流用
[`apps/server/scripts/release_notes.py`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/scripts/release_notes.py)
渲染该文档，并把结果作为 GitHub Release 正文发布，同时在其下方追加
自动生成的 commit 列表（按 `.github/release.yml` 分组）。

```bash
# preview exactly what the release page will show
uv run --directory apps/server poe release-notes --version 0.5.2
```

`CHANGELOG.md` 仍是仓库累积的、人工整理的更新日志；
该 JSON 文档则是发布页上展示的更短的公告。两者都是发布所必需的。

## 发布前检查清单

在推送标签之前：

- [ ] `main` 上所有 CI 检查通过，且 `main` 已推送。
- [ ] `apps/server/pyproject.toml` 的 `version` 已升级（你手动编辑的
      **唯一**版本字符串）。
- [ ] `CHANGELOG.md` 中有新版本的章节（把 `## [Unreleased]`
      改名为 `## [X.Y.Z] - YYYY-MM-DD`，并新增一个空的 `[Unreleased]`）。
- [ ] `release-notes/X.Y.Z.json` 存在且能渲染。
- [ ] 已运行并提交 `poe sync-versions`（三个 `package.json`
      文件加上 `server.json`）。
- [ ] `uv lock` 是最新的（`uv lock`）。
- [ ] `poe check`、`uv run reuse lint` 与 `poe check-versions` 全绿。
- [ ] 引用了上一版本功能集的教程已更新。

## 触发发布

### 方案 A：推送标签（常规路径）

标签就是发布决定。它必须指向一个已经在
`main` 上的 commit —— `validate` job 会检查祖先关系，并拒绝不在
基线上的标签：

```bash
git tag -a v0.5.2 -m "v0.5.2"
git push origin v0.5.2
```

工作流会从标签名解析版本号，并针对该 commit 运行完整的
流水线。

### 方案 B：workflow_dispatch（重跑已有标签）

从 GitHub Actions UI（或 CLI）手动触发，以重新构建并
重新发布一个**已有**标签 —— 在瞬时故障之后，或需要
刷新发布说明时很有用：

```bash
gh workflow run release.yml -f version=0.5.2
```

标签必须已经存在；这条路径永远不会重写它。

## 发布流水线

`release.yml` 工作流运行以下 job：

```{mermaid}
graph TD
    A[validate] --> B[build]
    B --> C[publish-pypi]
    B --> D[publish-ghcr]
    C --> E[github-release]
    D --> E
    C --> F[publish-mcp]
    D --> F
```

### 1. Validate

- 从标签（或 dispatch 输入）解析版本号，并拒绝任何
  不是 `X.Y.Z` 的值。
- 确认标签存在，且其 commit 是 `origin/main` 的祖先。
- 确认 `apps/server/pyproject.toml` 携带标签的版本号。
- 运行 `apps/server/scripts/sync_versions.py --check`：每个派生的 manifest
  都必须已经一致（仅校验 —— 不写入任何内容）。
- 确认 `CHANGELOG.md` 记录了该版本。
- 渲染 `release-notes/<version>.json` 并作为
  `release-notes` artifact 上传。

### 2. Build

- `uv build --package novelai-image-mcp` 生成 wheel + sdist。
- 把它们作为 CI artifact 上传（`python-distributions`）。

### 3. 发布到 PyPI

- 使用 **OIDC trusted publishing**（无需 API token）。
- 要求 GitHub 环境 `pypi` 已在 PyPI 侧配置为受信任
  发布。

### 4. 发布到 GHCR

- 构建 Docker 镜像（通过 Buildx 多平台）。
- 推送到 `ghcr.io/<owner>/<repo>:<version>`、`:<major>.<minor>`、
  `:<major>` 与 `:sha-<short>`。
- **用 cosign 为镜像签名**（keyless，经由 OIDC）。

### 5. GitHub Release

- 渲染 JSON 发布说明并追加自动生成的 commit 列表。
- 为**已存在的**标签创建 GitHub Release（`--verify-tag`），
  并附上 wheel + sdist。重跑会更新说明并重新上传
  资源，而不是失败。

### 6. 发布到 MCP Registry

- 在 PyPI 与 GHCR 上线之后运行
  （`needs: [validate, publish-pypi, publish-ghcr]`）。
- 安装 `mcp-publisher`，按 registry schema 校验 `server.json`，通过 GitHub OIDC 登录，
  发布，然后验证该服务器已被列在 `registry.modelcontextprotocol.io`。
- 内联在此而不是单独的标签触发工作流，这样一次标签推送就能
  原子地发布到所有地方。独立的 `publish-mcp.yml` 仍可用于
  在修好 `server.json` 之后手动重新发布。

## 走一次发布

一次完整的发布，端到端：

```bash
# 1. Make sure main is green and current
git checkout main
git pull
uv run --directory apps/server poe check

# 2. Bump the canonical version (the ONLY version string you edit)
#    apps/server/pyproject.toml: version = "0.5.2"

# 3. Close the changelog section
#    CHANGELOG.md: rename [Unreleased] to [0.5.2] - 2026-10-13,
#    add a fresh empty [Unreleased]

# 4. Author the announcement
#    release-notes/0.5.2.json  (see the format above)

# 5. Propagate the version and re-lock
uv run --directory apps/server poe sync-versions
uv lock

# 6. Verify everything the workflow will verify, then commit and push
uv run --directory apps/server poe check
uv run --directory apps/server poe check-versions
uv run reuse lint
git add apps/server/pyproject.toml CHANGELOG.md release-notes/0.5.2.json \
        package.json apps/server/package.json apps/docs/package.json \
        server.json uv.lock
git commit -m "🏷️ chore(release): 0.5.2"
git push

# 7. Tag the release commit and push the tag — this triggers the pipeline
git tag -a v0.5.2 -m "v0.5.2"
git push origin v0.5.2

# 8. Watch it
gh run watch
```

## 发布之后

- 在 PyPI 上验证该包：<https://pypi.org/project/novelai-image-mcp/>
- 在 GHCR 上验证镜像：`docker pull ghcr.io/<owner>/<repo>:0.5.2`
- 验证 GitHub Release：<https://github.com/xinvxueyuan/NovelAI-Image-MCP/releases>
- 验证 MCP Registry 条目（由 `publish-mcp` job 自动完成）：
  <https://registry.modelcontextprotocol.io/>
- 在项目的 discussion / chat 中公告。

## 回滚

如果某个发布坏了：

1. **不要在 PyPI 上重新发布同一个版本**（PyPI 不允许
   重复上传）。通过 PyPI 网页 UI yank 掉坏掉的发布。
2. 用修复切一个 patch 版本（`0.5.3`）。
3. 在 GitHub 上把坏掉的发布标记为 pre-release / yanked。

## 历史

截至并包括 0.5.1 的发布是通过推送 `releases/X.Y.Z` 分支触发的，
工作流会把同步后的 manifest 写回该分支。标签流程落地后
这些分支已被删除；历史 `vX.Y.Z` 标签仍然保留，是那些发布的记录。

## 参见

- [CHANGELOG](../about/changelog.md) —— 每个版本改了什么
- [`release-notes/README.md`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/release-notes/README.md) —— JSON 说明格式
- [`release.yml`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.github/workflows/release.yml)
- [`.github/release.yml`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.github/release.yml) —— 追加的 commit 列表的分组规则
- [PyPI trusted publishing 设置](https://docs.pypi.org/trusted-publishers/)
