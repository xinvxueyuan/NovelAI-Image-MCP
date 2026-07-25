---
name: 🐛 Bug report
description: Report something that's broken or behaves incorrectly
title: "🐛 <brief summary>"
labels: ["bug", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for taking the time to file a bug report.
        Fill in the sections below so we can reproduce and fix it quickly.
  - type: textarea
    id: what-happened
    attributes:
      label: What happened?
      description: A clear description of the bug. Include the exact error message or unexpected output.
      placeholder: "I tried to ... and got ..."
    validations:
      required: true
  - type: textarea
    id: expected
    attributes:
      label: What did you expect?
      description: What should have happened instead?
    validations:
      required: true
  - type: textarea
    id: reproduce
    attributes:
      label: Steps to reproduce
      description: Smallest set of steps that triggers the issue. Code blocks welcome.
      placeholder: |
        1. ...
        2. ...
    validations:
      required: true
  - type: input
    id: version
    attributes:
      label: Version
      description: Output of `uv pip show novelai-image-mcp` or the git commit hash.
      placeholder: "0.1.0 / commit abc1234"
    validations:
      required: true
  - type: dropdown
    id: transport
    attributes:
      label: Transport
      description: Which MCP transport were you using?
      options:
        - stdio
        - streamable-http
        - both / unknown
        - CLI (`novelai-image-mcp ...`)
    validations:
      required: false
  - type: textarea
    id: env
    attributes:
      label: Environment
      description: OS, Python version, MCP host (Claude Desktop / Cline / etc.), NovelAI model.
      placeholder: "Windows 11, Python 3.13.14, Claude Desktop 0.10.x, nai-diffusion-4-5-full"
    validations:
      required: false
  - type: textarea
    id: logs
    attributes:
      label: Logs
      description: Relevant log output (stack traces, MCP trace). Redact secrets (tokens / passwords) before pasting.
      render: shell
    validations:
      required: false
