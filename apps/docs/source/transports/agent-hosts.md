# Agent hosts

Copy-pasteable MCP configuration snippets for every major agent host. All
snippets use the standard stdio shape — `command` + `args` + `env` — because
`uvx` is a *command* (Astral's `uv` package runner), not a transport. The
MCP spec defines only two transports, `stdio` and `Streamable HTTP`; when
`command` is present, the host implicitly selects stdio.

## Summary

| Host | Config file | Format | Secret injection |
|---|---|---|---|
| [Claude Desktop](#claude-desktop) | `claude_desktop_config.json` | JSON | `env` literals, `${input:…}` |
| [Cline](#cline) | `cline_mcp_settings.json` / `~/.cline/mcp.json` | JSON | `env` literals |
| [Cursor](#cursor) | `mcp.json` (global or project) | JSON | `env` literals, `auth` (OAuth) |
| [Continue](#continue) | `config.yaml` / `config.json` | YAML or JSON | `env` literals, `${{ secrets.X }}` |
| [Windsurf](#windsurf) | `mcp_config.json` | JSON | `${env:VAR}`, `${file:/path}` |
| [Codex CLI](#codex-cli) | `config.toml` | TOML | `env_vars`, `bearer_token_env_var` |
| [Generic stdio](#generic-stdio) | (host-specific) | JSON | `env` literals |

## Claude Desktop

### Config file path

| OS | Path |
|---|---|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux (unofficial builds) | `~/.config/Claude/claude_desktop_config.json` |

The macOS path is also reachable via Settings → Developer → **Edit Config**,
which creates the file if absent.

### Snippet

```json
{
  "mcpServers": {
    "novelai-image": {
      "command": "uvx",
      "args": ["novelai-image-mcp", "serve"],
      "env": { "NOVELAI_TOKEN": "${input:novelai_token}" }
    }
  }
}
```

For a one-off test, inline a literal token (`"pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"`)
instead of the `${input:…}` reference.

### Secret injection

Claude Desktop reads secrets from the `env` object as literal strings, or
resolves `${input:…}` references through its own host-managed secret UI.
There is no `${env:VAR}` shell interpolation in the official schema.

### Host-specific fields

Claude Desktop uses the bare MCP-spec stdio shape — no `type`, no `disabled`,
no `autoApprove`. Remote servers use `url` + `headers` instead of
`command` + `args`.

### References

- [docs.open.cx/mcp/clients/claude-desktop](https://docs.open.cx/mcp/clients/claude-desktop)
- [github.com/mcp-finder/claude-mcp-config-examples](https://github.com/mcp-finder/claude-mcp-config-examples)
- [modelcontextprotocol.io/docs/develop/connect-local-servers](https://modelcontextprotocol.io/docs/develop/connect-local-servers)

## Cline

### Config file path

| Scope | Path |
|---|---|
| VS Code extension | Open via MCP Servers icon → Configure tab → **Configure MCP Servers** |
| Cline CLI | `~/.cline/mcp.json` |

The on-disk location of the extension's settings file has moved between
versions; the **Configure MCP Servers** button is the reliable route.
Older installs kept it under VS Code's
`globalStorage/saoudrizwan.claude-dev/settings/` — ⚠ unverified whether
the current extension version still writes there.

### Snippet

```json
{
  "mcpServers": {
    "novelai-image": {
      "command": "uvx",
      "args": ["novelai-image-mcp", "serve"],
      "env": { "NOVELAI_TOKEN": "pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### Secret injection

Cline reads secrets as literal strings inside the `env` object (or `headers`
for remote servers). No `${env:VAR}` interpolation is documented in the
official schema.

### Host-specific fields

- `disabled` (boolean) — toggle a server without deleting its config.
- `autoApprove` (string array) — per-server tool allow-list. **Not**
  `alwaysAllow` (that is the Roo Code fork spelling).
- `type` for remote servers — accepts `streamableHttp` (camelCase) or `sse`;
  omitting `type` defaults to legacy `sse`, so set it explicitly for the
  recommended transport.

### References

- [docs.cline.bot/mcp/mcp-overview](https://docs.cline.bot/mcp/mcp-overview)
- [policylayer.com/integrations/cline](https://policylayer.com/integrations/cline)

## Cursor

### Config file path

| Scope | Path |
|---|---|
| Global | `~/.cursor/mcp.json` (macOS/Linux); `%USERPROFILE%\.cursor\mcp.json` (Windows) |
| Project-specific | `.cursor/mcp.json` in the project root |

Project-level config is merged with the global file (⚠ unverified merge
semantics against official docs).

### Snippet

```json
{
  "mcpServers": {
    "novelai-image": {
      "command": "uvx",
      "args": ["novelai-image-mcp", "serve"],
      "env": { "NOVELAI_TOKEN": "pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" }
    }
  }
}
```

### Secret injection

stdio secrets are literal strings in `env`; remote-server secrets go in
`headers` (e.g. `"Authorization": "Bearer …"`) or are obtained via OAuth
through the `auth` object. No `${env:VAR}` substitution is documented in
the JSON schema.

### Host-specific fields

- `auth` — object with `CLIENT_ID` (required), `CLIENT_SECRET`, `scopes`
  for static-OAuth remote servers.
- `envFile` — referenced in some third-party guides for loading env vars
  from a file; ⚠ unverified against official docs.
- No `type`/`transport` field — Cursor auto-detects the transport from the
  field shape (`command` → stdio; `url` → SSE or Streamable HTTP).

### References

- [cursor.com/docs/mcp](https://cursor.com/docs/mcp)

## Continue

### Config file path

| OS | Path |
|---|---|
| macOS / Linux | `~/.continue/config.yaml` (or `config.json`) |
| Windows | `%USERPROFILE%\.continue\config.yaml` (or `config.json`) |
| Project-scoped | `.continue/config.yaml` in the workspace |
| Standalone MCP blocks | `.continue/mcpServers/<name>.yaml` or `.json` |

### Snippet

```yaml
mcpServers:
  - name: novelai-image
    command: uvx
    args:
      - "novelai-image-mcp"
      - "serve"
    env:
      NOVELAI_TOKEN: "pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

:::{warning}
Continue's `mcpServers` is an **array** of objects with an explicit `name`
field — not an object keyed by server name. Copying a Claude Desktop /
Cursor / Cline JSON config verbatim will not work. (Continue does accept
Claude-Desktop-shaped JSON dropped into `.continue/mcpServers/` for
migration.)
:::

### Secret injection

Three mechanisms: literal values in `env`; `${{ secrets.NAME }}`
placeholders that pull from Continue Mission Control's hosted secret
store; and OAuth (Continue opens a browser tab for the user to authorize).

### Host-specific fields

- `name` (required) — display name for the server (replaces the object-key
  convention used by other hosts).
- `type` — `stdio` (default), `sse`, or `streamable-http` (kebab-case, in
  contrast to Cline's `streamableHttp` camelCase).
- `${{ secrets.X }}` substitution in `env` / `args`.

:::{note}
MCP only works in Continue's **agent mode** — not in chat or autocomplete
modes.
:::

### References

- [docs.continue.dev/customize/deep-dives/mcp](https://docs.continue.dev/customize/deep-dives/mcp)
- [docs.continue.dev/reference](https://docs.continue.dev/reference)

## Windsurf

### Config file path

| OS | Path |
|---|---|
| macOS / Linux | `~/.codeium/windsurf/mcp_config.json` |
| Windows | `%USERPROFILE%\.codeium\windsurf\mcp_config.json` |

⚠ **Discrepancy:** the official Windsurf docs at
[docs.windsurf.com/windsurf/cascade/mcp](https://docs.windsurf.com/windsurf/cascade/mcp)
still show `~/.codeium/mcp_config.json` *without* the `windsurf/` segment.
Six independent third-party sources (open.cx, policylayer, quadratichq,
toolcog, the GitHub MCP Server install guide, and the mcp.directory
Windsurf validator) all reference the `windsurf/` subdirectory — the
official docs page appears to be stale on this point. Configuration is
global-only; there is no per-project file.

### Snippet

```json
{
  "mcpServers": {
    "novelai-image": {
      "command": "uvx",
      "args": ["novelai-image-mcp", "serve"],
      "env": { "NOVELAI_TOKEN": "${env:NOVELAI_TOKEN}" }
    }
  }
}
```

Export `NOVELAI_TOKEN` in your shell before launching Windsurf — the
`${env:VAR}` form keeps the literal token out of the config file.

### Secret injection

Three documented mechanisms: literal strings in `env`/`headers`;
`${env:VAR}` interpolation that pulls from the user's shell environment;
and `${file:/absolute/path}` that reads the first line of a file. All
three work in `command`, `args`, `env`, `serverUrl`, `url`, and `headers`.

### Host-specific fields

- `serverUrl` — Windsurf-specific alias for `url` (plain `url` is also
  accepted).
- `${env:VAR}` and `${file:/path}` interpolation in any string field.
- `disabledTools` — array of tool names to suppress per server
  (⚠ unverified against official docs).
- No `type` field — transport is auto-detected.

:::{warning}
Windsurf reads `mcp_config.json` only at startup. Editing the file
without restarting Cascade is the most common silent failure.
:::

### References

- [docs.windsurf.com/windsurf/cascade/mcp](https://docs.windsurf.com/windsurf/cascade/mcp)
- [docs.codeium.com/plugins/cascade/mcp](https://docs.codeium.com/plugins/cascade/mcp)

## Codex CLI

### Config file path

| Scope | Path |
|---|---|
| Global | `$CODEX_HOME/config.toml` (defaults to `~/.codex/config.toml`; on Windows `%USERPROFILE%\.codex\config.toml`) |
| Project-scoped | `.codex/config.toml` (only loaded for trusted projects) |

### Snippet

```toml
[mcp_servers.novelai-image]
command = "uvx"
args = ["novelai-image-mcp", "serve"]
env_vars = ["NOVELAI_TOKEN"]
startup_timeout_sec = 10.0

[mcp_servers.novelai-image.env]
NOVELAI_OUTPUT_DIR = "/tmp/novelai-outputs"
```

Export `NOVELAI_TOKEN` in your shell (e.g. in `~/.zshrc` or PowerShell
profile). `env_vars = ["NOVELAI_TOKEN"]` forwards it from the parent
process at runtime, keeping the literal token out of the config file.

:::{note}
TOML ordering matters: `command`, `args`, `env_vars`, `startup_timeout_sec`
must appear *above* the `[mcp_servers.<name>.env]` sub-table header —
anything below belongs to `env`. This is the only host in this list that
uses TOML; copying a JSON config from Claude Desktop / Cursor / Cline
will not work.
:::

### Secret injection

Codex is the most security-conscious of the seven hosts — tokens are
never meant to be literal in the config file. Use `env_vars` to forward
named env vars from the parent process (supports `source = "local"` or
`source = "remote"`); for HTTP servers use `bearer_token_env_var` to
name an env var Codex reads at runtime and inject as
`Authorization: Bearer <token>`. OAuth is also supported via
`codex mcp login`.

### Host-specific fields

- `env_vars` — list of variable names forwarded from the parent
  environment (strings or `{ name = "X", source = "local"|"remote" }`).
- `bearer_token_env_var` — names the env var holding the bearer token for
  HTTP servers.
- `env_http_headers` — populates HTTP headers from env vars at runtime.
- `enabled_tools` / `disabled_tools` — per-server tool allow/deny lists.
- `startup_timeout_sec` (default `10.0`) / `tool_timeout_sec` (default `60.0`).
- `experimental_environment = "remote"` — routes stdio server launch
  through a remote executor.
- Top-level `mcp_oauth_credentials_store` (`auto` | `file` | `keyring`).

### References

- [developers.openai.com/codex/mcp](https://developers.openai.com/codex/mcp)
- [developers.openai.com/codex/config-reference](https://developers.openai.com/codex/config-reference)
- [github.com/openai/codex](https://github.com/openai/codex)

## Generic stdio

The MCP specification defines only the wire protocol and the two
transports — it does not standardize a client config file format. The
de-facto "generic stdio" shape below is the one Claude Desktop, Cursor,
and Windsurf all accept as-is (Cline accepts it with optional extensions;
Continue and Codex CLI do not — see their sections above).

### Config file path

Host-specific — see the per-host sections.

### Snippet

```json
{
  "mcpServers": {
    "novelai-image": {
      "command": "uvx",
      "args": ["novelai-image-mcp", "serve"],
      "env": { "NOVELAI_TOKEN": "pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" }
    }
  }
}
```

### Secret injection

Bare `env` literals. Upgrade to a host-specific mechanism (`${input:…}`
in Claude Desktop, `${env:VAR}` in Windsurf, `env_vars` in Codex CLI)
where available.

### Host-specific fields

None — this is the canonical MCP-spec stdio shape.

### References

- [modelcontextprotocol.io/docs/develop/connect-local-servers](https://modelcontextprotocol.io/docs/develop/connect-local-servers)

## Common pitfalls

- **Putting `uvx` in a `type`/`transport` field.** `uvx` is a command —
  it belongs in `command`. The only MCP-spec transports are `stdio` and
  `Streamable HTTP` (plus legacy `sse`); when `command` is present, the
  host implicitly selects stdio.
- **Copying a Claude Desktop JSON config to Codex CLI.** Codex reads
  `~/.codex/config.toml` (TOML, not JSON) with `[mcp_servers.<name>]`
  tables; a JSON config will not parse.
- **Copying an object-keyed config to Continue.** Continue reads
  `mcpServers` as an array of objects with an explicit `name` field —
  not as an object keyed by server name.
- **Using `alwaysAllow` instead of `autoApprove` in Cline.** `alwaysAllow`
  is the Roo Code fork spelling and appears in outdated validators; the
  current authoritative name is `autoApprove`.
- **Mixing up `streamableHttp` vs `streamable-http`.** Cline uses
  camelCase (`streamableHttp`); Continue uses kebab-case
  (`streamable-http`).
- **Forgetting to restart the host after editing the config file.**
  Claude Desktop and Windsurf only read the config at launch — closing
  the window is not enough (macOS: `Cmd+Q`; Windsurf: full Cascade
  restart).

## Behind a corporate proxy

If you are behind a corporate or regional firewall (for example, mainland
China without direct access to `novelai.net`), add the standard proxy env
vars to the `env` block:

```json
"env": {
  "NOVELAI_TOKEN": "pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "HTTPS_PROXY": "http://127.0.0.1:10808",
  "HTTP_PROXY": "http://127.0.0.1:10808",
  "NO_PROXY": "localhost,127.0.0.1"
}
```

The server uses `httpx`, which respects the standard `HTTP_PROXY` /
`HTTPS_PROXY` / `NO_PROXY` environment variables. Without these, any tool
that calls the NovelAI API (`get_subscription`, `generate_image`,
`upscale_image`, …) will fail with a `NovelAI request transport failed`
error.

## See also

- [stdio transport](stdio.md)
- [streamable-http transport](http.md)
- [Configuration](../configuration.md)
