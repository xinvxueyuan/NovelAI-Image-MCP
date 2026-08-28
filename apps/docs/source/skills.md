# Agent skills

NovelAI Image MCP can be driven in three complementary ways. Each wraps the
same async `NovelAIClient` — they differ only in how you invoke it.

| Mode | Best for | Agent-visible | Concurrency |
|---|---|---|---|
| **MCP tools** — [Tools reference](tools/index.md) | Interactive agent sessions (Claude Desktop, Cline, …) | Yes — base64 `Image` content blocks | Single client per transport |
| **CLI** — `novelai-image-mcp generate …` | Shell scripting, CI jobs, one-off commands | No — saves PNG to disk, prints path | Process per invocation |
| **Agent skills** — this page | Portable instructions that teach an AI agent *how* to use the CLI or MCP tools | Inherits the underlying mode | Inherits the underlying mode |

Agent skills are [skills.sh][skills-sh] packages — markdown instruction
files that an AI agent (Claude Code, Codex, GitHub Copilot, Cursor, …) reads
at runtime to learn project-specific workflows. They don't replace the CLI or
MCP tools; they *guide* an agent on when and how to use them.

[skills-sh]: https://skills.sh

---

## Install skills

```bash
# Install all three skills globally (Claude Code, Codex, Copilot, …)
npx skills add --yes --global xinvxueyuan/NovelAI-Image-MCP
```

The `--yes` flag skips the interactive selection prompt; `--global` installs
to `~/.agents/skills/` so every project on your machine benefits. Omit
`--global` to install into the current project's `.agents/skills/` instead.

Verify the installation:

```bash
ls ~/.agents/skills/
# novelai-cli  novelai-mcp-tools  novelai-workflows
```

---

## The three skills

### novelai-cli

**Group**: CLI

Shell-level usage of the Typer CLI — `serve`, `generate`, `upscale`,
`director`, `annotate`, `info`. Covers installation (`pip install` / `uvx`),
credential configuration, and output behaviour. Use when scripting image
workflows outside an MCP host or batch-generating images.

### novelai-mcp-tools

**Group**: MCP Tools

Reference for the 11 MCP tools exposed by the server. Covers model selection
(V3 / V4 / V4.5 / Furry), parameter tuning (steps, scale, sampler, seed),
the `ImageContent` return shape, and Anlas cost awareness. Use when
generating or transforming images via an MCP host rather than the CLI.

### novelai-workflows

**Group**: Workflows

End-to-end creative pipelines that chain multiple tools: txt2img → upscale,
annotate → img2img, Director edits, and full production flows. Use when
asked to build multi-step image workflow recipes or pipelines.

---

## When to use which

```{mermaid}
graph TD
    Q{How will you use NovelAI?}
    Q -->|"Interactive session with Claude Desktop / Cline"| A[MCP tools<br/>see Tools reference]
    Q -->|"Shell script, CI job, one-off command"| B[CLI<br/>novelai-image-mcp generate …]
    Q -->|"Want an AI agent to drive either of the above"| C[Agent skills<br/>npx skills add …]
    C -->|"Agent picks CLI or MCP based on context"| A
    C --> B
```

Skills and the CLI/MCP tools are **not either/or**:

- **CLI + skills**: Install the `novelai-cli` skill so your AI coding agent
  (Claude Code, Codex, …) knows the CLI commands without you pasting docs.
- **MCP + skills**: Install the `novelai-mcp-tools` skill so your agent
  understands the 11 MCP tool parameters and model selection heuristics.
- **Workflows**: Install `novelai-workflows` so your agent can chain tools
  into multi-step pipelines (txt2img → upscale → Director edit, …).

You can install all three — they distribute guidance on demand and don't
duplicate each other's core content.

---

## See also

- [Tools reference](tools/index.md) — the 11 MCP tools, parameters, examples
- [Tutorials](tutorials/index.md) — end-to-end workflows
- [Transports](transports/index.md) — stdio vs streamable-http
- [skills.sh page](https://skills.sh/xinvxueyuan/NovelAI-Image-MCP) — install / security assessment
- [Agent host setup](transports/agent-hosts.md) — Claude Desktop, Cline, Cursor, …
