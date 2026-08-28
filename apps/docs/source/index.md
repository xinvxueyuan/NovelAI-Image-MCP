# NovelAI Image MCP

```{image} _static/logo.svg
:alt: NovelAI Image MCP
:width: 120px
:align: center
```

An [MCP (Model Context Protocol)][mcp] server that exposes
**NovelAI image generation** as tools for AI agents — Claude Desktop, Cline,
custom agents, and remote clients.

Built on FastMCP 4 (the fastmcp framework over the MCP SDK v2 `mcp>=2.0.0`), it lets an agent
generate images (txt2img / img2img / inpaint), upscale, run Director tools
(line art, emotion, background removal, …), annotate with ControlNet,
suggest tags, encode vibes, and query account subscription — all through the
standard MCP tool interface.

[mcp]: https://modelcontextprotocol.io/

---

## Highlights

- **11 MCP tools** covering the full NovelAI image API surface.
- **Two transports**: stdio (local agents) and streamable-http (remote / multi-client).
- **Dual return shape**: base64 `Image` content blocks (the agent *sees* the image)
  **and** PNG saved to disk (path returned as text).
- **Async + sync**: async tool handlers + a `typer` CLI for direct invocation.
- **Agent skills**: three [skills.sh](https://skills.sh) packages (`novelai-cli`,
  `novelai-mcp-tools`, `novelai-workflows`) that teach AI agents how to drive
  the CLI and MCP tools.
- **uv-managed monorepo**, MIT-licensed, Docker-ready, GitHub Pages docs.

---

## Get started

```{toctree}
:maxdepth: 2
:caption: Getting started
:hidden:

installation
quickstart
configuration
```

```{toctree}
:maxdepth: 2
:caption: Tools reference
:hidden:

tools/index
```

```{toctree}
:maxdepth: 1
:caption: Tutorials
:hidden:

tutorials/index
```

```{toctree}
:maxdepth: 1
:caption: Transports
:hidden:

transports/index
```

```{toctree}
:maxdepth: 1
:caption: Skills
:hidden:

skills
```

```{toctree}
:maxdepth: 1
:caption: Development
:hidden:

development/index
```

```{toctree}
:maxdepth: 1
:caption: API reference
:hidden:

api/index
```

```{toctree}
:maxdepth: 1
:caption: About
:hidden:

about/license
about/changelog
about/tool-validation
```

---

## Quick links

- [Quick start](quickstart.md) — install, configure, and generate your first image
- [Tools reference](tools/index.md) — every MCP tool, parameter, and example
- [Transports](transports/index.md) — stdio vs streamable-http
- [Agent skills](skills.md) — skills.sh packages that teach AI agents the CLI + MCP tools
- [Agent host setup](transports/agent-hosts.md) — Claude Desktop, Cline, Cursor, Continue, Windsurf, Codex CLI
- [API reference](api/index.md) — autodoc-generated Python API
- [Contributing](development/contributing.md) — how to hack on the server

---

## Project links

- **Source**: <https://github.com/xinvxueyuan/NovelAI-Image-MCP>
- **Issues**: <https://github.com/xinvxueyuan/NovelAI-Image-MCP/issues>
- **License**: [MIT](about/license.md)
- **Changelog**: [Keep a Changelog](about/changelog.md)
- **NovelAI API docs**: <https://image.novelai.net/docs/index.html>
