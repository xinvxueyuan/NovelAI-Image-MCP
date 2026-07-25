# Installation

NovelAI Image MCP runs on Python 3.13+ and is managed with [uv][uv] ≥ 0.5.
The repository is a uv workspace: the server lives at `apps/server/`, the
documentation site at `apps/docs/`. A single shared virtualenv at the repo
root holds both.

[uv]: https://docs.astral.sh/uv/

---

## 1. Clone the repository

```bash
git clone https://github.com/xinvxueyuan/NovelAI-Image-MCP.git
cd NovelAI-Image-MCP
```

## 2. Install uv

If you don't already have uv:

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

Verify the install:

```bash
uv --version
```

## 3. Sync the workspace virtualenv

From the repository root:

```bash
uv sync
```

This installs the MCP server runtime, the Sphinx documentation toolchain,
and the shared dev tools (ruff, pyright, prek, reuse) into one `.venv/` at
the repo root. The first run downloads wheels for ~60 packages; subsequent
runs are instant.

:::{tip}
To skip the dev / lint groups and install only what's needed to *run* the
server:

```bash
uv sync --no-dev --all-extras
```
:::

## 4. Configure credentials

Copy the example env file and fill in your NovelAI credentials:

```bash
cp .env.example .env
```

Edit `.env` and set **one** of the two auth methods:

```bash
# Method A (preferred): persistent API token from https://novelai.net > Account
NOVELAI_TOKEN=pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Method B: username + password (access key derived with argon2id)
# NOVELAI_USERNAME=your@email
# NOVELAI_PASSWORD=your-password
```

See [Configuration](configuration.md) for the full variable list.

## 5. Verify the install

```bash
# Server boots and exposes the CLI:
uv run python -m novelai_image_mcp --help

# Account info round-trips (validates your token):
uv run python -m novelai_image_mcp info
```

If `info` returns JSON with your account `tier` and Anlas balance, you're
ready to [generate your first image](quickstart.md).

---

## Optional: Node-side tooling

The repo also uses pnpm for cross-cutting Node tooling (turbo task runner,
husky git hooks, markdownlint). Install it if you plan to contribute:

```bash
# Install pnpm via corepack (Node ≥ 24):
corepack enable pnpm

# Install Node deps and wire the husky hooks:
pnpm install --frozen-lockfile
```

This step is **optional** for runtime use — the MCP server has zero Node
runtime dependencies.

---

## Optional: Docker

For a self-contained, reproducible deployment:

```bash
docker compose up --build
```

The image builds from [`apps/server/Dockerfile`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/Dockerfile)
and exposes the streamable-http transport on port `8000` by default. See
[Transports → streamable-http](transports/http.md) for advanced configuration.

## Next steps

- ⚡ [Quick start](quickstart.md) — generate your first image
- 🛠️ [Tools reference](tools/index.md) — every MCP tool
- 🔌 [Transports](transports/index.md) — stdio vs streamable-http
