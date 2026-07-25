# Account tools

Three tools that read account state and estimate costs without making
image-generation API calls. They're safe to call frequently — they don't
consume Anlas.

---

## `get_subscription`

Return the account's subscription details and Anlas balance.

### Parameters

None.

### Returns

`dict` mirroring NovelAI's `/user/subscription` response:

| Key | Type | Notes |
|---|---|---|
| `tier` | `int` | 0 = free, 1 = starter, 2 = ..., 3 = Opus. |
| `active` | `bool` | Whether the subscription is currently active. |
| `trainingStepsLeft` | `dict` | `{fixed: int, perStepUsage: bool}` — remaining Anlas-equivalent steps. |
| `fixedTrainingStepsLeft` | `int` | Anlas-equivalent steps that don't count per-use. |
| `perStepUsage` | `bool` | Whether steps are deducted per generation. |
| `subscriptionId` | `str` | Internal subscription id. |

### Example

```python
sub = await ctx.session.call_tool("get_subscription", {})
print(sub["tier"], sub["trainingStepsLeft"]["fixed"])
```

### CLI

```bash
uv run python -m novelai_image_mcp info
```

---

## `get_user_data`

Return the authenticated account's user data. Useful to confirm which
account the server is authenticated as before issuing generation commands.

### Parameters

None.

### Returns

`dict` with:

| Key | Type | Notes |
|---|---|---|
| `email` | `str` | The account's registered email. |
| `accountChain` | `str` | Registration source (e.g. `google`, `x`, `direct`). |
| `priority` | `int` | Internal epoch. |

### Example

```python
user = await ctx.session.call_tool("get_user_data", {})
print(f"Authenticated as: {user['email']}")
```

---

## `estimate_anlas_cost`

Estimate the Anlas cost of a generation **without** calling the API.
Mirrors NovelAI's public web-client cost formula.

### Parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `width` | `int` | *required* | Image width (px). |
| `height` | `int` | *required* | Image height (px). |
| `steps` | `int` | *required* | Sampler steps. |
| `n_samples` | `int` | `1` | Number of images. |
| `model` | `str` | `"nai-diffusion-4-5-full"` | Target model. |
| `action` | `str` | `"generate"` | `generate`, `img2img`, or `infill` (inpaint). |
| `strength` | `float \| None` | `None` | Required for `img2img` / `infill` (0.01–0.99). |
| `smea` | `bool \| None` | `None` | SMEA enabled. |
| `smea_dynamic` | `bool \| None` | `None` | Dynamic SMEA enabled. |
| `auto_smea` | `bool` | `False` | Auto SMEA. |
| `opus` | `bool` | `False` | Apply Opus-tier free-sample rules. |

### Returns

`dict` with:

| Key | Type | Notes |
|---|---|---|
| `anlas` | `int` | Estimated Anlas cost. |
| `opus_free_sample` | `bool` | `True` if Opus free-sample applies (no Anlas charged). |

### Example

```python
cost = await ctx.session.call_tool("estimate_anlas_cost", {
    "width": 832,
    "height": 1216,
    "steps": 28,
    "n_samples": 4,
    "model": "nai-diffusion-4-5-full",
})
# cost: {"anlas": 20, "opus_free_sample": False}
```

### Cost table (typical)

For reference — single sample, Opus tier, `nai-diffusion-4-5-full`, 28 steps:

| Resolution | Anlas (txt2img) | Anlas (img2img, strength=0.5) |
|---|---|---|
| 512 × 768 | 2 | 1 |
| 832 × 1216 | 5 | 3 |
| 1024 × 1024 | 5 | 3 |
| 1536 × 1024 | 7 | 4 |

:::{note}
Opus-tier subscribers get **free samples** for small generations (≤1024²,
≤28 steps). Set `opus=True` to estimate with free samples applied.
:::

## See also

- [`estimate_anlas_cost` API reference](../api/tools.md)
- [NovelAI Anlas documentation](https://docs.novelai.net/image/anlas.html)
- [Configuration](../configuration.md) — set generation defaults to control cost
