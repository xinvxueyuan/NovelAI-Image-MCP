# Insiders header, routing and audit

The insiders surface lets an HTTP client opt in to experimental behaviour and
declare *which* route, model, agent and session a request belongs to. This page
documents the header contract, what routing derives from it, the audit trail it
produces, and the boundaries of the feature as shipped.

Nothing here is active without the header: a request that does not send it
behaves exactly as it did before routing existed, with one deliberate exception
noted in [Backward compatibility](#backward-compatibility).

## Trust model

Routing headers are **client-supplied and therefore forgeable**. They are not an
authentication mechanism and must not be treated as an identity.

Treat the opt-in as a capability you grant to a caller that is already inside a
trust boundary. Run the server behind a gateway that authenticates callers (or
keep `MCP_HOST` on localhost) before relying on anything the header says. The
one place headers *do* participate in a security decision is
[route-bound tokens](#route-bound-tokens), and there a mismatch fails closed.

Route values are attacker-controlled strings that end up in filesystem paths and
log lines. Every route is therefore passed through a whitelist before use; see
[Route sanitisation](#route-sanitisation).

## The X-MCP-Insiders header

The header name defaults to `X-MCP-Insiders` and can be renamed with
`MCP_INSIDERS_HEADER`. Lookup is case-insensitive, because HTTP header names
are.

### Grammar

The value is a comma-separated list. Every problem is *reported* and ignored --
a typo can never break a request.

| Value | Effect |
|---|---|
| *(header absent)* | disabled |
| *(empty or whitespace)* | disabled |
| `false`, `0`, `off`, `no` | disabled |
| `true`, `1`, `on`, `yes` | enabled, every registered feature at its default |
| `model-routing=false` | enabled, `model-routing` forced off |
| `model-routing` | enabled, `model-routing` forced on (bare key) |
| `k=v, k2=v2` | enabled, each registered key overridden individually |

Additional rules:

- Key names are case-insensitive and treat `-` and `_` as the same character,
  so `Model_Routing` and `model-routing` address one feature.
- Keys that are not registered are collected into `unknown_keys` and ignored.
  A client can never activate a feature the server does not know about.
- An unparsable value (for example `model-routing=maybe`) is collected into
  `malformed` and that key is dropped.
- A header longer than 4096 characters disables the whole header and records
  `header-too-long` in `malformed`.

### Registered features

| Feature | Default | Effect when active |
|---|---|---|
| `model-routing` | on | the request's route, model, agent, client and session are resolved from the routing headers, and one audit record is appended per tool call |
| `experimental-tools` | on | insiders-tagged tools are listed and callable, and `director_tool` accepts its experimental `emotion` / `emotion_level` parameters |

"Default on" describes a feature's state **once the surface is enabled**. Sending
`X-MCP-Insiders: true` turns both on; sending no header at all turns nothing on.

Precedence, weakest first:

1. the registered default,
2. the per-request override in the header,
3. `MCP_INSIDERS_DISABLED_FEATURES` -- an operator kill switch that wins over
   anything a client sends.

A disabled header yields an empty feature set regardless of the other two.

## Declaring a route

When `model-routing` is active, routing reads a set of candidate headers. Each
group is an ordered list and the **first header carrying a non-empty value**
wins.

| Field | Default candidates | Environment override |
|---|---|---|
| model | `X-MCP-Model`, `X-MCP-Model-Name` | `MCP_MODEL_HEADERS` |
| agent | `X-MCP-Agent-ID`, `X-MCP-Agent`, `X-MCP-Agent-Source` | `MCP_AGENT_HEADERS` |
| client | `X-MCP-Client`, `X-MCP-Client-Session-Id` | `MCP_CLIENT_HEADERS` |
| session | the first client candidate whose name contains `session` | -- |

All three list variables are JSON, for example
`MCP_AGENT_HEADERS='["X-MCP-Agent-ID","X-MCP-Agent"]'`. A comma-separated
value is a settings error, not a list.

### Route priority

The route is the first of these that is available:

1. the first non-empty **agent** candidate,
2. the first non-empty **client** candidate,
3. the MCP client's advertised name (`client_info.name`),
4. `stdio` when the request did not arrive over HTTP, otherwise `unknown`.

### Route sanitisation

Whatever the route came from, it must survive a whitelist before it can be used
as a directory name or written to a log line:

- allowed characters: `A-Za-z0-9._-`
- length: 1 to 64 characters
- rejected: path separators (`/`, `\`), traversal (`.`, `..`), whitespace,
  non-ASCII text, the empty string, and anything longer than 64 characters

A rejected value becomes `unknown`. Note that only the *route* is sanitised
this way; the extracted `model`, `agent`, `client` and `session` fields keep
the raw value so an operator can see what a client actually sent.

## Per-route logging and the audit trail

### Log records

Every tool call emits one line to a logger named
`novelai_image_mcp.audit.<route>`, carrying the tool name, route, model, agent,
client, session, duration, outcome and the active features. Because the logger
name contains the route, an operator can route or filter per team with standard
logging configuration.

### Audit records

An audit record is appended to an append-only JSONL file **only while
`model-routing` is active**. The destination is `MCP_AUDIT_LOG_PATH` when set,
otherwise `audit.jsonl` inside `NOVELAI_OUTPUT_DIR`.

The file is opened with `O_APPEND` and each record is written with a single
`os.write`, so concurrent writers append whole lines instead of interleaving
halves of one. A crash mid-write can lose a line; it cannot corrupt a line that
was already written.

| Field | Content |
|---|---|
| `ts` | UTC timestamp, ISO-8601 |
| `route` | the sanitised route |
| `model` / `agent` / `client` / `session` | the extracted value, or `null` |
| `tool` | tool name |
| `duration_ms` | wall-clock duration, rounded to three decimals |
| `outcome` | `ok`, `error` or `rejected` |
| `features` | sorted names of the active features |
| `artifacts` | sorted `*.png` paths the result mentioned |
| `unknown_keys` | sorted unrecognised keys from the header |
| `malformed` | sorted unusable entries from the header |
| `headers` | the sanitised routing header snapshot, capped at 32 entries of at most 256 characters each |
| `arguments` | a summary of the call arguments (see below) |

### Redaction

The trail is designed so a payload cannot leak into it:

- Prompt-shaped arguments (`prompt`, `negative_prompt`, ...) become
  `{"length": n, "sha256": "<first 16 hex characters>"}`. The prompt text is
  never written.
- Image-shaped arguments (`image`, `mask`, `images`, `init_image`,
  `references`, `base64`) become the literal `[redacted image]`.
- **Any** string longer than 256 characters is digested rather than written, so
  a base64 blob cannot slip through under an unexpected argument name.
- Containers are reduced to their size; unknown objects to their type name.
- Credential-bearing headers -- `authorization`, `cookie`, `set-cookie`,
  `proxy-authorization`, and anything ending in `-token`, `-secret`,
  `-password`, `-passwd`, `-key` or `-credential(s)` -- are removed from the
  header snapshot before it is recorded, and are never logged.

### Failure behaviour

Auditing must never break the thing it observes. If the audit file cannot be
created or written, the failure is logged at `ERROR` and the tool call still
returns its normal result. There is no code path in which an audit problem
turns into a failed tool call.

## Route-scoped output

When routing is active **and** `MCP_ROUTE_SCOPED_OUTPUT` is true (the default),
generated images are written under a per-route subdirectory:

```text
<NOVELAI_OUTPUT_DIR>/<sanitised route>/<name>-<timestamp>-<hex>.png
```

The `novelai://outputs/{name}` resource resolves names in the same directory, so
a client reads back exactly what it wrote. The directory name comes from the
same whitelist described above, so a hostile route cannot escape the output
directory.

With routing off, or with `MCP_ROUTE_SCOPED_OUTPUT=false`, every path is the one
the server produced before routing existed.

## Route-bound tokens

`MCP_AUTH_TOKEN` keeps its original meaning: one static bearer token for the
HTTP transport, validated by FastMCP before any MCP request is served.

`MCP_ROUTE_TOKENS` adds *route-bound* tokens on top. It is a JSON object mapping
a route to its token:

```bash
MCP_AUTH_TOKEN=static-token
MCP_ROUTE_TOKENS='{"team-a":"token-for-team-a","team-b":"token-for-team-b"}'
```

A route token authenticates as its route, and is rejected when the same request
declares a *different* route through the routing headers. A mismatch makes the
verifier reject the request, which the bearer middleware turns into a `401` with
a `WWW-Authenticate` challenge -- not a `ToolError`. Both routes are logged at
`WARNING` so the rejection stays auditable.

Details worth knowing:

- A request with **no usable declared route** -- no routing header at all, or a
  value that sanitises to `unknown` -- is accepted and attributed to the token's
  own route. Only two *different*, both-present routes fail closed.
- The static token never takes part in route checking, so its semantics are
  unchanged whether or not route tokens are configured.
- An entry is skipped, with a warning, when it cannot be honoured: an empty
  token, a token equal to `MCP_AUTH_TOKEN` (the static token wins), a route name
  that does not pass the whitelist (that token is not registered at all, so it
  can never authenticate), or a token bound to two routes (the first route in
  sorted order wins).
- With neither setting configured, no auth middleware is installed and the
  endpoint behaves exactly as before.

## Backward compatibility

A request that does not send the insiders header sees today's server, with one
intentional exception:

- Tools, resources, prompts and schemas are unchanged.
- No tool is added or removed. No shipped tool carries the `insiders` tag, so
  the listing filter never hides anything from a client that has not opted in.
- Generated images keep the flat `NOVELAI_OUTPUT_DIR` layout.
- No audit file is written.
- `MCP_AUTH_TOKEN` behaves exactly as before.

:::{warning}
**`director_tool`'s `emotion` and `emotion_level` parameters are now gated.**
Passing either one without the `experimental-tools` opt-in fails with a
`ToolError`. This is a deliberate behaviour change and is recorded in the
CHANGELOG under `Changed`. A non-default `emotion_level` alone counts as
passing the parameter, so the default call shape is unaffected.
:::

## Extension points

- **Add a sibling feature.** Add one entry to `INSIDERS_FEATURES` in
  `apps/server/src/novelai_image_mcp/features.py` with its name,
  `default_enabled` and a one-line summary. The header parser, the middleware
  and every tool pick it up with no further change.
- **Gate a new tool.** Register it with `tags={"insiders"}`. The listing filter
  and the by-name rejection both follow from the tag. **Do not** add that tag to
  an existing tool: it would remove the tool from every client that does not
  send the header.
- **Gate a new parameter on an existing tool.** Read
  `features: frozenset[str] = Depends(get_effective_features)` and raise a
  `ToolError` from the body when `EXPERIMENTAL_TOOLS` is absent, the way
  `director_tool` does.

## v1 boundaries

- **Tool schemas are static.** FastMCP publishes a tool's parameter schema when
  the server starts, so a schema cannot vary per request. Experimental
  parameters therefore stay visible in the schema, and the opt-in is enforced in
  the tool body instead. A client that introspects the schema sees the parameter
  but cannot use it without the header.
- **Routing is per request, not per connection.** The header is read from the
  HTTP request that carries the tool call.
- **The header is not authentication.** See [Trust model](#trust-model).

## See also

- [HTTP transport](../transports/http.md)
- [Configuration](../configuration.md)
- [director_tool](../tools/director.md)
