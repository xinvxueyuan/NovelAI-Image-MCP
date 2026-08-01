# NovelAI Image MCP

[![skills.sh](https://skills.sh/b/xinvxueyuan/NovelAI-Image-MCP)](https://skills.sh/xinvxueyuan/NovelAI-Image-MCP)

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that
exposes **NovelAI image generation** as tools for AI agents (Claude Desktop,
Cline, custom agents, remote clients).

Built on the official MCP Python SDK v2 (`MCPServer`), it lets an agent generate
images (txt2img / img2img / inpaint), upscale, run Director tools (line art,
emotion, background removal, …), annotate with ControlNet, suggest tags, encode
vibes, and query account subscription — all through the standard MCP tool
interface.

This package is the **server** workspace member of the
[NovelAI-Image-MCP](https://github.com/xinvxueyuan/NovelAI-Image-MCP)
monorepo. The Sphinx documentation site lives at `apps/docs/`. See the
[repository root README](https://github.com/xinvxueyuan/NovelAI-Image-MCP#readme)
for the project overview and the [docs site](https://xinvxueyuan.github.io/NovelAI-Image-MCP/)
for full guides and API reference.

## Features

- **11 MCP tools** covering the full NovelAI image API surface.
- **Transports**: stdio (local agents) + streamable-http (remote / multi-client).
- **Image return**: base64 `Image` content blocks (the agent *sees* the image)
  **and** PNG saved to disk (path returned as text).
- **Async + sync**: async tool handlers + a `typer` CLI for direct invocation.

## Install

```bash
pip install novelai-image-mcp
```

## Quick start

```bash
# 1. Configure credentials
export NOVELAI_TOKEN=pst-...   # from https://novelai.net > Account

# 2. Run (stdio — for local agents)
novelai-image-mcp serve

# 3. Or over HTTP
MCP_TRANSPORT=streamable-http novelai-image-mcp serve
#   → http://127.0.0.1:8000/mcp
```

## Agent skills

Three [skills.sh](https://skills.sh) packages (`novelai-cli`,
`novelai-mcp-tools`, `novelai-workflows`) teach AI agents how to drive the
CLI and MCP tools:

```bash
npx skills add --yes --global xinvxueyuan/NovelAI-Image-MCP
```

## License

MIT — see [LICENSE](LICENSE). Per-file SPDX annotations live in
[REUSE.toml](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/REUSE.toml).

<!-- mcp-name: io.github.xinvxueyuan/novelai-image-mcp -->
