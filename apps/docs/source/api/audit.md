# `audit`

Append-only JSONL audit trail for routed tool calls: `build_record`,
`append_record`, `artifact_paths` and `resolve_audit_path`, plus the
redaction helpers that keep prompts, image payloads and credentials out of the
trail.

:::{admonition} See also
:class: tip

[Insiders header, routing and audit](../development/insiders-and-routing.md)
for when a record is written, and
[Configuration](../configuration.md) for `MCP_AUDIT_LOG_PATH`.
:::

```{eval-rst}
.. automodule:: novelai_image_mcp.audit
   :members:
   :undoc-members:
   :show-inheritance:
```

## When a record is written

The audit trail is part of the insiders surface: `ToolCallLoggingMiddleware`
appends **one record per tool call, and only while `model-routing` is
active**. A request that does not send the opt-in header writes nothing.

`resolve_audit_path` picks the destination — an explicit
`MCP_AUDIT_LOG_PATH` wins, otherwise `audit.jsonl` inside
`NOVELAI_OUTPUT_DIR`.

## Record fields

`build_record` emits one flat, JSON-serialisable object per call:

| Field | Content |
|---|---|
| `ts` | UTC timestamp, ISO-8601. |
| `route` | The sanitised route. |
| `model` / `agent` / `client` / `session` | The extracted routing value, or `null`. |
| `tool` | Tool name. |
| `duration_ms` | Wall-clock duration, rounded to three decimals. |
| `outcome` | `ok`, `error` or `rejected`. |
| `features` | Sorted names of the active insiders features. |
| `artifacts` | Sorted `*.png` paths the result mentioned. |
| `unknown_keys` | Sorted unrecognised keys from the insiders header. |
| `malformed` | Sorted unusable entries from the insiders header. |
| `headers` | Sanitised routing header snapshot, capped at `MAX_RECORDED_HEADERS` (32) entries of at most `MAX_RECORDED_HEADER_LENGTH` (256) characters, in lexicographic order of the lower-cased name. |
| `arguments` | Summarised call arguments — see below. |

`features`, `artifacts`, `unknown_keys` and `malformed` are sorted so two
records describing the same state are byte-identical.

## Redaction

`summarise_arguments` reduces every argument before it can reach the file:

- **Prompt-shaped** arguments (`prompt`, `prompts`, `negative_prompt`,
  `negativeprompt`) become `{"length": n, "sha256": "<first 16 hex
  characters>"}` via `digest_text`. The prompt text is never written.
- **Image-shaped** arguments (`image`, `images`, `init_image`, `mask`,
  `reference`, `references`, `base64`) become the literal
  `[redacted image]`.
- **Any** string longer than `MAX_ARGUMENT_LENGTH` (256) characters is
  digested rather than written, so a base64 blob cannot slip through under an
  unexpected argument name.
- Mappings are reduced to `{"keys": n}`; lists, tuples and sets to
  `{"items": n}`; any other object to its type name. `None`, booleans, ints
  and floats are recorded as they are.

Credential-bearing headers are removed upstream by
`routing._recorded`, so the snapshot this module caps never contains
`authorization`, `cookie`, `set-cookie`, `proxy-authorization` or any
`*-token` / `*-secret` / `*-password` / `*-key` / `*-credential`
header in the first place.

## Concurrency and durability

`append_record` serialises the record first, then writes it with **exactly
one `os.write`** on a descriptor opened with `O_APPEND` (mode `0o600`,
creating the parent directory when needed). Concurrent writers therefore append
whole lines instead of interleaving halves of one: a crash mid-write can lose a
line, but it cannot corrupt a line that was already written.

## Failure behaviour

Observability never becomes a dependency of the business path.
`append_record` catches its own `OSError` / `TypeError` / `ValueError`, logs
the failure with `logger.error`, and returns `False` — it never raises, so
there is no code path in which an unwritable audit file turns into a failed
tool call.

## See also

- [Insiders header, routing and audit](../development/insiders-and-routing.md) — the header grammar and route resolution
- [`middleware`](middleware.md) — the caller that appends the records
- [`routing`](routing.md) — the header snapshot this module caps
