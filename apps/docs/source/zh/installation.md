# 安装

NovelAI Image MCP 需要 Python 3.13+，并使用 [uv][uv] ≥ 0.5 进行依赖管理。
仓库采用 uv workspace 结构：服务器位于 `apps/server/`，文档站位于
`apps/docs/`。仓库根目录下的一个共享虚拟环境同时为两者提供服务。

[uv]: https://docs.astral.sh/uv/

---

## 1. 克隆仓库

```bash
git clone https://github.com/xinvxueyuan/NovelAI-Image-MCP.git
cd NovelAI-Image-MCP
```

## 2. 安装 uv

如果你还没有安装 uv：

=== "Unix / macOS"

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

=== "Windows (PowerShell)"

    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

=== "pip / pipx"

    ```bash
    pipx install uv
    ```

验证安装：

```bash
uv --version
```

## 3. 同步 workspace 虚拟环境

在仓库根目录下执行：

```bash
uv sync
```

这会将 MCP 服务器运行时、Sphinx 文档工具链以及共享的开发工具
（ruff、pyright、prek、reuse）安装到仓库根目录下的 `.venv/` 中。首次运行
会下载约 60 个包的 wheel；后续运行几乎是即时的。

:::{tip}
如果只想安装 *运行* 服务器所需的依赖，跳过 dev / lint 分组：

```bash
uv sync --no-dev --all-extras
```
:::

## 4. 配置凭据

复制示例 env 文件并填入你的 NovelAI 凭据：

```bash
cp .env.example .env
```

编辑 `.env`，设置以下两种认证方式 **之一**：

```bash
# 方式 A（推荐）：来自 https://novelai.net > Account 的持久 API token
NOVELAI_TOKEN=pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 方式 B：用户名 + 密码（用 argon2id 派生 access key）
# NOVELAI_USERNAME=your@email
# NOVELAI_PASSWORD=your-password
```

完整的变量列表见 [配置](configuration.md)。

## 5. 验证安装

```bash
# 服务器启动并暴露 CLI：
uv run python -m novelai_image_mcp --help

# 账户信息往返（验证你的 token）：
uv run python -m novelai_image_mcp info
```

如果 `info` 返回的 JSON 中包含你的账户 `tier` 和 Anlas 余额，说明你已经
准备好 [生成第一张图像](quickstart.md) 了。

---

## 可选：Node 侧工具

仓库还使用 pnpm 管理跨 cuts 的 Node 工具（turbo 任务运行器、husky git
钩子、markdownlint）。如果你打算参与贡献，请安装它：

```bash
# 通过 corepack 安装 pnpm（Node ≥ 24）：
corepack enable pnpm

# 安装 Node 依赖并连接 husky 钩子：
pnpm install --frozen-lockfile
```

这一步对于运行时使用是 **可选的** —— MCP 服务器没有任何 Node 运行时依赖。

---

## 可选：Docker

如需开箱即用、可复现的部署方式：

```bash
docker compose up --build
```

镜像基于 [`apps/server/Dockerfile`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/Dockerfile)
构建，默认在 `8000` 端口暴露 streamable-http 传输方式。高级配置（如自定义
主机与端口）请通过环境变量调整，详见 [配置](configuration.md)。

## 后续步骤

- ⚡ [快速开始](quickstart.md) —— 生成你的第一张图像
