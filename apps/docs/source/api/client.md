# `novelai_image_mcp.nai` — NovelAI HTTP client

The `nai/` subpackage is the NovelAI HTTP client. It is **MCP-agnostic** —
it can be used standalone from any async Python code, independent of the
MCP server.

## Submodules

### `novelai_image_mcp.nai.client`

The high-level async client. Wraps the wire-format encoder
(`payload.build_generation_payload`) and response decoder
(`response.parse_messagepack_images`) over a shared
`httpx.AsyncClient`.

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.client
   :members:
   :undoc-members:
   :show-inheritance:
```

### `novelai_image_mcp.nai.constants`

Enums for the NovelAI API surface: `Action`, `Model`, `Sampler`,
`DirectorTool`, `Emotion`, `EmotionLevel`, `ControlNetModel`, `Endpoint`,
`NoiseSchedule`. Plus the predicates `is_v4_model`, `is_v5_model`,
`supports_vibe`, and `is_inpaint_model`.

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.constants
   :members:
   :undoc-members:
   :show-inheritance:
```

### `novelai_image_mcp.nai.models`

Pydantic models for the wire format: `GenerationRequest`,
`CharacterPrompt`, `NovelAIGenerationPlan`.

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.models
   :members:
   :undoc-members:
   :show-inheritance:
```

### `novelai_image_mcp.nai.auth`

Argon2id access-key derivation + per-request tracking headers.

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.auth
   :members:
   :undoc-members:
   :show-inheritance:
```

### `novelai_image_mcp.nai.payload`

`build_generation_payload` — wire-format encoder (MessagePack-compatible).

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.payload
   :members:
   :undoc-members:
   :show-inheritance:
```

### `novelai_image_mcp.nai.response`

Response parsing: `NovelAIImage`, `parse_messagepack_images`,
`parse_zip_images`, `check_status`, `GenerationEvent`.

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.response
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: NovelAIProviderError, NovelAIResponseError, NovelAIAuthenticationError, NovelAIConcurrencyError, NovelAIInsufficientCreditsError, NovelAIValidationError
```

:::{note}
The exception classes listed above are imported into ``response`` for
raising in ``check_status``; they are documented under their defining
module, `novelai_image_mcp.nai.exceptions` (see the next subsection).
:::

### `novelai_image_mcp.nai.exceptions`

Domain exception hierarchy:

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.exceptions
   :members:
   :undoc-members:
   :show-inheritance:
```

### `novelai_image_mcp.nai.service`

`create_novelai_client` factory + `NovelAIConfigLike` protocol. The factory
takes a settings-like object and an `httpx.AsyncClient`, returns a fully
wired `NovelAIClient`.

```{eval-rst}
.. automodule:: novelai_image_mcp.nai.service
   :members:
   :undoc-members:
   :show-inheritance:
```

## Official error codes

Every NovelAI error raised by this client carries the error ``code`` (the
HTTP status, or the API's own stream code) and, where documented, NovelAI's
official explanation. Both are appended to the message and exposed as
attributes on the exception:

| Code | Meaning (official) |
|---|---|
| `400` | Invalid request (validation failed) |
| `401` | Authentication failed |
| `402` | Active subscription or Anlas required |
| `409` | Request conflict |
| `429` | Rate limit / concurrency limit |
| `5xx` | NovelAI upstream error |

All exceptions derive from ``NovelAIError`` and expose ``.code`` /
``.explanation`` (both ``None`` for transport, timeout, and local validation
failures that carry no server code). See the ``novelai_image_mcp.nai.errors``
module for the parsing helpers.

## See also

- [Architecture → `NovelAIClient`](../development/architecture.md#novelaiclient-the-nai-subpackage)
- [Source on GitHub](https://github.com/xinvxueyuan/NovelAI-Image-MCP/tree/main/apps/server/src/novelai_image_mcp/nai)
